#!/usr/bin/env python3
from pytubefix import YouTube as yt
import googleapiclient.discovery as dis
from urllib.parse import parse_qs, urlparse
import threading
import sys
import time
import re
import os
import subprocess
import dotenv

dotenv.load_dotenv()
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# NEW FLAGS
SYNC_DOWNLOADS = False                 # True = download links sequentially
MAX_WORKERS = 5                       # threads for threaded mode
SHOW_PER_VIDEO_PROGRESS = True        # show a per-video tqdm bar (recommended in sync mode)
SHOW_PER_VIDEO_PROGRESS_IN_THREADS = True  # set True if you really want multiple bars in threaded mode


STORAGE_NAME = "syncthing"
YT_DIR_NAME = "yt"

BASE_DIR = os.path.join(os.path.expanduser("~"),STORAGE_NAME,YT_DIR_NAME)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = dis.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def joinPath(basePath, dir):
    return os.path.join(basePath, dir)

def makeAbsolutePath(fileName):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), fileName)

downloads_base_path = BASE_DIR
mp3_mp4_path = joinPath(downloads_base_path, "Downloads")
links_download_path = joinPath(downloads_base_path, "DownloadFromLinks")
links_file_path = joinPath(BASE_DIR, "links.txt")
links_error_file_path = joinPath(BASE_DIR, "linksError.txt")
saveToReferencePath = False

downloadVideo = True

saveAudioAsMP3 = True

TARGET_RESOLUTION = "360p"  

MAX_RESOLUTION = False

def printHelp():
    print("Send [1 or a] to download [audio]")
    print("Send [2 or v] to download [videos]")
    print("Send [m] to download [MAX RESOLUTION]")

    print("Send [i or here] to change download path to [CWD]")
    print("Send [o or od] to open download path")
    print("Send [l] to download links")
    print("Send [ol] to open links file")
    print("Send [me] to open CWD")
    print("Send [r] to save to reference path")
    print("Send [m] to download MAX RESOLUTION")
    print("Send [q] to quit")

def colorize(text, color):
    return f"\033[{color}{text}\033[0m"

CYAN = "36m"
BRIGHT_CYAN = "96m"
YELLOW = "33m"
BG_CYAN = "46m"
RED = "31m"
LIGHT_GRAY = "37m"
DARK_GRAY = "90m"

def open_file_explorer(path):
    """Open file explorer on Ubuntu (uses xdg-open)"""
    try:
        subprocess.run(['xdg-open', path])
    except Exception as e:
        print(f"Could not open file explorer: {e}")

def open_file(file_path):
    """Open a file with the default application on Ubuntu"""
    try:
        subprocess.run(['xdg-open', file_path])
    except Exception as e:
        print(f"Could not open file: {e}")

def main(url=""):
    global downloadVideo
    global mp3_mp4_path
    global saveToReferencePath
    global TARGET_RESOLUTION

    modeText = f"[VIDEO {TARGET_RESOLUTION}]" if downloadVideo else "[AUDIO]  [m]"

    modeText = colorize(modeText, DARK_GRAY)

    if url == "":
        url = input(f"{modeText} Paste your link here:\n")

    isAYoutubeLink = ("playlist" in url) or ("yout" in url)

    if isAYoutubeLink:

        startTime = time.time()

        if "playlist" in url:
            downloadPlaylist(url)

        elif "yout" in url:
            downloadedfileName = downloadFromYoutube(url, mp3_mp4_path)

        endTime = time.time()
        print(f"[Downloading took {endTime - startTime} seconds]")
        print("")

    else:

        if url in ['1','a']:
            downloadVideo = False
            
        elif url in ['2','v']:
            downloadVideo = True

        elif url in ["c", "r"]:

            downloadVideo = True
            saveToReferencePath = True
            global MAX_RESOLUTION

            MAX_RESOLUTION = True
            TARGET_RESOLUTION = "MAX"


            print(colorize("[DOWNLOAD PATH CHANGED]", DARK_GRAY), mp3_mp4_path)

            os.makedirs(mp3_mp4_path, exist_ok=True)

        elif url == "m":
            downloadVideo = True
            MAX_RESOLUTION = True
            TARGET_RESOLUTION = "MAX"
            print(colorize("[DOWNLOAD MAX RESOLUTION]", DARK_GRAY))

        elif url == "openlinks" or url == "ol" or url == "l":
            open_file(links_file_path)

        elif url == "downloadLinks" or "dl" in url:
            # Ask for directory name
            dir_name = input("Enter directory name to save downloads (leave empty for default): ").strip()
            if dir_name == "":
                target_path = links_download_path
            else:
                sanitized_dir_name = remove_illegal_path_characters(dir_name)
                target_path = joinPath(links_download_path, sanitized_dir_name)
                os.makedirs(target_path, exist_ok=True)
            
            # Use the target_path in downloadLinks function call
            downloadLinks(target_path)


        elif url == "i" or url == "here"  or url == "h":
            mp3_mp4_path = os.getcwd()
            print(colorize("[DOWNLOAD PATH CHANGED to CWD]", DARK_GRAY), mp3_mp4_path)

        elif url == "me" or "m" in url:
            open_file_explorer(os.getcwd())

        elif url == "open" or url == "o" or "od" in url:
            open_file_explorer(downloads_base_path)
            print("[OPENED DOWNLOAD DIRECTORY]")
        elif url == "help":
            printHelp()
        elif url == "q" or url == "quit" or url == "exit":
            print("Exiting...")
            sys.exit(0)
        else:
            print("~This is not a youtube link~")
            printHelp()

