from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlmodel import create_engine
import os

load_dotenv()

MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
PLAYER_DB_HOST = os.getenv('PLAYER_DB_HOST')
CERT_PATH = os.getenv('CERT_PATH')
KEY_PATH = os.getenv('KEY_PATH')

DATABASE_URL = f'mysql+pymysql://root:{MYSQL_ROOT_PASSWORD}@{PLAYER_DB_HOST}:3306/{MYSQL_DB}' \
                '?ssl_cert={CERT_PATH}' \
                '&ssl_key={KEY_PATH}' \
                '&ssl_check_hostname=false' \
                '&ssl_verify_cert=false'

engine = create_engine(DATABASE_URL, max_overflow=50)