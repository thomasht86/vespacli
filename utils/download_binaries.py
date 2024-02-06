import hashlib
import logging
import os
import shutil
import tarfile
import tempfile
from zipfile import ZipFile

import requests


class VespaBinaryDownloader:
    # Constants
    VALID_OS_ARCH = {
        "windows": ["386", "amd64"],
        "darwin": ["amd64", "arm64"],
        "linux": ["amd64", "arm64"],
    }
    # Set installation directory to project root joined with vespacli/go-binaries
    INSTALLATION_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "vespacli",
        "go-binaries",
    )

    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def download_file(self, url):
        logging.info(f"Starting download from {url}")
        file_name = url.split("/")[-1]
        file_path = os.path.join(self.INSTALLATION_DIR, file_name)
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, "wb") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
        logging.info(f"Download complete to {file_path}")
        return file_path

    def extract_file(self, file_path, extract_to):
        logging.info(f"Extracting file {file_path} to {extract_to}")
        if file_path.endswith(".tar.gz"):
            with tarfile.open(file_path, "r:gz") as tar:
                tar.extractall(path=extract_to)
        elif file_path.endswith(".zip"):
            with ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
        os.remove(file_path)

    def ensure_directory_exists(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Ensured directory exists: {directory_path}")

    def download_and_extract_cli(self, version, os_name, arch):
        file_extension = "zip" if os_name == "windows" else "tar.gz"
        download_url = f"https://github.com/vespa-engine/vespa/releases/download/v{version}/vespa-cli_{version}_{os_name}_{arch}.{file_extension}"
        self.ensure_directory_exists(self.INSTALLATION_DIR)
        file_path = self.download_file(download_url)
        self.extract_file(file_path, self.INSTALLATION_DIR)
        return file_path

    def get_latest_version(self):
        logging.info("Retrieving the latest Vespa CLI version")
        response = requests.get(
            "https://api.github.com/repos/vespa-engine/vespa/releases/latest"
        )
        response.raise_for_status()
        return response.json()["tag_name"].strip("v")

    def download_checksum_file(self, version):
        logging.info("Downloading checksum file")
        checksum_url = f"https://github.com/vespa-engine/vespa/releases/download/v{version}/vespa-cli_{version}_sha256sums.txt"
        checksum_file = self.download_file(checksum_url)
        return checksum_file

    def verify_checksum(self, filename, checksum_content):
        logging.info(f"Verifying checksum for {filename}")
        # Checksum file format: <checksum> <filename>
        for line in checksum_content:
            if filename in line:
                sha = line.split()[0]
                # Generate checksum for the file and compare
                file_checksum = hashlib.sha256(open(filename, "rb").read()).hexdigest()
                if file_checksum == sha:
                    logging.info(f"Checksum verified for {filename}")
                else:
                    logging.error(f"Checksum verification failed for {filename}")
                    raise Exception(f"Checksum verification failed for {filename}")

    def run(self):
        version = self.get_latest_version()
        checksum_file = self.download_checksum_file(version)
        checksum_content = open(checksum_file, "r").readlines()
        logging.info(f"Latest Vespa CLI version: {version}")
        for os_name, archs in self.VALID_OS_ARCH.items():
            for arch in archs:
                file_path = self.download_and_extract_cli(version, os_name, arch)
                self.verify_checksum(file_path, checksum_content)

        logging.info("Binary download and extraction complete")


if __name__ == "__main__":
    VespaBinaryDownloader().run()
