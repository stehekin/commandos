import subprocess
import re
import signal
import os
import requests

def get_control_from_github(github_url):
    """
    Retrieves the content of the 'control' file from GitHub.

    Args:
        github_url (str): The raw URL of the 'control' file.

    Returns:
        str: The content of the file, or None if an error occurs.
    """
    try:
        response = requests.get(github_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching control file from GitHub: {e}")
        return None

def kill_process(username, pattern):
    """
    Kills processes started by a given user that match a regex pattern,
    checking both the command and its arguments.

    Args:
        username (str): The username of the processes to target.
        pattern (str): The regex pattern to match against process command lines and arguments.
    """

    try:
        # Get the list of processes for the given user, including arguments.
        command = ["ps", "-u", username, "-o", "pid,command"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"Error getting process list: {stderr}")
            return

        lines = stdout.strip().split('\n')
        # Skip the header line.
        for line in lines[1:]:
            parts = line.split(maxsplit=1)  # Split only once to keep command with args intact.
            if len(parts) < 2:
                continue

            pid_str, cmd = parts
            pid = int(pid_str.strip())

            if re.search(pattern, cmd):
                try:
                    os.kill(pid, signal.SIGTERM)  # Send SIGTERM first.
                    print(f"Sent SIGTERM to process {pid}: {cmd}")
                except OSError as e:
                    print(f"Error sending SIGTERM to process {pid}: {e}")
                    try:
                        os.kill(pid, signal.SIGKILL)  # Attempt to force kill with SIGKILL.
                        print(f"Sent SIGKILL to process {pid}: {cmd}")
                    except OSError as e2:
                        print(f"Error sending SIGKILL to process {pid}: {e2}")

    except Exception as e:
        print(f"An error occurred: {e}")

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
        print("Control file indicates 'enable' or fetch failed. Proceeding with process killing.")
        kill_process(username, pattern)
    else:
        print("Control file indicates 'disable'. Skipping process killing.")

if __name__ == "__main__":
    username = "501"  # Replace with the actual username.
    pattern = r"vi"  # Replace with the regex pattern.
    github_control_url = "https://raw.githubusercontent.com/stehekin/commandos/main/control"

    check_process(username, pattern, github_control_url)
