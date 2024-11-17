from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Player(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field(index=True)
    password: str = Field()
    balance: float = Field()

class Recharge(SQLModel):
    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="Player.id")
    amount: float = Field()

class Collection(SQLModel):
    player_id: int = Field(foreign_key="Player.id", primary_key=True)
    gacha_id: int = Field(primary_key=True)
    quantity: int = Field()

class Roll(SQLModel):
    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="Player.id")
    gacha_id: int = Field()
    paid_price: float = Field()

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def get_session(engine):
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]