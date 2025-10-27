"""
Connectors package for handling different data sources and destinations.
"""

from .github_connector import GitHubConnector, GitHubConfig, GitHubConnectorError
from .elasticsearch_connector import (
    ElasticsearchConnector, 
    ElasticsearchConfig, 
    ElasticsearchConnectorError,
    DocumentProcessor,
    ParserConfig
)

__all__ = [
    'GitHubConnector', 
    'GitHubConfig', 
    'GitHubConnectorError',
    'ElasticsearchConnector', 
    'ElasticsearchConfig', 
    'ElasticsearchConnectorError',
    'DocumentProcessor',
    'ParserConfig'
]
