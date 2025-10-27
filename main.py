"""
Main application orchestrating the GitHub and Elasticsearch connectors.

This module provides the main entry point for the application that:
1. Clones a GitHub repository using GitHubConnector
2. Processes documents and creates embeddings using ElasticsearchConnector
3. Stores the embeddings in Elasticsearch for vector search
"""

import sys
from typing import Optional

from connectors import GitHubConnector, ElasticsearchConnector
from connectors.github_connector import GitHubConfig, GitHubConnectorError
from connectors.elasticsearch_connector import ElasticsearchConfig, ElasticsearchConnectorError
from config import load_config, ConfigurationError


class KimchiPipeline:
    """
    Main pipeline orchestrating GitHub repository processing and Elasticsearch ingestion.
    
    This class coordinates the entire workflow:
    1. Clone/update repository from GitHub
    2. Parse documents and create embeddings
    3. Store embeddings in Elasticsearch
    """
    
    def __init__(self, 
                 github_config: Optional[GitHubConfig] = None,
                 elasticsearch_config: Optional[ElasticsearchConfig] = None,
                 embedding_model: str = "text-embedding-3-large"):
        """
        Initialize the pipeline with connectors.
        
        Args:
            github_config: Configuration for GitHub operations.
            elasticsearch_config: Configuration for Elasticsearch operations.
            embedding_model: OpenAI embedding model to use.
        """
        self.github_connector = GitHubConnector(github_config)
        self.elasticsearch_connector = ElasticsearchConnector(elasticsearch_config, embedding_model)
    
    def run(self, 
            force_reclone: bool = False, 
            update_repo: bool = False,
            verbose: bool = True,
            show_progress: bool = True) -> None:
        """
        Run the complete pipeline.
        
        Args:
            force_reclone: Force fresh clone of repository.
            update_repo: Try to update existing repository instead of clone.
            verbose: Enable verbose output during processing.
            show_progress: Show progress during ingestion.
        """
        try:
            # Step 1: Handle repository operations
            print("=== GitHub Repository Operations ===")
            if verbose:
                repo_info = self.github_connector.get_repository_info()
                print(f"Repository: {repo_info['owner']}/{repo_info['repo']}")
                print(f"Branch: {repo_info['branch']}")
                print(f"Local path: {repo_info['local_path']}")
                print(f"Exists locally: {repo_info['exists_locally']}")
            
            if update_repo:
                repo_path = self.github_connector.update_repository()
            else:
                repo_path = self.github_connector.clone_repository(force_reclone=force_reclone)
            
            print(f"Repository ready at: {repo_path}")
            
            # Step 2: Process documents and ingest into Elasticsearch
            print("\n=== Document Processing and Elasticsearch Ingestion ===")
            if verbose:
                es_info = self.elasticsearch_connector.get_store_info()
                print(f"Elasticsearch index: {es_info['index_name']}")
                print(f"Embedding model: {es_info['embedding_model']}")
                print(f"Batch size: {es_info['batch_size']}")
            
            self.elasticsearch_connector.process_and_ingest_documents(
                repo_path=repo_path,
                show_progress=show_progress,
                verbose=verbose
            )
            
            print("\n=== Pipeline Completed Successfully ===")
            
        except (GitHubConnectorError, ElasticsearchConnectorError) as e:
            print(f"Pipeline failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            # Ensure Elasticsearch connection is closed
            self.elasticsearch_connector.close()
    
    def get_pipeline_info(self) -> dict:
        """
        Get information about the pipeline configuration.
        
        Returns:
            dict: Pipeline configuration information.
        """
        return {
            'github': self.github_connector.get_repository_info(),
            'elasticsearch': self.elasticsearch_connector.get_store_info()
        }


def main():
    """Main entry point for the application."""
    try:
        # Load configuration from environment
        config = load_config()
        
        # Create pipeline with loaded configuration
        pipeline = KimchiPipeline(
            github_config=config.github,
            elasticsearch_config=config.elasticsearch,
            embedding_model=config.embedding_model
        )
        
        # Print pipeline information
        print("=== Kimchi Pipeline Starting ===")
        pipeline_info = pipeline.get_pipeline_info()
        print(f"GitHub Repository: {pipeline_info['github']['owner']}/{pipeline_info['github']['repo']}")
        print(f"Branch: {pipeline_info['github']['branch']}")
        print(f"Elasticsearch Index: {pipeline_info['elasticsearch']['index_name']}")
        print(f"Embedding Model: {pipeline_info['elasticsearch']['embedding_model']}")
        print()
        
        # Run the pipeline
        pipeline.run(
            verbose=config.verbose, 
            show_progress=config.show_progress
        )
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Please check your environment variables and .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
