import os
import sys
import time

from config import (
    BASE_DIR,
    TARGET_RESOLUTION,
    MAX_RESOLUTION,
)
from utils import (
    colorize,
    DARK_GRAY,
    LIGHT_GRAY,
    open_file,
    open_file_explorer,
    remove_illegal_path_characters,
    joinPath,
)
from download_manager import (
    download_links,
    download_playlist,
    download_from_youtube,
)

downloads_base_path = BASE_DIR
mp3_mp4_path = joinPath(downloads_base_path, "Downloads")
links_download_path = joinPath(downloads_base_path, "DownloadFromLinks")
links_file_path = joinPath(BASE_DIR, "links.txt")

def print_help():
    print("Send [1 or a] to download [audio]")
    print("Send [2 or v] to download [videos]")
    print("Send [m] to download [MAX RESOLUTION]")
    print("Send [i or here] to change download path to [CWD]")
    print("Send [o or od] to open download path")
    print("Send [l] to download links")
    print("Send [ol] to open links file")
    print("Send [me] to open CWD")
    print("Send [q] to quit")

def main():
    global mp3_mp4_path
    global TARGET_RESOLUTION
    global MAX_RESOLUTION

    download_video = True
    save_audio_as_mp3 = True

    while True:
        mode_text = f"[VIDEO {TARGET_RESOLUTION}]" if download_video else "[AUDIO]"
        mode_text = colorize(mode_text, DARK_GRAY)

        url = input(f"{mode_text} Paste your link here:\n")

        if ("playlist" in url) or ("yout" in url):
            start_time = time.time()

            if "playlist" in url:
                download_playlist(url, download_video, MAX_RESOLUTION, TARGET_RESOLUTION, save_audio_as_mp3)
            elif "yout" in url:
                download_from_youtube(url, mp3_mp4_path, True, 0, download_video, MAX_RESOLUTION, TARGET_RESOLUTION, save_audio_as_mp3)

            end_time = time.time()
            print(f"[Downloading took {end_time - start_time} seconds]")
            print("")
        else:
            if url in ['1', 'a']:
                download_video = False
            elif url in ['2', 'v']:
                download_video = True
            elif url == "m":
                MAX_RESOLUTION = True
                TARGET_RESOLUTION = "MAX"
                print(colorize("[DOWNLOAD MAX RESOLUTION]", DARK_GRAY))
            elif url in ["ol", "l"]:
                open_file(links_file_path)
            elif "dl" in url:
                dir_name = input("Enter directory name to save downloads (leave empty for default): ").strip()
                if dir_name == "":
                    target_path = links_download_path
                else:
                    sanitized_dir_name = remove_illegal_path_characters(dir_name)
                    target_path = joinPath(links_download_path, sanitized_dir_name)
                    os.makedirs(target_path, exist_ok=True)
                download_links(target_path, download_video, MAX_RESOLUTION, TARGET_RESOLUTION, save_audio_as_mp3)
            elif url in ["i", "here", "h"]:
                mp3_mp4_path = os.getcwd()
                print(colorize("[DOWNLOAD PATH CHANGED to CWD]", DARK_GRAY), mp3_mp4_path)
            elif url == "me":
                open_file_explorer(os.getcwd())
            elif url in ["o", "od"]:
                open_file_explorer(downloads_base_path)
                print("[OPENED DOWNLOAD DIRECTORY]")
            elif url == "help":
                print_help()
            elif url in ["q", "quit", "exit"]:
                print("Exiting...")
                sys.exit(0)
            else:
                print("~This is not a youtube link~")
                print_help()

if __name__ == "__main__":
    for path in [downloads_base_path, mp3_mp4_path, links_download_path]:
        os.makedirs(path, exist_ok=True)

    if not os.path.exists(links_file_path):
        with open(links_file_path, "w") as f:
            f.write("# Add YouTube links here, one per line\n")

    if len(sys.argv) > 1:
        url = sys.argv[1]
        if ("playlist" in url) or ("yout" in url):
            start_time = time.time()
            if "playlist" in url:
                download_playlist(url, True, False, "360p", True)
            elif "yout" in url:
                download_from_youtube(url, mp3_mp4_path, True, 0, True, False, "360p", True)
            end_time = time.time()
            print(f"[Downloading took {end_time - start_time} seconds]")
            sys.exit(0)
        else:
            print("~This is not a youtube link~")
            print_help()
            sys.exit(0)

    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
