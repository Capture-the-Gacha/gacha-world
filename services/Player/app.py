import uvicorn, os
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from connection import engine
from model import Player, Recharge, RechargePublic, Collection, CollectionPublic, Roll, RollPublic, create_db_and_tables
from typing import List, Annotated
from sqlmodel import Session, select

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
GACHAPON_PRICE = float(os.getenv('GACHAPON_PRICE'))

@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables(engine)

	# TODO: Remove this, testing only
	with Session(engine) as session:
		player = Player(username='test', password='test', balance=1000)
		session.add(player)
		session.commit()
	yield

def get_session():
	with Session(engine) as session:
		yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)



# TODO: Decorators for authentication?
@app.get('/getCollection/{player_id}')
async def get_collection(player_id: int, session: SessionDep) -> List[CollectionPublic]:
	query = select(Collection).where(Collection.player_id == player_id)
	return session.exec(query).all()


@app.post('/recharge/{player_id}')
async def recharge(player_id: int, amount: float, session: SessionDep) -> dict:
	if amount <= 0:
		raise HTTPException(status_code=400, detail='Amount must be positive')

	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')
	
	player.balance += amount
	session.add(Recharge(player_id=player_id, amount=amount))
	session.commit()
	return { 'message': 'Recharge successful' }

@app.get('/getBalance/{player_id}')
async def get_balance(player_id: int, session: SessionDep) -> dict:
	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')
	return { 'balance': player.balance }

@app.get('/getRecharges/{player_id}', response_model=List[RechargePublic])
async def get_recharges(player_id: int, session: SessionDep) -> List[Recharge]:
	query = select(Recharge).where(Recharge.player_id == player_id)
	return session.exec(query).all()


# TODO: Get from Gacha service
def get_random_gacha_id() -> int:
	return 1

@app.get('/roll/{player_id}')
async def roll(player_id: int, session: SessionDep) -> dict:
	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')

	if player.balance < GACHAPON_PRICE:
		raise HTTPException(status_code=400, detail='Insufficient funds')
	
	# Let Gacha service roll for us
	gacha_id = get_random_gacha_id()

	# Pay the price
	player.balance -= GACHAPON_PRICE

	# Add to roll history
	session.add(Roll(player_id=player_id, gacha_id=gacha_id, paid_price=GACHAPON_PRICE))

	# Add to collection
	query = select(Collection).where(Collection.player_id == player_id, Collection.gacha_id == gacha_id)
	entry = session.exec(query).first()
	if entry:
		entry.quantity += 1
	else:
		session.add(Collection(player_id=player_id, gacha_id=gacha_id, quantity=1))

	session.commit()
	return { 'gacha_id': gacha_id }

@app.get('/getRolls/{player_id}', response_model=List[RollPublic])
async def get_rolls(player_id: int, session: SessionDep) -> List[Roll]:
	query = select(Roll).where(Roll.player_id == player_id)
	return session.exec(query).all()



# @app.post('/login')
# async def login(username: str, password: str) -> bool:
# 	pass

# @app.post('/register')
# async def register(username: str, password: str) -> int:
# 	pass

# @app.post('/deleteAccount')
# async def delete_account(username: str, password: str) -> bool:
# 	pass

# @app.patch('/editAccount')
# async def edit_account(player_id: int, player: dict) -> bool:
# 	pass

# @app.post('/logout')
# async def logout(player_id: int) -> bool:
# 	pass



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)