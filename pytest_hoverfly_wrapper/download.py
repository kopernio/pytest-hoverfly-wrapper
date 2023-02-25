import contextlib
import os
import sys
from subprocess import Popen

import requests
import zipfile

OUTPATH = "./hoverfly_executables" # configure via plugin options
VERSION = "v2.0.0"
HOVERCTL = "hoverctl"
HOVERFLY = "hoverfly"

HOVERCTL_PATH = os.path.join(OUTPATH, HOVERCTL)
HOVERFLY_PATH = os.path.join(OUTPATH, HOVERFLY)


# TODO unit tests
# TODO work into plugin
# TODO run pylint/black
# TODO make outpath configurable?

def get_platform_architecture():
    if sys.platform.startswith("linux"):
        platform = "linux"
        if sys.maxsize > 2**32:
            architecture = "amd64"
        else:
            architecture = "386"
    elif sys.platform == "darwin":
        platform = "OSX"
        architecture = "amd64"
    # elif sys.platform.startswith('win'):
    #     platform = 'windows'
    #     architecture = '386'
    else:
        raise RuntimeError(
            "Could not determine chromedriver download URL for this platform."
        )
    return platform, architecture
from subprocess import run


def binaries_valid():
    """Binaries exist and are runnable"""
    try:
        output_1 = run([HOVERFLY_PATH, "-version"], capture_output=True)
        output_2 = run([HOVERCTL_PATH, "version"], capture_output=True)
        version = output_1.stdout.decode("utf-8").split("\n")[0]
        if output_1.returncode != 0 or output_2.returncode != 0:
            print("Error running files.")
            return False

        if version != VERSION:
            print("Version mismatch. Redownloading")
            return False
    except FileNotFoundError:
        print("Files missing. Redownloading")
        return False
    except PermissionError:
        print("Files not executable. Redownloading")
        return False
    print("Files look good.")
    return True


@contextlib.contextmanager
def download():
    platform, architecture = get_platform_architecture()
    # Define the remote file to retrieve
    remote_url = f"https://github.com/SpectoLabs/hoverfly/releases/download/{VERSION}/hoverfly_bundle_{platform}_{architecture}.zip"
    # Define the local filename to save data
    local_file = "hf.zip"
    # Make http request for remote file data
    data = requests.get(remote_url)
    # Save file data to local copy
    with open(local_file, "wb") as file:
        file.write(data.content)
    yield local_file
    os.remove(local_file)


def unzip(path_to_zip_file):
    with zipfile.ZipFile(path_to_zip_file, "r") as zip_ref:
        zip_ref.extractall(OUTPATH)
    for executable in (HOVERFLY_PATH, HOVERCTL_PATH):
        if not os.access(executable, os.X_OK):
            os.chmod(executable, 0o744)


def manage_executables():
    if binaries_valid():
        return
    with download() as zip_file_name:
        unzip(zip_file_name)

if __name__ == "__main__":
    manage_executables()