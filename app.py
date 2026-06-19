from flask import Flask, request, Response, jsonify
from pytubefix import YouTube
from pytubefix.cli import on_progress
import io

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

@app.route('/')
def index():
    return jsonify({'status': 'ok'})

@app.route('/download')
def download():
    url = request.args.get('url')
    type = request.args.get('type', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        yt = YouTube(url, on_progress_callback=on_progress, use_oauth=False, allow_oauth_cache=False)

        if type == 'mp3':
            stream = yt.streams.get_audio_only()
            filename = 'audio.mp3'
            mimetype = 'audio/mpeg'
        else:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').last()
            if not stream:
                stream = yt.streams.filter(file_extension='mp4').order_by('resolution').last()
            filename = 'video.mp4'
            mimetype = 'video/mp4'

        if not stream:
            return jsonify({'error': 'No stream found'}), 404

        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return Response(
            buffer,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': mimetype
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
