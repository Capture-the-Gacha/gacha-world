import uvicorn, os, requests as re, urllib3, jwt
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from connection import engine
from model import Auction, create_db_and_tables, get_current_timestamp, SessionDep
from typing import Annotated
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer
from fastapi_utils.tasks import repeat_every
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
TokenDep = Annotated[str, Depends(oauth2_scheme)]

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')
PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = os.getenv('PORT')
EXTEND_EXPIRATION_SECONDS = 30

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
	JWT_PUBLIC_KEY = f.read().strip()

@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables(engine)
	await check_auction_expiration()
	yield

app = FastAPI(lifespan=lifespan)

def validate(token: str) -> dict:
	try:
		return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail='Token expired')
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail='Invalid token')

@repeat_every(seconds=10)
async def check_auction_expiration() -> None:
	current_timestamp = get_current_timestamp()
	with Session(engine) as session:
		expired_auctions_ids = session.exec(select(Auction.id).where(Auction.is_closed == False, Auction.expiration_timestamp < current_timestamp)).all()
	
	for auction_id in expired_auctions_ids:
		close_auction(auction_id)

def close_auction(auction_id: int, session: SessionDep) -> None:
	auction = session.get(Auction, auction_id)
	if auction is None or auction.is_closed:
		return

	# If no one bid, return the gacha
	if auction.last_bidder_id is None:
		response = re.post(f'https://{PLAYER_HOST}:{PORT}/transferGacha/{auction.creator_id}/{auction.gacha_id}', verify=False)
		if not response.ok:
			return
		auction.is_closed = True
		session.commit()
		print(f'[AUCTION] Auction {auction.id} expired, gacha returned to creator')
		return

	# ! Consistency problems, what if one fails
	# If someone bid transfer the bid amount to the creator
	response = re.post(f'https://{PLAYER_HOST}:{PORT}/refundBid/{auction.creator_id}/{auction.highest_bid}', verify=False)
	if not response.ok:
		return
	# And transfer the gacha
	response = re.post(f'https://{PLAYER_HOST}:{PORT}/transferGacha/{auction.last_bidder_id}/{auction.gacha_id}', verify=False)
	if not response.ok:
		return
	auction.is_closed = True
	session.commit()
	print(f'[AUCTION] Auction {auction.id} closed with highest_bid = {auction.highest_bid}, gacha transferred to last_bidder_id = {auction.last_bidder_id}')

@app.post('/sell')
async def sell_gacha(gacha_id: int, base_price: float, expiration_timestamp: int, session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')

	# Check if base_price is positive
	if base_price <= 0:
		raise HTTPException(status_code=400, detail='Base price must be positive')

	# Check if expiration_timestamp is not in the past
	if expiration_timestamp < get_current_timestamp():
		raise HTTPException(status_code=400, detail='Expiration timestamp is in the past')
	
	# Create the auction
	auction = Auction(creator_id=player_id, gacha_id=gacha_id, base_price=base_price, expiration_timestamp=expiration_timestamp)
	session.add(auction)

	# Ask Player service to remove the gacha from the player's collection
	# In one API call we check if the player exists and if the player has the gacha
	# If the response is successful we create the auction
	response = re.post(f'https://{PLAYER_HOST}:{PORT}/sellGacha/{player_id}/{gacha_id}', verify=False)
	if not response.ok:
		session.rollback()
		raise HTTPException(status_code=404, detail='Player not found or does not have the gacha')
	
	session.commit()
	return { 'message': 'Auction created', 'auction_id': auction.id }

@app.post('/bid')
async def bid(auction_id: int, bid: float, session: SessionDep, token: TokenDep) -> dict:
	player_id = validate(token).get('sub')

	# Check if bid is positive
	if bid <= 0:
		raise HTTPException(status_code=400, detail='Bid must be positive')

	# Get the auction
	auction = session.get(Auction, auction_id)
	if auction is None:
		raise HTTPException(status_code=404, detail='Auction not found')

	# Check if the auction is closed or expired
	if auction.is_closed or auction.expiration_timestamp < get_current_timestamp():
		raise HTTPException(status_code=400, detail='Auction is closed')

	# Check if the player is not the creator of the auction
	if auction.creator_id == player_id:
		raise HTTPException(status_code=400, detail='Creator of the auction cannot bid')
	
	# Check if the player has not already bid
	if auction.last_bidder_id == player_id:
		raise HTTPException(status_code=400, detail='Player has already bid')

	# Check if bid is higher than the base price
	if bid < auction.base_price:
		raise HTTPException(status_code=400, detail='Bid must be higher than the base price')

	# Check if the bid is higher than the highest bid
	if bid <= auction.highest_bid:
		raise HTTPException(status_code=400, detail='Bid must be higher than the highest bid')

	# Refund the previous highest bid
	if auction.last_bidder_id is not None:
		response = re.post(f'https://{PLAYER_HOST}:{PORT}/refundBid/{auction.last_bidder_id}/{auction.highest_bid}', verify=False)
		if not response.ok:
			session.rollback()
			raise HTTPException(status_code=404, detail='Previous bidder not found')

	# Update the auction and eventually extend the expiration time
	auction.last_bidder_id = player_id
	auction.highest_bid = bid
	if auction.expiration_timestamp - get_current_timestamp() < EXTEND_EXPIRATION_SECONDS:
		auction.expiration_timestamp = get_current_timestamp() + EXTEND_EXPIRATION_SECONDS
	
	# Ask Player service to remove the bid amount from the player's balance
	response = re.post(f'https://{PLAYER_HOST}:{PORT}/placeBid/{player_id}/{bid}', verify=False)
	if not response.ok:
		session.rollback()
		raise HTTPException(status_code=400, detail='Player not found or does not have enough balance')

	session.commit()
	return { 'message': 'Bid successful' }



if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)
