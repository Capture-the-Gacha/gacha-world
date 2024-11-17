from sqlalchemy import create_engine
from dotenv import load_dotenv
import os, time

load_dotenv()

MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
PLAYER_DB_HOST = os.getenv('PLAYER_DB_HOST')
KEY_PATH = os.getenv('KEY_PATH')

# TODO: Can't figure out how to use HTTPS
DATABASE_URL = f'mysql+pymysql://root:{MYSQL_ROOT_PASSWORD}@{PLAYER_DB_HOST}:3306/{MYSQL_DB}'
engine = create_engine(DATABASE_URL)