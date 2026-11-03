# RIZEN OFFLINE AI

A private AI chatbot that runs fully on your own computer.

> **Model notice:** RIZEN OFFLINE AI is powered by the **Qwen3-8B** language model (GGUF build, Q4_K_M) from the **Qwen team at Alibaba Cloud**. Every answer is written by this model. The model is downloaded once from Hugging Face: https://huggingface.co/Qwen/Qwen3-8B-GGUF. Qwen3-8B is released under the Apache License 2.0. See NOTICE.md.

**Developed by Anunay Srivastava.**

---

## What you get

- A modern chat screen with streaming replies, so words appear as the model writes.
- Works offline after a one-time setup. Your chats stay on your computer.
- Stop, Regenerate and Copy buttons for every reply.
- Deep thinking mode for harder questions (the model shows its reasoning in a collapsible box).
- Saved chats with search, delete and export to Markdown.
- Code blocks with a Copy button, tables and lists.
- Dark and light themes.
- Settings for the system prompt, creativity and reply length.
- A `brain.md` file that defines the assistant. Edit it to change how RIZEN behaves.

## Quick start (Windows)

1. Install **Python 3.10, 3.11 or 3.12** from https://www.python.org/downloads/. On the first screen of the installer, tick **Add python.exe to PATH**.
2. Unzip `RIZEN-OFFLINE-AI.zip` into any folder, for example your Desktop.
3. Double-click **`start.bat`**.
4. Wait for the four steps in the black window to finish. Your browser opens at http://127.0.0.1:7860.

`start.bat` does everything for you:

| Step | What happens | How long |
| --- | --- | --- |
| 1 | Creates a private Python environment in `.venv` | Seconds |
| 2 | Installs the web server and the Qwen engine | Minutes |
| 3 | Downloads the Qwen3-8B model (about 5 GB) | 10 to 60 minutes, depending on your connection |
| 4 | Starts RIZEN OFFLINE AI | Seconds |

The first run is the only one that needs the internet. If the download stops, run `start.bat` again and it continues from where it stopped.

To stop the app, click the black window and press **Ctrl + C**.

### Open the chat again later

After the first setup, double-click **`open-rizen.bat`**. It opens http://127.0.0.1:7860 in your browser. If the app is not running yet, it starts it first in a small window. Use `start.bat` for the first setup and after you update the files.

## Going fully offline

Once step 3 has finished, the app works without internet. To check it yourself, turn off Wi-Fi or unplug the network cable, then run `start.bat` again. The chat still works. Nothing is sent online, and the app never reaches the internet while it runs.

## macOS and Linux

Open a terminal in the project folder and run:

```bash
chmod +x start.sh
./start.sh
```

