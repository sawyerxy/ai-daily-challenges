from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1] / "src" / "每日应用" / "day1-multi-agent-meeting-system"
sys.path.insert(0, str(PROJECT_DIR))

from action_extractor import ActionItemExtractor
from cli import MeetingCLI, main as cli_main
from database import MeetingDatabase


class FakeAudioProcessor:
    def __init__(self, model_size="tiny", language=None):
        self.model_size = model_size
        self.language = language

    def transcribe_audio(self, audio_path):
        return {
            "text": "小张需要在本周五前完成需求文档。小李负责整理用户反馈，下周一提交。",
            "segments": [{"end": 12.4}],
            "language": "zh",
        }

    def get_audio_duration_seconds(self, audio_path):
        return 12


class Day1MeetingSystemTests(unittest.TestCase):
    def test_action_item_extractor_finds_expected_owners(self):
        extractor = ActionItemExtractor()
        text = """
        小张需要在本周五前完成需求文档。
        小李负责整理用户反馈，下周一提交。
        王五要处理技术难题，月底前解决。
        """

        action_items = extractor.extract_action_items(text)

        self.assertEqual(len(action_items), 3)
        self.assertEqual(action_items[0]["owner"], "小张")
        self.assertEqual(action_items[1]["owner"], "小李")
        self.assertEqual(action_items[2]["owner"], "王五")

    def test_database_round_trip_with_custom_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "meetings.db"
            db = MeetingDatabase(db_path)
            meeting_id = db.add_meeting(
                title="项目启动会",
                transcript_text="今天我们讨论项目目标。",
                duration_seconds=120,
            )
            db.add_action_item(
                meeting_id=meeting_id,
                description="整理用户反馈",
                owner="小李",
                deadline="下周一",
            )

            meeting = db.get_meeting_with_actions(meeting_id)

            self.assertIsNotNone(meeting)
            self.assertEqual(meeting["title"], "项目启动会")
            self.assertEqual(len(meeting["action_items"]), 1)

    def test_cli_upload_works_with_injected_audio_processor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "meetings.db"
            audio_path = Path(temp_dir) / "demo.wav"
            audio_path.write_bytes(b"fake audio data")

            cli = MeetingCLI(
                db_path=db_path,
                audio_processor_factory=FakeAudioProcessor,
            )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                success = cli.upload_audio(str(audio_path), title="测试会议")
            meeting = cli.db.get_meeting_with_actions(1)

            self.assertTrue(success)
            self.assertIsNotNone(meeting)
            self.assertEqual(meeting["duration_seconds"], 12)
            self.assertEqual(len(meeting["action_items"]), 2)

    def test_cli_main_list_uses_custom_database_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "meetings.db"
            db = MeetingDatabase(db_path)
            db.add_meeting(title="周会", transcript_text="测试", duration_seconds=30)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(["--db-path", str(db_path), "list"])

            self.assertEqual(exit_code, 0)
            self.assertIn("周会", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
