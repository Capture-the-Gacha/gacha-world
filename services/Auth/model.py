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


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field()
    password: str = Field()
    role: str = Field(default='user')

class UserCredentials(SQLModel):
    username: str = Field()
    password: str = Field()

class PatchUser(SQLModel):
    username: str = Field(default=None)
    password: str = Field(default=None)
