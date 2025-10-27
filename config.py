"""
Configuration management for the Kimchi application.

This module provides centralized configuration management with validation
and default values for both GitHub and Elasticsearch connectors.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from connectors.github_connector import GitHubConfig
from connectors.elasticsearch_connector import ElasticsearchConfig, ParserConfig


@dataclass
class AppConfig:
    """Main application configuration combining all component configurations."""
    
    github: GitHubConfig
    elasticsearch: ElasticsearchConfig
    parser: ParserConfig = field(default_factory=ParserConfig)
    embedding_model: str = "text-embedding-3-large"
    verbose: bool = True
    show_progress: bool = True


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""
    pass


class ConfigManager:
    """
    Manages application configuration from environment variables and defaults.
    
    This class handles:
    - Loading configuration from environment variables
    - Validating required configuration values
    - Providing default values for optional settings
    - Creating configuration objects for connectors
    """
    
    def __init__(self, env_file: str = '.env'):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Path to environment file to load.
        """
        load_dotenv(env_file)
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """Validate that required environment variables are set."""
        required_vars = [
            'GITHUB_OWNER',
            'GITHUB_REPO', 
            'ELASTIC_CLOUD_ID',
            'ELASTIC_USER',
            'ELASTIC_PASSWORD',
            'ELASTIC_INDEX'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
    
    def create_github_config(self) -> GitHubConfig:
        """
        Create GitHubConfig from environment variables.
        
        Returns:
            GitHubConfig: Configured GitHub settings.
        """
        return GitHubConfig(
            owner=os.getenv('GITHUB_OWNER'),
            repo=os.getenv('GITHUB_REPO'),
            branch=os.getenv('GITHUB_BRANCH'),
            base_path=os.getenv('BASE_PATH', '/tmp'),
            max_retries=int(os.getenv('GITHUB_MAX_RETRIES', '3')),
            retry_delay=int(os.getenv('GITHUB_RETRY_DELAY', '10'))
        )
    
    def create_elasticsearch_config(self) -> ElasticsearchConfig:
        """
        Create ElasticsearchConfig from environment variables.
        
        Returns:
            ElasticsearchConfig: Configured Elasticsearch settings.
        """
        return ElasticsearchConfig(
            cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
            username=os.getenv('ELASTIC_USER'),
            password=os.getenv('ELASTIC_PASSWORD'),
            index_name=os.getenv('ELASTIC_INDEX'),
            batch_size=int(os.getenv('ELASTIC_BATCH_SIZE', '100')),
            request_timeout=int(os.getenv('ELASTIC_REQUEST_TIMEOUT', '120')),
            max_retries=int(os.getenv('ELASTIC_MAX_RETRIES', '5')),
            connection_retries=int(os.getenv('ELASTIC_CONNECTION_RETRIES', '20')),
            connection_retry_delay=int(os.getenv('ELASTIC_CONNECTION_RETRY_DELAY', '15'))
        )
    
    def create_parser_config(self) -> ParserConfig:
        """
        Create ParserConfig from environment variables.
        
        Returns:
            ParserConfig: Configured parser settings.
        """
        return ParserConfig(
            chunk_size=int(os.getenv('PARSER_CHUNK_SIZE', '750')),
            chunk_overlap=int(os.getenv('PARSER_CHUNK_OVERLAP', '50')),
            max_chars=int(os.getenv('PARSER_MAX_CHARS', '1500'))
        )
    
    def create_app_config(self) -> AppConfig:
        """
        Create complete application configuration.
        
        Returns:
            AppConfig: Complete application configuration.
        """
        return AppConfig(
            github=self.create_github_config(),
            elasticsearch=self.create_elasticsearch_config(),
            parser=self.create_parser_config(),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large'),
            verbose=os.getenv('VERBOSE', 'true').lower() == 'true',
            show_progress=os.getenv('SHOW_PROGRESS', 'true').lower() == 'true'
        )
    
    def print_config_summary(self, config: AppConfig) -> None:
        """
        Print a summary of the configuration.
        
        Args:
            config: Application configuration to summarize.
        """
        print("=== Configuration Summary ===")
        print(f"GitHub Repository: {config.github.owner}/{config.github.repo}")
        print(f"Branch: {config.github.branch}")
        print(f"Base Path: {config.github.base_path}")
        print(f"Max Retries: {config.github.max_retries}")
        print()
        print(f"Elasticsearch Index: {config.elasticsearch.index_name}")
        print(f"Batch Size: {config.elasticsearch.batch_size}")
        print(f"Request Timeout: {config.elasticsearch.request_timeout}s")
        print()
        print(f"Parser Chunk Size: {config.parser.chunk_size}")
        print(f"Parser Chunk Overlap: {config.parser.chunk_overlap}")
        print(f"Parser Max Chars: {config.parser.max_chars}")
        print()
        print(f"Embedding Model: {config.embedding_model}")
        print(f"Verbose Mode: {config.verbose}")
        print(f"Show Progress: {config.show_progress}")
        print("=" * 30)


def load_config(env_file: str = '.env') -> AppConfig:
    """
    Convenience function to load complete application configuration.
    
    Args:
        env_file: Path to environment file.
        
    Returns:
        AppConfig: Complete application configuration.
        
    Raises:
        ConfigurationError: If configuration is invalid.
    """
    config_manager = ConfigManager(env_file)
    return config_manager.create_app_config()
