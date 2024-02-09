from download_binaries import VespaBinaryDownloader
from vespacli._version_generated import vespa_version
import sys

if __name__ == "__main__":
    downloader = VespaBinaryDownloader()
    new_version = downloader.get_latest_version()
    found_newer = new_version != vespa_version
    if found_newer:
        print(f"New version found: {new_version}")
    else:
        print(f"Latest version already installed: {vespa_version}")
    # Return version number to be used in CI/CD pipelines
    sys.exit(0 if found_newer else 1)