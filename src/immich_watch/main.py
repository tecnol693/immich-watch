import requests
import os
from datetime import datetime
import time
import sys
from requests.exceptions import ConnectionError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#Config
API_KEY = os.environ["IMMICH_API_KEY"]#Set yout immich API in bashrc
if not API_KEY:
    raise RuntimeError("IMMICH_API_KEY not set")
BASE_URL = 'http://127.0.0.1:2283/api'
image = {"jpg", "jpeg", "png", "gif", "webp"}
video = {"mp4", "avi", "mov", "ogg", "wmv", "webm"}
exts = image | video

#Class for getting file name when created
class Upload(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file = event.src_path
            manage(file)

#wait for the file to be fully downloaded
def wait(file):
    checksize = -1

    while True:
        size = os.path.getsize(file)

        if size == checksize and size != 0:
            break
        else:
            checksize = size
            time.sleep(0.5)

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

#Upload all the file that were sitting in the folder
def preupload(folder):
    for file in os.scandir(folder):
        if file.is_file():
            manage(str(os.path.join(folder, file.name)))

#Extract, upload and remove the file
def manage(file):
    #Get file extension
    print("File: " + file)
    #ext = file.split(".")[-1].lower()
    if any(ext in file for ext in exts):
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
    folder = os.path.expanduser('~/Downloads') #WIP configparser

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

