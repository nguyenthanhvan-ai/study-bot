"""Study assistant chatbot with a privacy-filtered, retrieval-based memory.

Commands:
  /nho <noi dung>   save a memory (checked by the privacy filter first)
  /ky-uc            list saved memories
  /thoat            quit
Anything else is sent to the local model with relevant memories included.
"""
import sqlite3
import sys
import time
from pathlib import Path

import requests

from memory import migrate, validate
from retrieval import rank_memories

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"
DB_PATH = Path(__file__).parent / "memory.db"

SYSTEM_PROMPT = (
    "Bạn là trợ lý học tập, trả lời ngắn gọn bằng tiếng Việt. "
    "Nếu có ký ức liên quan của người dùng, hãy dùng khi thật sự hữu ích; "
    "không bịa thêm thông tin về người dùng."
)


def ensure_schema(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS ky_uc (id INTEGER PRIMARY KEY, loai TEXT, noi_dung TEXT, "
        "luc REAL, dung_lan_cuoi REAL DEFAULT 0, so_lan_dung INTEGER DEFAULT 0)"
    )
    migrate(conn)
    conn.row_factory = sqlite3.Row
    return conn


def save_memory(conn, text):
    """Return True if the memory passed the filter and was stored."""
    item = validate({"loai": "preference", "noi_dung": text, "confidence": 0.9})
    if item is None:
        return False
    conn.execute(
        "INSERT INTO ky_uc (loai, noi_dung, luc, confidence, source, status) VALUES (?, ?, ?, ?, 'user', 'active')",
        (item["loai"], item["noi_dung"], time.time(), item["confidence"]),
    )
    conn.commit()
    return True


def active_memories(conn):
    return conn.execute("SELECT * FROM ky_uc WHERE COALESCE(status, 'active') = 'active'").fetchall()


def build_messages(question, memories):
    system = SYSTEM_PROMPT
    if memories:
        system += "\n\nKý ức liên quan:\n" + "\n".join(f"- {m['noi_dung']}" for m in memories)
    return [{"role": "system", "content": system}, {"role": "user", "content": question}]


def ask_model(messages, model=MODEL):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model, "messages": messages, "stream": False, "think": False,
              "options": {"temperature": 0.3}},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def handle(conn, line):
    """Return (reply, keep_running)."""
    if line == "/thoat":
        return "Tạm biệt.", False
    if line == "/ky-uc":
        rows = active_memories(conn)
        return "\n".join(f"- {r['noi_dung']}" for r in rows) or "Chưa có ký ức nào.", True
    if line.startswith("/nho "):
        text = line[len("/nho "):].strip()
        ok = save_memory(conn, text)
        return ("Đã lưu." if ok else "Không lưu: nội dung không qua bộ lọc (quá ngắn, nhạy cảm hoặc không chắc chắn)."), True
    memories = rank_memories(line, active_memories(conn), limit=3, threshold=0.3)
    return ask_model(build_messages(line, memories)), True


def main():
    conn = ensure_schema(sqlite3.connect(DB_PATH))
    print("Trợ lý học tập. Gõ /nho <điều cần nhớ>, /ky-uc, hoặc /thoat.")
    while True:
        try:
            line = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        try:
            reply, keep = handle(conn, line)
        except requests.RequestException as exc:
            reply, keep = f"Không gọi được Ollama ({type(exc).__name__}). Kiểm tra Ollama đã chạy chưa.", True
        print(f"\nTrợ lý: {reply}")
        if not keep:
            break


if __name__ == "__main__":
    sys.exit(main())
