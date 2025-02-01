<img src="https://cdn.stord.site/files/32268/youtube_1738413332.png" alt="Zeronote" width="128"/>

# ZeroTube
[https://ztube.app](https://ztube.app)

Zero distractions, Zero comments, Zero algorithms ✨

## Features

- Distraction free YouTube experience
- Watch only the channels you love
- No comments, no spam
- No algorithm based suggestions
- Bring your own .yml config
- Supports multiple API keys
- Available online or self host
- Simple, clean interface
- Responsive design

## YouTube API & Channel IDs

1. You must first generate an API key in the [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com)

2. For an example .yml file check out `default_config.yml`

3. To find Channel ID:
> Creators Youtube page -> click channel description -> click Share Channel -> copy Channel ID.

4. There are strict API quota limits from Google. Multiple API keys are supported to help with this.

## Running with Docker

1. Clone this repo:
```bash
git clone https://github.com/dotcomdudee/ztube && cd ztube
```

2. Build the Docker image:
```bash
docker build -t ztube .
```

3. Run the container:
```bash
docker run -d --name ztube -p 4465:5000 -v $(pwd):/app ztube
```

The application will be available at `http://ip:4465`

## Usage

1. We use a cache of API results to avoid hitting API quotas from Youtube. At the moment it is set to 24 hours. You can change this by modifying `CACHE_EXPIRY_TIME = 86400` in app.py. 

2. You should ensure that `app.secret_key = 'your_secret_key_here'` is set to something unique.