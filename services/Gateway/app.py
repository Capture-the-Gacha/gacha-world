import uvicorn, os
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

PLAYER_HOST = os.getenv('PLAYER_HOST')
AUCTION_HOST = os.getenv('AUCTION_HOST')
AUTH_HOST = os.getenv('AUTH_HOST')
PORT = os.getenv('PORT')

app = FastAPI()

# TODO!

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)