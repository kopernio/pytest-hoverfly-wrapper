import contextlib
import os
import sys
import zipfile
from subprocess import CalledProcessError, run

import requests

from .logger import logger

OUTPATH = "./hoverfly_executables"  # configure via plugin options
VERSION = "v2.0.0"
HOVERCTL = f"hoverctl{'.exe' if sys.platform == 'win' else ''}"
HOVERFLY = f"hoverfly{'.exe' if sys.platform == 'win' else ''}"

HOVERCTL_PATH = os.path.join(OUTPATH, HOVERCTL)
HOVERFLY_PATH = os.path.join(OUTPATH, HOVERFLY)


def get_platform_architecture():
    if sys.maxsize > 2**32:
        architecture = "amd64"
    else:
        architecture = "386"
    if sys.platform.startswith("linux"):
        platform = "linux"
    elif sys.platform == "darwin":
        platform = "OSX"
        architecture = "amd64"
    elif sys.platform.startswith("win"):
        platform = "windows"
    else:
        raise RuntimeError(f"Unsupported operating system: {sys.platform}")
    return platform, architecture


def binaries_valid():
    """Binaries exist and are runnable"""
    try:
        output_1 = run([HOVERFLY_PATH, "-version"], capture_output=True, check=True)
        run([HOVERCTL_PATH, "version"], capture_output=True, check=True)
        version = output_1.stdout.decode("utf-8").split("\n")[0]
        if version != VERSION:
            logger.info("Version mismatch.")
            return False
    except FileNotFoundError:
        logger.info("Files missing.")
        return False
    except CalledProcessError:
        logger.info("Error running files.")
        return False
    except PermissionError:
        logger.info("Files not executable.")
        return False
    logger.debug("Hoverfly executables are valid.")
    return True


@contextlib.contextmanager
def download():
    platform, architecture = get_platform_architecture()
    # Define the remote file to retrieve
    remote_url = (
        f"https://github.com/SpectoLabs/hoverfly/releases/download/"
        f"{VERSION}/hoverfly_bundle_{platform}_{architecture}.zip"
    )
    # Define the local filename to save data
    local_file = "hf.zip"
    # Make http request for remote file data
    data = requests.get(remote_url, timeout=60)
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
