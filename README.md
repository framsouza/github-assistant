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

### Evaluation

The `evaluation.py` code processes documents, generates evaluation questions based on the content, and then evaluates the responses for relevancy (_Whether the response is relevant to the question_) and faithfulness (_Whether the response is faithful to the source content_) using a LLM. Here’s a step-by-step guide on how to use the code:

```
python evaluation.py --num_documents 5 --skip_documents 2 --num_questions 3 --skip_questions 1 --process_last_questions
```

You can run the code without any parameters, but the example above demonstrates how to use the parameters. Here's a breakdown of what each parameter does:

##### Document Processing:

- **--num_documents 5**: The script will process a total of 5 documents.
- **--skip_documents 2**: The first 2 documents will be skipped, and the script will start processing from the 3rd document onward. So, it will process documents 3, 4, 5, 6, and 7.

##### Question Generation:

After loading the documents, the script will generate a list of questions based on the content of these documents.
- **--num_questions 3**: Out of the generated questions, only 3 will be processed.
- **--skip_questions 1**: The script will skip the first question in the list and process questions starting from the 2nd question.
- **--process_last_questions**: Instead of processing the first 3 questions after skipping the first one, the script will take the last 3 questions in the list.

```
Number of documents loaded: 5
\All available questions generated:
0. What is the purpose of chunking monitors in the updated push command as mentioned in the changelog?
1. How does the changelog describe the improvement made to the performance of the push command?
2. What new feature is added to the synthetics project when it is created via the `init` command?
3. According to the changelog, what is the file size of the CHANGELOG.md document?
4. On what date was the CHANGELOG.md file last modified?
5. What is the significance of the example lightweight monitor yaml file mentioned in the changelog?
6. How might the changes described in the changelog impact the workflow of users creating or updating monitors?
7. What is the file path where the CHANGELOG.md document is located?
8. Can you identify the issue numbers associated with the changes mentioned in the changelog?
9. What is the creation date of the CHANGELOG.md file as per the context information?
10. What type of file is the document described in the context information?
11. On what date was the CHANGELOG.md file last modified?
12. What is the file size of the CHANGELOG.md document?
13. Identify one of the bug fixes mentioned in the CHANGELOG.md file.
14. What command is referenced in the context of creating new synthetics projects?
15. How does the CHANGELOG.md file address the issue of varying NDJSON chunked response sizes?
16. What is the significance of the number #680 in the context of the document?
17. What problem is addressed by skipping the addition of empty values for locations?
18. How many bug fixes are explicitly mentioned in the provided context?
19. What is the file path of the CHANGELOG.md document?
20. What is the file path of the document being referenced in the context information?
...

Generated questions:
1. What command is referenced in relation to the bug fix in the CHANGELOG.md?
2. On what date was the CHANGELOG.md file created?
3. What is the primary purpose of the document based on the context provided?

Total number of questions generated: 3

Processing Question 1 of 3:

Evaluation Result:
+---------------------------------------------------+-------------------------------------------------+----------------------------------------------------+----------------------+----------------------+-------------------+------------------+------------------+
| Query                                             | Response                                        | Source                                             | Relevancy Response   | Relevancy Feedback   |   Relevancy Score | Faith Response   | Faith Feedback   |
+===================================================+=================================================+====================================================+======================+======================+===================+==================+==================+
| What command is referenced in relation to the bug | The `init` command is referenced in relation to | Bug Fixes                                          | Pass                 | YES                  |                 1 | Pass             | YES              |
| fix in the CHANGELOG.md?                          | the bug fix in the CHANGELOG.md.                |                                                    |                      |                      |                   |                  |                  |
|                                                   |                                                 |                                                    |                      |                      |                   |                  |                  |
|                                                   |                                                 | - Pick the correct loader when bundling TypeScript |                      |                      |                   |                  |                  |
|                                                   |                                                 | or JavaScript journey files                        |                      |                      |                   |                  |                  |
|                                                   |                                                 |                                                    |                      |                      |                   |                  |                  |
|                                                   |                                                 |   during push command #626                         |                      |                      |                   |                  |                  |
+---------------------------------------------------+-------------------------------------------------+----------------------------------------------------+----------------------+----------------------+-------------------+------------------+------------------+

Processing Question 2 of 3:

Evaluation Result:
+-------------------------------------------------+------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+
| Query                                           | Response                                       | Source                       | Relevancy Response   | Relevancy Feedback   |   Relevancy Score | Faith Response   | Faith Feedback   |
+=================================================+================================================+==============================+======================+======================+===================+==================+==================+
| On what date was the CHANGELOG.md file created? | The date mentioned in the CHANGELOG.md file is | v1.0.0-beta-38 (20222-11-02) | Pass                 | YES                  |                 1 | Pass             | YES              |
|                                                 | November 2, 2022.                              |                              |                      |                      |                   |                  |                  |
+-------------------------------------------------+------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+

Processing Question 3 of 3:

Evaluation Result:
+---------------------------------------------------+---------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+
| Query                                             | Response                                          | Source                       | Relevancy Response   | Relevancy Feedback   |   Relevancy Score | Faith Response   | Faith Feedback   |
+===================================================+===================================================+==============================+======================+======================+===================+==================+==================+
| What is the primary purpose of the document based | The primary purpose of the document is to provide | v1.0.0-beta-38 (20222-11-02) | Pass                 | YES                  |                 1 | Pass             | YES              |
| on the context provided?                          | a changelog detailing the features and            |                              |                      |                      |                   |                  |                  |
|                                                   | improvements made in version 1.0.0-beta-38 of a   |                              |                      |                      |                   |                  |                  |
|                                                   | software project. It highlights specific          |                              |                      |                      |                   |                  |                  |
|                                                   | enhancements such as improved validation for      |                              |                      |                      |                   |                  |                  |
|                                                   | monitor schedules and an enhanced push command    |                              |                      |                      |                   |                  |                  |
|                                                   | experience.                                       |                              |                      |                      |                   |                  |                  |
+---------------------------------------------------+---------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+
(clean_env) (base) framsouza@Frams-MacBook-Pro-2 git-assistant % 
+-------------------------------------------------+------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+------+------------------+

Processing Question 3 of 3:

Evaluation Result:
+---------------------------------------------------+---------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+-----------+------------------+
| Query                                             | Response                                          | Source                       | Relevancy Response   | Relevancy Feedback   |   Relevancy Score | Faith Response   | Faith Feedback   |Response   | Faith Feedback   |
+===================================================+===================================================+==============================+======================+======================+===================+==================+==================+===========+==================+
| What is the primary purpose of the document based | The primary purpose of the document is to provide | v1.0.0-beta-38 (20222-11-02) | Pass                 | YES                  |                 1 | Pass             | YES              |           | YES              |
| on the context provided?                          | a changelog detailing the features and            |                              |                      |                      |                   |                  |                  |           |                  |
|                                                   | improvements made in version 1.0.0-beta-38 of a   |                              |                      |                      |                   |                  |                  |           |                  |
|                                                   | software project. It highlights specific          |                              |                      |                      |                   |                  |                  |           |                  |
|                                                   | enhancements such as improved validation for      |                              |                      |                      |                   |                  |                  |           |                  |
|                                                   | monitor schedules and an enhanced push command    |                              |                      |                      |                   |                  |                  |           |                  |
|                                                   | experience.                                       |                              |                      |                      |                   |                  |                  |           |                  |
+---------------------------------------------------+---------------------------------------------------+------------------------------+----------------------+----------------------+-------------------+------------------+------------------+-----------+------------------+
```

# Now what?

Here are a few ways you can utilize this code:

- Gain insights into a specific GitHub repository by asking questions about the code, such as locating functions or understanding how parts of the code work.
- Build a multi-agent RAG system that ingests GitHub PRs and issues, enabling automatic responses to issues and feedback on PRs.
- Combine your logs and metrics with the GitHub code in Elasticsearch to create a Production Readiness Review using RAG, helping assess the maturity of your services.

Happy RAG!