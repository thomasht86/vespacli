import logging
import os
import platform
import shutil
import subprocess
import tempfile
import requests
from zipfile import ZipFile
import tarfile

class VespaCLIInstaller:
    # Constants
    SUPPORTED_OS = ["windows", "darwin", "linux"]
    ARCH_MAP = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.os_name, self.arch = self.get_os_and_architecture()
        self.vespa_executable_name = "vespa.exe" if self.os_name == "windows" else "vespa"
        self.installation_path = self.get_installation_path()

    def get_installation_path(self):
        """Determine the installation path based on the operating system."""
        if self.os_name == "windows":
            return os.path.join(os.environ.get("USERPROFILE"), "bin")
        else:
            # Prefer ~/.local/bin if it exists, otherwise fallback to ~/bin
            local_bin = os.path.expanduser("~/.local/bin")
            if not os.path.exists(local_bin):
                os.makedirs(local_bin, exist_ok=True)
            return local_bin

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
        arch = self.ARCH_MAP.get(machine, None)
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
        """Extract files from a compressed archive."""
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
        finally:
            os.remove(file_path)  # Ensure the downloaded file is removed after extraction
        return extract_path

    def set_executable_permission(self, file_path):
        """Set executable permission for Unix-like systems."""
        if self.os_name != "windows":
            os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
            logging.info(f"Set executable permission for {file_path}")

    def ensure_directory_exists(self, directory_path):
        """Ensure the target directory exists."""
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Ensured directory exists: {directory_path}")

    def install_vespa_cli(self, vespa_bin_path):
        """Install the Vespa CLI executable to a permanent location."""
        self.ensure_directory_exists(self.installation_path)
        target_path = os.path.join(self.installation_path, self.vespa_executable_name)
        if not os.path.exists(target_path):
            shutil.move(vespa_bin_path, target_path)
            self.set_executable_permission(target_path)
            logging.info(f"Vespa CLI installed successfully at {target_path}")
            self.update_shell_profile(self.installation_path)
        else:
            logging.info(f"Vespa CLI already installed at {target_path}")

    def update_shell_profile(self, installation_path):
        """Append the installation path to the PATH environment variable in the user's shell profile."""
        shell = os.environ.get('SHELL', '')
        if 'zsh' in shell:
            profile = os.path.expanduser('~/.zshrc')
        elif 'bash' in shell:
            profile = os.path.expanduser('~/.bash_profile') if os.path.exists(os.path.expanduser('~/.bash_profile')) else os.path.expanduser('~/.bashrc')
        else:
            logging.info("Unsupported shell for automatic PATH update.")
            return

        path_update_command = f'\nexport PATH="{installation_path}:$PATH"\n'
        try:
            with open(profile, 'a') as file:
                file.write(path_update_command)
            logging.info(f"Updated {profile} with PATH to Vespa CLI.")
        except Exception as e:
            logging.error(f"Failed to update shell profile: {e}")

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

    def run(self):
        """Main installation process."""
        try:
            version = self.get_latest_version()
            extract_path = self.download_and_extract_cli(version)
            vespa_bin_path = self.find_vespa_executable(extract_path)
            self.install_vespa_cli(vespa_bin_path)
        except Exception as e:
            logging.exception(f"An error occurred during installation: {e}")

if __name__ == "__main__":
    VespaCLIInstaller().run()
