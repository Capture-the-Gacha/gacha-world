import uvicorn, os, httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PLAYER_HOST = os.getenv('PLAYER_HOST')
AUCTION_HOST = os.getenv('AUCTION_HOST')
PORT = os.getenv('PORT')

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with httpx.AsyncClient(verify=False) as client:
        player_routes = (await client.get(f'https://{PLAYER_HOST}:{PORT}/getRoutes')).json()['routes']
        auction_routes = (await client.get(f'https://{AUCTION_HOST}:{PORT}/getRoutes')).json()['routes']
    
    for route in player_routes:
        app.add_api_route(route['path'], create_proxy_route(route, PLAYER_HOST), methods=[route['method']])

    for route in auction_routes:
        app.add_api_route(route['path'], create_proxy_route(route, AUCTION_HOST), methods=[route['method']])

    yield

app = FastAPI(lifespan=lifespan)



def create_proxy_route(route, host):
    async def proxy(request: Request):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=route['method'],
                url=f"https://{host}:{PORT}{route['path']}",
                headers=request.headers,
                data=await request.body()
            )
            return response

    return proxy


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)