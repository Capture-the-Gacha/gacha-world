from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import bcrypt, jwt, datetime, uuid, os, httpx, uvicorn, urllib3
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Annotated
from contextlib import asynccontextmanager
from model import User, UserCredentials, PatchUser, create_db_and_tables, SessionDep
from sqlmodel import select

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
TIMEOUT = int( os.getenv('TIMEOUT', 10) )

with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
    JWT_PUBLIC_KEY = f.read().strip()
    
with open(JWT_PRIVATE_KEY_PATH, 'r') as f:
    JWT_PRIVATE_KEY = f.read().strip()

PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = os.getenv('PORT')

@asynccontextmanager
async def lifespan(_app: FastAPI):
	# Only on startup
	create_db_and_tables()
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

    response = httpx.post(f'https://{PLAYER_HOST}:{PORT}/newPlayer/{username}', verify=False, timeout=TIMEOUT)
    if response.status_code != 201:
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')
    
    return int( response.json()['player_id'] )

def delete_player(username: str):
    if ENV == 'test':
        return

    response = httpx.delete(f'https://{PLAYER_HOST}:{PORT}/deletePlayer/{username}', verify=False, timeout=TIMEOUT)
    if response.status_code != 204:
        raise HTTPException(status_code=404, detail='Player not found')

def edit_player(old_username: str, new_username: str):
    if ENV == 'test':
        return

    response = httpx.patch(f'https://{PLAYER_HOST}:{PORT}/editPlayer/{old_username}/{new_username}', verify=False, timeout=TIMEOUT)
    if response.status_code != 204:
        raise HTTPException(status_code=404, detail='Player not found')

def validate_username(username: str) -> None:
    if not username or len(username) < 3 or username[0].isdigit() or username[0] == '_' or not all(c.isalnum() or c == '_' for c in username):
        raise HTTPException(status_code=400, detail='Error: Username must be at least 3 characters long, contain only alphanumeric characters or underscores, and must start with a letter')
    
def validate_password(password: str) -> None:
    if not password or len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(c in '!?#$%&()*+,-.' for c in password):
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters long, contain at least one letter, one number, and one special character.')



@app.post('/register')
async def register(player: User, session: SessionDep) -> dict:
    username = player.username
    password = player.password

    if username == 'admin':
        raise HTTPException(status_code=403, detail='Cannot register as admin')

    # Check if username is already taken
    query = select(User).where(User.username == username)
    if session.exec(query).first():
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')

    # Validate credentials
    validate_username(username)
    validate_password(password)
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Forward request to Player service
    player_id = create_player(username)

    # Save player to database
    player = User(id=player_id, username=username, password=hashed, role='user')
    session.add(player)
    session.commit()
    
    return { 'message': 'User created', 'player_id': player_id }

@app.post('/registerAdmin')
async def register_admin(admin: User, session: SessionDep) -> dict:
    username = admin.username
    password = admin.password

    # Check if admin is already registered
    query = select(User).where(User.username == username)
    if session.exec(query).first():
        raise HTTPException(status_code=400, detail='Admin is already registered')

    # Validate credentials
    validate_username(username)
    validate_password(password)
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Forward request to Player service
    admin_id = create_player(username)

    # Save admin to database
    admin = User(id=admin_id, username=username, password=hashed, role='admin')
    session.add(admin)
    session.commit()
    
    return { 'message': 'Admin created', 'admin_id': admin_id }

@app.post('/login')
async def login(credentials: UserCredentials, session: SessionDep) -> dict:
    username = credentials.username
    password = credentials.password

    # Check if user exists and if password matches
    query = select(User).where(User.username == username)
    player = session.exec(query).first()
    if not player or not bcrypt.checkpw(password.encode('utf-8'), player.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail='Login failed: Invalid username or password')

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'iss': 'https://auth.server.com',
        'sub': str(player.id),
        'iat': now,
        'exp': now + datetime.timedelta(hours=1),
        'jti': str(uuid.uuid4()),
        'role': player.role
    }
    token = jwt.encode(payload, JWT_PRIVATE_KEY, algorithm='RS256')

    return { 'message': 'Login successful', 'token': token }

@app.post('/logout')
async def logout(token: TokenDep) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail='Token missing')
    validate(token)
    
    return { 'message': 'Logged out' }
     
@app.patch('/editAccount')
async def edit_account(new_player: PatchUser, session: SessionDep, token: TokenDep) -> dict:
    player_id = validate(token)['sub']

    if not new_player.username and not new_player.password:
        raise HTTPException(status_code=400, detail='No fields to update')

    query = select(User).where(User.id == player_id)
    player = session.exec(query).first()
    if not player:
        raise HTTPException(status_code=404, detail='Player not found')
    
    res = ''

    if new_player.username:
        # Check if it's unique
        query = select(User).where(User.username == new_player.username)
        if session.exec(query).first():
            raise HTTPException(status_code=400, detail=f'Username "{new_player.username}" is already taken')
        
        # Validate username
        validate_username(new_player.username)

        # Update username
        edit_player(player.username, new_player.username)
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
async def delete_account(token: TokenDep, session: SessionDep) -> dict:
    player_id = validate(token)['sub']

    query = select(User).where(User.id == player_id)
    player = session.exec(query).first()
    if not player:
        raise HTTPException(status_code=404, detail='Player not found')
    
    delete_player(player.username)
    session.delete(player)
    session.commit()
    return { 'message': 'Account deleted' }



if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)