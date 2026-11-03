# Changelog

## 1.1.0

- Skip button: while the model is thinking, press Skip to cut the reasoning short and get the answer straight away.
- The composer shows a spinner, a model badge (qwen3, 8B, thinking, fast, or answering), a live count of reasoning tokens, and square Stop and Skip icon buttons.
- The server closes the reasoning block itself on Skip or when `thinking_tokens` is reached, so the answer keeps going without a restart.
- Reasoning that was cut short is labelled in the chat.
- New `open-rizen.bat` for Windows: opens the chat straight in the browser at its local link, and starts the app first if it is not running.

## 1.0.0 - 2026

- First release of RIZEN OFFLINE AI.
- Offline chat with the Qwen3-8B model (GGUF) through llama-cpp-python.
- One-click setup for Windows (`start.bat`) and macOS or Linux (`start.sh`).
- Resumable one-time model download.
- Streaming replies, Stop, Regenerate, Copy, and Deep thinking mode.
- Saved chats with search, delete and Markdown export.
- Dark and light themes, settings for system prompt, creativity and reply length.
- `brain.md` defines the assistant. The system prompt is read on every reply.
- Developer credit, contact links, copyright and MIT license in the app.
