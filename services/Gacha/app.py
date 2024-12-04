import uvicorn, os, jwt, random, shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from connection import engine
from model import Gacha, create_db_and_tables, get_session

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
    JWT_PUBLIC_KEY = f.read().strip()

def validate(token: str) -> dict:
	try:
		return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail='Token expired')
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail='Invalid token')

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Only on startup
    create_db_and_tables(engine)
    yield

app = FastAPI(lifespan=lifespan)

TokenDep = Annotated[str, Depends(oauth2_scheme)]
SessionDep = Annotated[Session, Depends(get_session)]

@app.post('/add')
async def add_gacha(name: str, image: UploadFile, token: TokenDep, session: SessionDep):
    validate(token)
    image_filename = f'images/{image.filename}'
    with open(image_filename, 'wb') as buffer:
        shutil.copyfileobj(image.file, buffer)
    gacha = Gacha(name=name, image_url=image_filename)
    session.add(gacha)
    session.commit()
    return { 'message': 'Gacha added successfully', 'gacha_id': gacha.id }

@app.get('/roll')
async def roll_gacha(token: TokenDep, session: SessionDep):
    validate(token)
    gachas = session.exec(select(Gacha)).all()
    if not gachas:
        raise HTTPException(status_code=404, detail='No gacha available')
    gacha = random.choice(gachas)
    return { 'gacha_id': gacha.id, 'name': gacha.name, 'image_url': gacha.image_url }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)