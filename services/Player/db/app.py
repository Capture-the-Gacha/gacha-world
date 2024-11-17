from fastapi import FastAPI
from contextlib import asynccontextmanager
from model import create_db_and_tables
import uvicorn
from dotenv import load_dotenv
from connection import engine

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
	# Only on startup
	create_db_and_tables(engine)
	yield

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)