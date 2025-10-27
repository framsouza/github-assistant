"""
Tests for GitHubConnector module.
"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import git

from connectors.github_connector import GitHubConnector


class TestGitHubConnector(unittest.TestCase):
    """Test cases for GitHubConnector class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_repo_url = "https://github.com/test/repo.git"
        self.test_local_path = "/tmp/test_repo"
        self.connector = GitHubConnector()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_local_path = os.path.join(self.temp_dir, "test_repo")

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('git.Repo.clone_from')
    def test_clone_repository_success(self, mock_clone):
        """Test successful repository cloning."""
        # Arrange
        mock_repo = MagicMock()
        mock_clone.return_value = mock_repo
        
        # Act
        result = self.connector.clone_repository(self.test_repo_url, self.test_local_path)
        
        # Assert
        self.assertTrue(result)
        mock_clone.assert_called_once_with(self.test_repo_url, self.test_local_path)

    @patch('git.Repo.clone_from')
    def test_clone_repository_failure(self, mock_clone):
        """Test repository cloning failure."""
        # Arrange
        mock_clone.side_effect = git.exc.GitCommandError("clone", "error")
        
        # Act
        result = self.connector.clone_repository(self.test_repo_url, self.test_local_path)
        
        # Assert
        self.assertFalse(result)

    @patch('git.Repo.clone_from')
    @patch('os.path.exists')
    def test_clone_repository_existing_directory(self, mock_exists, mock_clone):
        """Test cloning when directory already exists."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        result = self.connector.clone_repository(self.test_repo_url, self.test_local_path)
        
        # Assert
        self.assertFalse(result)
        mock_clone.assert_not_called()

    def test_get_supported_file_extensions(self):
        """Test getting supported file extensions."""
        # Act
        extensions = self.connector.get_supported_file_extensions()
        
        # Assert
        self.assertIsInstance(extensions, list)
        self.assertIn('.py', extensions)
        self.assertIn('.js', extensions)
        self.assertIn('.md', extensions)

    def test_is_file_supported_python(self):
        """Test file support check for Python files."""
        # Act & Assert
        self.assertTrue(self.connector.is_file_supported("test.py"))
        self.assertTrue(self.connector.is_file_supported("module/__init__.py"))

    def test_is_file_supported_javascript(self):
        """Test file support check for JavaScript files."""
        # Act & Assert
        self.assertTrue(self.connector.is_file_supported("script.js"))
        self.assertTrue(self.connector.is_file_supported("app.jsx"))

    def test_is_file_not_supported(self):
        """Test file support check for unsupported files."""
        # Act & Assert
        self.assertFalse(self.connector.is_file_supported("image.png"))
        self.assertFalse(self.connector.is_file_supported("document.pdf"))
        self.assertFalse(self.connector.is_file_supported("binary.exe"))

    def test_should_skip_directory_hidden(self):
        """Test skipping hidden directories."""
        # Act & Assert
        self.assertTrue(self.connector.should_skip_directory(".git"))
        self.assertTrue(self.connector.should_skip_directory(".vscode"))

    def test_should_skip_directory_cache(self):
        """Test skipping cache directories."""
        # Act & Assert
        self.assertTrue(self.connector.should_skip_directory("__pycache__"))
        self.assertTrue(self.connector.should_skip_directory("node_modules"))

    def test_should_not_skip_regular_directory(self):
        """Test not skipping regular directories."""
        # Act & Assert
        self.assertFalse(self.connector.should_skip_directory("src"))
        self.assertFalse(self.connector.should_skip_directory("lib"))

    @patch('builtins.open', new_callable=mock_open, read_data="print('Hello World')")
    def test_read_file_content_success(self, mock_file):
        """Test successful file content reading."""
        # Act
        content = self.connector.read_file_content("test.py")
        
        # Assert
        self.assertEqual(content, "print('Hello World')")
        mock_file.assert_called_once_with("test.py", 'r', encoding='utf-8')

    @patch('builtins.open')
    def test_read_file_content_encoding_error(self, mock_file):
        """Test file reading with encoding errors."""
        # Arrange
        mock_file.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')
        
        # Act
        content = self.connector.read_file_content("test.py")
        
        # Assert
        self.assertIsNone(content)

    @patch('builtins.open')
    def test_read_file_content_file_not_found(self, mock_file):
        """Test file reading when file doesn't exist."""
        # Arrange
        mock_file.side_effect = FileNotFoundError()
        
        # Act
        content = self.connector.read_file_content("nonexistent.py")
        
        # Assert
        self.assertIsNone(content)

    @patch('os.walk')
    @patch.object(GitHubConnector, 'read_file_content')
    def test_extract_code_files(self, mock_read_content, mock_walk):
        """Test extracting code files from repository."""
        # Arrange
        mock_walk.return_value = [
            ('/repo', ['src'], ['main.py', 'README.md']),
            ('/repo/src', [], ['module.py', 'test.txt'])
        ]
        mock_read_content.side_effect = [
            "print('main')",  # main.py
            "# README",       # README.md
            "def func(): pass",  # module.py
            None              # test.txt (not supported)
        ]
        
        # Act
        files = self.connector.extract_code_files("/repo")
        
        # Assert
        self.assertEqual(len(files), 3)
        self.assertEqual(files[0]['file_path'], '/repo/main.py')
        self.assertEqual(files[0]['content'], "print('main')")
        self.assertEqual(files[1]['file_path'], '/repo/README.md')
        self.assertEqual(files[2]['file_path'], '/repo/src/module.py')

    @patch('os.walk')
    def test_extract_code_files_skip_directories(self, mock_walk):
        """Test that certain directories are skipped during extraction."""
        # Arrange
        mock_walk.return_value = [
            ('/repo', ['.git', 'src', '__pycache__'], ['main.py']),
            ('/repo/.git', [], ['config']),
            ('/repo/src', [], ['module.py']),
            ('/repo/__pycache__', [], ['main.pyc'])
        ]
        
        with patch.object(self.connector, 'read_file_content') as mock_read:
            mock_read.side_effect = ["print('main')", "def func(): pass"]
            
            # Act
            files = self.connector.extract_code_files("/repo")
            
            # Assert
            # Should only call read_file_content for main.py and module.py
            self.assertEqual(mock_read.call_count, 2)
            file_paths = [f['file_path'] for f in files]
            self.assertIn('/repo/main.py', file_paths)
            self.assertIn('/repo/src/module.py', file_paths)

    @patch.object(GitHubConnector, 'clone_repository')
    @patch.object(GitHubConnector, 'extract_code_files')
    def test_process_repository_success(self, mock_extract, mock_clone):
        """Test successful repository processing."""
        # Arrange
        mock_clone.return_value = True
        mock_extract.return_value = [
            {'file_path': '/repo/main.py', 'content': 'print("hello")'}
        ]
        
        # Act
        result = self.connector.process_repository(
            self.test_repo_url, 
            self.test_local_path
        )
        
        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_path'], '/repo/main.py')
        mock_clone.assert_called_once_with(self.test_repo_url, self.test_local_path)
        mock_extract.assert_called_once_with(self.test_local_path)

    @patch.object(GitHubConnector, 'clone_repository')
    def test_process_repository_clone_failure(self, mock_clone):
        """Test repository processing when cloning fails."""
        # Arrange
        mock_clone.return_value = False
        
        # Act
        result = self.connector.process_repository(
            self.test_repo_url, 
            self.test_local_path
        )
        
        # Assert
        self.assertEqual(result, [])

    def test_validate_github_url_valid(self):
        """Test GitHub URL validation with valid URLs."""
        # Act & Assert
        self.assertTrue(self.connector.validate_github_url("https://github.com/user/repo"))
        self.assertTrue(self.connector.validate_github_url("https://github.com/user/repo.git"))
        self.assertTrue(self.connector.validate_github_url("git@github.com:user/repo.git"))

    def test_validate_github_url_invalid(self):
        """Test GitHub URL validation with invalid URLs."""
        # Act & Assert
        self.assertFalse(self.connector.validate_github_url("https://gitlab.com/user/repo"))
        self.assertFalse(self.connector.validate_github_url("not-a-url"))
        self.assertFalse(self.connector.validate_github_url(""))

    def test_get_repository_name_from_url(self):
        """Test extracting repository name from URL."""
        # Act & Assert
        self.assertEqual(
            self.connector.get_repository_name_from_url("https://github.com/user/myrepo"),
            "myrepo"
        )
        self.assertEqual(
            self.connector.get_repository_name_from_url("https://github.com/user/myrepo.git"),
            "myrepo"
        )
        self.assertEqual(
            self.connector.get_repository_name_from_url("git@github.com:user/myrepo.git"),
            "myrepo"
        )


if __name__ == '__main__':
    unittest.main()
