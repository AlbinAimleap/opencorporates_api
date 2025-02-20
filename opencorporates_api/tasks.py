from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///tasks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)
    query = Column(String, index=True)
    jurisdiction = Column(String, nullable=True)
    output = Column(Text, nullable=True)

# Create the tasks table (if it doesn't already exist)
Base.metadata.create_all(bind=engine)