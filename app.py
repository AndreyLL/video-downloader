from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import subprocess
import os
import tempfile
import threading
import time
import uuid

app = Flask(__name__)
CORS(app)

# Хранилище для статуса загрузок
downloads = {}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Downloader Server</title>
    </head>
    <body>
        <h1>Video Downloader API</h1>
        <p>Endpoints:</p>
        <ul>
            <li>POST /download - Start download</li>
            <li>GET /status/{id} - Check status</li>
            <li>GET /file/{id} - Get file</li>
        </ul>
    </body>
    </html>
    '''

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    password = data.get('password')

    # Проверка пароля
    if password != '111':
        return jsonify({'error': 'Invalid password'}), 401

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Проверяем, если это страница Monari - извлекаем видео URL
    if 'monari.com' in url and not url.endswith('.m3u8'):
        try:
            import requests
            import re

            # Получаем HTML страницы
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            html = response.text

            # Ищем Cloudflare Stream ID
            match = re.search(r'cloudflarestream\.com/([a-f0-9]{32})', html)
            if match:
                video_id = match.group(1)
                # Заменяем URL на прямую ссылку на видео
                url = f"https://customer-jzsbiavb05u7bp8k.cloudflarestream.com/{video_id}/manifest/video.m3u8"
            else:
                return jsonify({'error': 'Video not found on Monari page'}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to extract video: {str(e)}'}), 400

    # Генерируем уникальный ID
    download_id = str(uuid.uuid4())

    # Запускаем скачивание в фоне
    thread = threading.Thread(target=download_video, args=(url, download_id))
    thread.start()

    downloads[download_id] = {
        'status': 'processing',
        'progress': 0,
        'filename': None
    }

    return jsonify({
        'id': download_id,
        'status': 'processing',
        'check_url': f'/status/{download_id}'
    })

def download_video(url, download_id):
    """Скачивает видео используя yt-dlp"""
    try:
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f'{download_id}.mp4')

        # Команда yt-dlp
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]/best',
            '-o', output_path,
            '--no-warnings',
            '--quiet',
            '--no-playlist',
            url
        ]

        # Выполняем команду
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_path):
            downloads[download_id] = {
                'status': 'completed',
                'progress': 100,
                'filename': output_path
            }
        else:
            downloads[download_id] = {
                'status': 'failed',
                'error': result.stderr or 'Download failed'
            }
    except Exception as e:
        downloads[download_id] = {
            'status': 'failed',
            'error': str(e)
        }

@app.route('/status/<download_id>')
def get_status(download_id):
    if download_id not in downloads:
        return jsonify({'error': 'Download not found'}), 404

    status = downloads[download_id].copy()
    if status['status'] == 'completed':
        status['download_url'] = f'/file/{download_id}'

    return jsonify(status)

@app.route('/file/<download_id>')
def get_file(download_id):
    if download_id not in downloads:
        return jsonify({'error': 'Download not found'}), 404

    download = downloads[download_id]
    if download['status'] != 'completed':
        return jsonify({'error': 'Download not completed'}), 400

    filename = download['filename']
    if not os.path.exists(filename):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        filename,
        as_attachment=True,
        download_name=f'video_{download_id}.mp4'
    )

# Очистка старых файлов каждые 30 минут
def cleanup_old_files():
    while True:
        time.sleep(1800)  # 30 минут
        for download_id, info in list(downloads.items()):
            if info.get('filename') and os.path.exists(info['filename']):
                try:
                    # Удаляем файлы старше 1 часа
                    file_age = time.time() - os.path.getctime(info['filename'])
                    if file_age > 3600:
                        os.remove(info['filename'])
                        del downloads[download_id]
                except:
                    pass

# Запускаем очистку в фоне
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)