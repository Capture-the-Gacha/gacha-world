from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import bcrypt, jwt, datetime, uuid, os, requests as re, uvicorn, urllib3
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Annotated
from contextlib import asynccontextmanager
from model import Player, PlayerCredentials, PatchPlayer, create_db_and_tables, SessionDep
from sqlmodel import select
from connection import engine

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')
TokenDep = Annotated[str, Depends(oauth2_scheme)]

# Set to 'test' for unit testing
ENV = os.getenv('ENV', 'prod')
MOCK_ID = 0

USERNAME = 'root'
AUTH_DB_HOST = os.getenv('AUTH_DB_HOST')
DATABASE = 'ctg'
PLAYERS_COLLECTION = 'players'

CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')
JWT_PRIVATE_KEY_PATH = os.getenv('JWT_PRIVATE_KEY_PATH')

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
    JWT_PUBLIC_KEY = f.read().strip()

with open(JWT_PRIVATE_KEY_PATH, 'r') as f:
    JWT_PRIVATE_KEY = f.read().strip()

PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = os.getenv('PORT')



@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables(engine)
	yield

app = FastAPI(lifespan=lifespan)

def validate(token: str) -> dict:
	try:
		return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail='Token expired')
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail='Invalid token')


def create_player(username: str) -> str:
    if ENV == 'test':
        global MOCK_ID
        MOCK_ID += 1
        return MOCK_ID

    response = re.post(f'https://{PLAYER_HOST}:{PORT}/newPlayer/{username}', verify=False)
    if response.status_code != 201:
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')
    
    return int( response.json()['player_id'] )

def validate_username(username: str) -> None:
    if not username or len(username) < 3 or username[0].isdigit() or username[0] == '_' or not all(c.isalnum() or c == '_' for c in username):
        raise HTTPException(status_code=400, detail='Error: Username must be at least 3 characters long, contain only alphanumeric characters or underscores, and must start with a letter')
    
def validate_password(password: str) -> None:
    if not password or len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(c in '!?#$%&()*+,-.' for c in password):
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters long, contain at least one letter, one number, and one special character.')



@app.post('/register')
async def register(player: Player, session: SessionDep):
    username = player.username
    password = player.password

    # Check if username is already taken
    query = select(Player).where(Player.username == username)
    if session.exec(query).first():
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')

    # Validate credentials
    validate_username(username)
    validate_password(password)
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Forward request to Player service
    player_id = create_player(username)

    # Save player to database
    player = Player(id=player_id, username=username, password=hashed)
    session.add(player)
    session.commit()
    
    return { 'message': 'User created', 'player_id': player_id }

@app.post('/login')
async def login(credentials: PlayerCredentials, session: SessionDep):
    username = credentials.username
    password = credentials.password

    # Check if user exists and if password matches
    query = select(Player).where(Player.username == username)
    player = session.exec(query).first()
    if not player or not bcrypt.checkpw(password.encode('utf-8'), player.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail='Login failed: Invalid username or password')

    now = datetime.datetime.now(datetime.UTC)
    token = jwt.encode({
        'iss': 'https://auth.server.com',
        'sub': str(player.id),
        'iat': now,
        'exp': now + datetime.timedelta(hours=1),
        'jti': str(uuid.uuid4())
    }, JWT_PRIVATE_KEY, algorithm='RS256')

    return { 'message': 'Login successful', 'token': token }

@app.post('/logout')
async def logout(token: TokenDep):
    if not token:
        raise HTTPException(status_code=401, detail='Token missing')
    validate(token)
    
    return { 'message': 'Logged out' }
     
@app.patch('/editAccount')
async def edit_account(new_player: PatchPlayer, session: SessionDep, token: TokenDep):
    player_id = validate(token)['sub']

    if not new_player.username and not new_player.password:
        raise HTTPException(status_code=400, detail='No fields to update')

    query = select(Player).where(Player.id == player_id)
    player = session.exec(query).first()
    if not player:
        raise HTTPException(status_code=404, detail='Player not found')
    
    res = ''

    if new_player.username:
        # Check if it's unique
        query = select(Player).where(Player.username == new_player.username)
        if session.exec(query).first():
            raise HTTPException(status_code=400, detail=f'Username "{new_player.username}" is already taken')
        # Validate username
        validate_username(new_player.username)
        # Update username
        player.username = new_player.username
        res = f'Username updated to "{new_player.username}"'

    if new_player.password:
        # Validate password
        validate_password(new_player.password)
        # Update password
        player.password = bcrypt.hashpw(new_player.password.encode('utf-8'), bcrypt.gensalt())
        if res:
            res += '; '
        res += 'Password updated'

    session.commit()
    return { 'message': res }

@app.delete('/deleteAccount')
async def delete_account(token: TokenDep, session: SessionDep):
    player_id = validate(token)['sub']

    query = select(Player).where(Player.id == player_id)
    player = session.exec(query).first()
    if not player:
        raise HTTPException(status_code=404, detail='Player not found')
    
    session.delete(player)
    session.commit()
    return { 'message': 'Account deleted' }



if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)