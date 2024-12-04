from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel
from datetime import datetime
from connection import engine

def get_current_timestamp():
    return int(datetime.now().timestamp())

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


class Player(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field()
    password: str = Field()

class PlayerCredentials(SQLModel):
    username: str = Field()
    password: str = Field()

class PatchPlayer(SQLModel):
    username: str = Field(default=None)
    password: str = Field(default=None)
