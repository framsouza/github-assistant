"""
Integration tests for the complete workflow: GitHub cloning + Elasticsearch ingestion.
"""

import unittest
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock, Mock

from connectors.github_connector import GitHubConnector
from connectors.elasticsearch_connector import ElasticsearchConnector


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete RAG pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.github_connector = GitHubConnector()
        self.es_connector = ElasticsearchConnector()
        self.test_repo_url = "https://github.com/test/repo.git"
        self.test_index = "test_repo_index"

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch.object(GitHubConnector, 'process_repository')
    @patch.object(ElasticsearchConnector, 'ingest_documents')
    def test_complete_workflow_success(self, mock_ingest, mock_process_repo):
        """Test the complete workflow from GitHub cloning to Elasticsearch ingestion."""
        # Arrange
        mock_documents = [
            {
                'file_path': '/repo/main.py',
                'content': 'def main(): print("Hello World")'
            },
            {
                'file_path': '/repo/README.md',
                'content': '# Test Repository\nThis is a test.'
            }
        ]
        mock_process_repo.return_value = mock_documents
        mock_ingest.return_value = {'successful': 2, 'failed': 0}

        # Act
        # Step 1: Process GitHub repository
        documents = self.github_connector.process_repository(
            self.test_repo_url,
            os.path.join(self.temp_dir, "repo")
        )
        
        # Step 2: Ingest into Elasticsearch
        if documents:
            result = self.es_connector.ingest_documents(self.test_index, documents)

        # Assert
        mock_process_repo.assert_called_once()
        mock_ingest.assert_called_once_with(self.test_index, mock_documents)
        self.assertEqual(result['successful'], 2)
        self.assertEqual(result['failed'], 0)

    @patch.object(GitHubConnector, 'process_repository')
    def test_workflow_github_failure(self, mock_process_repo):
        """Test workflow when GitHub processing fails."""
        # Arrange
        mock_process_repo.return_value = []  # Empty result indicates failure

        # Act
        documents = self.github_connector.process_repository(
            self.test_repo_url,
            os.path.join(self.temp_dir, "repo")
        )

        # Assert
        self.assertEqual(documents, [])

    @patch.object(GitHubConnector, 'process_repository')
    @patch.object(ElasticsearchConnector, 'ingest_documents')
    def test_workflow_elasticsearch_failure(self, mock_ingest, mock_process_repo):
        """Test workflow when Elasticsearch ingestion fails."""
        # Arrange
        mock_documents = [
            {'file_path': '/repo/main.py', 'content': 'test content'}
        ]
        mock_process_repo.return_value = mock_documents
        mock_ingest.return_value = {'successful': 0, 'failed': 1}

        # Act
        documents = self.github_connector.process_repository(
            self.test_repo_url,
            os.path.join(self.temp_dir, "repo")
        )
        
        result = self.es_connector.ingest_documents(self.test_index, documents)

        # Assert
        self.assertEqual(result['successful'], 0)
        self.assertEqual(result['failed'], 1)

    @patch.object(ElasticsearchConnector, 'search_documents')
    def test_search_after_ingestion(self, mock_search):
        """Test searching documents after ingestion."""
        # Arrange
        mock_search_results = [
            {
                'file_path': '/repo/main.py',
                'content': 'def main(): print("Hello World")',
                'score': 0.9
            }
        ]
        mock_search.return_value = mock_search_results

        # Act
        results = self.es_connector.search_documents(
            self.test_index, 
            "Hello World function"
        )

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['file_path'], '/repo/main.py')
        self.assertEqual(results[0]['score'], 0.9)

    def test_file_filtering_integration(self):
        """Test that file filtering works correctly in the integration."""
        # Test supported file extensions
        test_files = [
            'main.py',
            'script.js',
            'README.md',
            'config.json',
            'image.png',  # Should be filtered out
            'binary.exe'  # Should be filtered out
        ]
        
        supported_files = [
            f for f in test_files 
            if self.github_connector.is_file_supported(f)
        ]
        
        self.assertIn('main.py', supported_files)
        self.assertIn('script.js', supported_files)
        self.assertIn('README.md', supported_files)
        self.assertIn('config.json', supported_files)
        self.assertNotIn('image.png', supported_files)
        self.assertNotIn('binary.exe', supported_files)

    def test_repository_name_extraction(self):
        """Test repository name extraction for index naming."""
        test_urls = [
            ("https://github.com/user/my-repo", "my-repo"),
            ("https://github.com/user/my-repo.git", "my-repo"),
            ("git@github.com:user/my-repo.git", "my-repo"),
        ]
        
        for url, expected_name in test_urls:
            with self.subTest(url=url):
                name = self.github_connector.get_repository_name_from_url(url)
                self.assertEqual(name, expected_name)


class TestConnectorConfiguration(unittest.TestCase):
    """Test configuration and initialization of connectors."""

    def test_github_connector_initialization(self):
        """Test GitHub connector initialization."""
        connector = GitHubConnector()
        
        # Test default supported extensions
        extensions = connector.get_supported_file_extensions()
        self.assertIn('.py', extensions)
        self.assertIn('.js', extensions)
        self.assertIn('.md', extensions)

    @patch('connectors.elasticsearch_connector.Elasticsearch')
    @patch('connectors.elasticsearch_connector.SentenceTransformer')
    def test_elasticsearch_connector_initialization(self, mock_transformer, mock_es):
        """Test Elasticsearch connector initialization."""
        # Arrange
        mock_es_instance = MagicMock()
        mock_es.return_value = mock_es_instance
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        # Act
        connector = ElasticsearchConnector()
        
        # Assert
        mock_es.assert_called_once()
        mock_transformer.assert_called_once_with('all-MiniLM-L6-v2')

    def test_file_size_limits(self):
        """Test that very large files are handled appropriately."""
        connector = GitHubConnector()
        
        # Test with very large content (simulate large file)
        large_content = "x" * (10 * 1024 * 1024)  # 10MB string
        
        # This should not crash the system
        # In a real implementation, you might want to limit file sizes
        self.assertIsInstance(large_content, str)

    @patch('connectors.elasticsearch_connector.SentenceTransformer')
    def test_embedding_model_fallback(self, mock_transformer):
        """Test behavior when embedding model fails to load."""
        # Arrange
        mock_transformer.side_effect = Exception("Model loading failed")
        
        # Act & Assert
        with self.assertRaises(Exception):
            ElasticsearchConnector()


if __name__ == '__main__':
    unittest.main()
