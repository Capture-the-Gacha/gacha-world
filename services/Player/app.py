import uvicorn, os, jwt
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from model import Player, Recharge, RechargePublic, Collection, CollectionPublic, Roll, RollPublic, create_db_and_tables, SessionDep
from typing import List, Annotated
from sqlmodel import select
from fastapi.security import OAuth2PasswordBearer

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
TokenDep = Annotated[str, Depends(oauth2_scheme)]

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
GACHAPON_PRICE = float(os.getenv('GACHAPON_PRICE'))
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
	JWT_PUBLIC_KEY = f.read().strip()

def validate(token: str) -> dict:
	try:
		return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail='Token expired')
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail='Invalid token')

@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables()
	yield

app = FastAPI(lifespan=lifespan)

@app.get('/getCollection')
async def get_collection(session: SessionDep, token: TokenDep) -> List[CollectionPublic]:
	player_id = validate(token).get('sub')
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

@app.get('/getBalance')
async def get_balance(session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')
	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')
	return { 'balance': player.balance }

@app.get('/getRecharges', response_model=List[RechargePublic])
async def get_recharges(session: SessionDep, token: TokenDep) -> List[Recharge]:
	player_id = validate(token).get('sub')
	query = select(Recharge).where(Recharge.player_id == player_id)
	return session.exec(query).all()


# TODO: Get from Gacha service
def get_random_gacha_id() -> int:
	return 1

@app.get('/roll')
async def roll(session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')
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

@app.get('/getRolls', response_model=List[RollPublic])
async def get_rolls(session: SessionDep, token: TokenDep) -> List[Roll]:
	player_id = validate(token).get('sub')
	query = select(Roll).where(Roll.player_id == player_id)
	return session.exec(query).all()



# ===================
# === AUCTION API ===
# ===================

@app.post('/placeBid/{bid}')
async def place_bid(bid: float, session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')

	if bid <= 0:
		raise HTTPException(status_code=400, detail='Bid must be positive')

	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')

	if player.balance < bid:
		raise HTTPException(status_code=400, detail='Insufficient funds')

	player.balance -= bid
	session.commit()
	return { 'message': 'Bid successful' }

@app.post('/refundBid/{player_id}/{bid}')
async def refund_bid(player_id: int, bid: float, session: SessionDep) -> dict:
	if bid <= 0:
		raise HTTPException(status_code=400, detail='Bid must be positive')

	query = select(Player).where(Player.id == player_id)
	player = session.exec(query).first()

	if not player:
		raise HTTPException(status_code=404, detail='Player not found')

	player.balance += bid
	session.commit()
	return { 'message': 'Bid refunded' }

@app.post('/sellGacha/{gacha_id}')
async def sell_gacha(gacha_id: int, session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')
	query = select(Collection).where(Collection.player_id == player_id, Collection.gacha_id == gacha_id)
	entry = session.exec(query).first()

	if not entry or entry.quantity == 0:
		raise HTTPException(status_code=404, detail='Player does not have the gacha')

	entry.quantity -= 1
	if entry.quantity == 0:
		session.delete(entry)
	session.commit()
	return { 'message': 'Gacha sold' }

@app.post('/transferGacha/{player_id}/{gacha_id}')
async def transfer_gacha(player_id: int, gacha_id: int, session: SessionDep) -> dict:
	query = select(Collection).where(Collection.player_id == player_id, Collection.gacha_id == gacha_id)
	entry = session.exec(query).first()

	if not entry:
		session.add(Collection(player_id=player_id, gacha_id=gacha_id, quantity=1))
	else:
		entry.quantity += 1
	
	session.commit()
	return { 'message': 'Gacha transferred' }



# ================
# === AUTH API ===
# ================

@app.post('/newPlayer/{username}', status_code=201)
async def create_account(username: str, session: SessionDep) -> dict:
	query = select(Player).where(Player.username == username)
	if session.exec(query).first():
		raise HTTPException(status_code=400, detail='Username already taken')

	player = Player(username=username, balance=0)
	session.add(player)
	session.commit()
	return { 'player_id': player.id }



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)