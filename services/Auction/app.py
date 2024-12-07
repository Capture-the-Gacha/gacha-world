import uvicorn, os, httpx, urllib3, jwt, logging, sys
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from model import Auction, AuctionPublic, create_db_and_tables, get_current_timestamp, SessionDep
from typing import Annotated
from sqlmodel import select, Session
from connection import engine
from fastapi.security import OAuth2PasswordBearer
from fastapi_utils.tasks import repeat_every
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set to 'test' for unit testing
ENV = os.getenv('ENV', 'prod')
MOCK_SELLER_ID = 1
MOCK_BUYER_ID = 2

load_dotenv()
if ENV == 'prod':
	oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
else:
	oauth2_scheme = lambda: 'mock_token'
TokenDep = Annotated[str, Depends(oauth2_scheme)]

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')
PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = os.getenv('PORT')
TIMEOUT = int( os.getenv('TIMEOUT', 10) )
EXTEND_EXPIRATION_SECONDS = 30

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
	JWT_PUBLIC_KEY = f.read().strip()


# Logging for lifespan
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(name)s     %(message)s')
logger = logging.getLogger('AUCTION')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables()
	if ENV == 'prod':
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
	
	if not expired_auctions_ids:
		logger.info('No expired auctions to handle...')

	for auction_id in expired_auctions_ids:
		await close_auction(auction_id)

def close_auction(auction_id: int) -> None:
	logger.info(f'Handling expired auction {auction_id}')

	with Session(engine) as session:
		auction = session.get(Auction, auction_id)
		if auction is None or auction.is_closed:
			return

		# If no one bid, return the gacha
		if auction.last_bidder_id is None:
			response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/transferGacha/{auction.creator_id}/{auction.gacha_id}', verify=False, timeout=TIMEOUT)
			if not response.is_success:
				return
			auction.is_closed = True
			session.commit()
			logger.info(f'Auction {auction.id} expired, gacha returned to creator')
			return

		# ! Consistency problems, what if one fails
		# If someone bid transfer the bid amount to the creator
		response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/refundBid/{auction.creator_id}/{auction.highest_bid}', verify=False, timeout=TIMEOUT)
		if not response.is_success:
			return
		# And transfer the gacha
		response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/transferGacha/{auction.last_bidder_id}/{auction.gacha_id}', verify=False, timeout=TIMEOUT)
		if not response.is_success:
			return
		auction.is_closed = True
		session.commit()
		
	logger.info(f'Auction {auction.id} expired, gacha transferred to last_bidder_id = {auction.last_bidder_id}')



def remove_gacha(session: Session, player_id: int, gacha_id: int) -> None:
	response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/sellGacha/{player_id}/{gacha_id}', verify=False, timeout=TIMEOUT)
	if not response.is_success:
		session.rollback()
		raise HTTPException(status_code=404, detail='Player not found or does not have the gacha')

@app.post('/sell')
async def sell_gacha(auction: AuctionPublic, session: SessionDep, token: TokenDep) -> dict:
	if ENV == 'prod':
		player_id = validate(token).get('sub')
	else:
		player_id = MOCK_SELLER_ID

	base_price = auction.base_price
	expiration_timestamp = auction.expiration_timestamp
	gacha_id = auction.gacha_id

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
	if ENV == 'prod':
		remove_gacha(session, player_id, gacha_id)
	
	session.commit()
	return { 'message': 'Auction created', 'auction_id': auction.id }



def gift_money(session: Session, player_id: int, amount: float) -> None:
	response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/refundBid/{player_id}/{amount}', verify=False, timeout=TIMEOUT)
	if not response.is_success:
		session.rollback()
		raise HTTPException(status_code=404, detail='Previous bidder not found')
	
def remove_money(session: Session, player_id: int, amount: float) -> None:
	response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/placeBid/{player_id}/{amount}', verify=False, timeout=TIMEOUT)
	if not response.is_success:
		session.rollback()
		raise HTTPException(status_code=400, detail='Player not found or does not have enough balance')

@app.post('/bid/{auction_id}/{bid}')
async def bid(auction_id: int, bid: float, session: SessionDep, token: TokenDep) -> dict:
	if ENV == 'prod':
		player_id = validate(token).get('sub')
	else:
		player_id = MOCK_BUYER_ID

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
	if ENV == 'prod':
		if auction.last_bidder_id is not None:
			gift_money(session, auction.last_bidder_id, auction.highest_bid)

	# Update the auction and eventually extend the expiration time
	auction.last_bidder_id = player_id
	auction.highest_bid = bid
	if auction.expiration_timestamp - get_current_timestamp() < EXTEND_EXPIRATION_SECONDS:
		auction.expiration_timestamp = get_current_timestamp() + EXTEND_EXPIRATION_SECONDS
	
	# Ask Player service to remove the bid amount from the player's balance
	if ENV == 'prod':
		remove_money(session, player_id, bid)

	session.commit()
	return { 'message': 'Bid successful' }

@app.get('/getAuctions')
async def get_auctions(session: SessionDep, token: TokenDep) -> list[Auction]:
	if ENV == 'prod':
		player_id = validate(token).get('sub')
	else:
		player_id = MOCK_SELLER_ID

	auctions = session.exec(select(Auction).where((Auction.creator_id == player_id) | (Auction.last_bidder_id == player_id)).order_by(Auction.expiration_timestamp)).all()
	return auctions



if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)
