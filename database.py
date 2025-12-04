from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

client = None
db = None

def init_db():
    global client, db
    mongodb_uri = os.environ.get('MONGODB_URI')
    
    if not mongodb_uri:
        raise ValueError("MONGODB_URI не установлен в переменных окружения")
    
    client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
    db = client['music_qr_database']
    
    # Создаем индекс для быстрого поиска по токену
    db.songs.create_index('token', unique=True)
    
    print("База данных подключена успешно")

def get_db():
    if db is None:
        init_db()
    return db
