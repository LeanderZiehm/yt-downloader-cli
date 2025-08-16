import os
from utils import colorize, RED

links_error_file_path = os.path.join(os.path.expanduser("~"), "syncthing", "yt", "linksError.txt")

def log_error(url, error_msg):
    print(colorize(f"[ERROR: {error_msg}] {url}", RED))
    with open(links_error_file_path, "a") as f:
        f.write(f"{url}\n")

def log_missing_stream(url):
    print(colorize(f"[No matching stream found] {url}", RED))
    with open(links_error_file_path, "a") as f:
        f.write(f"{url}\n")

