from flask import request, jsonify, send_file, render_template, abort
import os
import qrcode
from io import BytesIO
from PIL import Image
from app.models import Song
from app.database import get_db
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app):
    db = get_db()
    
    @app.route('/')
    def index():
        return "Музыкальный сервер с QR-кодами. Доступ только по ссылкам."
    
    @app.route('/upload', methods=['POST'])
    def upload_song():
        """Только для админа - загрузка песен (защитить в продакшене)"""
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        title = request.form.get('title', 'Unknown')
        artist = request.form.get('artist', 'Unknown')
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Создаем запись в БД
        song = Song(title, artist, filename)
        db.songs.insert_one(song.to_dict())
        
        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # URL для доступа к песне
        base_url = os.environ.get('BASE_URL', request.host_url)
        song_url = f"{base_url}play/{song.token}"
        qr.add_data(song_url)
        qr.make(fit=True)
        
        # Сохраняем QR-код
        qr_filename = f"qr_{song.token}.png"
        qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_path)
        
        return jsonify({
            'message': 'Песня загружена',
            'song_url': song_url,
            'qr_code': f"/qr/{qr_filename}",
            'token': song.token
        })
    
    @app.route('/play/<token>')
    def play_song(token):
        """Страница проигрывателя для конкретной песни"""
        song_data = db.songs.find_one({'token': token})
        
        if not song_data:
            abort(404)
        
        song = Song.from_dict(song_data)
        
        # Обновляем счетчик прослушиваний
        db.songs.update_one(
            {'token': token},
            {'$inc': {'play_count': 1}}
        )
        
        base_url = request.host_url
        audio_url = f"{base_url}audio/{song.filename}"
        
        return render_template('player.html', 
                             song=song.to_dict(),
                             audio_url=audio_url)
    
    @app.route('/audio/<filename>')
    def serve_audio(filename):
        """Отдача аудиофайла с проверкой реферера"""
        # Проверяем, что запрос пришел с нашего же домена
        # Это предотвращает прямое скачивание файлов
        referer = request.headers.get('Referer')
        if not referer or not request.host in referer:
            abort(403)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            abort(404)
        
        return send_file(filepath, mimetype='audio/mpeg')
    
    @app.route('/qr/<filename>')
    def serve_qr(filename):
        """Отдача QR-кода"""
        filepath = os.path.join(app.config['QR_FOLDER'], filename)
        if not os.path.exists(filepath):
            abort(404)
        
        return send_file(filepath, mimetype='image/png')
    
    @app.route('/admin/songs')
    def list_songs():
        """Админская страница (защитить в продакшене)"""
        songs = list(db.songs.find())
        return jsonify([
            {
                'title': s['title'],
                'artist': s['artist'],
                'play_count': s['play_count'],
                'qr_url': f"/qr/qr_{s['token']}.png",
                'play_url': f"/play/{s['token']}"
            }
            for s in songs
        ])
