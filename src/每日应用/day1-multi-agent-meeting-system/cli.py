import argparse
import sys
import tempfile
from pathlib import Path

from action_extractor import ActionItemExtractor
from app_paths import DEFAULT_MODEL_SIZE, EXAMPLE_AUDIO_PATH
from audio_processor import AudioProcessor
from database import MeetingDatabase


class MeetingCLI:
    """命令行界面控制器"""

    def __init__(self, db_path=None, model_size=DEFAULT_MODEL_SIZE, audio_processor_factory=AudioProcessor):
        self.db = MeetingDatabase(db_path)
        self.model_size = model_size
        self.audio_processor_factory = audio_processor_factory
        self.audio_processor = None
        self.action_extractor = ActionItemExtractor()

    def _get_audio_processor(self):
        if self.audio_processor is None:
            self.audio_processor = self.audio_processor_factory(model_size=self.model_size)

        return self.audio_processor

    @staticmethod
    def _format_duration(duration_seconds):
        if duration_seconds is None:
            return "未知"

        minutes, seconds = divmod(max(duration_seconds, 0), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def upload_audio(self, audio_path, title=None):
        """上传音频文件并处理。"""
        try:
            audio_file = Path(audio_path).expanduser().resolve()
            if not audio_file.exists():
                print(f"错误: 文件不存在: {audio_file}")
                return False

            if title is None:
                title = audio_file.stem

            print(f"正在处理音频文件: {audio_file}")
            print(f"会议标题: {title}")

            processor = self._get_audio_processor()
            transcript_result = processor.transcribe_audio(str(audio_file))
            transcript_text = transcript_result["text"].strip()

            duration_seconds = None
            try:
                duration_seconds = processor.get_audio_duration_seconds(str(audio_file))
            except Exception:
                segments = transcript_result.get("segments", [])
                if segments:
                    duration_seconds = int(round(segments[-1].get("end", 0)))
                else:
                    duration_seconds = 0

            meeting_id = self.db.add_meeting(
                title=title,
                audio_path=str(audio_file),
                transcript_text=transcript_text,
                duration_seconds=duration_seconds,
            )

            print(f"会议记录已保存，ID: {meeting_id}")
            print(f"转写文本长度: {len(transcript_text)} 字符")

            action_items = self.action_extractor.extract_action_items(transcript_text)

            if action_items:
                print(f"提取到 {len(action_items)} 个行动项:")
                for index, item in enumerate(action_items, 1):
                    action_id = self.db.add_action_item(
                        meeting_id=meeting_id,
                        description=item["description"],
                        owner=item.get("owner"),
                        deadline=item.get("deadline"),
                        priority=item.get("priority", "medium"),
                    )
                    snippet = item["description"][:50]
                    suffix = "..." if len(item["description"]) > 50 else ""
                    print(f"  {index}. {snippet}{suffix} (ID: {action_id})")
            else:
                print("未发现明确的行动项")

            print("\n" + "=" * 60)
            print(f"处理完成! 会议ID: {meeting_id}")
            print(f"标题: {title}")
            print(f"音频: {audio_file}")
            print(f"转写文本已保存，行动项: {len(action_items)} 个")
            print("=" * 60)
            return True

        except Exception as exc:
            print(f"处理失败: {exc}")
            return False

    def list_meetings(self, limit=10):
        """显示会议列表。"""
        meetings = self.db.get_meetings(limit=limit)

        if not meetings:
            print("暂无会议记录")
            return True

        print(f"\n会议列表 (最近{len(meetings)}个):")
        print("-" * 80)
        print(f"{'ID':<5} {'标题':<30} {'日期':<12} {'时长':<8} {'行动项'}")
        print("-" * 80)

        for meeting in meetings:
            action_count = len(self.db.get_action_items(meeting_id=meeting["id"]))
            duration_str = self._format_duration(meeting["duration_seconds"])
            print(
                f"{meeting['id']:<5} {meeting['title'][:28]:<30} "
                f"{meeting['meeting_date']:<12} {duration_str:<8} {action_count}"
            )

        return True

    def list_actions(self, meeting_id=None, status=None):
        """显示行动项列表。"""
        action_items = self.db.get_action_items(meeting_id=meeting_id, status=status)

        if not action_items:
            if meeting_id:
                print(f"会议ID {meeting_id} 暂无行动项")
            else:
                print("暂无行动项记录")
            return True

        print(f"\n行动项列表 (共{len(action_items)}个):")
        print("-" * 100)
        print(f"{'ID':<5} {'会议ID':<8} {'描述':<40} {'负责人':<10} {'截止时间':<12} {'状态':<12}")
        print("-" * 100)

        for item in action_items:
            desc = item["description"]
            if len(desc) > 38:
                desc = desc[:35] + "..."

            print(
                f"{item['id']:<5} {item['meeting_id']:<8} {desc:<40} "
                f"{item['owner'] or '未指定':<10} {item['deadline'] or '未指定':<12} "
                f"{item['status']:<12}"
            )

        return True

    def show_summary(self, meeting_id):
        """显示会议摘要。"""
        meeting = self.db.get_meeting_with_actions(meeting_id)

        if not meeting:
            print(f"错误: 会议ID {meeting_id} 不存在")
            return False

        print("\n" + "=" * 60)
        print(f"会议摘要 - ID: {meeting_id}")
        print("=" * 60)
        print(f"标题: {meeting['title']}")
        print(f"日期: {meeting['meeting_date']}")
        print(f"音频文件: {meeting['audio_path'] or '未上传'}")
        print(f"创建时间: {meeting['created_at']}")

        if meeting["transcript_text"]:
            print(f"\n转写文本预览 ({len(meeting['transcript_text'])} 字符):")
            print("-" * 40)
            preview = meeting["transcript_text"][:300]
            print(preview + ("..." if len(meeting["transcript_text"]) > 300 else ""))
            print("-" * 40)

        action_items = meeting.get("action_items", [])
        print(f"\n行动项 ({len(action_items)} 个):")

        if action_items:
            for index, item in enumerate(action_items, 1):
                print(f"\n{index}. {item['description']}")
                print(f"   负责人: {item['owner'] or '未指定'}")
                print(f"   截止时间: {item['deadline'] or '未指定'}")
                print(f"   状态: {item['status']} | 优先级: {item['priority']}")
        else:
            print("  暂无行动项")

        print("\n" + "=" * 60)
        return True

    def _run_test(self, include_audio=False):
        """运行轻量级自检，不依赖已有数据库内容。"""
        print("开始运行内置自检...")

        sample_text = """
        今天的会议我们讨论项目进展。
        小张需要在本周五前完成需求文档。
        小李负责整理用户反馈，下周一提交。
        王五要处理技术难题，月底前解决。
        """
        action_items = self.action_extractor.extract_action_items(sample_text)
        print(f"行动项提取测试通过，提取到 {len(action_items)} 个行动项。")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db_path = Path(temp_dir) / "smoke_test.db"
            temp_db = MeetingDatabase(temp_db_path)
            meeting_id = temp_db.add_meeting(
                title="Smoke Test",
                transcript_text="测试会议",
                duration_seconds=60,
            )
            temp_db.add_action_item(
                meeting_id=meeting_id,
                description="完成 smoke test",
                owner="测试用户",
                deadline="本周内",
            )
            stored_meeting = temp_db.get_meeting_with_actions(meeting_id)
            print(f"数据库测试通过，临时会议 ID: {meeting_id}。")
            print(f"数据库路径: {temp_db.db_path}")

        if include_audio:
            if not EXAMPLE_AUDIO_PATH.exists():
                print(f"错误: 未找到示例音频 {EXAMPLE_AUDIO_PATH}")
                return False

            print("开始运行示例音频上传测试...")
            return self.upload_audio(str(EXAMPLE_AUDIO_PATH), title="CLI 自检示例会议")

        print("内置自检完成。")
        return bool(action_items) and stored_meeting is not None

    def run_command(self, args):
        """执行命令行参数。"""
        if args.command == "upload":
            return self.upload_audio(args.audio_path, args.title)

        if args.command == "list":
            return self.list_meetings(args.limit)

        if args.command == "actions":
            return self.list_actions(args.meeting_id, args.status)

        if args.command == "summary":
            if not args.meeting_id:
                print("错误: 需要提供会议ID (--meeting-id)")
                return False
            return self.show_summary(args.meeting_id)

        if args.command == "test":
            return self._run_test(args.include_audio)

        print("错误: 未知命令")
        return False


def main(argv=None):
    """主函数：解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="多智能体会议纪要与行动项追踪系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s upload meeting.mp3 --title "项目启动会"
  %(prog)s list
  %(prog)s actions --meeting-id 1
  %(prog)s summary --meeting-id 1
        """,
    )

    parser.add_argument(
        "--db-path",
        help="自定义数据库路径。默认使用项目目录下的 data/meetings.db，也支持环境变量 MEETING_DB_PATH。",
    )
    parser.add_argument(
        "--model-size",
        default=DEFAULT_MODEL_SIZE,
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小，默认 tiny，也支持环境变量 MEETING_MODEL_SIZE。",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    upload_parser = subparsers.add_parser("upload", help="上传音频文件")
    upload_parser.add_argument("audio_path", help="音频文件路径 (mp3/wav)")
    upload_parser.add_argument("--title", help="会议标题 (可选)")

    list_parser = subparsers.add_parser("list", help="显示会议列表")
    list_parser.add_argument("--limit", type=int, default=10, help="显示数量限制")

    actions_parser = subparsers.add_parser("actions", help="显示行动项列表")
    actions_parser.add_argument("--meeting-id", type=int, help="筛选特定会议的行动项")
    actions_parser.add_argument("--status", help="筛选状态 (pending/in_progress/completed)")

    summary_parser = subparsers.add_parser("summary", help="显示会议摘要")
    summary_parser.add_argument("--meeting-id", type=int, required=True, help="会议ID")

    test_parser = subparsers.add_parser("test", help="运行内置自检")
    test_parser.add_argument("--include-audio", action="store_true", help="连同示例音频上传链路一起测试")

    if argv is None and len(sys.argv) == 1:
        parser.print_help()
        return 1

    args = parser.parse_args(argv)
    cli = MeetingCLI(db_path=args.db_path, model_size=args.model_size)
    success = cli.run_command(args)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
