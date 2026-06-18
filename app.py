from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import requests
import os

app = Flask(__name__)
CORS(app, origins="*")

SUPABASE_URL = "https://hmewxqlrhqjznmmygelw.supabase.co"
SUPABASE_KEY = "sb_secret_2SrgeIULs2hHYQJXtdXIPg_-Egfqgng"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COBALT_API = "https://api.cobalt.tools"

@app.route('/fetch', methods=['POST', 'OPTIONS'])
def fetch():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    url = data.get('url')
    fmt = data.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        payload = {
            'url': url,
            'videoQuality': '1080',
            'audioFormat': 'mp3' if fmt == 'mp3' else 'best',
            'downloadMode': 'audio' if fmt == 'mp3' else 'auto',
        }
        res = requests.post(COBALT_API, json=payload, headers=headers, timeout=30)
        result = res.json()

        if result.get('status') == 'error':
            return jsonify({'error': result.get('error', {}).get('code', 'Unknown error')}), 500

        download_url = result.get('url') or (result.get('tunnel'))
        filename = result.get('filename', 'video.mp4')

        try:
            supabase.table('downloads').insert({
                'video_url': url,
                'video_title': filename,
                'format': fmt,
                'quality': 'best',
                'ip_address': request.remote_addr
            }).execute()
        except:
            pass

        return jsonify({
            'title': filename.replace('.mp4','').replace('.mp3',''),
            'duration': '?',
            'status': 'ready',
            'download_url': download_url,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    fmt = request.args.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        payload = {
            'url': url,
            'videoQuality': '1080',
            'audioFormat': 'mp3' if fmt == 'mp3' else 'best',
            'downloadMode': 'audio' if fmt == 'mp3' else 'auto',
        }
        res = requests.post(COBALT_API, json=payload, headers=headers, timeout=30)
        result = res.json()

        if result.get('status') == 'error':
            return jsonify({'error': result.get('error', {}).get('code', 'Unknown error')}), 500

        download_url = result.get('url') or result.get('tunnel')
        filename = result.get('filename', f'video.{fmt}')

        return jsonify({'download_url': download_url, 'filename': filename})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    try:
        res = supabase.table('stats').select('*').eq('id', 1).execute()
        return jsonify(res.data[0])
    except:
        return jsonify({'total_downloads': 0})

@app.route('/')
def home():
    return 'YTDown backend is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
