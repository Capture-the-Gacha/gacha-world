import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
import httpx
from typing import Annotated
from pydantic import BaseModel

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PORT = int(os.getenv('PORT'))
ADMIN_PORT = int(os.getenv('ADMIN_PORT'))

GACHA_HOST = os.getenv('GACHA_HOST')
AUTH_HOST = os.getenv('AUTH_HOST')

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

# === Auth ===

class UserCredentials(BaseModel):
    username: str
    password: str

@app.post('/registerAdmin')
async def registerAdmin(credentials: UserCredentials, request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/registerAdmin')

@app.post('/login')
async def login(credentials: UserCredentials, request: Request):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/login')

@app.post('/logout')
async def logout(request: Request, token: TokenDep):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/logout')

@app.delete('/deleteAccount')
async def deleteAccount(request: Request, token: TokenDep):
    return await forward(request, f'https://{AUTH_HOST}:{PORT}/deleteAccount')

# === Gacha ===

@app.get('/gachas')
async def getCollection(request: Request, token: TokenDep):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas')

@app.get('/gachas/{gacha_id}')
async def getCollection(request: Request, token: TokenDep, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.post('/gachas')
async def addGacha(request: Request, token: TokenDep):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas')

@app.put('/gachas/{gacha_id}')
async def updateGacha(request: Request, token: TokenDep, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.delete('/gachas/{gacha_id}')
async def deleteGacha(request: Request, token: TokenDep, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.get('/images/{gacha_name}')
async def get_image(request: Request, token: TokenDep, gacha_name: str) -> dict:
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/images/{gacha_name}')

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ADMIN_PORT,
        ssl_certfile=CERT_PATH,
        ssl_keyfile=KEY_PATH
    )
