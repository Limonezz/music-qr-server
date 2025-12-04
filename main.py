from flask import Flask, render_template, send_file, abort
from flask_cors import CORS
from app.database import init_db
from app.routes import init_routes
import os

def create_app():
    app = Flask(__name__)
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['UPLOAD_FOLDER'] = 'static/audio'
    app.config['QR_FOLDER'] = 'static/qr_codes'
    
    # Создаем папки если их нет
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
    
    # Инициализация
    CORS(app)
    init_db()
    init_routes(app)
    
    @app.errorhandler(404)
    def not_found(error):
        return "Страница не найдена", 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return "Доступ запрещен", 403
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
