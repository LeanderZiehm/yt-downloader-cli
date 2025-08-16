import os
import re
import subprocess

CYAN = "36m"
BRIGHT_CYAN = "96m"
YELLOW = "33m"
BG_CYAN = "46m"
RED = "31m"
LIGHT_GRAY = "37m"
DARK_GRAY = "90m"

def colorize(text, color):
    return f"\033[{color}{text}\033[0m"

def remove_illegal_path_characters(name):
    illegal_characters = r'[<>:"/\\|?*\x00-\x1F\x7F!]'
    cleaned_name = re.sub(illegal_characters, "", name)
    cleaned_name = cleaned_name.replace(" ", "_")
    return cleaned_name

def hasWritePermissions():
    current_directory = os.getcwd()
    if os.access(current_directory, os.W_OK):
        print("Script has permission to save files in the current working directory")
        return True
    else:
        print("Script does not have permission to save files in the current working directory")
        return False

def open_file(path):
    try:
        subprocess.run(['xdg-open', path])
    except Exception as e:
        print(f"Could not open file: {e}")

def open_file_explorer(path):
    try:
        subprocess.run(['xdg-open', path])
    except Exception as e:
        print(f"Could not open file explorer: {e}")

def joinPath(base, dir):
    return os.path.join(base, dir)

def makeAbsolutePath(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
