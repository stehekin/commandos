#!/usr/bin/env python3
import subprocess
import re
import signal
import os

DEBUG_FILE = "/tmp/.commandos"

def log(message):
    """Logs messages to the debug file, overwriting it."""
    try:
        with open(DEBUG_FILE, "w") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")  # Fallback to stdout if log file fails

def has_internet():
    """Checks if the node has internet access using /usr/bin/curl."""
    try:
        command = ["/usr/bin/curl", "-s", "--head", "https://www.google.com", "-o", "/dev/null"]
        subprocess.run(command, check=True) #check=True raises an exception on error
        return True
    except subprocess.CalledProcessError:
        return False

def get_control_from_github(github_url):
    """
    Retrieves the content of the 'control' file from GitHub using /usr/bin/curl.

    Args:
        github_url (str): The raw URL of the 'control' file.

    Returns:
        str: The content of the file, or None if an error occurs.
    """
    if not has_internet():
        log("No internet access. Skipping GitHub control check.")
        return None
    try:
        command = [
            "/usr/bin/curl",
            "-s",  # Silent mode
            "-H", "Cache-Control: no-cache, no-store, must-revalidate",
            "-H", "Pragma: no-cache",
            "-H", "Expires: 0",
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            github_url,
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            log(f"Error fetching control file with /usr/bin/curl: {stderr}")
            return None

        return stdout.strip()

    except FileNotFoundError:
        log("Error: /usr/bin/curl command not found.")
        return None
    except Exception as e:
        log(f"An error occurred: {e}")
        return None

def kill_process(username, pattern):
    """
    Kills processes started by a given user that match a regex pattern,
    checking both the command and its arguments (case-insensitive). Uses SIGKILL.

    Args:
        username (str): The username of the processes to target.
        pattern (str): The regex pattern to match against process command lines and arguments.
    """

    try:
        command = ["ps", "-u", username, "-o", "pid,command"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            log(f"Error getting process list: {stderr}")
            return

        lines = stdout.strip().split('\n')
        for line in lines[1:]:
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue

            pid_str, cmd = parts
            pid = int(pid_str.strip())

            if re.search(pattern, cmd, re.IGNORECASE):
                try:
                    os.kill(pid, signal.SIGKILL)
                    log(f"Sent SIGKILL to process {pid}: {cmd}")
                except OSError as e:
                    log(f"Error sending SIGKILL to process {pid}: {e}")

    except Exception as e:
        log(f"An error occurred: {e}")

def check_process(username, pattern, github_control_url):
    """
    Checks if process killing should be enabled based on GitHub control file, and if so, kills matching processes.

    Args:
        username (str): The username of the processes to target.
        pattern (str): The regex pattern to match against process command lines and arguments.
        github_control_url (str): The raw URL of the 'control' file on GitHub.
    """
    control_content = get_control_from_github(github_control_url)

    if control_content == "enable" or control_content is None:
        log("Control file indicates 'enable' or fetch failed. Proceeding with process killing.")
        kill_process(username, pattern)
    else:
        log("Control file indicates 'disable'. Skipping process killing.")

if __name__ == "__main__":
    github_control_url = "https://raw.githubusercontent.com/stehekin/commandos/main/control"

    process_targets = [
        {"username": "0", "pattern": r"protonvpn"},
        {"username": "501", "pattern": r"minecraft"},
        {"username": "502", "pattern": r"minecraft"},        
    ]

    for target in process_targets:
        check_process(target["username"], target["pattern"], github_control_url)
