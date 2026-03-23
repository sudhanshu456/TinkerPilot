# TinkerPilot - Model Selection & Justification

## Executive Summary

TinkerPilot uses three local AI models, all running on-device via Apple Silicon Metal GPU acceleration. No cloud APIs are used. The models were selected to maximize capability within the strict constraint of an **8GB RAM Apple M1 MacBook**.

| Model | Purpose | Size (on disk) | RAM Usage | Inference Engine |
|-------|---------|----------------|-----------|------------------|
| **Qwen2.5-3B-Instruct** (Q4_K_M GGUF) | Chat, summarization, code explanation, task extraction | ~2.0 GB | ~2.2 GB | llama-cpp-python (Metal) |
| **nomic-embed-text-v1.5** (Q4_K_M GGUF) | Text embeddings for RAG semantic search | ~78 MB | ~150 MB | llama-cpp-python (Metal) |
| **Whisper small** (int8, CTranslate2) | Speech-to-text transcription | ~500 MB | ~500 MB | faster-whisper |
| **Total** | | **~2.6 GB** | **~2.9 GB** | |

With macOS using ~2.5 GB baseline + app overhead (~500 MB for Python, ChromaDB, SQLite, FastAPI), the total footprint is approximately **5.9 GB**, leaving ~2.1 GB headroom on an 8 GB machine.

---

## 1. LLM: Qwen2.5-3B-Instruct

### Why This Model

Qwen2.5-3B-Instruct was chosen over all alternatives at the 1-4B parameter range because it offers the best combination of:

1. **Instruction Following**: Scored highest among 3B models on IFEval (instruction following benchmark), which directly impacts TinkerPilot's structured output tasks (extracting JSON action items from meetings, generating formatted summaries).

2. **Code Understanding**: Strong performance on HumanEval and MBPP benchmarks. Critical for explaining codebases, suggesting debugging steps, and analyzing scripts.

3. **Summarization Quality**: On summarization benchmarks (CNN/DailyMail, XSum), Qwen2.5-3B produces more coherent and factually accurate summaries than comparably-sized models.

4. **32K Context Window**: Supports processing up to ~24,000 words of text in a single prompt. A 1-hour meeting transcript is typically 8,000-12,000 words, fitting comfortably.

5. **Quantization Efficiency**: The Q4_K_M quantization (4-bit, K-quant mixed) preserves 97%+ of full-precision quality while reducing model size by ~4x. On Apple Silicon, the unified memory architecture means both CPU and GPU access the same memory pool, making quantized models particularly efficient.

### Alternatives Considered and Rejected

| Model | Parameters | Q4 Size | Why Not |
|-------|-----------|---------|---------|
| **Gemma 3 1B** | 1B | ~0.7 GB | Too weak for multi-step reasoning. Produces shallow, often inaccurate summaries. Struggles with structured JSON output. Useful only for classification, not an assistant. |
| **Gemma 3 4B** | 4B | ~2.8 GB | Strong model with 128K context. However, at 2.8 GB + 2.9 GB for other models + 3 GB system = 8.7 GB, it would cause memory swapping on an 8 GB machine, degrading performance significantly. Would be the top choice on a 16 GB machine. |
| **Llama 3.2-3B** | 3B | ~2.0 GB | Good model but benchmarks show Qwen2.5-3B outperforms it on MMLU (+3.2%), HumanEval (+5.1%), and summarization tasks. Same size, less capable. |
| **Phi-4-mini (3.8B)** | 3.8B | ~2.3 GB | Strong at math and reasoning, but weaker at creative summarization and natural language generation. 16K context window (vs 32K) limits meeting transcript processing. |
| **Mistral 7B** | 7B | ~4.1 GB | Won't fit on 8 GB alongside other models. Would require unloading all other models for each inference call. |
| **SmolLM2 1.7B** | 1.7B | ~1.1 GB | Decent for its size but noticeably worse at code explanation and structured extraction compared to Qwen2.5-3B. |

### How It's Used in TinkerPilot

- **RAG Chat**: Answers questions about ingested documents with source citations
- **Meeting Summarization**: Produces structured JSON with summary, decisions, action items, follow-ups
- **Code Explanation**: Analyzes scripts and codebases, identifies patterns and issues
- **Task Extraction**: Extracts action items from arbitrary text
- **Log Analysis**: Identifies error patterns and suggests fixes
- **Command Generation**: Converts natural language to shell commands
- **Daily Digest**: Generates morning briefing from aggregated data
- **Git Digest**: Summarizes recent commit activity

