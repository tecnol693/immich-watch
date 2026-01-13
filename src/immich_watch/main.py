import requests
import os
from datetime import datetime
import time
from requests.exceptions import ConnectionError

#Set yout immich API in bashrc
API_KEY = os.environ["IMMICH_API_KEY"]
if not API_KEY:
    raise RuntimeError("IMMICH_API_KEY not set")
BASE_URL = 'http://127.0.0.1:2283/api'

#wait for the file to be fully downloaded
def wait(file):
    size = os.path.getsize(file)
    checksize = -1
    
    #Skip for already downloaded files, should work but dont fully trust it
    if size != 0:
        return

    while True:
        size = os.path.getsize(file)

        if size == checksize and size != 0:
            break
        else:
            checksize = size
            time.sleep(1)

#Actually upload
def upload(file):
    stats = os.stat(file)

    headers = {
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }

    data = {
        'deviceAssetId': f'{file}-{stats.st_mtime}',
        'deviceId': 'python',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime),
        'isFavorite': 'false',
    }
    
    with open(file, 'rb') as f:
        files = {'assetData': f}
        response = requests.post(f'{BASE_URL}/assets', headers=headers, data=data, files=files)
        print(response.json())

#Costantly watch if file present inside download folder, WIP configparser
def watch():
    image = {"jpg", "jpeg", "png", "gif", "webp"}
    video = {"mp4", "avi", "mov", "ogg", "wmv", "webm"}
    exts = image | video
    folder = os.path.expanduser('~/Downloads')
    
    #Heavy CPU usage, WIP detection of empty folder
    while True:
        for f in os.listdir(folder):
            file = os.path.join(folder, f)
            ext = file.split(".")[-1].lower()
            
            if ext in exts:
                wait(file)
                try:
                    upload(file)
                except ConnectionError:
                    print("Immich server is down")
                    return
                except FileNotFoundError:
                    print("File does not exist")
                    return
                os.remove(file) 

def main():
    try:
        watch()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

