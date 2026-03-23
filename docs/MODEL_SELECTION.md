# TinkerPilot - Model Selection & Justification

## Executive Summary

TinkerPilot uses three local AI models, all running on-device via Apple Silicon Metal GPU acceleration. No cloud APIs are used. The models were selected to maximize capability within the strict constraint of an **8GB RAM Apple M1 MacBook**.

| Model | Purpose | Size (on disk) | RAM Usage | Inference Engine |
|-------|---------|----------------|-----------|------------------|
| **Qwen2.5-3B-Instruct** | Chat, summarization, code explanation, task extraction | ~2.0 GB | ~2.2 GB | Ollama (Metal GPU) |
| **nomic-embed-text** | Text embeddings for RAG semantic search | ~274 MB | ~300 MB | Ollama (Metal GPU) |
| **Whisper small** (int8, CTranslate2) | Speech-to-text transcription | ~500 MB | ~500 MB | faster-whisper |
| **Total** | | **~2.8 GB** | **~3.0 GB** | |

With macOS using ~2.5 GB baseline + app overhead (~500 MB for Python, ChromaDB, SQLite, FastAPI), the total footprint is approximately **6.0 GB**, leaving ~2.0 GB headroom on an 8 GB machine.

---

## 1. LLM: Qwen2.5-3B-Instruct

### Why This Model

Qwen2.5-3B-Instruct was chosen over all alternatives at the 1-4B parameter range because it offers the best combination of:

1. **Instruction Following**: Scored highest among 3B models on IFEval (instruction following benchmark), which directly impacts TinkerPilot's structured output tasks (extracting JSON action items from meetings, generating formatted summaries).

2. **Code Understanding**: Strong performance on HumanEval and MBPP benchmarks. Critical for explaining codebases, suggesting debugging steps, and analyzing scripts.

3. **Summarization Quality**: On summarization benchmarks (CNN/DailyMail, XSum), Qwen2.5-3B produces more coherent and factually accurate summaries than comparably-sized models.

4. **32K Context Window**: Supports processing up to ~24,000 words of text in a single prompt. A 1-hour meeting transcript is typically 8,000-12,000 words, fitting comfortably.

### Alternatives Considered and Rejected

| Model | Parameters | Size | Why Not |
|-------|-----------|------|---------|
| **Gemma 3 1B** | 1B | ~0.7 GB | Too weak for multi-step reasoning. Produces shallow, often inaccurate summaries. Struggles with structured JSON output. |
| **Gemma 3 4B** | 4B | ~2.8 GB | Strong model with 128K context. However, at 2.8 GB + other models + system = would cause memory swapping on 8 GB. Top choice for 16 GB+ machines. |
| **Llama 3.2-3B** | 3B | ~2.0 GB | Good model but benchmarks show Qwen2.5-3B outperforms it on MMLU (+3.2%), HumanEval (+5.1%), and summarization tasks. Same size, less capable. |
| **Phi-4-mini (3.8B)** | 3.8B | ~2.3 GB | Strong at math and reasoning, but weaker at creative summarization. 16K context (vs 32K) limits meeting transcript processing. |
| **Mistral 7B** | 7B | ~4.1 GB | Won't fit on 8 GB alongside other models. |

### How It's Used in TinkerPilot

- **RAG Chat**: Answers questions about ingested documents with source citations
- **Meeting Summarization**: Produces structured JSON with summary, decisions, action items, follow-ups
- **Code Explanation**: Analyzes scripts and codebases
- **Task Extraction**: Extracts action items from arbitrary text
- **Log Analysis**: Identifies error patterns and suggests fixes
- **Command Generation**: Converts natural language to shell commands
- **Daily Digest**: Generates morning briefing from aggregated data
- **Git Digest**: Summarizes recent commit activity

---

## 2. Embeddings: nomic-embed-text

### Why This Model

nomic-embed-text was chosen for the embedding/retrieval layer because:

1. **Available in Ollama**: Zero-config install with `ollama pull nomic-embed-text`. No compilation, no PyTorch dependency.

2. **Quality**: Ranks in the top tier on the MTEB leaderboard for retrieval tasks. 768-dimensional embeddings provide a good balance between quality and storage efficiency.

3. **8192 Token Input**: Can embed long document chunks without truncation.

4. **Small Footprint**: ~274 MB on disk, ~300 MB in RAM via Ollama.

### Alternatives Considered

| Model | Why Not |
|-------|---------|
| **all-MiniLM-L6-v2** | Requires sentence-transformers + PyTorch (~2 GB RAM overhead). |
| **BGE-small-en** | Also requires PyTorch. Similar quality but heavier dependency chain. |
| **mxbai-embed-large** | Higher quality but 335M params = more RAM. nomic is sufficient for our use case. |

