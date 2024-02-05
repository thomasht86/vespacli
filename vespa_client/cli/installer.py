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
        self.vespa_executable_name = "vespa.exe" if self.os_name == "windows" else "vespa"

    def find_vespa_executable(self, extract_path):
        """Dynamically find the path to the Vespa CLI executable."""
        for root, dirs, files in os.walk(extract_path):
            if self.vespa_executable_name in files:
                return os.path.join(root, self.vespa_executable_name)
        logging.error(f"Vespa CLI executable not found in {extract_path}")
        raise FileNotFoundError(f"{self.vespa_executable_name} not found after extraction")

    @staticmethod
    def get_os_and_architecture():
        """Determine the operating system and architecture."""
        os_name = platform.system().lower()
        machine = platform.machine().lower()
        arch = ARCH_MAP.get(machine, None)  # No default architecture
        if os_name not in SUPPORTED_OS or arch is None:
            raise ValueError(f"Unsupported OS or architecture: OS={os_name}, Arch={machine}")
        logging.info(f"Detected OS: {os_name}, architecture: {machine} mapped to {arch}")
        return os_name, arch

    def download_and_extract_cli(self, version):
        """Download and extract the Vespa CLI."""
        file_extension = "zip" if self.os_name == "windows" else "tar.gz"
        download_url = f"https://github.com/vespa-engine/vespa/releases/download/v{version}/vespa-cli_{version}_{self.os_name}_{self.arch}.{file_extension}"
        file_path = self.download_file(download_url, file_extension)
        extract_path = self.extract_file(file_path, file_extension)
        return extract_path

    @staticmethod
    def download_file(url, file_extension):
        """Download a file to a temporary location."""
        logging.info(f"Starting download from {url}")
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as tmp_file:
            file_path = tmp_file.name
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logging.info(f"Download completed and saved to {file_path}")
            return file_path
        except requests.exceptions.RequestException as e:
            logging.exception("Failed to download file")
            raise

    @staticmethod
    def extract_file(file_path, file_extension):
        """Extract files from a compressed archive."""
        logging.info(f"Extracting file {file_path}")
        extract_path = tempfile.mkdtemp()  # Use a temporary directory for extraction
        try:
            if file_extension == "tar.gz":
                with tarfile.open(file_path) as tar:
                    tar.extractall(path=extract_path)
            elif file_extension == "zip":
                with ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
            logging.info("Extraction completed")
        finally:
            os.remove(file_path)  # Clean up the downloaded archive
        return extract_path

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
        """Create an alias for vespa executable on Unix-like systems in a user-accessible location."""
        # Define the target path within the user's home directory
        user_bin_path = os.path.join(os.environ.get("HOME"), "bin")
        self.ensure_directory_exists(user_bin_path)  # Ensure the directory exists
        target_path = os.path.join(user_bin_path, self.vespa_executable_name)

        # Remove existing vespa executable or symlink if it exists
        if os.path.exists(target_path) or os.path.islink(target_path):
            os.remove(target_path)
        # Create a symlink in the user's bin directory
        os.symlink(vespa_bin_path, target_path)
        logging.info(f"Created symlink for vespa at {target_path}")

        # Add the user's bin directory to PATH if not already present
        self.add_to_user_path(user_bin_path)

    def add_to_user_path(self, new_path):
        """Add the given path to the user's PATH environment variable, persistently."""
        shell_profile = self.detect_shell_profile()
        if shell_profile and new_path not in os.environ.get("PATH", ""):
            with open(shell_profile, "a") as f:
                f.write(f'\n# Add Vespa CLI to PATH\nexport PATH="$PATH:{new_path}"\n')
            logging.info(f"Added {new_path} to PATH in {shell_profile}")

    @staticmethod
    def detect_shell_profile():
        """Detect the user's shell profile script."""
        home = os.environ.get("HOME")
        if os.path.exists(os.path.join(home, ".bash_profile")):
            return os.path.join(home, ".bash_profile")
        elif os.path.exists(os.path.join(home, ".bashrc")):
            return os.path.join(home, ".bashrc")
        elif os.path.exists(os.path.join(home, ".zshrc")):
            return os.path.join(home, ".zshrc")
        else:
            logging.warning("Could not detect shell profile script.")
            return None

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
        """Main installation process with updated executable path handling."""
        try:
            res = requests.get("https://api.github.com/repos/vespa-engine/vespa/releases/latest")
            res.raise_for_status()
            version = res.json()["tag_name"].replace("v", "")
            extract_path = self.download_and_extract_cli(version)
            vespa_bin_path = self.find_vespa_executable(extract_path)  # Use the new method to find the executable
            self.set_executable_permission(vespa_bin_path)
            self.create_alias(vespa_bin_path)
        except Exception as e:
            logging.exception(f"An error occurred during installation: {e}")


if __name__ == "__main__":
    VespaCLIInstaller().run()
