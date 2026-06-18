from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
from supabase import create_client
import os

app = Flask(__name__)
CORS(app, origins="*")

SUPABASE_URL = "https://hmewxqlrhqjznmmygelw.supabase.co"
SUPABASE_KEY = "sb_secret_2SrgeIULs2hHYQJXtdXIPg_-Egfqgng"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_ydl_opts():
    return {
        'quiet': False,
        'ignoreerrors': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded'],
            }
        },
    }

@app.route('/fetch', methods=['POST', 'OPTIONS'])
def fetch():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    url = data.get('url')
    fmt = data.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = get_ydl_opts()
    ydl_opts['skip_download'] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return jsonify({'error': 'Could not fetch video info.'}), 500
            title = info.get('title', 'Unknown')
            duration = info.get('duration_string', '?')

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

        return jsonify({'title': title, 'duration': duration, 'status': 'ready'})

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

    ydl_opts = get_ydl_opts()
    ydl_opts['skip_download'] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return jsonify({'error': 'Could not get video URL.'}), 500

            if fmt == 'mp3':
                # get best audio format URL
                formats = info.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if audio_formats:
                    best_audio = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]
                    direct_url = best_audio.get('url')
                else:
                    direct_url = info.get('url')
            else:
                # get best mp4 format URL
                formats = info.get('formats', [])
                mp4_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('vcodec') != 'none']
                if mp4_formats:
                    best_mp4 = sorted(mp4_formats, key=lambda x: x.get('height', 0), reverse=True)[0]
                    direct_url = best_mp4.get('url')
                else:
                    direct_url = info.get('url')

            if not direct_url:
                return jsonify({'error': 'Could not get download URL.'}), 500

            title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
            ext = 'mp3' if fmt == 'mp3' else 'mp4'

            return jsonify({'download_url': direct_url, 'filename': f'{title}.{ext}'})

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
