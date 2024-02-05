import os
import platform
import shutil
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from vespa_client.cli.installer import VespaCLIInstaller

@pytest.fixture
def installer():
    """Fixture to create a VespaCLIInstaller instance for testing."""
    return VespaCLIInstaller()

@pytest.mark.skipif(platform.system().lower() not in VespaCLIInstaller.SUPPORTED_OS, reason="Unsupported OS for this test")
class TestVespaCLIInstaller:
    def test_get_os_and_architecture(self, installer):
        """Test if the correct OS and architecture are detected."""
        os_name, arch = installer.get_os_and_architecture()
        assert os_name in VespaCLIInstaller.SUPPORTED_OS
        assert arch in VespaCLIInstaller.ARCH_MAP.values()

    @pytest.mark.skipif(platform.system().lower() != 'windows', reason="Windows specific test")
    def test_create_alias_windows(self, installer, mocker):
        """Test alias creation on Windows."""
        user_profile_path = 'C:\\Users\\TestUser'
        mocker.patch('os.environ.get', return_value=user_profile_path)
        mocker.patch('os.path.exists', side_effect=lambda path: False)
        mocker.patch('os.makedirs')
        with tempfile.NamedTemporaryFile(suffix=".exe") as temp_file:
            with mocker.patch('shutil.copy') as mock_copy:
                installer.create_alias_windows(temp_file.name)
                mock_copy.assert_called_once_with(temp_file.name, os.path.join(user_profile_path, 'bin', 'vespa.exe'))
    
    
    @pytest.mark.skipif(platform.system().lower() == 'windows', reason="Non-Windows specific test")
    def test_create_alias_unix(self, installer, mocker):
        # TODO: write this
        pass
    
    def test_download_and_extract_cli(self, installer, mocker):
        """Test the download and extraction process."""
        mocker.patch('requests.get')
        temp_file = MagicMock(name='tempfile')
        temp_file.__enter__.return_value.name = 'tempfile'  # Mocking context manager protocol
        mocker.patch('tempfile.NamedTemporaryFile', return_value=temp_file)
        mocker.patch('tarfile.open')
        mocker.patch('zipfile.ZipFile')
        mocker.patch.object(installer, 'extract_file', return_value='/path/to/extracted')
        extract_path = installer.download_and_extract_cli('0.0.1')
        assert extract_path == '/path/to/extracted'

    @pytest.mark.skipif(platform.system().lower() == 'windows', reason="Non-Windows specific test")
    def test_set_executable_permission(self, installer, mocker):
        """Test setting executable permission."""
        temp_file = MagicMock()
        temp_file.name = 'tempfile'
        mocker.patch('os.chmod')
        installer.set_executable_permission(temp_file.name)
        os.chmod.assert_called_once()

    def test_download_file_failure_handling(self, installer, mocker):
        """Test download file handling when a network error occurs."""
        mocker.patch('requests.get', side_effect=Exception("Network error"))
        with pytest.raises(Exception) as exc_info:
            installer.download_file("http://example.com/vespa-cli.tar.gz", "tar.gz")
        assert "Network error" in str(exc_info.value)

        
    def test_extract_file_failure_handling_and_cleanup(self, installer, mocker):
        """Test that extract_file logs and re-raises exceptions, and cleans up the temporary file on failure."""
        # Setup
        file_path = 'path/to/nonexistent.tar.gz'
        file_extension = 'tar.gz'
        temp_dir = '/tmp/fake_dir'
        mocker.patch('tempfile.mkdtemp', return_value=temp_dir)
        mocker.patch('os.remove')

        # Mock tarfile.open or zipfile.ZipFile to raise an exception to simulate extraction failure
        mocker.patch('tarfile.open', side_effect=Exception("Mocked tar extraction failure"))
        # Alternatively, for zip files:
        # mocker.patch('zipfile.ZipFile', side_effect=Exception("Mocked zip extraction failure"))

        # Mock logging to verify error logging
        mocked_logger_error = mocker.patch('logging.error')

        # Execute and Verify
        with pytest.raises(Exception) as exc_info:
            installer.extract_file(file_path, file_extension)

        # Verify the exception was re-raised as expected
        assert "Mocked tar extraction failure" in str(exc_info.value) or "Mocked zip extraction failure" in str(exc_info.value)

        # Verify cleanup was performed
        os.remove.assert_called_with(file_path)

        # Verify logging of the error
        mocked_logger_error.assert_called()



    @pytest.mark.skip(reason="Integration test that requires network access")
    def test_get_latest_version(self, installer):
        """Test retrieval of the latest version from GitHub."""
        version = installer.get_latest_version()
        assert version, "Should retrieve a version string"

if __name__ == "__main__":
    pytest.main()