On Apple Silicon Macs the engine uses Metal (Apple's GPU API) automatically when it compiles. Python 3.10 to 3.12 is recommended. Install it with Homebrew (`brew install python@3.12`) or from python.org.

## Manual setup (if start.bat does not work)

Windows (Command Prompt, in the project folder):

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python download_model.py
python app.py
```

macOS or Linux (Terminal, in the project folder):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_model.py
python app.py
```

Then open http://127.0.0.1:7860 in your browser.

## Folder layout

```
RIZEN-OFFLINE-AI/
  start.bat          Windows: one-click setup and launch
  open-rizen.bat     Windows: open the chat in your browser (after setup)
  start.sh           macOS and Linux: one-click setup and launch
  app.py             The local server that runs the model
  download_model.py  Downloads Qwen3-8B once (resumes if interrupted)
  config.json        Settings (model file, address, speed)
  brain.md           The assistant's brain: identity and system prompt
  requirements.txt   Python packages
  README.md          This guide
  REQUIREMENTS.md    What your computer needs
  LICENSE            MIT License (copyright and terms of use)
  NOTICE.md          Notices for the Qwen model and other open-source parts
  CHANGELOG.md       Version history
  static/            The web interface (HTML, CSS, JavaScript)
  models/            The Qwen3-8B model file goes here
  data/chats/        Your saved chats (one JSON file per chat)
```

## Settings: config.json

| Setting | Default | What it does |
| --- | --- | --- |
| `model_path` | `models/Qwen3-8B-Q4_K_M.gguf` | Which model file to load |
| `host` | `127.0.0.1` | Keep this value so only your computer can reach the app |
| `port` | `7860` | The address you open in the browser |
| `thinking_tokens` | `1536` | The most reasoning tokens Deep thinking may use before the answer is forced. Lower is faster |
| `context_size` | `4096` | How much conversation the model can see at once. Larger uses more memory |
| `threads` | `0` | CPU threads. `0` means automatic |
| `gpu_layers` | `0` | Layers to run on a graphics card. `0` is CPU only |
| `open_browser` | `true` | Open the browser when the app starts |

Restart the app after you change `config.json`.

## Settings in the app

Click the sliders icon at the top right.

- **System prompt:** the instructions the assistant follows. Leave it as it is to use `brain.md`.
- **Creativity:** lower gives exact answers, higher gives more varied ones. Good values: 0.6 to 0.8.
- **Word range:** how wide a choice the model makes for each word. Keep 0.8 unless you know you need a change.
- **Longest reply:** the maximum length of one answer.
- **Delete all:** removes every saved chat.

Qwen3 suggests slightly different values for Deep thinking: creativity 0.6 and word range 0.95. Try them if the reasoning feels off.

## Using the app

| Action | How |
| --- | --- |
| Send a message | Press **Enter** |
| New line inside a message | **Shift + Enter** |
| New chat | **Ctrl + K** (Mac: Cmd + K) or the **New chat** button |
| Skip the thinking and answer now | **Skip** button (arrow with a bar). It is active while the model is thinking |
| Stop a reply | **Stop** button (square) |
| Try again | **Regenerate** under the last reply |
| Copy a reply | **Copy** under the reply, or the **Copy** button on a code block |
| Save a chat as a file | Download icon at the top |
| Light or dark theme | Half-circle icon at the top |
| Show or hide the chat list | Lines icon at the top left |

## Deep thinking and Skip

Turn on **Deep thinking** for hard questions. The model reasons first, and its reasoning appears in a *Reasoning* box above the answer. The badge at the bottom shows what the model is doing (fast, thinking, or answering) and how many reasoning tokens it has written so far.

Reasoning can take a long time. Press **Skip** to stop thinking right away. The model writes the answer using the reasoning it has already done, and the box is labelled *Reasoning, cut short*. Skip works only while the model is thinking.

If the reasoning reaches the limit set by `thinking_tokens` in `config.json` (default 1536), the app cuts it short in the same way.

## brain.md: the assistant's brain

`brain.md` describes RIZEN OFFLINE AI: its name, the model, what it can and cannot do, and the system prompt. The system prompt is the block between the two HTML comment markers at the bottom of the file. Change the wording there and the next reply follows the new instructions. No restart is needed.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| "Python was not found" | Install Python 3.10 to 3.12 and tick **Add python.exe to PATH**. Open a new window and run `start.bat` again. |
| The top badge says **Model not found** | The download has not finished. Run `start.bat` again while connected to the internet. |
| The download is very slow or stopped | Run `start.bat` again. It resumes. |
| Install fails with "Microsoft Visual C++ 14.0 is required" | Install **Build Tools for Visual Studio** with the *Desktop development with C++* workload, then run `start.bat` again. |
| "Port 7860 is in use" | Change `port` in `config.json` (for example to `7861`) and start again. |
| Replies are very slow | Normal on a laptop CPU. Press **Skip** while the model is thinking, use a smaller reply length, or set `gpu_layers` if you have an NVIDIA graphics card with a CUDA build. |
| "Out of memory" or the computer slows down | Close other programs, or lower `context_size` to `2048`. |
| The page is blank | Wait 20 to 60 seconds while the model loads, then refresh. The top badge shows the progress. |

## Use a different GGUF model

You can try another model that works with the ChatML format. Put the file in `models/`, then change `model_path` in `config.json`. Qwen3-8B is the model this app was built and tested for, so use it unless you have a reason to change.

## Contact

- GitHub: https://github.com/anunaysrivastava04-coder
- LinkedIn: https://www.linkedin.com/in/anunay-srivastava-2638a1362/
- Instagram: https://www.instagram.com/anunay_srivastava108

## License and copyright

Copyright (c) 2026 Anunay Srivastava. RIZEN OFFLINE AI is released under the MIT License. You may use, copy, change and share it, including for commercial use, as long as the license notice stays with the code. See the LICENSE file.

The Qwen3-8B model has its own license (Apache License 2.0) and is not part of this zip. See NOTICE.md.
