import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, Header, HTTPException
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
import httpx
from typing import List, Annotated

from player_model import Player, Recharge, RechargePublic, Collection, CollectionPublic, Roll, RollPublic
from auth_model import User, UserCredentials, PatchUser
from auction_model import Auction, AuctionPublic

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PLAYER_HOST = os.getenv('PLAYER_HOST')
AUCTION_HOST = os.getenv('AUCTION_HOST')
AUTH_HOST = os.getenv('AUTH_HOST')
GACHA_HOST = os.getenv('GACHA_HOST')
PORT = int(os.getenv('PORT'))

app = FastAPI()

async def forward(request: Request, url: str):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(
            method=request.method, 
            url=url, 
            content=await request.body(), 
            headers=request.headers
        )
    
    return Response(content=response.content, status_code=response.status_code, headers=response.headers)


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_token(token: str = Depends(api_key_header)) -> str:
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    if not token.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="`Bearer ` prefix is missing")

TokenDep = Annotated[str, Depends(verify_token)]

# ===== Player =====

@app.get('/getCollection')
async def getCollection(request: Request, token: TokenDep) -> List[CollectionPublic]:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getCollection')

@app.post('/recharge/{player_id}/{amount}')
async def recharge(player_id: str, amount: str, request: Request) -> dict:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/recharge/{player_id}/{amount}')

@app.get('/getBalance')
async def getBalance(request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getBalance')

@app.get('/getRecharges', response_model=List[RechargePublic])
async def getRecharges(request: Request, token: TokenDep) -> List[Recharge]:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getRecharges')

@app.get('/roll')
async def roll(request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/roll')

@app.get('/getRolls', response_model=List[RollPublic])
async def getRolls(request: Request, token: TokenDep) -> List[Roll]:
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getRolls')

# ===== Auction =====

@app.post('/sell')
async def sell(auction: AuctionPublic, request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{AUCTION_HOST}:{PORT}/sell')

@app.post('/bid/{auction_id}/{bid}')
async def bid(auction_id: str, bid: str, request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{AUCTION_HOST}:{PORT}/bid/{auction_id}/{bid}')

@app.get('/getAuctions')
async def getAuctions(request: Request, token: TokenDep) -> List[Auction]:
    return await forward(request, f'https://{AUCTION_HOST}:{PORT}/getAuctions')

# ===== Gacha =====

@app.get('/gachas')
async def get_gachas(request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas')

@app.get('/gachas/{gacha_id}')
async def get_gacha(request: Request, token: TokenDep, gacha_id: int) -> dict:
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.get('/images/{gacha_name}')
async def get_image(request: Request, token: TokenDep, gacha_name: str) -> dict:
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/images/{gacha_name}')

# ===== Auth =====

@app.post('/register')
async def register(player: UserCredentials, request: Request) -> dict:
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/register')

@app.post('/login')
async def login(player: UserCredentials, request: Request) -> dict:
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/login')

@app.post('/logout')
async def logout(request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/logout')

@app.patch('/editAccount')
async def editAccount(new_player: PatchUser, request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/editAccount')

@app.delete('/deleteAccount')
async def deleteAccount(request: Request, token: TokenDep) -> dict:
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/deleteAccount')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)
