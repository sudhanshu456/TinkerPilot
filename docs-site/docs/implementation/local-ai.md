---
sidebar_position: 3
sidebar_label: Local AI
title: Local AI Implementation
---
TinkerPilot is designed to run entirely on your local machine, without relying on any cloud-based AI services. This is achieved by using a combination of local AI engines and carefully selected models that offer a good balance of performance and resource usage.

## AI Engines

TinkerPilot uses three main AI engines for its features:

-   **[Ollama](https://ollama.ai/):** Ollama is used for running the Large Language Model (LLM) and the text embedding model. It provides a simple and efficient way to run state-of-the-art models on your local hardware, with automatic hardware acceleration (Apple Metal on macOS, CUDA on Linux).
-   **[Moonshine Voice](https://github.com/moonshine-ai/moonshine):** Moonshine Voice is a lightweight and fast speech-to-text (STT) engine that runs locally. It is used for transcribing meetings and voice notes.
-   **[Kokoro](https://github.com/hexgrad/kokoro):** Kokoro is a text-to-speech (TTS) engine that generates natural-sounding speech from text. It is used for the "speak" command in the CLI.

## AI Models

The following models are used in TinkerPilot:

| Model                | Purpose                          | Size     | Engine             |
| -------------------- | -------------------------------- | -------- | ------------------ |
| Qwen2.5-3B-Instruct  | Chat, summarization, code analysis | ~2.0 GB  | Ollama             |
| Qwen3-Embedding 0.6B | Text embeddings for RAG          | ~639 MB  | Ollama             |
| Moonshine Voice      | Speech-to-text (streaming)       | ~250 MB  | Moonshine (ONNX)   |
| Kokoro-82M           | Text-to-speech (6 voices)        | ~82 MB   | PyTorch            |


## RAG Pipeline

The \"Chat with Documents\" feature is powered by a Retrieval-Augmented Generation (RAG) pipeline. The implementation can be found in `backend/app/core/rag.py`.

The RAG pipeline consists of two main processes: ingestion and querying.

### Ingestion

The ingestion process involves the following steps:
1.  **Parsing:** The input file is parsed to extract its text content and metadata. The parser supports a wide range of file types, including PDF, Markdown, Python, and more.
2.  **Chunking:** The extracted text is split into smaller, overlapping chunks. This is done to ensure that the context provided to the LLM is focused and relevant.
3.  **Embedding:** Each chunk is converted into a vector embedding using the text embedding model (Qwen3-Embedding 0.6B).
4.  **Storage:** The embeddings are stored in a [ChromaDB](https://www.trychroma.com/) vector database. The metadata for the ingested documents is also stored in the SQLite database.

### Querying

When you ask a question in the chat, the following steps are performed:
1.  **Embedding:** Your question is converted into a vector embedding using the same embedding model.
2.  **Retrieval:** The vector database is searched to find the most similar chunks to your question's embedding.
3.  **Generation:** The retrieved chunks are passed to the LLM as context, along with your original question. The LLM then generates an answer based on the provided context.
4.  **Streaming:** The answer is streamed back to the frontend in real-time, providing a responsive user experience.

## Configuration

You can customize the AI models and other settings in the `~/.tinkerpilot/config.yaml` file. For example, you can change the LLM model used for chat, the embedding model, and the size of the speech-to-text model.

```yaml
llm:
  model_name: "qwen2.5:3b"  # any model from: ollama list
  temperature: 0.7

embedding:
  model_name: "qwen3-embedding:0.6b"  # or nomic-embed-text, mxbai-embed-large

stt:
  model_size: small  # tiny, base, small, medium, large
```
This allows you to tailor the AI's performance and resource usage to your specific needs and hardware.
