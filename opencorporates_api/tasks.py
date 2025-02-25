from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
import os

DATABASE_URL = "sqlite:///tasks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)
    query = Column(String, index=True)
    jurisdiction = Column(String, nullable=True)
    output = Column(Text, nullable=True)

# Create the tasks table (if it doesn't already exist)
Base.metadata.create_all(bind=engine)

def create_default_user():
    db = SessionLocal()
    default_user = db.query(User).filter_by(username="admin").first()
    if not default_user:
        default_user = User(
            id=os.getenv("DEFAULT_USER_ID", 1),
            username="admin",
            api_key=os.getenv("DEFAULT_API_KEY"),
        )
        db.add(default_user)
        db.commit()
    db.close()

create_default_user()