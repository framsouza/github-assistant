"""
Tests for ElasticsearchConnector module.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import numpy as np
from datetime import datetime

from connectors.elasticsearch_connector import ElasticsearchConnector


class TestElasticsearchConnector(unittest.TestCase):
    """Test cases for ElasticsearchConnector class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.connector = ElasticsearchConnector()
        self.sample_document = {
            'file_path': '/repo/test.py',
            'content': 'def hello(): return "world"'
        }

    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_init_with_custom_config(self, mock_es_class):
        """Test initialization with custom configuration."""
        # Arrange
        mock_client = MagicMock()
        mock_es_class.return_value = mock_client
        config = {
            'host': 'custom-host',
            'port': 9200,
            'username': 'user',
            'password': 'pass'
        }
        
        # Act
        connector = ElasticsearchConnector(es_config=config)
        
        # Assert
        mock_es_class.assert_called_once_with(
            hosts=[{'host': 'custom-host', 'port': 9200}],
            basic_auth=('user', 'pass'),
            verify_certs=False
        )

    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_init_default_config(self, mock_es_class):
        """Test initialization with default configuration."""
        # Arrange
        mock_client = MagicMock()
        mock_es_class.return_value = mock_client
        
        # Act
        connector = ElasticsearchConnector()
        
        # Assert
        mock_es_class.assert_called_once_with(
            hosts=[{'host': 'localhost', 'port': 9200}],
            basic_auth=('elastic', 'changeme'),
            verify_certs=False
        )

    @patch('connectors.elasticsearch_connector.SentenceTransformer')
    def test_init_sentence_transformer(self, mock_transformer_class):
        """Test sentence transformer initialization."""
        # Arrange
        mock_model = MagicMock()
        mock_transformer_class.return_value = mock_model
        
        # Act
        connector = ElasticsearchConnector()
        
        # Assert
        mock_transformer_class.assert_called_once_with('all-MiniLM-L6-v2')
        self.assertEqual(connector.model, mock_model)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_create_embeddings(self, mock_es_class, mock_init_transformer):
        """Test creating embeddings for text."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        embeddings = connector.create_embeddings("test content")
        
        # Assert
        mock_model.encode.assert_called_once_with("test content")
        np.testing.assert_array_equal(embeddings, np.array([0.1, 0.2, 0.3]))

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_create_embeddings_exception(self, mock_es_class, mock_init_transformer):
        """Test creating embeddings when model throws exception."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Model error")
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        embeddings = connector.create_embeddings("test content")
        
        # Assert
        self.assertIsNone(embeddings)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_prepare_document_for_indexing(self, mock_es_class, mock_init_transformer):
        """Test preparing document for indexing."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        prepared_doc = connector.prepare_document_for_indexing(self.sample_document)
        
        # Assert
        self.assertEqual(prepared_doc['file_path'], '/repo/test.py')
        self.assertEqual(prepared_doc['content'], 'def hello(): return "world"')
        self.assertEqual(prepared_doc['content_length'], len('def hello(): return "world"'))
        self.assertIn('embeddings', prepared_doc)
        self.assertIn('indexed_at', prepared_doc)
        self.assertIsInstance(prepared_doc['indexed_at'], str)
        np.testing.assert_array_equal(prepared_doc['embeddings'], [0.1, 0.2, 0.3])

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_prepare_document_with_embedding_failure(self, mock_es_class, mock_init_transformer):
        """Test preparing document when embedding creation fails."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Embedding error")
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        prepared_doc = connector.prepare_document_for_indexing(self.sample_document)
        
        # Assert
        self.assertIsNone(prepared_doc)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_create_index_success(self, mock_es_class, mock_init_transformer):
        """Test successful index creation."""
        # Arrange
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {'acknowledged': True}
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        result = connector.create_index("test_index")
        
        # Assert
        self.assertTrue(result)
        mock_client.indices.exists.assert_called_once_with(index="test_index")
        mock_client.indices.create.assert_called_once()

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_create_index_already_exists(self, mock_es_class, mock_init_transformer):
        """Test creating index when it already exists."""
        # Arrange
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = True
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        result = connector.create_index("test_index")
        
        # Assert
        self.assertTrue(result)
        mock_client.indices.create.assert_not_called()

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_create_index_failure(self, mock_es_class, mock_init_transformer):
        """Test index creation failure."""
        # Arrange
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.side_effect = Exception("Index creation failed")
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        result = connector.create_index("test_index")
        
        # Assert
        self.assertFalse(result)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_index_document_success(self, mock_es_class, mock_init_transformer):
        """Test successful document indexing."""
        # Arrange
        mock_client = MagicMock()
        mock_client.index.return_value = {'_id': 'doc123', 'result': 'created'}
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        prepared_doc = {
            'file_path': '/repo/test.py',
            'content': 'test content',
            'embeddings': [0.1, 0.2, 0.3],
            'indexed_at': '2023-01-01T00:00:00'
        }
        
        # Act
        result = connector.index_document("test_index", prepared_doc)
        
        # Assert
        self.assertTrue(result)
        mock_client.index.assert_called_once_with(
            index="test_index",
            document=prepared_doc
        )

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_index_document_failure(self, mock_es_class, mock_init_transformer):
        """Test document indexing failure."""
        # Arrange
        mock_client = MagicMock()
        mock_client.index.side_effect = Exception("Indexing failed")
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        prepared_doc = {'file_path': '/repo/test.py', 'content': 'test'}
        
        # Act
        result = connector.index_document("test_index", prepared_doc)
        
        # Assert
        self.assertFalse(result)

    @patch.object(ElasticsearchConnector, 'create_index')
    @patch.object(ElasticsearchConnector, 'prepare_document_for_indexing')
    @patch.object(ElasticsearchConnector, 'index_document')
    def test_ingest_documents_success(self, mock_index_doc, mock_prepare_doc, mock_create_index):
        """Test successful document ingestion."""
        # Arrange
        mock_create_index.return_value = True
        mock_prepare_doc.side_effect = [
            {'file_path': '/repo/test1.py', 'content': 'content1'},
            {'file_path': '/repo/test2.py', 'content': 'content2'}
        ]
        mock_index_doc.return_value = True
        
        documents = [
            {'file_path': '/repo/test1.py', 'content': 'content1'},
            {'file_path': '/repo/test2.py', 'content': 'content2'}
        ]
        
        # Act
        result = self.connector.ingest_documents("test_index", documents)
        
        # Assert
        self.assertEqual(result, {'successful': 2, 'failed': 0})
        mock_create_index.assert_called_once_with("test_index")
        self.assertEqual(mock_prepare_doc.call_count, 2)
        self.assertEqual(mock_index_doc.call_count, 2)

    @patch.object(ElasticsearchConnector, 'create_index')
    def test_ingest_documents_index_creation_failure(self, mock_create_index):
        """Test document ingestion when index creation fails."""
        # Arrange
        mock_create_index.return_value = False
        documents = [{'file_path': '/repo/test.py', 'content': 'content'}]
        
        # Act
        result = self.connector.ingest_documents("test_index", documents)
        
        # Assert
        self.assertEqual(result, {'successful': 0, 'failed': 1})

    @patch.object(ElasticsearchConnector, 'create_index')
    @patch.object(ElasticsearchConnector, 'prepare_document_for_indexing')
    def test_ingest_documents_preparation_failure(self, mock_prepare_doc, mock_create_index):
        """Test document ingestion when document preparation fails."""
        # Arrange
        mock_create_index.return_value = True
        mock_prepare_doc.return_value = None  # Preparation failed
        
        documents = [{'file_path': '/repo/test.py', 'content': 'content'}]
        
        # Act
        result = self.connector.ingest_documents("test_index", documents)
        
        # Assert
        self.assertEqual(result, {'successful': 0, 'failed': 1})

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_search_documents_success(self, mock_es_class, mock_init_transformer):
        """Test successful document search."""
        # Arrange
        mock_client = MagicMock()
        mock_search_result = {
            'hits': {
                'hits': [
                    {
                        '_source': {'file_path': '/repo/test.py', 'content': 'test'},
                        '_score': 0.9
                    }
                ]
            }
        }
        mock_client.search.return_value = mock_search_result
        mock_es_class.return_value = mock_client
        
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        results = connector.search_documents("test_index", "search query")
        
        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['file_path'], '/repo/test.py')
        self.assertEqual(results[0]['score'], 0.9)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_search_documents_failure(self, mock_es_class, mock_init_transformer):
        """Test document search failure."""
        # Arrange
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Search failed")
        mock_es_class.return_value = mock_client
        
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        connector = ElasticsearchConnector()
        connector.model = mock_model
        
        # Act
        results = connector.search_documents("test_index", "search query")
        
        # Assert
        self.assertEqual(results, [])

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_get_index_stats(self, mock_es_class, mock_init_transformer):
        """Test getting index statistics."""
        # Arrange
        mock_client = MagicMock()
        mock_stats = {
            'indices': {
                'test_index': {
                    'total': {
                        'docs': {'count': 100},
                        'store': {'size_in_bytes': 1024}
                    }
                }
            }
        }
        mock_client.indices.stats.return_value = mock_stats
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        stats = connector.get_index_stats("test_index")
        
        # Assert
        self.assertEqual(stats['document_count'], 100)
        self.assertEqual(stats['size_in_bytes'], 1024)

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_delete_index_success(self, mock_es_class, mock_init_transformer):
        """Test successful index deletion."""
        # Arrange
        mock_client = MagicMock()
        mock_client.indices.delete.return_value = {'acknowledged': True}
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        result = connector.delete_index("test_index")
        
        # Assert
        self.assertTrue(result)
        mock_client.indices.delete.assert_called_once_with(index="test_index")

    @patch.object(ElasticsearchConnector, '_ElasticsearchConnector__init_sentence_transformer')
    @patch('connectors.elasticsearch_connector.Elasticsearch')
    def test_delete_index_failure(self, mock_es_class, mock_init_transformer):
        """Test index deletion failure."""
        # Arrange
        mock_client = MagicMock()
        mock_client.indices.delete.side_effect = Exception("Delete failed")
        mock_es_class.return_value = mock_client
        connector = ElasticsearchConnector()
        
        # Act
        result = connector.delete_index("test_index")
        
        # Assert
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
