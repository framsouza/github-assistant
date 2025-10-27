"""
Test configuration and utilities for the test suite.
"""

import os
import tempfile
import shutil
from unittest.mock import MagicMock
from typing import Dict, Any, List


class TestConfig:
    """Configuration settings for tests."""
    
    # Test Elasticsearch configuration
    TEST_ES_CONFIG = {
        'host': 'localhost',
        'port': 9200,
        'username': 'test_user',
        'password': 'test_password'
    }
    
    # Test repository URLs
    TEST_GITHUB_URLS = [
        "https://github.com/test/repo1.git",
        "https://github.com/test/repo2",
        "git@github.com:test/repo3.git"
    ]
    
    # Test file extensions
    SUPPORTED_EXTENSIONS = [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', 
        '.h', '.hpp', '.go', '.rs', '.php', '.rb', '.swift', '.kt',
        '.scala', '.cs', '.vb', '.pl', '.r', '.m', '.sh', '.sql',
        '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        '.md', '.rst', '.txt', '.json', '.xml', '.yaml', '.yml',
        '.toml', '.ini', '.cfg', '.conf'
    ]
    
    # Directories to skip during processing
    SKIP_DIRECTORIES = [
        '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
        'node_modules', '.vscode', '.idea', '.venv', 'venv',
        '.env', 'dist', 'build', 'target', 'bin', 'obj'
    ]


class MockFileSystem:
    """Mock file system for testing."""
    
    def __init__(self):
        self.files = {}
        self.directories = set()
    
    def add_file(self, path: str, content: str):
        """Add a file to the mock filesystem."""
        self.files[path] = content
        # Add parent directories
        parent = os.path.dirname(path)
        while parent and parent != '/':
            self.directories.add(parent)
            parent = os.path.dirname(parent)
    
    def add_directory(self, path: str):
        """Add a directory to the mock filesystem."""
        self.directories.add(path)
    
    def get_file_content(self, path: str) -> str:
        """Get file content from mock filesystem."""
        return self.files.get(path)
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists in mock filesystem."""
        return path in self.files
    
    def directory_exists(self, path: str) -> bool:
        """Check if directory exists in mock filesystem."""
        return path in self.directories
    
    def list_files(self, directory: str = '/') -> List[str]:
        """List files in a directory."""
        return [
            path for path in self.files.keys()
            if path.startswith(directory)
        ]


class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def create_sample_repository() -> Dict[str, str]:
        """Create a sample repository structure with various file types."""
        return {
            '/repo/main.py': '''#!/usr/bin/env python3
"""
Main application module.
"""

def main():
    """Main entry point of the application."""
    print("Hello, World!")
    
    # Initialize components
    config = load_config()
    app = create_app(config)
    app.run()

def load_config():
    """Load application configuration."""
    return {"debug": True, "port": 8000}

def create_app(config):
    """Create and configure the application."""
    class App:
        def __init__(self, config):
            self.config = config
        
        def run(self):
            print(f"Starting app on port {self.config['port']}")
    
    return App(config)

if __name__ == "__main__":
    main()
''',
            '/repo/utils.py': '''"""
Utility functions for the application.
"""

import re
import json
from typing import Dict, Any, Optional

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and parse JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

class DataProcessor:
    """Process and transform data."""
    
    def __init__(self):
        self.processed_count = 0
    
    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item."""
        self.processed_count += 1
        return {
            'id': item.get('id'),
            'processed': True,
            'timestamp': item.get('timestamp'),
            'data': item.get('data', {})
        }
''',
            '/repo/README.md': '''# Test Repository

This is a test repository for demonstrating the GitHub connector and Elasticsearch ingestion.

## Features

- Python code processing
- Multiple file type support
- Elasticsearch integration
- Vector embeddings generation

## Usage

```python
from connectors import GitHubConnector, ElasticsearchConnector

# Clone and process repository
github_conn = GitHubConnector()
documents = github_conn.process_repository(repo_url, local_path)

# Ingest into Elasticsearch
es_conn = ElasticsearchConnector()
result = es_conn.ingest_documents(index_name, documents)
```

## File Structure

```
/repo/
├── main.py          # Main application
├── utils.py         # Utility functions
├── README.md        # This file
├── package.json     # Node.js dependencies
└── src/
    ├── components/
    │   └── app.js   # React component
    └── styles/
        └── main.css # Stylesheet
```

## Installation

```bash
pip install -r requirements.txt
npm install
```
''',
            '/repo/package.json': '''{
  "name": "test-repository",
  "version": "1.0.0",
  "description": "Test repository for connector testing",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "test": "jest",
    "build": "webpack --mode production"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21",
    "axios": "^0.27.0"
  },
  "devDependencies": {
    "jest": "^28.0.0",
    "webpack": "^5.72.0"
  },
  "keywords": ["test", "connector", "elasticsearch"],
  "author": "Test Author",
  "license": "MIT"
}''',
            '/repo/src/components/app.js': '''/**
 * Main React application component
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/data');
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchData();
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Test Application</h1>
        <button onClick={handleRefresh} className="refresh-btn">
          Refresh Data
        </button>
      </header>
      
      <main className="app-main">
        <div className="data-grid">
          {data.map(item => (
            <div key={item.id} className="data-item">
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <span className="timestamp">{item.timestamp}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default App;
''',
            '/repo/src/styles/main.css': '''/* Main stylesheet for the application */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f5f5;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  color: #2c3e50;
  font-size: 2rem;
}

.refresh-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.refresh-btn:hover {
  background: #2980b9;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.data-item {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.data-item:hover {
  transform: translateY(-2px);
}

.data-item h3 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.data-item p {
  margin-bottom: 15px;
  color: #7f8c8d;
}

.timestamp {
  font-size: 12px;
  color: #95a5a6;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.error {
  color: #e74c3c;
}
'''
        }
    
    @staticmethod
    def create_mock_elasticsearch_response(query: str, num_results: int = 3) -> Dict[str, Any]:
        """Create a mock Elasticsearch search response."""
        hits = []
        for i in range(num_results):
            hits.append({
                '_score': 0.9 - (i * 0.1),
                '_source': {
                    'file_path': f'/repo/file_{i}.py',
                    'content': f'This is content for file {i} that matches {query}',
                    'content_length': 50 + i * 10,
                    'indexed_at': '2023-01-01T00:00:00',
                    'embeddings': [0.1 + i * 0.1, 0.2 + i * 0.1, 0.3 + i * 0.1]
                }
            })
        
        return {
            'hits': {
                'total': {'value': num_results},
                'hits': hits
            }
        }


class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_temp_directory() -> str:
        """Create a temporary directory for testing."""
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_directory(path: str):
        """Clean up a temporary directory."""
        if os.path.exists(path):
            shutil.rmtree(path)
    
    @staticmethod
    def create_mock_git_repo():
        """Create a mock Git repository object."""
        mock_repo = MagicMock()
        mock_repo.git_dir = '/repo/.git'
        mock_repo.working_dir = '/repo'
        return mock_repo
    
    @staticmethod
    def assert_file_structure(files: List[Dict[str, str]], expected_files: List[str]):
        """Assert that the extracted files match expected structure."""
        file_paths = [f['file_path'] for f in files]
        for expected_file in expected_files:
            assert any(path.endswith(expected_file) for path in file_paths), \
                f"Expected file {expected_file} not found in {file_paths}"
