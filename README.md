
# OpenCorporates API Scraper

A FastAPI-based service that scrapes company data from OpenCorporates using the Zyte API.

## Features

- Asynchronous web scraping of company data from OpenCorporates
- RESTful API endpoints for searching companies
- Stream-based and batch processing options
- Background task processing with SQLite storage
- Docker support for easy deployment
- Task management system for tracking scraping operations

## Prerequisites

- Python 3.9+
- Docker (optional)
- Zyte API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/open_corporates.git
cd open_corporates
```

2. Create a `.env` file in the root directory:

    - ZYTE_API_KEY="your_zyte_api_key"


3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running Locally

Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Running with Docker

Build and run using Make commands:

| Command | Description |
|----------|-------------|
| make build | Build Docker image |
| make run | Run container |
| make dbuild | Build and run |
| make stop | Stop container |
| make clean | Clean Docker system |

## API Endpoints

### Search Endpoints

- `GET /search/stream?query=<search_term>&jurisdiction=<optional_jurisdiction>`
  - Streams company results as they are scraped

- `GET /search?query=<search_term>&jurisdiction=<optional_jurisdiction>`
  - Returns all company results in a single response

### Task Management

- `GET /queue?query=<search_term>&jurisdiction=<optional_jurisdiction>`
  - Queues a new scraping task
  - Returns a task ID

- `GET /tasks`
  - Lists all tasks

- `GET /task/{task_id}`
  - Gets status and results of a specific task

- `GET /task/{task_id}/delete`
  - Deletes a specific task

- `GET /delete`
  - Deletes all tasks

## Response Format

```json
{
  "success": boolean,
  "message": string,
  "data": {
    "companies": [
      {
        "company_link": string,
        "company_name": string,
        "company_number": string,
        "status": string,
        "incorporation_date": string,
        "company_type": string,
        "jurisdiction": string,
        "registered_address": string,
        "agent_name": string,
        "agent_address": string,
        "directors_officers": string,
        ...
      }
    ]
  }
}
```

## Project Structure

```

├── opencorporates_api/
│   ├── __init__.py
│   ├── api_async.py      # FastAPI application
│   ├── opencorporates.py # Scraping logic
│   └── tasks.py         # Database models
├── .env                 # Environment variables
├── Dockerfile          # Docker configuration
├── Makefile           # Build automation
├── main.py            # Application entry point
└── requirements.txt   # Python dependencies
```

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- aiohttp - Async HTTP client
- BeautifulSoup4 - HTML parsing
- SQLAlchemy - Database ORM
- Pydantic - Data validation
- python-dotenv - Environment management
