from datetime import datetime
import secrets
import string

def generate_token(length=32):
    """Генерация уникального токена для QR-кода"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class Song:
    def __init__(self, title, artist, filename, token=None, play_count=0, created_at=None):
        self.title = title
        self.artist = artist
        self.filename = filename
        self.token = token or generate_token()
        self.play_count = play_count
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self):
        return {
            'title': self.title,
            'artist': self.artist,
            'filename': self.filename,
            'token': self.token,
            'play_count': self.play_count,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        return Song(
            title=data['title'],
            artist=data['artist'],
            filename=data['filename'],
            token=data['token'],
            play_count=data.get('play_count', 0),
            created_at=data.get('created_at')
        )
