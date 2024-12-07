import os
import random
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Union

import jwt
import uvicorn
import httpx
import urllib3
from connection import engine
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from model import Gacha, SessionDep, create_db_and_tables, get_session
from PIL import Image
from sqlmodel import Session, select
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENV = os.getenv('ENV', 'prod')
MOCK_ID = 1

load_dotenv()
if ENV == 'prod':
	oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
else:
	oauth2_scheme = lambda: 'mock_token'

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')
PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = int( os.getenv('PORT') )
TIMEOUT = int( os.getenv('TIMEOUT', 10) )

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
    JWT_PUBLIC_KEY = f.read().strip()

RARITIES = ['common', 'rare', 'epic', 'legendary']
PROBABILITIES = [0.5, 0.3, 0.15, 0.05]

def validate(token: str) -> dict:
    if ENV != 'prod': return {'role': 'admin'}
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

def save_image(image, name):
    image_filepath = f'images/{name}.jpg'
    try:
        im = Image.open(image.file)
        if im.mode in ("RGBA", "P"): 
            im = im.convert('RGB')
        im.save(image_filepath, 'JPEG')  # Save as JPEG
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid image')
    return "/" + image_filepath

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Only on startup
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/images", StaticFiles(directory="images"), name="images")

TokenDep = Annotated[str, Depends(oauth2_scheme)]

# ===== EVERYONE =====

@app.get('/gachas')
async def get_gachas(token: TokenDep, session: SessionDep):
    gachas = session.exec(select(Gacha)).all()
    return [gacha.dict() for gacha in gachas]

@app.get('/gachas/{gacha_id}')
async def get_gacha(gacha_id: int, token: TokenDep, session: SessionDep):
    gacha = session.get(Gacha, gacha_id)
    if not gacha:
        raise HTTPException(status_code=404, detail='Gacha not found')
    return gacha.dict()

# ===== ADMIN =====

@app.post('/gachas')
async def add_gacha(name: Annotated[str, Form()], rarity: Annotated[str, Form()], token: TokenDep, session: SessionDep, image: UploadFile):
    payload = validate(token)
    role = payload.get('role')
    if role != 'admin':
        raise HTTPException(status_code=403, detail='Only administrators can add gachas')
    if rarity not in RARITIES:
        raise HTTPException(status_code=400, detail='Invalid rarity value')
    image_filepath = save_image(image, name)
    gacha = Gacha(name=name, rarity=rarity, image_url=image_filepath)
    session.add(gacha)
    session.commit()
    return { 'message': 'Gacha added successfully', 'gacha_id': gacha.id }

@app.put('/gachas/{gacha_id}')
async def update_gacha(gacha_id: int, token: TokenDep, session: SessionDep, image: UploadFile | None = None, name: Annotated[Union[str, None], Form()] = None, rarity: Annotated[Union[str, None], Form()] = None):
    payload = validate(token)
    role = payload.get('role')
    if role != 'admin':
        raise HTTPException(status_code=403, detail='Only administrators can update gachas')
    gacha = session.get(Gacha, gacha_id)
    if not gacha:
        raise HTTPException(status_code=404, detail='Gacha not found')
    if name:
        gacha.name = name
    if rarity:
        if rarity not in RARITIES:
            raise HTTPException(status_code=400, detail='Invalid rarity value')
        gacha.rarity = rarity
    if image:
        # Optionally remove old image file
        if gacha.image_url and os.path.exists(gacha.image_url):
            os.remove(gacha.image_url)
        image_filepath = save_image(image, gacha.name)
        gacha.image_url = image_filepath
    session.commit()
    return {'message': 'Gacha updated successfully'}

@app.delete('/gachas/{gacha_id}')
async def delete_gacha(gacha_id: int, token: TokenDep, session: SessionDep):
    payload = validate(token)
    role = payload.get('role')
    if role != 'admin':
        raise HTTPException(status_code=403, detail='Only administrators can delete gachas')
    gacha = session.get(Gacha, gacha_id)
    if not gacha:
        raise HTTPException(status_code=404, detail='Gacha not found')
    
    # Delete all gachas from users collections
    response = httpx.delete(f'https://{PLAYER_HOST}:{PORT}/deleteGacha/{gacha_id}', verify=False, timeout=TIMEOUT)
    if not response.is_success:
        raise HTTPException(status_code=400, detail='Error deleting gacha from users collections')

    session.delete(gacha)
    session.commit()
    return {'message': 'Gacha deleted successfully'}

# From Player service
@app.get('/roll')
async def roll_gacha(session: SessionDep):
    selected_rarity = random.choices(RARITIES, PROBABILITIES)[0]
    gachas = session.exec(select(Gacha).where(Gacha.rarity == selected_rarity)).all()
    if not gachas:
        # Fallback to any gacha if none of the selected rarity
        gachas = session.exec(select(Gacha)).all()
        if not gachas:
            raise HTTPException(status_code=404, detail='No gacha available')
    gacha = random.choice(gachas)
    return {
        'id': gacha.id,
        'name': gacha.name,
        'rarity': gacha.rarity,
        'image_url': gacha.image_url
    }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)