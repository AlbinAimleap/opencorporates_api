from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
from typing import Optional
import uuid
import json
import secrets

from opencorporates_api.opencorporates import search
from opencorporates_api.tasks import redis_client, Task, User

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()


class Company(BaseModel):
    company_link: Optional[str] = None
    company_name: Optional[str] = None
    company_number: Optional[str] = None
    status: Optional[str] = None
    incorporation_date: Optional[str] = None
    company_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    registered_address: Optional[str] = None
    agent_name: Optional[str] = None
    agent_address: Optional[str] = None
    directors_officers: Optional[str] = None
    dissolution_date: Optional[str] = None
    previous_names: Optional[str] = None
    alternative_names: Optional[str] = None
    branch: Optional[str] = None
    business_classification_text: Optional[str] = None
    inactive_directors_officers: Optional[str] = None
    industry_codes: Optional[str] = None
    business_number: Optional[str] = None
    governing_legislation: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class UserCreate(BaseModel):
    username: str

async def get_api_key(api_key_header: str = Security(api_key_header), apikey: Optional[str] = None):
    api_key = api_key_header or apikey
    if not api_key:
        raise HTTPException(status_code=403, detail="API Key is required")
    
    user_key = redis_client.get(f"user:api_key:{api_key}")
    if not user_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    user_data = redis_client.get(user_key)
    if not user_data:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.post("/register-obfuscated-pathparameter-internal-use-only", response_model=ApiResponse)
async def register_user(user: UserCreate):
    user_key = f"user:{user.username}"
    if redis_client.exists(user_key):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    api_key = secrets.token_urlsafe(32)
    new_user = User(
        id=str(secrets.token_hex(16)),
        username=user.username,
        api_key=api_key
    )
    redis_client.set(user_key, new_user.to_dict())
    redis_client.set(f"user:api_key:{api_key}", user_key)
    return ApiResponse(success=True, message="User registered successfully", data={"api_key": api_key})

@app.get("/search/stream")
async def get_companies_stream(
    query: str,
    jurisdiction: Optional[str] = None,
    use_cache: bool = True,
    api_key: str = Depends(get_api_key)
):
    if use_cache:
        task_key = f"task:{query}:{jurisdiction}"
        task_data = redis_client.get(task_key)
        if task_data:
            task = Task.from_dict(task_data)
            if task.status == "completed" and task.output:
                async def cached_streamer():
                    companies = json.loads(task.output)
                    for company in companies:
                        yield json.dumps({"success": True, "message": "Data retrieved from cache", "data": company}) + "\n"
                return StreamingResponse(cached_streamer(), media_type="application/x-ndjson")
    
    async def streamer():
        async for companies in search(query, jurisdiction):
            for company in companies:
                yield json.dumps({"success": True, "message": "Data retrieved successfully", "data": company}) + "\n"
    return StreamingResponse(streamer(), media_type="application/x-ndjson")

@app.get("/search", response_model=ApiResponse)
async def get_companies(
    query: str,
    jurisdiction: Optional[str] = None,
    use_cache: bool = True,
    api_key: str = Depends(get_api_key)
):
    if use_cache:
        task_key = f"task:{query}:{jurisdiction}"
        task_data = redis_client.get(task_key)
        if task_data:
            task = Task.from_dict(task_data)
            if task.status == "completed" and task.output:
                result = json.loads(task.output)
                return ApiResponse(success=True, message="Data retrieved from cache", data={"companies": result})
    
    result = await collect_results(query, jurisdiction)
    
    if use_cache:
        task = Task(
            id=str(uuid.uuid4()),
            status="completed",
            query=query,
            jurisdiction=jurisdiction,
            output=json.dumps(result)
        )
        redis_client.set(f"task:{task.id}", task.to_dict())
        redis_client.set(f"task:{query}:{jurisdiction}", task.to_dict())
    
    return ApiResponse(success=True, message="Data retrieved successfully", data={"companies": result})

async def process_scraping_task(task_id: str, query: str, jurisdiction: Optional[str] = None):
    task_key = f"task:{task_id}"
    task_data = redis_client.get(task_key)
    if task_data:
        task = Task.from_dict(task_data)
        task.status = "processing"
        task.query = query
        task.jurisdiction = jurisdiction
        redis_client.set(task_key, task.to_dict())
        result = await collect_results(query, jurisdiction)
        task.output = json.dumps(result)
        task.status = "completed"
        redis_client.set(task_key, task.to_dict())
        redis_client.set(f"task:{query}:{jurisdiction}", task.to_dict())

async def collect_results(query: str, jurisdiction: Optional[str] = None):
    results = []
    async for companies in search(query, jurisdiction):
        results.extend(companies)
    return results

@app.get("/queue", response_model=ApiResponse)
async def queue_scraping(
    query: str,
    jurisdiction: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    use_cache: bool = True,
    api_key: str = Depends(get_api_key)
):
    if use_cache:
        task_key = f"task:{query}:{jurisdiction}"
        task_data = redis_client.get(task_key)
        if task_data:
            task = Task.from_dict(task_data)
            if task.status == "completed" and task.output:
                result = json.loads(task.output)
                return ApiResponse(success=True, message="Data retrieved from cache", data={"companies": result})
    
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, status="queued", query=query, jurisdiction=jurisdiction)
    redis_client.set(f"task:{task_id}", task.to_dict())

    background_tasks.add_task(process_scraping_task, task_id, query, jurisdiction)
    return ApiResponse(success=True, message="Task queued successfully", data={"task_id": task_id})

@app.get("/tasks", response_model=ApiResponse)
async def get_tasks(api_key: str = Depends(get_api_key)):
    tasks = []
    for key in redis_client.scan_iter("task:*"):
        if ":" not in key[5:]:  # Only get task IDs, not query-based keys
            task_data = redis_client.get(key)
            if task_data:
                task = Task.from_dict(task_data)
                tasks.append({"task_id": task.id, "status": task.status})
    return ApiResponse(
        success=True,
        message="Tasks retrieved successfully",
        data={"tasks": tasks}
    )

@app.get("/task/{task_id}/delete", response_model=ApiResponse)
async def delete_task(task_id: str, api_key: str = Depends(get_api_key)):
    task_key = f"task:{task_id}"
    if redis_client.exists(task_key):
        task_data = redis_client.get(task_key)
        task = Task.from_dict(task_data)
        redis_client.delete(task_key)
        redis_client.delete(f"task:{task.query}:{task.jurisdiction}")
        return ApiResponse(success=True, message="Task deleted successfully")
    return ApiResponse(success=False, message="Task not found")

@app.get("/delete", response_model=ApiResponse)
async def delete_all_tasks(api_key: str = Depends(get_api_key)):
    for key in redis_client.scan_iter("task:*"):
        redis_client.delete(key)
    return ApiResponse(success=True, message="All tasks deleted successfully")

@app.get("/task/{task_id}", response_model=ApiResponse)
async def get_task(task_id: str, api_key: str = Depends(get_api_key)):
    task_key = f"task:{task_id}"
    task_data = redis_client.get(task_key)
    if task_data:
        task = Task.from_dict(task_data)
        output = json.loads(task.output) if task.output else None
        return ApiResponse(
            success=True,
            message="Task retrieved successfully",
            data={"task_id": task_id, "status": task.status, "output": output}
        )
    return ApiResponse(success=False, message="Task not found")