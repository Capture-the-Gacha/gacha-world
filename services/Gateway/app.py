import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PLAYER_HOST = os.getenv('PLAYER_HOST')
AUCTION_HOST = os.getenv('AUCTION_HOST')
AUTH_HOST = os.getenv('AUTH_HOST')
GACHA_HOST = os.getenv('GACHA_HOST')
PORT = os.getenv('PORT')

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


# ===== Player =====

@app.get('/getCollection')
async def getCollection(request: Request):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getCollection')

@app.post('/recharge/{player_id}/{amount}')
async def recharge(request: Request, player_id: str, amount: str):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/recharge/{player_id}/{amount}')

@app.get('/getBalance')
async def getBalance(request: Request):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getBalance')

@app.get('/getRecharges')
async def getRecharges(request: Request):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getRecharges')

@app.get('/roll')
async def roll(request: Request):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/roll')

@app.get('/getRolls')
async def getRolls(request: Request):
    return await forward(request, f'https://{PLAYER_HOST}:{PORT}/getRolls')

# ===== Auction =====

@app.post('/sell')
async def sell(request: Request):
    return await forward(request, f'https://{AUCTION_HOST}:{PORT}/sell')

@app.post('/bid/{auction_id}/{bid}')
async def bid(request: Request, auction_id: str, bid: str):
    return await forward(request, f'https://{AUCTION_HOST}:{PORT}/bid/{auction_id}/{bid}')

# ===== Auth =====

@app.post('/register')
async def register(request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/register')

@app.post('/login')
async def login(request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/login')

@app.post('/logout')
async def logout(request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/logout')

@app.patch('/editAccount')
async def editAccount(request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/editAccount')

@app.delete('/deleteAccount')
async def deleteAccount(request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/deleteAccount')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)