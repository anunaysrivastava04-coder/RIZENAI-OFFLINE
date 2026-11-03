# Requirements

> RIZEN OFFLINE AI runs the **Qwen3-8B** model by the Qwen team at Alibaba Cloud. The model is downloaded once and then runs on your computer.

## Computer

| Part | Minimum | Recommended |
| --- | --- | --- |
| Operating system | Windows 10 or 11 (64-bit), macOS 12 or newer, Ubuntu 22.04 or similar | Windows 11 (64-bit) or macOS on Apple Silicon |
| Memory (RAM) | 8 GB (tight, use a smaller reply length) | 16 GB or more |
| Free disk space | 10 GB (model about 5 GB, environment and packages about 1 GB) | 15 GB or more |
| Processor | Any 64-bit CPU from the last 7 years with AVX2 | Modern 8-core CPU or Apple Silicon |
| Graphics card | Not needed | Optional. NVIDIA card with CUDA, or Apple Silicon |

Replies run on your processor by default. Expect a few words per second on a typical laptop. A graphics card makes replies much faster.

## Software

| Software | Version | Why |
| --- | --- | --- |
| Python | 3.10, 3.11 or 3.12 (64-bit) | Runs the server and the Qwen engine. Python 3.13 and newer may not have ready-made engine packages yet. |
| Web browser | Chrome, Edge, Firefox or Safari (recent versions) | Shows the chat screen |
| Build tools (only if needed) | Visual Studio Build Tools with the C++ workload (Windows), Xcode Command Line Tools (macOS), or `build-essential` and `cmake` (Linux) | Only needed if the engine has to be compiled from source |

## Network

- **First run only:** internet is needed to install packages and download the model (about 5 GB) from Hugging Face.
- **After setup:** no internet is needed. RIZEN OFFLINE AI does not send your messages anywhere.

## Python packages

Listed in `requirements.txt`:

| Package | Purpose | License |
| --- | --- | --- |
| flask | Local web server for the interface | BSD-3-Clause |
| llama-cpp-python | Python binding for llama.cpp, which runs the GGUF model | MIT |

The standard library provides everything else, including the model downloader.

## Model

| Item | Value |
| --- | --- |
| Name | Qwen3-8B (GGUF) |
| Maker | Qwen team, Alibaba Cloud |
| File | `Qwen3-8B-Q4_K_M.gguf` (about 5 GB) |
| Source | https://huggingface.co/Qwen/Qwen3-8B-GGUF |
| License | Apache License 2.0 (check the model card for the latest terms) |
| Context window | 4096 tokens by default (set `context_size` in `config.json`) |

## Optional: NVIDIA graphics card (faster replies)

1. Install the latest NVIDIA driver and the CUDA runtime.
2. In `requirements.txt`, replace the `cpu` line with a CUDA index, for example `https://abetlen.github.io/llama-cpp-python/whl/cu124`.
3. Reinstall the packages: `python -m pip install -r requirements.txt --force-reinstall`
4. In `config.json`, set `"gpu_layers": -1` to move all layers to the graphics card.

Check the index address on the llama-cpp-python project page if the CUDA version you need is not listed.

## Ports and addresses

- The app listens only on `127.0.0.1` (your computer) by default.
- Default port: `7860`. Change it in `config.json` if another program uses it.
