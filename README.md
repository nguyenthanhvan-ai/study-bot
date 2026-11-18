# Study Assistant Chatbot with Filtered Memory

A command-line study assistant that runs a local model (Qwen3 8B via Ollama) and remembers
things the user chooses to save. Memories pass a privacy filter before they are stored, and
only relevant memories are included in each answer.

## Commands

- `/mon <subject>`: save a subject you are studying, for example `/mon Giải tích 1`.
- `/muc-tieu <goal>`: save a study goal, for example `/muc-tieu IELTS Writing band 7.0`.
- `/ke-hoach`: ask the model for a one-week plan based on your saved subjects and goals.
- `/quiz <topic>`: ask the model for three practice questions with answers.
- `/nho <text>`: save any memory. The text is checked by the privacy filter first.
- `/ky-uc`: list saved memories. `/thoat`: quit.
- Any other message is answered by the local model. The three most relevant memories, found by
  keyword ranking, are added to the prompt.

Memory is stored in a local SQLite file (`memory.db`). It is not committed to Git.

## Files

- `chat.py`: command-line loop, Ollama call, and prompt assembly.
- `memory.py`: privacy filter and database migration (shared with the memory-filter project).
- `retrieval.py`: keyword-based memory ranking.
- `tests/test_chat.py`: tests for saving, refusing, listing, quitting, and prompt building.

## Setup and run

```powershell
ollama pull qwen3:8b
pip install -r requirements.txt
python chat.py
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

The tests do not call the model. They check the memory logic and prompt building only.

## Limitations

- Memories are saved only with `/nho`. The bot does not decide on its own what to remember.
- Ranking is keyword-based, so a question worded very differently from a memory may not retrieve it.
- The model's answers are not evaluated here. See the separate `local-llm-eval` project for that.