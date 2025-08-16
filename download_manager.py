import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from youtube_client import YouTubeDownloader, get_playlist_id, get_all_links_from_playlist, get_playlist_name
from utils import remove_illegal_path_characters, joinPath, colorize, YELLOW, RED
from config import (
    SYNC_DOWNLOADS,
    MAX_WORKERS,
    SHOW_PER_VIDEO_PROGRESS,
    SHOW_PER_VIDEO_PROGRESS_IN_THREADS,
    BASE_DIR
)

links_file_path = os.path.join(BASE_DIR, "links.txt")
links_download_path = os.path.join(BASE_DIR, "DownloadFromLinks")

def download_from_youtube(url, target_path, show_progress, position, download_video, max_resolution, target_resolution, save_audio_as_mp3):
    downloader = YouTubeDownloader(
        url=url,
        target_path=target_path,
        show_progress=show_progress,
        position=position,
        download_video=download_video,
        max_resolution=max_resolution,
        target_resolution=target_resolution,
        save_audio_as_mp3=save_audio_as_mp3
    )
    return downloader.download()

def download_links(target_path, download_video, max_resolution, target_resolution, save_audio_as_mp3):
    os.makedirs(target_path, exist_ok=True)
    try:
        with open(links_file_path) as file:
            urls = [line.rstrip() for line in file if line.strip() and not line.startswith("#")]

        total = len(urls)
        print(f"[Downloading {total} files to {target_path}]")

        if total == 0:
            print(colorize("[No URLs found in links.txt]", YELLOW))
            return

        if SYNC_DOWNLOADS:
            with tqdm(total=total, desc="Overall", unit="video") as overall:
                for u in urls:
                    download_from_youtube(
                        u, target_path, SHOW_PER_VIDEO_PROGRESS, 1, download_video, max_resolution, target_resolution, save_audio_as_mp3
                    )
                    overall.update(1)
        else:
            if SHOW_PER_VIDEO_PROGRESS_IN_THREADS:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                    futures = []
                    for idx, u in enumerate(urls, start=1):
                        futures.append(ex.submit(download_from_youtube, u, target_path, True, idx, download_video, max_resolution, target_resolution, save_audio_as_mp3))
                    with tqdm(total=total, desc="Overall", unit="video", position=0) as overall:
                        for f in futures:
                            f.result()
                            overall.update(1)
            else:
                from functools import partial
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                    work = list(ex.map(partial(download_from_youtube, target_path=target_path, show_progress=False, position=0, download_video=download_video, max_resolution=max_resolution, target_resolution=target_resolution, save_audio_as_mp3=save_audio_as_mp3), urls))
                with tqdm(total=total, desc="Overall", unit="video") as overall:
                    for _ in range(total):
                        overall.update(1)

    except FileNotFoundError:
        print(colorize(f"Links file not found at {links_file_path}", RED))
        with open(links_file_path, "w") as f:
            f.write("# Add YouTube links here, one per line\n")
        print(f"Created empty links file at {links_file_path}")

def download_playlist(url, download_video, max_resolution, target_resolution, save_audio_as_mp3):
    playlist_id = get_playlist_id(url)
    urls = get_all_links_from_playlist(playlist_id)
    playlist_name = get_playlist_name(playlist_id)

    usable_playlist_name = remove_illegal_path_characters(playlist_name)
    usable_playlist_name = usable_playlist_name.encode("ascii", "ignore").decode("ascii")
    download_path = joinPath(BASE_DIR, usable_playlist_name)
    
    os.makedirs(download_path, exist_ok=True)

    print(f"[Downloading {len(urls)} files from playlist: {playlist_name}]")
    for u in urls:
        download_from_youtube(u, download_path, False, 0, download_video, max_resolution, target_resolution, save_audio_as_mp3)