def hasWritePermissions():
    current_directory = os.getcwd()
    if os.access(current_directory, os.W_OK):
        print("Script has permission to save files in the current working directory")
        return True
    else:
        print("Script does not have permission to save files in the current working directory")
        return False

from tqdm import tqdm
SYNC_DOWNLOADS = True

def downloadLinks(target_path=links_download_path):
    os.makedirs(target_path, exist_ok=True)
    try:
        with open(links_file_path) as file:
            lines = [line.rstrip() for line in file if line.strip() and not line.startswith("#")]
        urls = lines

        total = len(urls)
        print(f"[Downloading {total} files to {target_path}]")

        if total == 0:
            print(colorize("[No URLs found in links.txt]", YELLOW))
            return

        if SYNC_DOWNLOADS:
            # Overall bar + optional per-video bars
            with tqdm(total=total, desc="Overall", unit="video") as overall:
                for u in urls:
                    downloadFromYoutube(
                        u, target_path,
                        show_progress=SHOW_PER_VIDEO_PROGRESS,
                        position=1  # keep overall at position 0, per-video at 1
                    )
                    overall.update(1)
        else:
            # Threaded: keep a clean overall bar by default
            if SHOW_PER_VIDEO_PROGRESS_IN_THREADS:
                # Multiple bars: each thread gets its own position (can get messy in small terminals)
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                    futures = []
                    for idx, u in enumerate(urls, start=1):  # position 0 reserved for overall
                        futures.append(ex.submit(downloadFromYoutube, u, target_path, True, idx))
                    with tqdm(total=total, desc="Overall", unit="video", position=0) as overall:
                        for f in futures:
                            f.result()
                            overall.update(1)
            else:
                # Cleanest: only an overall bar while threads download
                from functools import partial
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                    work = list(ex.map(partial(downloadFromYoutube, downloads_base_path=target_path,
                                               show_progress=False, position=0), urls))
                    # Show overall progress after (or you can wrap ex.map in manual loop to tick)
                    # For immediate feedback, wrap in tqdm over urls and submit individually:
                with tqdm(total=total, desc="Overall", unit="video") as overall:
                    for _ in range(total):
                        overall.update(1)

    except FileNotFoundError:
        print(colorize(f"Links file not found at {links_file_path}", RED))
        with open(links_file_path, "w") as f:
            f.write("# Add YouTube links here, one per line\n")
        print(f"Created empty links file at {links_file_path}")

def remove_illegal_path_characters(image_name):
    illegal_characters = r'[<>:"/\\|?*\x00-\x1F\x7F!]'
    cleaned_name = re.sub(illegal_characters, "", image_name)
    cleaned_name = cleaned_name.replace(" ", "_")
    return cleaned_name

def downloadPlaylist(url):
    playlistId = getPlaylistId(url)
    urls = getAllLinksFromPlaylist(playlistId)
    length = len(urls)
    playlist_name = getPlaylistName(playlistId)

    usablePlaylistName = remove_illegal_path_characters(playlist_name)
    usablePlaylistName = usablePlaylistName.encode("ascii", "ignore").decode("ascii")
    print(f"Playlist Name: {playlist_name}")
    downloadPath = joinPath(downloads_base_path, usablePlaylistName)
    
    os.makedirs(downloadPath, exist_ok=True)

    threads = []
    print(f"[Downloading {length} files]")
    for u in urls:
        t = threading.Thread(target=downloadFromYoutube, args=(u, downloadPath))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()

def getPlaylistId(playUrl):
    query = parse_qs(urlparse(playUrl).query, keep_blank_values=True)
    playlistId = query["list"][0]
    return playlistId

