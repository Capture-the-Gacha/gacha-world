from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
import bcrypt, jwt, datetime, uuid, os, requests as re, uvicorn, urllib3, cryptography
from dotenv import load_dotenv
from pydantic import BaseModel
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# Set to 'test' for unit testing
ENV = os.getenv('ENV', 'prod')

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

with open('/run/secrets/mongo-root-password', 'r') as f:
    MONGO_ROOT_PASSWORD = f.read().strip()

PLAYER_HOST = os.getenv('PLAYER_HOST')
PORT = os.getenv('PORT')

uri = f"mongodb://{USERNAME}:{MONGO_ROOT_PASSWORD}@{AUTH_DB_HOST}:27017/{DATABASE}?authSource=admin&tls=true&tlsAllowInvalidCertificates=true"
client = MongoClient(uri)
db = client[DATABASE]

players = db[PLAYERS_COLLECTION]



app = FastAPI()

def validate(token: str) -> dict:
	try:
		return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail='Token expired')
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail='Invalid token')


def create_player(username: str) -> str:
    if ENV == 'test':
        return str(uuid.uuid4())

    response = re.post(f'https://{PLAYER_HOST}:{PORT}/newPlayer/{username}', verify=False)
    if response.status_code != 201:
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')
    return response.json()['player_id']

class Credentials(BaseModel):
    username: str
    password: str

@app.post('/register')
async def register(credentials: Credentials):
    username = credentials.username
    password = credentials.password

    # Check if username is already taken
    if players.find_one({ 'username': username }):
        raise HTTPException(status_code=400, detail=f'Username "{username}" is already taken')

    # Validate username
    if not username or len(username) < 3 or username[0].isdigit() or username[0] == '_' or not all(c.isalnum() or c == '_' for c in username):
        raise HTTPException(status_code=400, detail='Error: Username must be at least 3 characters long, contain only alphanumeric characters or underscores, and must start with a letter')
    
    # Validate password
    if not password or len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(c in '!?#$%&()*+,-.' for c in password):
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters long, contain at least one letter, one number, and one special character.')
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Forward request to Player service
    player_id = create_player(username)
    
    players.insert_one({ 'player_id': player_id, 'username': username, 'password': hashed })
    return { 'message': 'User created', 'player_id': player_id }

@app.post('/login')
async def login(credentials: Credentials):
    username = credentials.username
    password = credentials.password

    user = players.find_one({ 'username': username })
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        raise HTTPException(status_code=401, detail='Login failed: Invalid username or password')
    
    now = datetime.datetime.now(datetime.UTC)
    token = jwt.encode({
        'iss': 'https://auth.server.com',
        'sub': str(user.get('player_id')),
        'iat': now,
        'exp': now + datetime.timedelta(hours=1),
        'jti': str(uuid.uuid4())
    }, JWT_PRIVATE_KEY, algorithm='RS256')

    return { 'message': 'Login successful', 'token': token }

@app.post('/logout')
async def logout(token=Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail='Token missing')
    validate(token)
    
    return { 'message': 'Logged out' }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)