# AI Daily Challenges

这是一个面向「每日 AI 原型实战」的仓库，目标是持续交付可以直接运行的工具原型。当前仓库已经整理为默认分支 `main` 可用，首次 clone 后可以直接按下面的步骤启动 Day 1 示例项目。

## 当前可运行项目

- Day 1: 多智能体会议纪要与行动项追踪系统
- 代码目录: `src/每日应用/day1-multi-agent-meeting-system`
- 根目录快捷入口: `run_day1.py`

## 快速开始

### 1. 准备 Python 环境

推荐使用 Python `3.10`、`3.11` 或 `3.12`。

Windows:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. 安装 FFmpeg

Whisper 处理音频需要 FFmpeg。安装完成后，执行下面命令应当能看到版本号：

```bash
ffmpeg -version
```

### 3. 运行 Day 1 项目

查看命令帮助：

```bash
python run_day1.py --help
```

处理示例音频：

```bash
python run_day1.py upload src/每日应用/day1-multi-agent-meeting-system/example_meeting.mp3 --title "示例会议"
```

查看结果：

```bash
python run_day1.py list
python run_day1.py actions
python run_day1.py summary --meeting-id 1
```

### 4. 运行内置自检

```bash
python run_day1.py test
```

如果你想连同示例音频上传链路一起验证：

```bash
python run_day1.py test --include-audio
```

## 已知约束

- `openai-whisper` 目前在 Python `3.13+` 上兼容性较差，建议使用 Python `3.10-3.12`
- 第一次执行 `upload` 时会下载 Whisper 模型，耗时取决于网络环境
- 当前行动项提取仍然是规则法，更适合原型验证和内部工具，不适合直接替代成熟会议产品

## 仓库结构

```text
.
├── README.md
├── requirements.txt
├── run_day1.py
├── docs/
├── outputs/
└── src/
    └── 每日应用/
        └── day1-multi-agent-meeting-system/
```

## 后续方向

- 将更多每日原型统一整理到默认分支
- 补充自动化测试和 CI
- 提升行动项提取精度
- 增加 Web 界面和更完整的配置项