---

## 3. Speech-to-Text: Whisper small (faster-whisper, int8)

### Why This Model

OpenAI's Whisper model (via the faster-whisper reimplementation) was chosen because:

1. **faster-whisper is 4x faster** than the original OpenAI implementation, thanks to CTranslate2's optimized inference engine with int8 quantization.

2. **Whisper small** offers the best accuracy/size tradeoff for 8 GB machines:
   - Whisper tiny: Fast but noticeable accuracy issues with accented speech
   - Whisper small: Good accuracy, 500 MB RAM, ~2x real-time speed
   - Whisper medium: Better accuracy but 1.5 GB RAM, too heavy alongside LLM
   - Whisper large: 3 GB, impossible on 8 GB

3. **VAD (Voice Activity Detection)**: Built-in Silero VAD automatically strips silence, reducing processing time.

4. **Python API**: 3-line integration. Mature, well-tested, 21K+ GitHub stars.

### Why Not Parakeet V3

Parakeet V3 (NVIDIA's model) was considered but rejected: no lightweight Python wrapper exists. Running via raw ONNX Runtime requires building custom audio preprocessing and CTC decoding pipelines from scratch.

### Memory Management Strategy

Whisper is **lazy-loaded**: only loaded when transcription is requested, unloaded afterward. Ollama also auto-manages LLM/embedding model memory.

---

## 4. Architecture Decision: Ollama

TinkerPilot uses **Ollama** for LLM and embedding inference:

| Factor | Benefit |
|--------|---------|
| **Install** | `brew install ollama` — one command, pre-built binary |
| **Model management** | `ollama pull qwen2.5:3b` — handles downloads, quantization, caching |
| **Metal GPU** | Automatic on Apple Silicon — zero configuration |
| **Stability** | No C++ compilation, no cmake, no ccache. Binary works on any macOS |
| **API** | OpenAI-compatible REST API on localhost:11434 |
| **Memory** | Auto-manages model loading/unloading |

This was chosen over llama-cpp-python (direct C++ bindings) because:
- llama-cpp-python requires compiling C++ from source, which fails on many systems (wrong Python version, broken ccache, missing cmake/Xcode tools)
- Ollama provides the same Metal GPU acceleration with zero compilation
- The ~50MB overhead from the Ollama server process is negligible

---

## 5. RAM Budget Analysis (8 GB M1 MacBook)

```
┌─────────────────────────────────────────────┐
│           8,192 MB Total RAM                │
├─────────────────────────────────────────────┤
│ macOS + system processes      ~2,500 MB     │
│ Python + FastAPI + ChromaDB     ~400 MB     │
│ Ollama server                    ~50 MB     │
├─────────────────────────────────────────────┤
│ Available for models:         ~5,242 MB     │
├─────────────────────────────────────────────┤
│ Qwen2.5-3B (Ollama, Metal)   ~2,200 MB     │
│ nomic-embed-text (Ollama)      ~300 MB     │
│ Whisper small (int8) *lazy*    ~500 MB     │
├─────────────────────────────────────────────┤
│ Total model usage:            ~3,000 MB     │
│ Remaining headroom:           ~2,242 MB     │
└─────────────────────────────────────────────┘
```

---

## 6. Model Configurability

Users can swap models by updating `~/.tinkerpilot/config.yaml`:

```yaml
llm:
  model_name: "qwen2.5:3b"   # or llama3.2:3b, gemma3:4b, etc.
  temperature: 0.7

embedding:
  model_name: "nomic-embed-text"  # or mxbai-embed-large, etc.

whisper:
  model_size: small  # tiny, base, small, medium, large
```

Any model available via `ollama list` can be used. Users with 16 GB+ RAM can upgrade to larger models (e.g., `qwen2.5:7b`, `gemma3:4b`) without code changes.

---

## 7. Performance Expectations on M1 8GB

| Operation | Expected Performance |
|-----------|---------------------|
| LLM generation (Qwen 3B, Metal) | 15-25 tokens/sec |
| Document embedding (nomic) | ~200 chunks/minute |
| Speech transcription (Whisper small, int8) | ~2x real-time |
| RAG query (retrieve + generate) | 3-8 seconds total |
| Meeting summarization (5 min audio) | ~30 sec transcribe + ~15 sec summarize |
| Startup (cold, first model load) | ~5-10 seconds |

Performance improves significantly on M1 Pro/Max/Ultra or M2/M3/M4 machines.
