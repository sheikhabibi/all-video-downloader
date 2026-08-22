import os
import uuid
import threading
import tempfile
from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)

# In-memory storage for download tasks
TASKS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    
    cookie_paths = ['cookies.txt', '/etc/secrets/cookies.txt', '/etc/secrets/cookies']
    for cp in cookie_paths:
        if os.path.exists(cp):
            ydl_opts['cookiefile'] = cp
            break
            
    if not ydl_opts.get('cookiefile') and os.path.exists('/etc/secrets'):
        secrets = os.listdir('/etc/secrets')
        return jsonify({'error': f'Cookies not found. Files in secrets dir: {secrets}'}), 400
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract available resolutions
            resolutions = set()
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('height'):
                    resolutions.add(f.get('height'))
            
            sorted_res = sorted(list(resolutions), reverse=True)
            
            simplified_options = []
            
            # Add options for each available resolution
            for res in sorted_res:
                simplified_options.append({
                    'id': f'bestvideo[height<={res}]+bestaudio/best[height<={res}]/best',
                    'label': f'Video ({res}p) - MP4',
                    'is_audio': False
                })
                
            # Fallback if no specific resolutions were found
            if not simplified_options:
                simplified_options.append({'id': 'bestvideo+bestaudio/best', 'label': 'Best Quality Video (MP4)', 'is_audio': False})
                
            # Add Best Audio option (converted to MP3 later)
            simplified_options.append({'id': 'bestaudio/best', 'label': 'Audio Only (Best Quality MP3)', 'is_audio': True})
            
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'options': simplified_options
            })
    except Exception as e:
        err_msg = str(e)
        if ydl_opts.get('cookiefile'):
            err_msg += f" [DIAGNOSTIC: Cookies WERE loaded from {ydl_opts['cookiefile']}]"
        return jsonify({'error': err_msg}), 500

def download_worker(task_id, url, format_id, is_audio):
    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            import re
            p = re.sub(r'\x1b\[[0-9;]*m', '', p)
            TASKS[task_id]['progress'] = p
        elif d['status'] == 'finished':
            TASKS[task_id]['status'] = 'completed'
            
            # For MP3 conversion, yt-dlp changes the extension, so we need to infer the new filename
            # But yt-dlp usually updates the filename in the postprocessor hook or we can just glob it.
            # To be safe, we just store the initial filename; get_file will handle extension changes.
            TASKS[task_id]['filename'] = d['filename']
            
    task_dir = os.path.join(tempfile.gettempdir(), f'videodl_{task_id}')
    os.makedirs(task_dir, exist_ok=True)
    
    outtmpl_name = '%(title)s_Audio.%(ext)s' if is_audio else '%(title)s_%(height)sp.%(ext)s'
            
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(task_dir, outtmpl_name),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
    }
    
    cookie_paths = ['cookies.txt', '/etc/secrets/cookies.txt', '/etc/secrets/cookies']
    for cp in cookie_paths:
        if os.path.exists(cp):
            ydl_opts['cookiefile'] = cp
            break
            
    if not ydl_opts.get('cookiefile') and os.path.exists('/etc/secrets'):
        secrets = os.listdir('/etc/secrets')
        TASKS[task_id]['status'] = 'error'
        TASKS[task_id]['error'] = f'Cookies not found. Files in secrets dir: {secrets}'
        return
    
    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['merge_output_format'] = 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        TASKS[task_id]['status'] = 'error'
        TASKS[task_id]['error'] = str(e)

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id', 'best')
    is_audio = data.get('is_audio', False)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        'status': 'downloading',
        'progress': '0%',
        'filename': None,
        'error': None
    }
    
    thread = threading.Thread(target=download_worker, args=(task_id, url, format_id, is_audio))
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/api/file/<task_id>', methods=['GET'])
def get_file(task_id):
    task = TASKS.get(task_id)
    if not task or task['status'] != 'completed':
        return "File not ready", 404
        
    task_dir = os.path.join(tempfile.gettempdir(), f'videodl_{task_id}')
    if not os.path.exists(task_dir):
        return "File not found", 404
        
    final_file = None
    for f in os.listdir(task_dir):
        if not f.endswith('.part') and not f.endswith('.ytdl'):
            final_file = os.path.join(task_dir, f)
            break
            
    if not final_file or not os.path.exists(final_file):
        return "File not found", 404
        
    return send_file(final_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
