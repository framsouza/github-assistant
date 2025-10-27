"""
GitHub Connector - Handles repository cloning and management.

This module provides functionality to clone GitHub repositories with retry logic
and proper error handling.
"""

import os
import subprocess
import time
import re
from typing import Optional, List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
from urllib.parse import urlparse
from pathlib import Path
import git


@dataclass
class GitHubConfig:
    """Configuration for GitHub repository operations."""
    
    owner: str
    repo: str
    branch: Optional[str] = None
    base_path: str = "/tmp"
    max_retries: int = 3
    retry_delay: int = 10


class GitHubConnectorError(Exception):
    """Custom exception for GitHub connector operations."""
    pass


class GitHubConnector:
    """
    Handles GitHub repository operations including cloning with retry logic.
    
    This connector is responsible for:
    - Cloning repositories from GitHub
    - Managing local repository paths
    - Handling retry logic for failed operations
    - Environment variable configuration
    """
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        """
        Initialize the GitHub connector.
        
        Args:
            config: GitHubConfig object. If None, will load from environment variables.
        """
        load_dotenv('.env')
        
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()
        
        self.supported_extensions = {
            # Programming languages
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', 
            '.h', '.hpp', '.go', '.rs', '.php', '.rb', '.swift', '.kt',
            '.scala', '.cs', '.vb', '.pl', '.r', '.m', '.sh', '.sql',
            # Web technologies
            '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            # Documentation and config
            '.md', '.rst', '.txt', '.json', '.xml', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf'
        }
        
        self.skip_directories = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'node_modules', '.vscode', '.idea', '.venv', 'venv',
            '.env', 'dist', 'build', 'target', 'bin', 'obj'
        }
    
    def _load_config_from_env(self) -> GitHubConfig:
        """Load configuration from environment variables."""
        owner = os.getenv('GITHUB_OWNER')
        repo = os.getenv('GITHUB_REPO')
        branch = os.getenv('GITHUB_BRANCH')
        base_path = os.getenv('BASE_PATH', "/tmp")
        
        if not owner or not repo:
            raise GitHubConnectorError(
                "GITHUB_OWNER and GITHUB_REPO environment variables must be set."
            )
        
        return GitHubConfig(
            owner=owner,
            repo=repo,
            branch=branch,
            base_path=base_path
        )
    
    def get_local_repo_path(self) -> str:
        """Get the local path where the repository will be/is cloned."""
        return os.path.join(self.config.base_path, self.config.owner, self.config.repo)
    
    def get_clone_url(self) -> str:
        """Get the clone URL for the repository."""
        return f"https://github.com/{self.config.owner}/{self.config.repo}.git"
    
    def clone_repository(self, force_reclone: bool = False) -> str:
        """
        Clone the GitHub repository to local path.
        
        Args:
            force_reclone: If True, remove existing directory and clone fresh.
            
        Returns:
            str: Path to the cloned repository.
            
        Raises:
            GitHubConnectorError: If cloning fails after all retries.
        """
        if not self.config.branch:
            raise GitHubConnectorError(
                "Branch is not provided and GITHUB_BRANCH environment variable is not set."
            )
        
        local_repo_path = self.get_local_repo_path()
        clone_url = self.get_clone_url()
        
        # Check if repository already exists
        if os.path.exists(local_repo_path) and not force_reclone:
            print(f"Repository already exists at {local_repo_path}. Skipping clone.")
            return local_repo_path
        
        # Remove existing directory if force_reclone is True
        if force_reclone and os.path.exists(local_repo_path):
            import shutil
            shutil.rmtree(local_repo_path)
            print(f"Removed existing repository at {local_repo_path}")
        
        # Clone with retry logic
        return self._clone_with_retry(clone_url, local_repo_path)
    
    def _clone_with_retry(self, clone_url: str, local_repo_path: str) -> str:
        """
        Clone repository with retry logic.
        
        Args:
            clone_url: URL to clone from.
            local_repo_path: Local path to clone to.
            
        Returns:
            str: Path to the cloned repository.
            
        Raises:
            GitHubConnectorError: If cloning fails after all retries.
        """
        for attempt in range(self.config.max_retries):
            try:
                os.makedirs(local_repo_path, exist_ok=True)
                print(f"Attempting to clone repository... Attempt {attempt + 1}")
                
                subprocess.run([
                    "git", "clone", "-b", self.config.branch, 
                    clone_url, local_repo_path
                ], check=True, capture_output=True, text=True)
                
                print(f"Repository cloned successfully into {local_repo_path}")
                return local_repo_path
                
            except subprocess.CalledProcessError as e:
                print(f"Attempt {attempt + 1} failed: {e.stderr}")
                
                if attempt < self.config.max_retries - 1:
                    print(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    raise GitHubConnectorError(
                        f"Failed to clone repository after {self.config.max_retries} attempts: {e.stderr}"
                    )
    
    def update_repository(self) -> str:
        """
        Update an existing repository or clone if it doesn't exist.
        
        Returns:
            str: Path to the repository.
        """
        local_repo_path = self.get_local_repo_path()
        
        if os.path.exists(local_repo_path):
            try:
                # Try to pull latest changes
                subprocess.run([
                    "git", "-C", local_repo_path, "pull", "origin", self.config.branch
                ], check=True, capture_output=True, text=True)
                
                print(f"Repository updated at {local_repo_path}")
                return local_repo_path
                
            except subprocess.CalledProcessError as e:
                print(f"Failed to update repository: {e.stderr}")
                print("Attempting fresh clone...")
                return self.clone_repository(force_reclone=True)
        else:
            return self.clone_repository()
    
    def get_repository_info(self) -> dict:
        """
        Get information about the repository configuration.
        
        Returns:
            dict: Repository information.
        """
        return {
            'owner': self.config.owner,
            'repo': self.config.repo,
            'branch': self.config.branch,
            'clone_url': self.get_clone_url(),
            'local_path': self.get_local_repo_path(),
            'exists_locally': os.path.exists(self.get_local_repo_path())
        }
    
    def get_supported_file_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.supported_extensions)
    
    def is_file_supported(self, file_path: str) -> bool:
        """Check if a file type is supported for processing."""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_extensions
    
    def should_skip_directory(self, directory_name: str) -> bool:
        """Check if a directory should be skipped during processing."""
        return directory_name in self.skip_directories
    
    def validate_github_url(self, url: str) -> bool:
        """Validate if URL is a valid GitHub repository URL."""
        if not url:
            return False
            
        # Support both HTTPS and SSH URLs
        github_patterns = [
            r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
            r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$'
        ]
        
        return any(re.match(pattern, url) for pattern in github_patterns)
    
    def get_repository_name_from_url(self, url: str) -> str:
        """Extract repository name from GitHub URL."""
        if url.startswith('git@'):
            # SSH format: git@github.com:user/repo.git
            repo_part = url.split(':')[1]
        else:
            # HTTPS format: https://github.com/user/repo or https://github.com/user/repo.git
            parsed = urlparse(url)
            repo_part = parsed.path.lstrip('/')
        
        # Remove .git suffix if present
        if repo_part.endswith('.git'):
            repo_part = repo_part[:-4]
        
        # Extract just the repository name (last part after /)
        return repo_part.split('/')[-1]
    
    def clone_repository(self, repo_url: str, local_path: str) -> bool:
        """
        Clone a GitHub repository to local path.
        
        Args:
            repo_url: GitHub repository URL
            local_path: Local path to clone to
            
        Returns:
            bool: True if cloning was successful, False otherwise
        """
        try:
            if os.path.exists(local_path):
                print(f"Directory {local_path} already exists")
                return False
            
            print(f"Cloning repository {repo_url} to {local_path}")
            git.Repo.clone_from(repo_url, local_path)
            return True
            
        except git.exc.GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during cloning: {e}")
            return False
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        Read file content with proper encoding handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            str: File content or None if reading failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            print(f"Could not decode file {file_path}")
            return None
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def extract_code_files(self, repo_path: str) -> List[Dict[str, str]]:
        """
        Extract all supported code files from repository.
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            List of dictionaries containing file path and content
        """
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not self.should_skip_directory(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self.is_file_supported(file_path):
                    content = self.read_file_content(file_path)
                    if content is not None:
                        code_files.append({
                            'file_path': file_path,
                            'content': content
                        })
        
        return code_files
    
    def process_repository(self, repo_url: str, local_path: str) -> List[Dict[str, str]]:
        """
        Process a GitHub repository: clone and extract code files.
        
        Args:
            repo_url: GitHub repository URL
            local_path: Local path to clone to
            
        Returns:
            List of dictionaries containing file information
        """
        print(f"Processing repository: {repo_url}")
        
        # Validate URL
        if not self.validate_github_url(repo_url):
            print(f"Invalid GitHub URL: {repo_url}")
            return []
        
        # Clone repository
        if not self.clone_repository(repo_url, local_path):
            print("Failed to clone repository")
            return []
        
        # Extract code files
        code_files = self.extract_code_files(local_path)
        print(f"Extracted {len(code_files)} code files from repository")
        
        return code_files
