# Test Suite for Kimchi Project

This directory contains comprehensive tests for the GitHub connector and Elasticsearch connector modules.

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── test_github_connector.py       # Unit tests for GitHub connector
├── test_elasticsearch_connector.py # Unit tests for Elasticsearch connector  
├── test_integration.py            # Integration tests for complete workflow
├── test_utils.py                  # Test utilities and helpers
├── run_tests.py                   # Test runner script
└── README.md                      # This file
```

## Running Tests

### Using Python unittest

```bash
# Run all tests
python -m tests.run_tests

# Run specific test module
python -m tests.run_tests test_github_connector

# Run individual test
python -m unittest tests.test_github_connector.TestGitHubConnector.test_clone_repository_success
```

### Using pytest (recommended)

```bash
# Install test dependencies first
pip install -r test-requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_github_connector.py

# Run tests with coverage
pytest --cov=connectors --cov-report=html

# Run tests with specific markers
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m github        # Only GitHub connector tests
pytest -m elasticsearch # Only Elasticsearch connector tests
```

## Test Categories

### Unit Tests

#### GitHub Connector Tests (`test_github_connector.py`)
- Repository cloning functionality
- File extraction and filtering
- Content reading with proper encoding handling
- Directory traversal with skip logic
- URL validation and repository name extraction
- Error handling for various failure scenarios

#### Elasticsearch Connector Tests (`test_elasticsearch_connector.py`)
- Embedding generation using sentence transformers
- Document preparation and indexing
- Index creation and management
- Search functionality with vector similarity
- Error handling and resilience
- Configuration and initialization

### Integration Tests (`test_integration.py`)
- Complete workflow from GitHub cloning to Elasticsearch ingestion
- End-to-end data pipeline testing
- Error propagation and handling across components
- Configuration compatibility between connectors

### Test Utilities (`test_utils.py`)
- Mock file system for testing file operations
- Test data generators for various scenarios
- Configuration helpers and test fixtures
- Common assertion helpers

## Test Data

The test suite includes comprehensive test data:

- **Mock Repositories**: Sample repository structures with various file types
- **Mock Responses**: Elasticsearch responses for search operations
- **Edge Cases**: Large files, binary files, encoding issues
- **Error Scenarios**: Network failures, permission errors, invalid data

## Mocking Strategy

The tests use extensive mocking to:

- **Avoid External Dependencies**: No actual GitHub cloning or Elasticsearch connections
- **Test Error Scenarios**: Simulate various failure conditions
- **Ensure Deterministic Results**: Consistent test outcomes
- **Speed Up Execution**: Fast test runs without network operations

### Key Mock Objects

- `git.Repo.clone_from`: Git repository cloning
- `Elasticsearch`: Elasticsearch client operations
- `SentenceTransformer`: Embedding model operations
- File system operations: Reading, writing, directory traversal

## Test Configuration

### Environment Variables

```bash
# For integration testing (optional)
export TEST_ES_HOST=localhost
export TEST_ES_PORT=9200
export TEST_ES_USERNAME=test_user
export TEST_ES_PASSWORD=test_password
```

### Pytest Markers

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.github`: GitHub connector specific tests
- `@pytest.mark.elasticsearch`: Elasticsearch connector specific tests

## Coverage Goals

The test suite aims for:

- **Line Coverage**: >90% for all connector modules
- **Branch Coverage**: >85% for critical paths
- **Function Coverage**: 100% for public APIs

## Common Test Patterns

### Testing File Operations

```python
@patch('builtins.open', new_callable=mock_open, read_data="test content")
def test_file_reading(self, mock_file):
    content = self.connector.read_file_content("test.py")
    self.assertEqual(content, "test content")
```

### Testing External API Calls

```python
@patch('connectors.elasticsearch_connector.Elasticsearch')
def test_elasticsearch_operation(self, mock_es_class):
    mock_client = MagicMock()
    mock_es_class.return_value = mock_client
    # Test implementation
```

### Testing Error Scenarios

```python
@patch('git.Repo.clone_from')
def test_clone_failure(self, mock_clone):
    mock_clone.side_effect = git.exc.GitCommandError("clone", "error")
    result = self.connector.clone_repository(url, path)
    self.assertFalse(result)
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- **Fast Execution**: All tests complete in under 2 minutes
- **No External Dependencies**: Fully mocked external services
- **Deterministic**: Consistent results across environments
- **Comprehensive**: Covers all major functionality and error scenarios

## Adding New Tests

When adding new features:

1. **Write Tests First**: Follow TDD practices
2. **Cover Happy Path**: Test normal operation
3. **Test Error Cases**: Handle failures gracefully
4. **Add Integration Tests**: Ensure components work together
5. **Update Documentation**: Keep this README current

### Example Test Structure

```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    def test_normal_operation(self):
        """Test normal operation of the feature."""
        pass
    
    def test_error_handling(self):
        """Test error handling in the feature.""" 
        pass
    
    @patch('external.dependency')
    def test_with_mocked_dependency(self, mock_dep):
        """Test with mocked external dependency."""
        pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Mock Failures**: Check mock object configuration
3. **Async Issues**: Use proper async test patterns
4. **File Path Issues**: Use absolute paths in tests

### Debugging Tests

```bash
# Run with verbose output
pytest -v -s

# Run specific test with debugging
pytest -v -s tests/test_github_connector.py::TestGitHubConnector::test_clone_repository_success

# Run with PDB debugging
pytest --pdb
```
