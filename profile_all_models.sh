#!/bin/bash
# This script profiles a list of known Ollama models to build the fingerprint database.

set -e

MODELS=(
    "llama2:13b"
    "llama2:7b"
    "llama3.2:3b"
    "llama3.2:1b"
    "llama3.1:8b"
    "qwen3:1.7b"
    "qwen3:8b"
    "qwen3:4b"
    "deepseek-r1:latest"
    "mistral:latest"
    "codellama:13b"
    "llama3:8b"
)

for model in "${MODELS[@]}"; do
    echo "================================================="
    echo "Profiling model: $model"
    echo "================================================="
    python fingerprint_profiler.py --url http://localhost:11434/api/chat --model "$model" --save-as "$model" --runs 3
done

echo "================================================="
echo "All models have been profiled."
echo "================================================="