### Inference Configuration

```python
n_ctx = 4096        # Context window (conservative for RAM; expandable to 32K)
n_gpu_layers = -1   # Offload ALL layers to Metal GPU
n_threads = 4       # CPU threads for non-GPU operations
temperature = 0.7   # Balanced creativity/accuracy (lowered to 0.3 for structured tasks)
```

On Apple M1, this configuration yields approximately **15-25 tokens/second** for generation, which is responsive enough for interactive chat.

---

## 2. Embeddings: nomic-embed-text-v1.5

### Why This Model

nomic-embed-text-v1.5 was chosen for the embedding/retrieval layer because:

1. **Runs via llama.cpp**: Unlike sentence-transformers models that require PyTorch (~2 GB overhead), nomic-embed-text has a GGUF variant that runs through the same llama-cpp-python engine. This eliminates an entire framework dependency and saves ~1.5 GB of RAM.

2. **Quality**: Ranks in the top tier on the MTEB leaderboard for retrieval tasks. 768-dimensional embeddings provide a good balance between quality and storage efficiency.

3. **Task Prefixes**: Supports `search_document:` and `search_query:` prefixes, which improve retrieval accuracy by 5-8% compared to models without asymmetric prefixes. This is implemented in TinkerPilot's embedding layer.

4. **8192 Token Input**: Can embed long document chunks without truncation.

5. **Tiny Footprint**: Only 78 MB on disk, ~150 MB in RAM.

### Alternatives Considered

| Model | Why Not |
|-------|---------|
| **all-MiniLM-L6-v2** | Requires sentence-transformers + PyTorch (~2 GB RAM overhead). Lower quality embeddings. |
| **BGE-small-en** | Also requires PyTorch. Similar quality to nomic but heavier dependency chain. |
| **GTE-small** | Same PyTorch dependency issue. |
| **mxbai-embed-large** | Higher quality but 335M params = more RAM. nomic is sufficient for our use case. |

### How It's Used

- **Document Ingestion**: Every text chunk is embedded and stored in ChromaDB
- **Semantic Search**: User queries are embedded with query prefix, then compared against document embeddings using cosine similarity
- **RAG Retrieval**: Top-K most relevant chunks are retrieved and fed to the LLM as context

---

## 3. Speech-to-Text: Whisper small (faster-whisper, int8)

### Why This Model

OpenAI's Whisper model (via the faster-whisper reimplementation) was chosen because:

1. **faster-whisper is 4x faster** than the original OpenAI implementation and uses less memory, thanks to CTranslate2's optimized inference engine with int8 quantization.

2. **Whisper small** offers the best accuracy/size tradeoff for 8 GB machines:
   - Whisper tiny: Fast but noticeable accuracy issues with accented speech, technical jargon
   - Whisper small: Good accuracy, 500 MB RAM, ~2x real-time speed on CPU
   - Whisper medium: Better accuracy but 1.5 GB RAM, too heavy alongside LLM
   - Whisper large: 3 GB, impossible on 8 GB

3. **int8 Quantization**: Reduces RAM usage by ~40% with negligible accuracy loss (<0.5% WER increase).

4. **VAD (Voice Activity Detection)**: Built-in Silero VAD automatically strips silence, reducing processing time for meetings with pauses.

5. **Python API**: 3-line integration. Mature, well-tested, 21K GitHub stars, 9K+ dependents.

### Why Not Parakeet V3

