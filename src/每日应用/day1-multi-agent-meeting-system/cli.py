import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# 导入项目模块
from audio_processor import AudioProcessor
from action_extractor import ActionItemExtractor
from database import MeetingDatabase

class MeetingCLI:
    """命令行界面控制器"""
    
    def __init__(self):
        self.db = MeetingDatabase()
        self.audio_processor = None
        self.action_extractor = ActionItemExtractor()
    
    def upload_audio(self, audio_path, title=None):
        """
        上传音频文件并处理
        
        Args:
            audio_path: 音频文件路径
            title: 会议标题（可选，默认为文件名）
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                print(f"错误: 文件不存在: {audio_path}")
                return False
            
            # 如果没有提供标题，使用文件名
            if title is None:
                title = Path(audio_path).stem
            
            print(f"正在处理音频文件: {audio_path}")
            print(f"会议标题: {title}")
            
            # 初始化音频处理器（第一次使用时加载模型）
            if self.audio_processor is None:
                self.audio_processor = AudioProcessor(model_size="tiny")
            
            # 转录音频
            transcript_result = self.audio_processor.transcribe_audio(audio_path)
            transcript_text = transcript_result["text"]
            
            # 估算时长（简单估算：每秒约15个字符）
            text_length = len(transcript_text)
            estimated_duration = text_length // 15 if text_length > 0 else 0
            
            # 保存会议记录到数据库
            meeting_id = self.db.add_meeting(
                title=title,
                audio_path=audio_path,
                transcript_text=transcript_text,
                duration_seconds=estimated_duration
            )
            
            print(f"会议记录已保存，ID: {meeting_id}")
            print(f"转写文本长度: {len(transcript_text)} 字符")
            
            # 提取行动项
            action_items = self.action_extractor.extract_action_items(transcript_text)
            
            if action_items:
                print(f"提取到 {len(action_items)} 个行动项:")
                for i, item in enumerate(action_items, 1):
                    action_id = self.db.add_action_item(
                        meeting_id=meeting_id,
                        description=item["description"],
                        owner=item.get("owner"),
                        deadline=item.get("deadline"),
                        priority=item.get("priority", "medium")
                    )
                    print(f"  {i}. {item['description'][:50]}... (ID: {action_id})")
            else:
                print("未发现明确的行动项")
            
            # 显示摘要
            print("\n" + "="*60)
            print(f"处理完成! 会议ID: {meeting_id}")
            print(f"标题: {title}")
            print(f"音频: {audio_path}")
            print(f"转写文本已保存，行动项: {len(action_items)} 个")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"处理失败: {e}")
            return False
    
    def list_meetings(self, limit=10):
        """显示会议列表"""
        meetings = self.db.get_meetings(limit=limit)
        
        if not meetings:
            print("暂无会议记录")
            return
        
        print(f"\n会议列表 (最近{len(meetings)}个):")
        print("-" * 80)
        print(f"{'ID':<5} {'标题':<30} {'日期':<12} {'时长':<8} {'行动项'}")
        print("-" * 80)
        
        for meeting in meetings:
            # 获取该会议的行动项数量
            action_items = self.db.get_action_items(meeting_id=meeting["id"])
            action_count = len(action_items)
            
            # 格式化时长
            duration = meeting["duration_seconds"]
            if duration:
                duration_str = f"{duration//60:02d}:{duration%60:02d}"
            else:
                duration_str = "未知"
            
            print(f"{meeting['id']:<5} {meeting['title'][:28]:<30} "
                  f"{meeting['meeting_date']:<12} {duration_str:<8} {action_count}")
    
    def list_actions(self, meeting_id=None, status=None):
        """显示行动项列表"""
        action_items = self.db.get_action_items(meeting_id=meeting_id, status=status)
        
        if not action_items:
            if meeting_id:
                print(f"会议ID {meeting_id} 暂无行动项")
            else:
                print("暂无行动项记录")
            return
        
        print(f"\n行动项列表 (共{len(action_items)}个):")
        print("-" * 100)
        print(f"{'ID':<5} {'会议ID':<8} {'描述':<40} {'负责人':<10} {'截止时间':<12} {'状态':<12}")
        print("-" * 100)
        
        for item in action_items:
            desc = item["description"]
            if len(desc) > 38:
                desc = desc[:35] + "..."
            
            print(f"{item['id']:<5} {item['meeting_id']:<8} {desc:<40} "
                  f"{item['owner'] or '未指定':<10} {item['deadline'] or '未指定':<12} "
                  f"{item['status']:<12}")
    
    def show_summary(self, meeting_id):
        """显示会议摘要"""
        meeting = self.db.get_meeting_with_actions(meeting_id)
        
        if not meeting:
            print(f"错误: 会议ID {meeting_id} 不存在")
            return
        
        print("\n" + "="*60)
        print(f"会议摘要 - ID: {meeting_id}")
        print("="*60)
        print(f"标题: {meeting['title']}")
        print(f"日期: {meeting['meeting_date']}")
        print(f"音频文件: {meeting['audio_path'] or '未上传'}")
        print(f"创建时间: {meeting['created_at']}")
        
        if meeting['transcript_text']:
            print(f"\n转写文本预览 ({len(meeting['transcript_text'])} 字符):")
            print("-" * 40)
            preview = meeting['transcript_text'][:300]
            print(preview + ("..." if len(meeting['transcript_text']) > 300 else ""))
            print("-" * 40)
        
        action_items = meeting.get('action_items', [])
        print(f"\n行动项 ({len(action_items)} 个):")
        
        if action_items:
            for i, item in enumerate(action_items, 1):
                print(f"\n{i}. {item['description']}")
                print(f"   负责人: {item['owner'] or '未指定'}")
                print(f"   截止时间: {item['deadline'] or '未指定'}")
                print(f"   状态: {item['status']} | 优先级: {item['priority']}")
        else:
            print("  暂无行动项")
        
        print("\n" + "="*60)
    
    def run_command(self, args):
        """执行命令行参数"""
        if args.command == 'upload':
            self.upload_audio(args.audio_path, args.title)
        
        elif args.command == 'list':
            self.list_meetings(args.limit)
        
        elif args.command == 'actions':
            self.list_actions(args.meeting_id, args.status)
        
        elif args.command == 'summary':
            if not args.meeting_id:
                print("错误: 需要提供会议ID (--meeting-id)")
                return
            self.show_summary(args.meeting_id)
        
        elif args.command == 'test':
            self._run_test()


def main():
    """主函数：解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="多智能体会议纪要与行动项追踪系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s upload meeting.mp3 --title "项目启动会"
  %(prog)s list
  %(prog)s actions --meeting-id 1
  %(prog)s summary --meeting-id 1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传音频文件')
    upload_parser.add_argument('audio_path', help='音频文件路径 (mp3/wav)')
    upload_parser.add_argument('--title', help='会议标题 (可选)')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='显示会议列表')
    list_parser.add_argument('--limit', type=int, default=10, help='显示数量限制')
    
    # actions 命令
    actions_parser = subparsers.add_parser('actions', help='显示行动项列表')
    actions_parser.add_argument('--meeting-id', type=int, help='筛选特定会议的动项')
    actions_parser.add_argument('--status', help='筛选状态 (pending/in_progress/completed)')
    
    # summary 命令
    summary_parser = subparsers.add_parser('summary', help='显示会议摘要')
    summary_parser.add_argument('--meeting-id', type=int, required=True, help='会议ID')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='运行测试')
    
    # 如果没有提供参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # 运行CLI
    cli = MeetingCLI()
    cli.run_command(args)


if __name__ == "__main__":
    main()