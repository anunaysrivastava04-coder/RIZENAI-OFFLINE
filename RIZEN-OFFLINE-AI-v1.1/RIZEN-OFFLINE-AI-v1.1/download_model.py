#!/usr/bin/env python3
"""
Download the Qwen3-8B GGUF model file once. Safe to run again: it resumes
where it stopped if the connection drops.

Model: Qwen3-8B by the Qwen team (Alibaba Cloud), GGUF build from
https://huggingface.co/Qwen/Qwen3-8B-GGUF
"""

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_URL = "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf"
TARGET = BASE_DIR / "models" / "Qwen3-8B-Q4_K_M.gguf"
PARTIAL = TARGET.with_name(TARGET.name + ".part")
MIN_VALID_BYTES = 3 * 1024 ** 3  # the real file is about 5 GB


def human(size):
    if size >= 1024 ** 3:
        return f"{size / 1024 ** 3:.2f} GB"
    return f"{size / 1024 ** 2:.0f} MB"


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists() and TARGET.stat().st_size >= MIN_VALID_BYTES:
        print("Model already downloaded:", TARGET.name)
        return 0

    start_at = PARTIAL.stat().st_size if PARTIAL.exists() else 0
    headers = {"User-Agent": "RIZEN-OFFLINE-AI/1.0"}
    if start_at:
        headers["Range"] = f"bytes={start_at}-"

    print("Downloading Qwen3-8B (about 5 GB). This only happens once.")
    print("Source:", MODEL_URL)
    if start_at:
        print(f"Resuming from {human(start_at)}")

    try:
        request = urllib.request.Request(MODEL_URL, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            resumed = bool(start_at) and response.status == 206
            if start_at and not resumed:
                print("The server did not allow resuming. Starting again from zero.")
                start_at = 0
            length = response.headers.get("Content-Length")
            total = int(length) + start_at if length else 0
            done = start_at
            last_print = 0.0
            with open(PARTIAL, "ab" if resumed else "wb") as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    now = time.time()
                    if now - last_print > 0.5:
                        last_print = now
                        if total:
                            percent = done * 100 / total
                            print(f"\r  {human(done)} of {human(total)} ({percent:5.1f}%)   ", end="", flush=True)
                        else:
                            print(f"\r  {human(done)} downloaded   ", end="", flush=True)
            print()
    except urllib.error.HTTPError as exc:
        if exc.code != 416:  # 416 means the partial file is already complete
            print(f"\nDownload failed: the server answered with code {exc.code}. Try again later.")
            return 1
    except urllib.error.URLError:
        print("\nDownload failed: no internet connection right now.")
        print("Connect to the internet and run start.bat again. The download resumes where it stopped.")
        return 1
    except OSError as exc:
        print(f"\nDownload failed: {exc}")
        return 1

    if not PARTIAL.exists() or PARTIAL.stat().st_size < MIN_VALID_BYTES:
        print("The file looks incomplete. Run start.bat again to resume the download.")
        return 1
    PARTIAL.replace(TARGET)
    print("Model ready:", TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
