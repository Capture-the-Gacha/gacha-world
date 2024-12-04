from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel
from datetime import datetime

def get_current_timestamp():
    return int(datetime.now().timestamp())

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def get_session(engine):
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


class Player(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str
    password: str

class PlayerCredentials(SQLModel):
    username: str
    password: str

class PatchPlayer(SQLModel):
    username: str = None
    password: str = None
