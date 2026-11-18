import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat import (active_memories, build_messages, build_plan_messages, build_quiz_messages,
                  ensure_schema, handle, save_memory)


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.conn = ensure_schema(sqlite3.connect(":memory:"))

    def tearDown(self):
        self.conn.close()

    def test_saves_a_valid_memory(self):
        self.assertTrue(save_memory(self.conn, "The user prefers short summaries."))
        self.assertEqual(len(active_memories(self.conn)), 1)

    def test_refuses_sensitive_memory(self):
        self.assertFalse(save_memory(self.conn, "The user has a diagnosis of asthma."))
        self.assertEqual(len(active_memories(self.conn)), 0)

    def test_list_command_shows_saved_memory(self):
        save_memory(self.conn, "The user studies linear algebra this semester.")
        reply, keep = handle(self.conn, "/ky-uc")
        self.assertIn("linear algebra", reply)
        self.assertTrue(keep)

    def test_quit_command_stops_loop(self):
        _, keep = handle(self.conn, "/thoat")
        self.assertFalse(keep)

    def test_prompt_includes_relevant_memory_only_when_given(self):
        plain = build_messages("What is a matrix?", [])
        self.assertNotIn("Ký ức liên quan", plain[0]["content"])
        with_memory = build_messages("What is a matrix?", [{"noi_dung": "The user studies linear algebra."}])
        self.assertIn("The user studies linear algebra.", with_memory[0]["content"])
        self.assertEqual(with_memory[1]["content"], "What is a matrix?")


    def test_subject_is_saved_as_fact(self):
        reply, _ = handle(self.conn, "/mon Giải tích 1")
        self.assertIn("Đã lưu", reply)
        self.assertIn("Đang học môn: Giải tích 1", active_memories(self.conn)[0]["noi_dung"])

    def test_goal_is_saved(self):
        reply, _ = handle(self.conn, "/muc-tieu IELTS Writing band 7.0")
        self.assertIn("Đã lưu", reply)
        self.assertIn("IELTS Writing band 7.0", active_memories(self.conn)[0]["noi_dung"])

    def test_plan_prompt_lists_saved_subjects_and_goals(self):
        save_memory(self.conn, "Đang học môn: Đại số tuyến tính", loai="fact")
        messages = build_plan_messages(active_memories(self.conn))
        self.assertIn("Đại số tuyến tính", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")

    def test_plan_prompt_handles_empty_memory(self):
        messages = build_plan_messages([])
        self.assertIn("chưa có môn học", messages[0]["content"])

    def test_quiz_prompt_contains_topic(self):
        messages = build_quiz_messages("đạo hàm")
        self.assertIn("đạo hàm", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()