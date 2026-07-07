import requests
import os
from datetime import datetime, timezone
import time
import sys
from requests.exceptions import ConnectionError, HTTPError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import configparser

#Config
global url, api
image = {"jpg", "jpeg", "png", "gif", "webp"}
video = {"mp4", "avi", "mov", "ogg", "wmv", "webm"}
exts = image | video


def loadcnfg():
    CONFIG_FILE = os.path.expanduser('~/.config/immich-watch.ini')
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if 'immich' not in config:
        config['immich'] = {
            'folder': input('Folder to watch: '),
            'url': input('Immich url: '),
            'api': input('Immich api: '),
        }
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)

    return config['immich']['folder'], config['immich']['url'], config['immich']['api']

#Class for getting file name when created
class Upload(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file = event.src_path
            manage(file)

#Wait for the file to be fully downloaded
def wait(file):
    checksize = -1

    while True:
        size = os.path.getsize(file)

        if size == checksize and size != 0:
            break
        else:
            checksize = size
            time.sleep(2)

#Actually upload
def upload(file):
    global url, api

    stats = os.stat(file)

    headers = {
        'Accept': 'application/json',
        'x-api-key': api
    }

    taken_at = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat()
    data = {
        'deviceAssetId': f'{file}-{stats.st_mtime}',
        'deviceId': 'python',
        'fileCreatedAt': taken_at,
        'fileModifiedAt': taken_at,
        'isFavorite': 'false',
    }
    
    with open(file, 'rb') as f:
        files = {'assetData': f}
        response = requests.post(f'{url}/assets', headers=headers, data=data, files=files)
    
    response.raise_for_status()
    print(response.json())

#Upload all the file that were sitting in the folder
def preupload(folder):
    for file in os.scandir(folder):
        if file.is_file():
            manage(str(os.path.join(folder, file.name)))

#Extract, upload and remove the file
def manage(file):
    #Get file extension
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
        except HTTPError as e:
            try:
                detail = e.response.json()
            except ValueError:
                detail = e.response.text
            print("Upload rejected")
            return

        os.remove(file)

def main():
    global url, api
    folder, url, api = loadcnfg()

    preupload(folder)

    observer = Observer()
    observer.schedule(Upload(), path=folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        pass

    observer.join()

if __name__ == "__main__":
    main()

