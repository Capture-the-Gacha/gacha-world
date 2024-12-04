import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
import httpx
from httpx import HTTPError
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PLAYER_HOST = os.getenv('PLAYER_HOST')
AUCTION_HOST = os.getenv('AUCTION_HOST')
AUTH_HOST = os.getenv('AUTH_HOST')
PORT = os.getenv('PORT')

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

# Funzione per inoltrare richieste al servizio Player
async def forward_to_player(path: str, method: str = 'GET', params: dict = None, data: dict = None, token: str = None):
    url = f'https://{PLAYER_HOST}:{PORT}{path}'
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.request(method, url, params=params, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    except HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# Funzione per inoltrare richieste al servizio Auction
async def forward_to_auction(path: str, method: str = 'GET', params: dict = None, data: dict = None, token: str = None):
    url = f'https://{AUCTION_HOST}:{PORT}{path}'
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.request(method, url, params=params, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    except HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# Funzione per inoltrare richieste al servizio Auth
async def forward_to_auth(path: str, method: str = 'POST', data: dict = None):
    url = f'https://{AUTH_HOST}:{PORT}{path}'
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.request(method, url, json=data)
            response.raise_for_status()
            return response.json()
    except HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=response.text)

@app.post('/register')
async def register(credentials: dict):
    return await forward_to_auth('/register', data=credentials)

@app.post('/login')
async def login(credentials: dict):
    return await forward_to_auth('/login', data=credentials)

@app.post('/logout')
async def logout(token: str = Depends(oauth2_scheme)):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(f'https://{AUTH_HOST}:{PORT}/logout', headers=headers)
            response.raise_for_status()
            return response.json()
    except HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=response.text)

@app.get('/player/getCollection')
async def get_collection(token: str = Depends(oauth2_scheme)):
    return await forward_to_player('/getCollection', token=token)

@app.get('/player/getBalance')
async def get_balance(token: str = Depends(oauth2_scheme)):
    return await forward_to_player('/getBalance', token=token)

@app.get('/player/getRecharges')
async def get_recharges(token: str = Depends(oauth2_scheme)):
    return await forward_to_player('/getRecharges', token=token)

@app.get('/player/roll')
async def roll(token: str = Depends(oauth2_scheme)):
    return await forward_to_player('/roll', token=token)

@app.post('/auction/sell')
async def sell_gacha(data: dict, token: str = Depends(oauth2_scheme)):
    return await forward_to_auction('/sell', method='POST', data=data, token=token)

@app.post('/auction/bid')
async def bid(data: dict, token: str = Depends(oauth2_scheme)):
    return await forward_to_auction('/bid', method='POST', data=data, token=token)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)