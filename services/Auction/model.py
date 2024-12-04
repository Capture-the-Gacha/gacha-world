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



class Auction(SQLModel, table=True):
    id: int = Field(primary_key=True)
    creator_id: int = Field()
    last_bidder_id: int | None = Field(default=None)
    gacha_id: int = Field()
    base_price: float = Field()
    highest_bid: float = Field(default=0)
    expiration_timestamp: int = Field()
    is_closed: bool = Field(default=False)

class AuctionPublic(SQLModel):
    gacha_id: int
    base_price: float
    expiration_timestamp: int