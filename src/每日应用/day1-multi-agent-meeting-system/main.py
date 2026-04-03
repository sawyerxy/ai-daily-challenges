#!/usr/bin/env python3
"""
多智能体会议纪要与行动项追踪系统 - 主程序入口
"""

import sys
import os

# 添加当前目录到Python路径，确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import main as cli_main

def run_demo():
    """运行演示模式"""
    print("=" * 60)
    print("多智能体会议纪要与行动项追踪系统 - 演示模式")
    print("=" * 60)
    
    # 检查是否有示例音频文件
    example_audio = "example_meeting.mp3"
    if not os.path.exists(example_audio):
        print(f"提示: 请将测试音频文件放在 {example_audio}")
        print("或使用您自己的音频文件运行: python cli.py upload <音频文件路径>")
        return
    
    print(f"发现示例音频文件: {example_audio}")
    print("开始处理...")
    
    # 模拟命令行参数
    sys.argv = ["cli.py", "upload", example_audio, "--title", "示例会议"]
    cli_main()

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 如果有命令行参数，传递给CLI
        cli_main()
    else:
        # 否则运行演示模式
        run_demo()

if __name__ == "__main__":
    main()