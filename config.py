import os
import dotenv
dotenv.load_dotenv()

STORAGE_NAME = "syncthing"
YT_DIR_NAME = "yt"
BASE_DIR = os.path.join(os.path.expanduser("~"), STORAGE_NAME, YT_DIR_NAME)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# print(YOUTUBE_API_KEY)
SHOW_PER_VIDEO_PROGRESS_IN_THREADS = True

SYNC_DOWNLOADS = False
MAX_WORKERS = 5
SHOW_PER_VIDEO_PROGRESS = True
TARGET_RESOLUTION = "360p"
MAX_RESOLUTION = False
