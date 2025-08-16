import os
from pytubefix import YouTube as yt
import googleapiclient.discovery as dis
from urllib.parse import parse_qs, urlparse
from tqdm import tqdm

from utils import remove_illegal_path_characters, colorize, DARK_GRAY
from errors import log_missing_stream, log_error
from config import YOUTUBE_API_KEY

youtube = dis.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_playlist_id(url):
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]
    return playlist_id

def get_playlist_name(playlist_id):
    playlist_response = youtube.playlists().list(part="snippet", id=playlist_id).execute()
    playlist_name = playlist_response["items"][0]["snippet"]["title"]
    return playlist_name

def get_all_links_from_playlist(playlist_id):
    request = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=100)
    response = request.execute()
    playlistItems = []

    while request is not None:
        response = request.execute()
        playlistItems += response["items"]
        request = youtube.playlistItems().list_next(request, response)

    links = []
    for item in playlistItems:
        video_id = item["snippet"]["resourceId"]["videoId"]
        link = f"https://www.youtube.com/watch?v={video_id}"
        links.append(link)

    return links

class YouTubeDownloader:
    def __init__(self, url, target_path, show_progress=False, position=0, download_video=True, max_resolution=False, target_resolution="360p", save_audio_as_mp3=True):
        self.url = url
        self.target_path = target_path
        self.show_progress = show_progress
        self.position = position
        self.download_video = download_video
        self.max_resolution = max_resolution
        self.target_resolution = target_resolution
        self.save_audio_as_mp3 = save_audio_as_mp3

    def download(self):
        try:
            os.makedirs(self.target_path, exist_ok=True)

            ytUrl = yt(self.url, use_oauth=True, allow_oauth_cache=True)
            streams = ytUrl.streams
            extension = ".mp4"

            if self.download_video:
                if self.max_resolution:
                    file = streams.filter(progressive=True, file_extension="mp4").order_by("resolution").last()
                else:
                    file = streams.filter(res=self.target_resolution, progressive=True, file_extension="mp4").first()
            else:
                file = streams.filter(only_audio=True).first()
                if self.save_audio_as_mp3:
                    extension = ".mp3"

            if file is None:
                log_missing_stream(self.url)
                return None

            title = remove_illegal_path_characters(ytUrl.title or "Downloading")[:60]

            pbar = None
            last_n = 0

            def on_progress(stream, chunk, bytes_remaining):
                nonlocal pbar, last_n
                if not self.show_progress:
                    return
                total = getattr(stream, "filesize", 0)
                downloaded = max(0, total - bytes_remaining)

                if pbar is None:
                    pbar = tqdm(
                        total=total,
                        unit="B",
                        unit_scale=True,
                        desc=title,
                        position=self.position,
                        leave=True,
                        dynamic_ncols=True,
                    )
                delta = downloaded - last_n
                if delta > 0:
                    pbar.update(delta)
                    last_n = downloaded

            def on_complete(stream, file_path):
                if pbar:
                    total = getattr(stream, "filesize", 0)
                    if total and pbar.n < total:
                        pbar.update(total - pbar.n)
                    pbar.close()

            ytUrl.register_on_progress_callback(on_progress)
            ytUrl.register_on_complete_callback(on_complete)

            fileName = file.default_filename[:-4] + extension
            fileName = fileName.encode("ascii", "ignore").decode("ascii")

            if not self.show_progress:
                print(colorize(f"[Downloading] ", DARK_GRAY) + fileName)

            file.download(self.target_path, filename=fileName)

            if not self.show_progress:
                print(colorize(f"[Saved] ", DARK_GRAY) + os.path.join(self.target_path, fileName))

            return fileName

        except Exception as e:
            log_error(self.url, str(e))
            return None
