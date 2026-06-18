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
        # Step 1: analyze the video
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.y2mate.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        res = requests.post('https://www.y2mate.com/mates/analyzeV2/ajax', data={
            'k_query': url,
            'k_page': 'home',
            'hl': 'en',
            'q_auto': 1
        }, headers=headers, timeout=20)
        result = res.json()

        title = result.get('title', 'Video')
        vid = result.get('vid', '')
        
        # get available formats
        links = result.get('links', {})
        if fmt == 'mp3':
            formats = links.get('mp3', {})
            quality_key = list(formats.keys())[0] if formats else None
        else:
            formats = links.get('mp4', {})
            # prefer 720p or best available
            quality_key = '720p' if '720p' in formats else (list(formats.keys())[0] if formats else None)

        if not quality_key or not vid:
            return jsonify({'error': 'Could not find download format'}), 500

        try:
            supabase.table('downloads').insert({
                'video_url': url,
                'video_title': title,
                'format': fmt,
                'quality': quality_key,
                'ip_address': request.remote_addr
            }).execute()
        except:
            pass

        return jsonify({
            'title': title,
            'duration': '?',
            'status': 'ready',
            'vid': vid,
            'quality_key': quality_key,
            'fmt': fmt
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    fmt = request.args.get('format', 'mp4')
    vid = request.args.get('vid', '')
    quality_key = request.args.get('quality', '720p')

    if not url or not vid:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.y2mate.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        res = requests.post('https://www.y2mate.com/mates/convertV2/index', data={
            'vid': vid,
            'k': quality_key
        }, headers=headers, timeout=20)
        result = res.json()
        download_url = result.get('dlink')
        if not download_url:
            return jsonify({'error': 'Could not get download link'}), 500

        ext = 'mp3' if fmt == 'mp3' else 'mp4'
        return jsonify({'download_url': download_url, 'filename': f'video.{ext}'})

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
