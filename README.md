# HR Document Generator

A local LLM-powered tool for generating performance reviews and onboarding plans using GPU acceleration.

## Features

- Generate performance reviews with 3 template styles (formal, casual, technical)
- Generate onboarding plans for new hires
- PDF export with professional styling
- GPU-accelerated inference (NVIDIA CUDA)
- Response caching for faster repeat requests
- RESTful API with FastAPI
- MongoDB for employee data storage

## Requirements

- Python 3.10+
- MongoDB
- Llama 3.2 3B model (GGUF format)
- NVIDIA GPU with CUDA 12+ (recommended) or CPU fallback

## Installation

```bash
cd performance-review-generator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### GPU Setup (Recommended)

For GPU acceleration, install llama-cpp-python with CUDA support:

```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

Requires CUDA 12.1+ toolkit installed on your system.

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=hr_database
EMPLOYEES_COLLECTION=employees

# Model settings
MODEL_PATH=/path/to/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_THREADS=2            # CPU threads (lower when using GPU)
MODEL_CTX=3072             # Context size
MODEL_BATCH=512            # Batch size for prompt processing
MODEL_GPU_LAYERS=-1        # -1 = all layers on GPU, 0 = CPU only

# Performance
CACHE_ENABLED=true         # Cache responses for identical requests

# Output
OUTPUT_DIR=./output
```

### GPU vs CPU Configuration

| Setting            | GPU (Recommended) | CPU Only        |
| ------------------ | ----------------- | --------------- |
| `MODEL_GPU_LAYERS` | `-1` (all layers) | `0`             |
| `MODEL_THREADS`    | `2`               | `4-6`           |
| Expected Speed     | ~6s per review    | ~12s per review |

---