Parakeet V3 (NVIDIA's model used by Handy and Meetily) was seriously considered because it offers excellent English accuracy with CPU-only inference. However:

1. **No Python API**: Parakeet is primarily accessible via Rust (`transcription-rs`) or NVIDIA NeMo (~10 GB dependency). There's no lightweight Python wrapper.
2. **ONNX Runtime complexity**: Running Parakeet via raw ONNX Runtime requires building custom audio preprocessing and CTC/TDT decoding pipelines from scratch -- significant engineering effort with no quality advantage over Whisper small.
3. **Whisper's ecosystem**: far more battle-tested in production Python applications.

If a quality Python wrapper for Parakeet emerges, swapping it in would be straightforward since TinkerPilot's whisper wrapper is a thin abstraction layer.

### Memory Management Strategy

Whisper is **lazy-loaded**: it's only loaded into memory when transcription is requested, and can be unloaded afterward. This prevents it from competing with the LLM for RAM during normal chat/RAG operations:

```
Normal operation:  LLM (2.2GB) + Embeddings (150MB) + App (500MB) = ~2.85 GB
During transcribe: LLM unloaded -> Whisper (500MB) + Embeddings (150MB) + App (500MB) = ~1.15 GB
```

---

## 4. Vector Database: ChromaDB

ChromaDB was chosen as the local vector store because:

1. **Embedded mode**: Runs in-process, no separate server needed. Data persists to `~/.tinkerpilot/data/chroma/`.
2. **Custom embedding functions**: Integrates directly with our llama.cpp embedder via a custom `EmbeddingFunction` class.
3. **HNSW index**: Uses cosine similarity with HNSW (Hierarchical Navigable Small World) indexing for fast approximate nearest neighbor search.
4. **Metadata filtering**: Supports filtering by file type, filename, etc. during retrieval.
5. **Lightweight**: ~50 MB RAM overhead for typical document collections.

---

## 5. RAM Budget Analysis (8 GB M1 MacBook)

```
┌─────────────────────────────────────────────┐
│           8,192 MB Total RAM                │
├─────────────────────────────────────────────┤
│ macOS + system processes      ~2,500 MB     │
│ Python runtime + FastAPI        ~200 MB     │
│ ChromaDB (in-process)           ~100 MB     │
│ SQLite + other app overhead     ~100 MB     │
├─────────────────────────────────────────────┤
│ Available for models:         ~5,292 MB     │
├─────────────────────────────────────────────┤
│ Qwen2.5-3B (Q4_K_M, Metal)   ~2,200 MB     │
│ nomic-embed-text-v1.5 (Q4)     ~150 MB     │
│ Whisper small (int8) *lazy*     ~500 MB     │
├─────────────────────────────────────────────┤
│ Total model usage:            ~2,850 MB     │
│ Remaining headroom:           ~2,442 MB     │
└─────────────────────────────────────────────┘

* Whisper is lazy-loaded and can be swapped with LLM
```

This budget leaves comfortable headroom for:
- macOS memory pressure spikes
- Browser tabs (for the web UI)
- File system caching
- Processing large documents

---

## 6. Architecture Decision: llama-cpp-python vs Ollama

TinkerPilot uses **llama-cpp-python** (direct C++ bindings) rather than Ollama because:

| Factor | llama-cpp-python | Ollama |
|--------|-----------------|--------|
| Dependency | Single pip package | Separate application to install and run |
| Integration | In-process, direct API calls | HTTP API to separate process |
| Memory control | Fine-grained (n_gpu_layers, n_ctx) | Limited configuration |
| Embedding support | Native `model.embed()` | Requires separate API call |
| Startup | Model loads with the app | Separate service must be running |
| User experience | `pip install` + run | Install Ollama + pull models + start server |

For a developer tool that should "just work" after setup, eliminating the Ollama dependency removes a common failure point and simplifies the user experience.

---

## 7. Model Configurability

TinkerPilot's model layer is designed to be **model-agnostic**. Users can swap models by:

1. Dropping a different GGUF file in the `models/` directory
2. Updating `~/.tinkerpilot/config.yaml`:

```yaml
llm:
  model_path: /path/to/different-model.gguf
  n_ctx: 8192
  n_gpu_layers: -1

embedding:
  model_path: /path/to/different-embeddings.gguf

whisper:
  model_size: medium  # or tiny, base, small, large
```

This means users with 16 GB+ RAM can easily upgrade to Qwen2.5-7B, Gemma 3 4B, or even Llama 3.1-8B without any code changes.

---

## 8. Performance Expectations on M1 8GB

| Operation | Expected Performance |
|-----------|---------------------|
| LLM generation (Qwen 3B, Q4, Metal) | 15-25 tokens/sec |
| Document embedding (nomic, Q4) | ~200 chunks/minute |
| Speech transcription (Whisper small, int8) | ~2x real-time |
| RAG query (retrieve + generate) | 3-8 seconds total |
| Meeting summarization (5 min audio) | ~30 sec transcribe + ~15 sec summarize |
| Startup (cold, loading LLM) | ~5-10 seconds |

These are practical, tested estimates for the M1 8GB configuration. Performance improves significantly on M1 Pro/Max/Ultra or M2/M3/M4 machines with more RAM and GPU cores.
