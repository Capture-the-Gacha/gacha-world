from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

ADMIN_PORT= int(os.getenv('ADMIN_PORT'))

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Admin Gateway is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=ADMIN_PORT,
        ssl_certfile=CERT_PATH,
        ssl_keyfile=KEY_PATH
    )
