"""Testes do buffer de logs Web."""

import unittest

from traveling_salesman_problem.web.log_buffer import LogBuffer


class LogBufferTests(unittest.TestCase):
    def test_log_buffer_keeps_last_n_entries(self):
        buffer = LogBuffer(max_entries=3)
        for index in range(5):
            buffer.append("generation", f"msg {index}")
        entries = buffer.snapshot()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["message"], "msg 2")
        self.assertEqual(entries[-1]["message"], "msg 4")

    def test_log_buffer_clear(self):
        buffer = LogBuffer()
        buffer.append("event", "hello")
        buffer.clear()
        self.assertEqual(buffer.snapshot(), [])


if __name__ == "__main__":
    unittest.main()
