import json
import os
import random
import time
from datetime import datetime, timezone
from dateutil import parser
from flask import Flask, render_template, jsonify, request, session, send_file
from googleapiclient.discovery import build
import uuid
import yaml

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # You should ensure that this is set to something strong and unique!
API_KEYS = []
CHANNEL_IDS = []
CACHE_EXPIRY_TIME = 86400  # We use a cache of API results to avoid hitting API quotas from Youtube. At the moment it is set to 24 hours in seconds.
USERFILES_DIR = os.path.join(os.path.dirname(__file__), 'userfiles')

if not os.path.exists(USERFILES_DIR):
    os.makedirs(USERFILES_DIR)

def get_random_api_key():
    return random.choice(API_KEYS)

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

def fetch_videos(start_index=0, max_results=30, user_cache_key=""):
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
            youtube = build('youtube', 'v3', developerKey=get_random_api_key())
            response = youtube.search().list(
                channelId=channel_id,
                part="snippet",
                maxResults=max_results,
                order="date"
            ).execute()
            cache[cache_key] = {
                'timestamp': time.time(),
                'data': response['items']
            }
            results.extend(response['items'])
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
            user_config = json.load(f)
        global API_KEYS, CHANNEL_IDS
        API_KEYS = user_config.get('api_keys', [])
        CHANNEL_IDS = user_config.get('channels', [])
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
    config_filename = get_config_filename()
    with open(config_filename, 'r') as f:
        user_config = json.load(f)
    user_cache_key = get_user_cache_key()
    videos = fetch_videos(start_index=start_index, user_cache_key=user_cache_key)
    for video in videos:
        video['time_ago'] = time_ago(video['snippet']['publishedAt'])
    return jsonify(videos)

@app.route('/video/<video_id>')
def video(video_id):
    config_filename = get_config_filename()
    with open(config_filename, 'r') as f:
        user_config = json.load(f)
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
        config = yaml.safe_load(yaml_data)
        config_filename = get_config_filename()
        with open(config_filename, 'w') as f:
            json.dump(config, f)
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