from redis import Redis
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
import os
import json

redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', 'YOUR_STRONG_PASSWORD_HERE'),
    decode_responses=True
)

class User:
    def __init__(self, id, username, api_key, created_at=None):
        self.id = id
        self.username = username
        self.api_key = api_key
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @staticmethod
    def from_dict(data):
        return User(**json.loads(data))

    def to_dict(self):
        return json.dumps({
            'id': self.id,
            'username': self.username,
            'api_key': self.api_key,
            'created_at': self.created_at
        })

class Task:
    def __init__(self, id, status, query, jurisdiction=None, output=None):
        self.id = id
        self.status = status
        self.query = query
        self.jurisdiction = jurisdiction
        self.output = output

    @staticmethod
    def from_dict(data):
        return Task(**json.loads(data))

    def to_dict(self):
        return json.dumps({
            'id': self.id,
            'status': self.status,
            'query': self.query,
            'jurisdiction': self.jurisdiction,
            'output': self.output
        })

def create_default_user():
    user_key = "user:admin"
    if not redis_client.exists(user_key):
        default_user = User(
            id=os.getenv("DEFAULT_USER_ID"),
            username="admin",
            api_key=os.getenv("DEFAULT_API_KEY")
        )
        redis_client.set(user_key, default_user.to_dict())
        redis_client.set(f"user:api_key:{default_user.api_key}", user_key)

create_default_user()