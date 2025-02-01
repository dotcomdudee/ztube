import json
import os
import time
import requests
from datetime import datetime, timezone
from dateutil import parser
from flask import Flask, render_template, jsonify, request, session, send_file
import uuid
import yaml
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.secret_key = 'yoursecretkey'  # Change this to something secure!
CHANNEL_IDS = []
CACHE_EXPIRY_TIME = 1800  # Cache expiry set to 30 minutes
USERFILES_DIR = os.path.join(os.path.dirname(__file__), 'userfiles')
if not os.path.exists(USERFILES_DIR):
    os.makedirs(USERFILES_DIR)

def get_user_cache_key():
    user_id = session.get('user_id')
    return os.path.join(USERFILES_DIR, f"cache_{user_id}.json")

def get_config_filename():
    user_id = session.get('user_id')
    return os.path.join(USERFILES_DIR, f"user_config_{user_id}.json")

def load_cache(user_cache_key):
    if os.path.exists(user_cache_key):
        with open(user_cache_key, 'r') as file:
            return json.load(file)
    return {}

def save_cache(cache, user_cache_key):
    with open(user_cache_key, 'w') as file:
        json.dump(cache, file)

def is_cache_expired(cache_timestamp):
    return (time.time() - cache_timestamp) > CACHE_EXPIRY_TIME

def fetch_videos(start_index=0, max_results=48, user_cache_key=""):
    if not user_cache_key:
        raise ValueError("A valid user cache key must be provided.")
    cache = load_cache(user_cache_key)
    results = []
    for channel_id in CHANNEL_IDS:
        cache_key = f"{channel_id}:{start_index}"
        cache_entry = cache.get(cache_key, {})
        if cache_entry and not is_cache_expired(cache_entry.get('timestamp', 0)):
            results.extend(cache_entry['data'])
        else:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            response = requests.get(url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                channel_videos = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    video_data = {
                        'id': {'videoId': entry.findtext('{http://www.youtube.com/xml/schemas/2015}videoId')},
                        'snippet': {
                            'publishedAt': entry.findtext('{http://www.w3.org/2005/Atom}published'),
                            'title': entry.findtext('{http://www.w3.org/2005/Atom}title'),
                            'channelTitle': entry.find('{http://www.w3.org/2005/Atom}author').findtext('{http://www.w3.org/2005/Atom}name'),
                            'thumbnails': {
                                'medium': {
                                    'url': entry.find('{http://search.yahoo.com/mrss/}group').find('{http://search.yahoo.com/mrss/}thumbnail').attrib['url']
                                }
                            }
                        }
                    }
                    channel_videos.append(video_data)
                cache[cache_key] = {
                    'timestamp': time.time(),
                    'data': channel_videos
                }
                results.extend(channel_videos)
    save_cache(cache, user_cache_key)
    results.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
    return results[start_index:start_index + max_results]

def time_ago(published_at):
    current_time = datetime.now(timezone.utc)
    published_time = parser.isoparse(published_at)
    delta = current_time - published_time
    days, seconds = delta.days, delta.seconds
    if days > 0:
        return f"{days} days ago" if days > 1 else "1 day ago"
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours} hours ago" if hours > 1 else "1 hour ago"
    elif seconds >= 60:
        minutes = seconds // 60
        return f"{minutes} minutes ago" if minutes > 1 else "1 minute ago"
    else:
        return f"{seconds} seconds ago" if seconds > 1 else "1 second ago"

@app.before_request
def before_request():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

@app.route('/')
def index():
    try:
        config_filename = get_config_filename()
        if not os.path.exists(config_filename):
            return render_template('config_input.html')
        with open(config_filename, 'r') as f:
            user_config = yaml.safe_load(f)
        global CHANNEL_IDS
        CHANNEL_IDS = user_config.get('channels', [])
        if not CHANNEL_IDS:
            return "No channels configured", 500
        user_cache_key = get_user_cache_key()
        videos = fetch_videos(user_cache_key=user_cache_key)
        for video in videos:
            video['time_ago'] = time_ago(video['snippet']['publishedAt'])
        return render_template('index.html', videos=videos)
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/load_more')
def load_more():
    start_index = int(request.args.get('start_index', 0))
    user_cache_key = get_user_cache_key()
    videos = fetch_videos(start_index=start_index, user_cache_key=user_cache_key)
    for video in videos:
        video['time_ago'] = time_ago(video['snippet']['publishedAt'])
    return jsonify(videos)

@app.route('/video/<video_id>')
def video(video_id):
    user_cache_key = get_user_cache_key()
    videos = fetch_videos(user_cache_key=user_cache_key)
    for video in videos:
        video['time_ago'] = time_ago(video['snippet']['publishedAt'])
    video_to_play = next((video for video in videos if video['id']['videoId'] == video_id), videos[0])
    return render_template('player.html', video_id=video_to_play['id']['videoId'], videos=videos)

@app.route('/load_config', methods=['POST'])
def load_config():
    yaml_data = request.json.get('config', '')
    try:
        yaml.safe_load(yaml_data)
        config_filename = get_config_filename()
        
        with open(config_filename, 'w') as f:
            f.write(yaml_data)
        return jsonify(success=True)
    except yaml.YAMLError as exc:
        return jsonify(success=False, error=str(exc))

@app.route('/config')
def config_input():
    config_filename = get_config_filename()
    existing_config = ""
    if os.path.exists(config_filename):
        with open(config_filename, 'r') as f:
            existing_config = f.read()
    else:
        default_config_path = os.path.join(os.path.dirname(__file__), 'default_config.yml')
        if os.path.exists(default_config_path):
            with open(default_config_path, 'r') as f:
                existing_config = f.read()
    return render_template('config_input.html', existing_config=existing_config)

@app.route('/clear_config', methods=['POST'])
def clear_config():
    try:
        config_filename = get_config_filename()
        if os.path.exists(config_filename):
            os.remove(config_filename)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/download_template')
def download_template():
    default_config_path = os.path.join(os.path.dirname(__file__), 'default_config.yml')
    return send_file(default_config_path, as_attachment=True, download_name='default_config.yml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
