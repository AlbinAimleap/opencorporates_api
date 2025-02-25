from opencorporates_api.api import app
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env", raise_error_if_not_found=True))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("opencorporates_api.api_async:app", host="0.0.0.0", port=8000, reload=True)