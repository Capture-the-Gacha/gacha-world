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
    username: str = Field(index=True)
    balance: float = Field()

class Recharge(SQLModel, table=True):
    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    amount: float = Field()
    timestamp: int = Field(default_factory=get_current_timestamp)

class RechargePublic(SQLModel):
    amount: float
    timestamp: int

class Collection(SQLModel, table=True):
    player_id: int = Field(foreign_key="player.id", primary_key=True)
    gacha_id: int = Field(primary_key=True)
    quantity: int = Field()

class CollectionPublic(SQLModel):
    gacha_id: int
    quantity: int

class Roll(SQLModel, table=True):
    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    gacha_id: int = Field()
    paid_price: float = Field()
    timestamp: int = Field(default_factory=get_current_timestamp)

class RollPublic(SQLModel):
    gacha_id: int
    paid_price: float
    timestamp: int