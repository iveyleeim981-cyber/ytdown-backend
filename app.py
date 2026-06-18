from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
from supabase import create_client

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://hmewxqlrhqjznmmygelw.supabase.co"
SUPABASE_KEY = "sb_secret_2SrgeIULs2hHYQJXtdXIPg_-Egfqgng"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/fetch', methods=['POST'])
def fetch():
    data = request.json
    url = data.get('url')
    fmt = data.get('format', 'mp4')
    quality = data.get('quality', '1080p')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if fmt == 'mp4' else 'bestaudio/best',
        'ignoreerrors': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration_string', '?')

        try:
            supabase.table('downloads').insert({
                'video_url': url,
                'video_title': title,
                'format': fmt,
                'quality': quality,
                'ip_address': request.remote_addr
            }).execute()
            col = 'total_mp4' if fmt == 'mp4' else 'total_mp3'
            supabase.rpc('increment_stats', {'col_name': col}).execute()
        except:
            pass

        return jsonify({'title': title, 'duration': duration, 'status': 'ready'})

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
