from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from opencorporates_api.opencorporates import search
from opencorporates_api.tasks import SessionLocal, Task

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

@app.get("/search/stream")
async def get_companies_stream(query: str, jurisdiction: Optional[str] = None):
    session = SessionLocal()
    existing_task = session.query(Task).filter(
        Task.query == query,
        Task.jurisdiction == jurisdiction,
        Task.status == "completed"
    ).first()
    
    if existing_task and existing_task.output:
        async def cached_streamer():
            companies = json.loads(existing_task.output)
            for company in companies:
                yield json.dumps({"success": True, "message": "Data retrieved from cache", "data": company}) + "\n"
        session.close()
        return StreamingResponse(cached_streamer(), media_type="application/x-ndjson")
    
    async def streamer():
        async for companies in search(query, jurisdiction):
            for company in companies:
                yield json.dumps({"success": True, "message": "Data retrieved successfully", "data": company}) + "\n"
    session.close()
    return StreamingResponse(streamer(), media_type="application/x-ndjson")

@app.get("/search", response_model=ApiResponse)
async def get_companies(query: str, jurisdiction: Optional[str] = None):
    session = SessionLocal()
    existing_task = session.query(Task).filter(
        Task.query == query,
        Task.jurisdiction == jurisdiction,
        Task.status == "completed"
    ).first()
    
    if existing_task and existing_task.output:
        result = json.loads(existing_task.output)
        session.close()
        return ApiResponse(success=True, message="Data retrieved from cache", data={"companies": result})
    
    result = await collect_results(query, jurisdiction)
    
    # Save the results to database
    task = Task(
        id=str(uuid.uuid4()),
        status="completed",
        query=query,
        jurisdiction=jurisdiction,
        output=json.dumps(result)
    )
    session.add(task)
    session.commit()
    session.close()
    
    return ApiResponse(success=True, message="Data retrieved successfully", data={"companies": result})

async def process_scraping_task(task_id: str, query: str, jurisdiction: Optional[str] = None):
    session = SessionLocal()
    task = session.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = "processing"
        task.query = query
        task.jurisdiction = jurisdiction
        session.commit()
        result = await collect_results(query, jurisdiction)
        task.output = json.dumps(result)
        task.status = "completed"
        session.commit()
    session.close()

async def collect_results(query: str, jurisdiction: Optional[str] = None):
    results = []
    async for companies in search(query, jurisdiction):
        results.extend(companies)
    return results

@app.get("/queue", response_model=ApiResponse)
async def queue_scraping(query: str, jurisdiction: Optional[str] = None, background_tasks: BackgroundTasks = None):
    session = SessionLocal()
    
    # Check if we already have results for this query
    existing_task = session.query(Task).filter(
        Task.query == query,
        Task.jurisdiction == jurisdiction,
        Task.status == "completed"
    ).first()
    
    if existing_task and existing_task.output:
        result = json.loads(existing_task.output)
        session.close()
        return ApiResponse(success=True, message="Data retrieved from cache", data={"companies": result})
    
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, status="queued", query=query, jurisdiction=jurisdiction)
    session.add(task)
    session.commit()
    session.close()

    background_tasks.add_task(process_scraping_task, task_id, query, jurisdiction)
    return ApiResponse(success=True, message="Task queued successfully", data={"task_id": task_id})

@app.get("/tasks", response_model=ApiResponse)
async def get_tasks():
    session = SessionLocal()
    tasks = session.query(Task).all()
    session.close()
    return ApiResponse(
        success=True,
        message="Tasks retrieved successfully",
        data={"tasks": [{"task_id": task.id, "status": task.status} for task in tasks]}
    )

@app.get("/task/{task_id}/delete", response_model=ApiResponse)
async def delete_task(task_id: str):
    session = SessionLocal()
    task = session.query(Task).filter(Task.id == task_id).first()
    if task:
        session.delete(task)
        session.commit()
        session.close()
        return ApiResponse(success=True, message="Task deleted successfully")
    session.close()
    return ApiResponse(success=False, message="Task not found")

@app.get("/delete", response_model=ApiResponse)
async def delete_all_tasks():
    session = SessionLocal()
    tasks = session.query(Task).all()
    for task in tasks:
        session.delete(task)
    session.commit()
    session.close()
    return ApiResponse(success=True, message="All tasks deleted successfully")

@app.get("/task/{task_id}", response_model=ApiResponse)
async def get_task(task_id: str):
    session = SessionLocal()
    task = session.query(Task).filter(Task.id == task_id).first()
    session.close()
    if task:
        output = json.loads(task.output) if task.output else None
        return ApiResponse(
            success=True,
            message="Task retrieved successfully",
            data={"task_id": task_id, "status": task.status, "output": output}
        )
    return ApiResponse(success=False, message="Task not found")