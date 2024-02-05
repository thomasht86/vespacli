import logging
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile

import requests

# Constants
SUPPORTED_OS = ["windows", "darwin", "linux"]
ARCH_MAP = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}


class VespaCLIInstaller:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.os_name, self.arch = self.get_os_and_architecture()
        self.vespa_cli_path = ""
        self.vespa_executable_name = "vespa.exe" if self.os_name == "windows" else "vespa"

    @staticmethod
    def get_os_and_architecture():
        """Determine the operating system and architecture."""
        os_name = platform.system().lower()
        machine = platform.machine().lower()
        arch = ARCH_MAP.get(machine, "386")  # Default to "386" for unknown architectures
        if os_name not in SUPPORTED_OS:
            raise ValueError(f"Unsupported OS: {os_name}")
        logging.info(f"Detected OS: {os_name}, architecture: {machine} mapped to {arch}")
        return os_name, arch

    def download_and_extract_cli(self, version):
        """Download and extract the Vespa CLI."""
        file_extension = "zip" if self.os_name == "windows" else "tar.gz"
        download_url = f"https://github.com/vespa-engine/vespa/releases/download/v{version}/vespa-cli_{version}_{self.os_name}_{self.arch}.{file_extension}"
        tar_file_path = self.download_file(download_url, file_extension)
        self.extract_file(tar_file_path, file_extension)
        logging.info("Vespa CLI has been successfully installed.")

    @staticmethod
    def download_file(url, file_extension):
        """Download a file to a temporary location."""
        logging.info(f"Starting download from {url}")
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as tmp_file:
            tar_file_path = tmp_file.name
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(tar_file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logging.info(f"Download completed and saved to {tar_file_path}")
            return tar_file_path
        except requests.exceptions.RequestException as e:
            logging.exception("Failed to download file")
            raise

    @staticmethod
    def extract_file(file_path, file_extension):
        """Extract files from a compressed archive."""
        logging.info(f"Extracting file {file_path}")
        try:
            if file_extension == "tar.gz":
                with tarfile.open(file_path) as tar:
                    tar.extractall(path=".")
            elif file_extension == "zip":
                with ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(".")
            logging.info("Extraction completed")
        finally:
            os.remove(file_path)

    @staticmethod
    def set_executable_permission(file_path):
        """Set executable permission for Unix-like systems."""
        if platform.system().lower() != "windows":
            os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
            logging.info(f"Set executable permission for {file_path}")

    @staticmethod
    def ensure_directory_exists(directory_path):
        """Ensure the target directory exists."""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logging.info(f"Created directory {directory_path}")

    def create_alias_windows(self, vespa_bin_path):
        """Create an alias for vespa executable on Windows."""
        target_path = os.path.join(os.environ.get("USERPROFILE"), "bin", self.vespa_executable_name)
        self.ensure_directory_exists(os.path.dirname(target_path))
        if not os.path.exists(target_path):
            shutil.copy(vespa_bin_path, target_path)
        self.add_to_path(os.path.dirname(target_path))

    def create_alias_unix(self, vespa_bin_path):
        """Create an alias for vespa executable on Unix-like systems."""
        target_path = "/usr/local/bin/vespa"
        if os.path.exists(target_path) or os.path.islink(target_path):
            os.remove(target_path)
        os.symlink(vespa_bin_path, target_path)
        logging.info(f"Created symlink for vespa at {target_path}")

    def create_alias(self, vespa_bin_path):
        """Create an alias for vespa executable based on the operating system."""
        if self.os_name == "windows":
            self.create_alias_windows(vespa_bin_path)
        else:
            self.create_alias_unix(vespa_bin_path)

    def add_to_path(self, new_path):
        """Add the given path to the system's PATH environment variable on Windows."""
        if self.os_name == "windows":
            self.update_system_path_windows(new_path)

    @staticmethod
    def update_system_path_windows(new_path):
        """Update the system's PATH variable on Windows."""
        try:
            subprocess.run(["setx", "PATH", f"%PATH%;{new_path}"], check=True)
            logging.info("Successfully added Vespa CLI to PATH.")
        except subprocess.SubprocessError as e:
            logging.exception("Failed to update system PATH")

    def run(self):
        """Main installation process."""
        try:
            res = requests.get("https://api.github.com/repos/vespa-engine/vespa/releases/latest")
            res.raise_for_status()
            version = res.json()["tag_name"].replace("v", "")
            self.download_and_extract_cli(version)
            vespa_bin_path = os.path.abspath(f"vespa-cli_{version}_{self.arch}/bin/{self.vespa_executable_name}")
            self.set_executable_permission(vespa_bin_path)
            self.create_alias(vespa_bin_path)
        except Exception as e:
            logging.exception(f"An error occurred during installation: {e}")


if __name__ == "__main__":
    VespaCLIInstaller().run()
