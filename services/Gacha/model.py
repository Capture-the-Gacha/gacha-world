
from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def get_session(engine):
    with Session(engine) as session:
        yield session
        
class Gacha(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_url: str

