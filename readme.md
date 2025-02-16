<img src="https://cdn.stord.site/files/32268/youtube_1738413332.png" alt="Zeronote" width="128"/>

# ZeroTube
[https://ztube.app](https://ztube.app)

Zero distractions, Zero comments, Zero algorithms ✨

## TO DO
* Better player window on mobile/thumbnail rendering

## Demo Config
```
channels:
  - UCW5OrUZ4SeUYkUg1XqcjFYA # GeoWizard
  - UCXuqSBlHAE6Xw-yeJA0Tunw # LinusTechTips
  - UCdBK94H6oZT2Q7l0-b0xmMg # ShortCircuit
  - UCbguawtJlHjxXzdAskubQVg # WilliamOsman2
  - UCWizIdwZdmr43zfxlCktmNw # AlecSteele
```

## Features

- Distraction free YouTube experience
- Watch only the channels you love
- No comments, no spam
- No algorithm based suggestions
- Bring your own .yml config
- No API needed
- Available online or self host
- Simple, clean interface
- Responsive design

## YouTube Channel IDs

1. For an example .yml file check out `default_config.yml`

2. To find Channel ID:
> Creators Youtube page -> click channel description -> click Share Channel -> copy Channel ID.

## Export YouTube Subscriptions
A simple and fast method for extracting your YouTube subscriptions ✨

1. Included is the file 'getsubs.py'.
2. Head to https://www.youtube.com/feed/channels and load the entire page (you may need to scroll down)
3. Right click and view page source code 
4. Copy and paste the FULL page source code to a text file and save it as 'viewsource.txt' in the same directory
5. Run `python3 getsubs.py`
6. A new file should be generated 'extracted_channels.yml'
7. ✨

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

1. We use a cache of XML results to keep things fast. At the moment it is set to 30 mins. You can change this by modifying `CACHE_EXPIRY_TIME = 1800` in app.py. 

2. You should ensure that `app.secret_key = 'your_secret_key_here'` is set to something unique.

3. `max_results` is currently set to 48, on line 41. If you follow a larger number of channels, you may want to increase this number!

## Ads

Zerotube WILL NOT remove ads. If you are a Youtube user with a Premium membership using this app on desktop (as intended), then you will have the best viewing experience.
