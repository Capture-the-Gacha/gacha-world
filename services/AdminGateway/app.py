import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PORT = int(os.getenv('PORT'))
ADMIN_PORT= int(os.getenv('ADMIN_PORT'))

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


# === Auth ===

# TODO

# === Gacha ===

@app.get('/gachas')
async def getCollection(request: Request):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas')

@app.get('/gachas/{gacha_id}')
async def getCollection(request: Request, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.post('/gachas')
async def addGacha(request: Request):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas')

@app.put('/gachas/{gacha_id}')
async def updateGacha(request: Request, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

@app.delete('/gachas/{gacha_id}')
async def deleteGacha(request: Request, gacha_id: int):
    return await forward(request, f'https://{GACHA_HOST}:{PORT}/gachas/{gacha_id}')

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=ADMIN_PORT,
        ssl_certfile=CERT_PATH,
        ssl_keyfile=KEY_PATH
    )
