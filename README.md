# GitHub Assistant

Easily ask questions about your GitHub repository using RAG.

### Key Considerations:
- **Quality of Data**: The output is only as good as the input—ensure your data is clean and well-structured.
- **Chunk Size**: Proper chunking of data is crucial for optimal performance.
- **Performance Evaluation**: Regularly assess the performance of your RAG-based application.

This project allows you to interact directly with a GitHub repository and leverage semantic search to understand the codebase. Ask specific questions about the repository's code and receive meaningful, context-aware responses.

### Components
- **Elasticsearch**: Serves as the vector database for efficient storage and retrieval of embeddings.
- **LlamaIndex**: A framework for building applications powered by LLM.
- **OpenAI**: Used for both the LLM and generating embeddings.

### Architecture

![Github RAG](./images/github-rag.png)

The process starts by cloning a GitHub repository locally to the `/tmp` directory. The `SimpleDirectoryReader` is then used to load the cloned repository for indexing. Documents are split into chunks based on file type, utilizing `CodeSplitter` for code files, along with `JSON`, `Markdown`, and `SentenceSplitters` for other formats. After parsing the nodes, embeddings are generated using the `text-embedding-3-large` model and stored in Elasticsearch. This setup enables semantic search, allowing us to ask meaningful questions about the code.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/framsouza/github-assistant.git
   cd github-assistant
    ```

2. **Install Required Libraries**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Set Up Environment Variables**:
Update the `.env` file with your Elasticsearch credentials and the target GitHub repository details (eg, `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BRANCH`, `ELASTIC_CLOUD_ID`, `ELASTIC_USER`, `ELASTIC_PASSWORD`, `ELASTIC_INDEX`).

### Usage

1. **Index your data and create the embeddings by running**:
   ```bash
   python index.py
    ```

An Elasticsearch index will be generated, housing the embeddings. You can then connect to your ESS deployment and run search query against the index, you will see a new field named `embeddings`.

2. **Ask questions about your codebase by running**:
   ```bash
   python query.py
    ```
**Example:**
 ```
python query.py                                    
Please enter your query: Give me a detailed list of the external dependencies being used in this repository

 Based on the provided context, the following is a list of third-party dependencies used in the given Elastic Cloud on K8s project:
1. dario.cat/mergo (BSD-3-Clause, v1.0.0)
2. Masterminds/sprig (MIT, v3.2.3)
3. Masterminds/semver (MIT, v4.0.0)
4. go-spew (ISC, v1.1.2-0.20180830191138-d8f796af33cc)
5. elastic/go-ucfg (Apache-2.0, v0.8.8)
6. ghodss/yaml (MIT, v1.0.0)
7. go-logr/logr (Apache-2.0, v1.4.1)
8. go-test/deep (MIT, v1.1.0)
9. gobuffalo/flect (MIT, v1.0.2)
10. google/go-cmp (BSD-3-Clause, v0.6.0)
...

This list includes both direct and indirect dependencies as identified in the context.None
 ```

Questions you might want to ask:
- Give me a detailed description of what are the main functionalities implemented in the code?
- How does the code handle errors and exceptions?
- Could you evaluate the test coverage of this codebase and also provide detailed insights into potential enhancements to improve test coverage significantly?

Happy RAG!