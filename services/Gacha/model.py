from fastapi import Depends
from sqlmodel import SQLModel, Field, Session
from typing import Annotated, Optional
from connection import engine  # Import the engine

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]

class Gacha(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_url: str
    rarity: str = Field(default='common')

