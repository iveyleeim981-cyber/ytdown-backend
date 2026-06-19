from flask import Flask, request, Response, jsonify
from pytubefix import YouTube
from pytubefix.cli import on_progress
import io
import time
import random

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Disposition'
    return response

@app.route('/')
def index():
    return jsonify({'status': 'ok'})

@app.route('/info')
def info():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL'}), 400
    try:
        clients_to_try = ['MWEB', 'IOS', 'ANDROID', 'WEB', 'TVHTML5']
        for client in clients_to_try:
            try:
                yt = YouTube(url, client=client)
                return jsonify({'title': yt.title, 'duration': yt.length})
            except:
                continue
        return jsonify({'error': 'Could not fetch info'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    url = request.args.get('url')
    type = request.args.get('type', 'mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    time.sleep(random.uniform(0.3, 0.8))

    # Try every available client
    clients_to_try = ['TVHTML5', 'MWEB', 'IOS', 'ANDROID', 'WEB', 'ANDROID_MUSIC', 'ANDROID_CREATOR']
    yt = None
    last_error = None

    for client in clients_to_try:
        try:
            yt = YouTube(url, client=client, on_progress_callback=on_progress)
            _ = yt.title
            streams = yt.streams
            if not streams:
                raise Exception('No streams')
            break
        except Exception as e:
            last_error = e
            yt = None
            time.sleep(0.3)
            continue

    if not yt:
        return jsonify({'error': str(last_error)}), 500

    try:
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

        file_size = stream.filesize

        def generate():
            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)
            while True:
                chunk = buffer.read(8192)
                if not chunk:
                    break
                yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': mimetype,
        }
        if file_size:
            headers['Content-Length'] = str(file_size)

        return Response(generate(), mimetype=mimetype, headers=headers)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
