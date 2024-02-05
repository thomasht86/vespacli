import logging
import os
import platform
import shutil
import tarfile
import tempfile
from zipfile import ZipFile
import subprocess

import requests

class VespaCLIInstaller:
    # Constants
    SUPPORTED_OS = ["windows", "darwin", "linux"]
    ARCH_MAP = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}
    
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

    def get_os_and_architecture(self):
        """Determine the operating system and architecture."""
        os_name = platform.system().lower()
        machine = platform.machine().lower()
        arch = self.ARCH_MAP.get(machine, None)  # No default architecture
        if os_name not in self.SUPPORTED_OS or arch is None:
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
            logging.exception(f"Failed to download file: {e}")
            raise

    @staticmethod
    def extract_file(file_path, file_extension):
        """Extract files from a compressed archive, re-raise exceptions after cleanup."""
        logging.info(f"Extracting file {file_path}")
        extract_path = tempfile.mkdtemp()
        try:
            if file_extension == "tar.gz":
                with tarfile.open(file_path) as tar:
                    tar.extractall(path=extract_path)
            elif file_extension == "zip":
                with ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
            logging.info("Extraction completed")
        except Exception as e:
            logging.error(f"Failed to extract file {file_path}: {e}")
            raise  # Re-raise the exception after logging
        finally:
            os.remove(file_path)  # Ensure the downloaded file is removed after extraction
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
            # Update system PATH
            self.update_system_path_windows(os.path.dirname(target_path))
            logging.info(f"Created alias for vespa in {target_path}")
        else:
            logging.info(f"Alias for vespa already exists at {target_path}")

    def create_alias_unix(self, vespa_bin_path):
        """Create an alias for vespa executable on Unix-like systems."""
        shell_profile = self.detect_shell_profile()
        if not shell_profile:
            logging.error("Shell profile not found. Manual alias creation required.")
            return

        alias_command = f'\n# Alias for Vespa CLI\nalias vespa="{vespa_bin_path}"\n'
        try:
            with open(shell_profile, "a") as f:
                f.write(alias_command)
            logging.info(f"Added alias for vespa in {shell_profile}")

            # Prompt the user to source their profile or open a new shell to apply changes
            logging.info(f"Please source your shell profile ({shell_profile}) or open a new terminal session for the alias to take effect.")
        except Exception as e:
            logging.error(f"Failed to add alias for vespa. {e}")

    @staticmethod
    def update_system_path_windows(new_path):
        """Update the user-level PATH variable on Windows."""
        subprocess.run(["setx", "PATH", f"%PATH%;{new_path}"], shell=True)
        logging.info("Successfully added Vespa CLI to system PATH.")

    def detect_shell_profile(self):
        """Detect the user's shell profile script."""
        home = os.environ.get("HOME")
        shell_profiles = [
            ".bash_profile",
            ".bashrc",
            ".zshrc",
            ".config/fish/config.fish",
        ]
        for profile in shell_profiles:
            profile_path = os.path.join(home, profile)
            if os.path.exists(profile_path):
                return profile_path
        logging.warning("Could not detect shell profile script.")
        return None

    def create_alias(self, vespa_bin_path):
        """Create an alias for vespa executable based on the operating system."""
        if self.os_name == "windows":
            self.create_alias_windows(vespa_bin_path)
        else:
            self.create_alias_unix(vespa_bin_path)

    def get_latest_version(self):
        """Retrieve the latest Vespa CLI version."""
        try:
            res = requests.get("https://api.github.com/repos/vespa-engine/vespa/releases/latest")
            res.raise_for_status()
            version = res.json()["tag_name"].replace("v", "")
            logging.info(f"Latest Vespa CLI version: {version}")
            return version
        except requests.exceptions.RequestException as e:
            logging.exception(f"Failed to retrieve the latest version: {e}")
            raise
    
    def check_brew_installed(self):
        """Check if brew is installed on macOS."""
        try:
            res = subprocess.run(["which", "brew"], capture_output=True, text=True)
            if res.returncode == 0:
                logging.info("Homebrew is installed")
                return True
            else:
                logging.info("Homebrew is not installed. Attempting binary installation.")
                return False
        except Exception as e:
            logging.exception(f"An error occurred while checking for Homebrew: {e}")
            return False

    def run(self):
        """Main installation process."""
        try:
            if self.os_name == "darwin" and self.check_brew_installed():
                logging.info("Using Homebrew to install Vespa CLI")
                install_cmd = subprocess.run(["brew", "install", "vespa-cli"], capture_output=True, text=True)
                if install_cmd.returncode == 0:
                    logging.info("Vespa CLI installed successfully")
                    return
                else:
                    logging.info(f"Failed to install Vespa CLI with homebrew: {install_cmd.stderr}. Attempting binary installation.")
            version = self.get_latest_version()
            extract_path = self.download_and_extract_cli(version)
            vespa_bin_path = self.find_vespa_executable(extract_path)
            self.set_executable_permission(vespa_bin_path)
            self.create_alias(vespa_bin_path)
        except Exception as e:
            logging.exception(f"An error occurred during installation: {e}")


if __name__ == "__main__":
    VespaCLIInstaller().run()
