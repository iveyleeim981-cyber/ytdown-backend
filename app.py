from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import requests
import re

app = Flask(__name__)
CORS(app, origins="*")

SUPABASE_URL = "https://hmewxqlrhqjznmmygelw.supabase.co"
SUPABASE_KEY = "sb_secret_2SrgeIULs2hHYQJXtdXIPg_-Egfqgng"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RAPIDAPI_KEY = "278d329200msh779264ddd93c10fp134262jsndff7f26828e6"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

def get_headers():
    return {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

@app.route('/fetch', methods=['POST', 'OPTIONS'])
def fetch():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    url = data.get('url')
    fmt = data.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        res = requests.get(
            f"{BASE_URL}/get-video-info/{video_id}",
            headers=get_headers(),
            params={"return_available_quality": "true"},
            timeout=60
        )
        result = res.json()
        title = result.get('title', 'Video')
        duration = result.get('duration', '?')

        try:
            supabase.table('downloads').insert({
                'video_url': url,
                'video_title': title,
                'format': fmt,
                'quality': 'best',
                'ip_address': request.remote_addr
            }).execute()
        except:
            pass

        return jsonify({
            'title': title,
            'duration': str(duration),
            'status': 'ready',
            'video_id': video_id
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

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        if fmt == 'mp3':
            endpoint = f"{BASE_URL}/download_audio/{video_id}"
            params = {"quality": "251"}
        else:
            endpoint = f"{BASE_URL}/download_video/{video_id}"
            params = {"quality": "247"}

        res = requests.get(endpoint, headers=get_headers(), params=params, timeout=60)
        result = res.json()

        download_url = result.get('file') or result.get('reserved_file') or result.get('url') or result.get('download_url')

        if not download_url:
            # try quality 137 for mp4 as fallback
            if fmt == 'mp4':
                res2 = requests.get(endpoint, headers=get_headers(), params={"quality": "137"}, timeout=60)
                result2 = res2.json()
                download_url = result2.get('url') or result2.get('download_url') or result2.get('link')

        if not download_url:
            return jsonify({'error': 'Could not get download link', 'raw': result}), 500

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