def getPlaylistName(playlistId):
    global youtube
    playlist_response = youtube.playlists().list(part="snippet", id=playlistId).execute()
    playlist_name = playlist_response["items"][0]["snippet"]["title"]

    return playlist_name

def getAllLinksFromPlaylist(playlistId):
    global youtube
    request = youtube.playlistItems().list(part="snippet", playlistId=playlistId, maxResults=100)
    response = request.execute()
    playlistItems = []

    while request is not None:
        response = request.execute()
        playlistItems += response["items"]
        request = youtube.playlistItems().list_next(request, response)

    links = []
    data = []
    for link in playlistItems:
        processedLink = "https://www.youtube.com/watch?v=" + link["snippet"]["resourceId"]["videoId"] + "&list=" + playlistId + "&t=0s"
        data.append(link)
        links.append(processedLink)

    return links

def downloadFromYoutube(url, downloads_base_path="", show_progress=False, position=0):
    try:
        os.makedirs(downloads_base_path, exist_ok=True)

        # Build YT object first (without callbacks), pick stream, then wire callbacks
        ytUrl = yt(url, use_oauth=True, allow_oauth_cache=True)
        streams = ytUrl.streams
        extension = ".mp4"

        if downloadVideo:
            if MAX_RESOLUTION:
                file = streams.filter(progressive=True, file_extension="mp4").order_by("resolution").last()
            else:
                file = streams.filter(res=TARGET_RESOLUTION, progressive=True, file_extension="mp4").first()
        else:
            file = streams.filter(only_audio=True).first()
            if saveAudioAsMP3:
                extension = ".mp3"

        if file is None:
            print(colorize(f"[No matching stream found] {url}", RED))
            with open(links_error_file_path, "a") as f:
                f.write(f"{url}\n")
            return None

        # Prepare a friendly title for the bar
        try:
            raw_title = ytUrl.title or "Downloading"
        except Exception:
            raw_title = "Downloading"
        title = remove_illegal_path_characters(raw_title)[:60]

        # Setup per-video progress bar using callbacks
        pbar = None
        last_n = 0

        def _ensure_total(stream):
            total = getattr(stream, "filesize", None) or getattr(stream, "filesize_approx", None)
            return total or 0

        def on_progress(stream, chunk, bytes_remaining):
            nonlocal pbar, last_n
            if not show_progress:
                return
            total = _ensure_total(stream)
            downloaded = max(0, total - bytes_remaining)

            if pbar is None:
                # Create the bar lazily on first callback (once we know/guess total)
                pbar = tqdm(
                    total=total if total > 0 else None,
                    unit="B",
                    unit_scale=True,
                    desc=title,
                    position=position,
                    leave=True,
                    dynamic_ncols=True,
                )
            # Update incrementally
            delta = downloaded - last_n
            if delta > 0:
                pbar.update(delta)
                last_n = downloaded

        def on_complete(stream, file_path):
            if pbar:
                # Ensure it ends at 100%
                total = _ensure_total(stream)
                if total and pbar.n < total:
                    pbar.update(total - pbar.n)
                pbar.close()

        # Register callbacks (pytube/pytubefix support both register_* and ctor args)
        try:
            ytUrl.register_on_progress_callback(on_progress)
            ytUrl.register_on_complete_callback(on_complete)
        except AttributeError:
            # Fallback to passing in constructor if register_* is unavailable
            ytUrl = yt(url, use_oauth=True, allow_oauth_cache=True,
                       on_progress_callback=on_progress,
                       on_complete_callback=on_complete)

        # Build filename and download
        fileName = file.default_filename[:-4] + extension
        fileName = fileName.encode("ascii", "ignore").decode("ascii")

        # If we’re not showing a per-video bar, still show some feedback
        if not show_progress:
            print(colorize(f"[Downloading] ", DARK_GRAY) + fileName)

        file.download(downloads_base_path, filename=fileName)

        if not show_progress:
            print(colorize(f"[Saved] ", DARK_GRAY) + os.path.join(downloads_base_path, fileName))

        return fileName

    except Exception as e:
        print(colorize(f"todo implement yt-dlp if age restricted [ERROR {e}] {url}", RED))
        with open(links_error_file_path, "a") as f:
            f.write(f"{url}\n")
        return None


if __name__ == "__main__":
    
    for path in [downloads_base_path, mp3_mp4_path, links_download_path]:
        os.makedirs(path, exist_ok=True)
    
    if not os.path.exists(links_file_path):
        with open(links_file_path, "w") as f:
            f.write("# Add YouTube links here, one per line\n")

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = ""
        print(colorize("Send [1] to download [audio] and [help] to get help", LIGHT_GRAY))
    
    try:
        while True:
            main(url)
            url = ""  
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)