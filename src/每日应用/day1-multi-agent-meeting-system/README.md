# 多智能体会议纪要与行动项追踪系统

一个基于 AI 的会议纪要自动生成与行动项追踪系统，通过语音转写和规则提取自动沉淀会议记录、行动项和摘要，适合做内部工具原型和会议效率验证。

详细使用说明请查看：

`docs/每日应用/day1-multi-agent-meeting-system/详细使用文档.md`

移动端 demo 设计和 Flutter 源码请查看：

- `docs/每日应用/day1-multi-agent-meeting-system/flutter_app_design.md`
- `apps/meeting_assistant_mobile/`

## 运行前提

- Python `3.10`、`3.11` 或 `3.12`
- 已安装 `ffmpeg`
- 首次运行 `upload` 时允许联网下载 Whisper 模型

## 功能特性

- **语音转写**：支持mp3/wav格式音频文件，使用OpenAI Whisper模型进行高精度语音识别
- **行动项提取**：支持规则法、本地 Ollama 和 OpenRouter 在线 LLM，识别负责人、截止时间等关键信息
- **数据存储**：使用SQLite数据库保存会议记录和行动项，支持CRUD操作
- **命令行界面**：简单易用的CLI工具，支持上传音频、查看会议列表、查看行动项等功能

## 系统架构

```
src/每日应用/day1-multi-agent-meeting-system/
├── audio_processor.py    # 语音处理模块 (Whisper)
├── action_extractor.py   # 行动项提取模块 (规则匹配)
├── database.py           # 数据存储模块 (SQLite)
├── cli.py                # 命令行界面
├── main.py               # 主程序入口
├── requirements.txt      # Python依赖包
└── README.md             # 说明文档
```

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

**依赖包说明**:
- `openai-whisper`: OpenAI 开源的语音识别模型
- `pydub`: 音频文件处理库，用于读取音频时长

### 2. 安装系统依赖 (可选)

Whisper模型需要FFmpeg来处理音频文件。如果系统没有安装FFmpeg，请先安装：

**Ubuntu/Debian**:
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS (使用Homebrew)**:
```bash
brew install ffmpeg
```

**Windows**:
下载FFmpeg并添加到系统PATH: https://ffmpeg.org/download.html

### 3. 推荐使用虚拟环境

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

## 使用方法

### 基本命令

```bash
# 上传音频文件并处理
python cli.py upload meeting.mp3 --title "项目启动会"

# 显示会议列表
python cli.py list

# 显示特定会议的行动项
python cli.py actions --meeting-id 1

# 显示会议摘要
python cli.py summary --meeting-id 1

# 运行内置自检
python cli.py test
```

### 可选参数

```bash
# 指定数据库路径
python cli.py --db-path ./data/demo.db list

# 指定 Whisper 模型大小
python cli.py --model-size base upload meeting.mp3 --title "项目启动会"

# 使用本地 Ollama 提取行动项
python cli.py --action-extractor ollama --action-model your-local-model upload meeting.mp3 --title "项目启动会"

# 使用 OpenRouter 在线模型提取行动项
python cli.py --action-extractor openrouter --action-model your-openrouter-model upload meeting.mp3 --title "项目启动会"
```

### 详细示例

#### 1. 处理会议音频

```bash
# 上传会议录音
python cli.py upload /path/to/meeting_audio.mp3 --title "2024年第一季度规划会议"

# 输出示例:
# 正在处理音频文件: /path/to/meeting_audio.mp3
# 会议标题: 2024年第一季度规划会议
# 正在加载Whisper tiny模型...
# 模型加载完成
# 正在转录音频: /path/to/meeting_audio.mp3
# 会议记录已保存，ID: 1
# 转写文本长度: 1560 字符
# 提取到 3 个行动项:
#   1. 小张需要在本周五前完成需求文档... (ID: 1)
#   2. 小李负责整理用户反馈，下周一提交... (ID: 2)
#   3. 王五要处理技术难题，月底前解决... (ID: 3)
```

#### 2. 查看会议记录

```bash
# 查看最近10个会议
python cli.py list

# 输出示例:
# 会议列表 (最近3个):
# --------------------------------------------------------------------------------
# ID   标题                           日期         时长      行动项
# --------------------------------------------------------------------------------
# 1    2024年第一季度规划会议          2024-04-03  15:30     3
# 2    项目启动会                      2024-04-02  20:15     2
# 3    团队周会                        2024-04-01  45:00     5
```

#### 3. 查看行动项

```bash
# 查看所有行动项
python cli.py actions

# 查看特定会议的行动项
python cli.py actions --meeting-id 1

# 查看待处理的行动项
python cli.py actions --status pending
```

#### 4. 查看会议详情

```bash
python cli.py summary --meeting-id 1
```

## 模块说明

### 1. AudioProcessor (音频处理)

位于 `audio_processor.py`，负责音频文件的转写功能：
- 支持多种音频格式 (mp3, wav, m4a等)
- 使用Whisper模型进行语音识别
- 可配置模型大小 (tiny/base/small/medium/large)
- 返回转写文本和分段信息

### 2. ActionItemExtractor (行动项提取)

位于 `action_extractor.py`，基于规则匹配提取行动项：
- 识别行动项触发词（需要、要、完成、负责等）
- 提取负责人信息
- 提取截止时间
- 生成行动项摘要

### 3. MeetingDatabase (数据存储)

位于 `database.py`，提供数据持久化功能：
- 使用SQLite数据库
- 会议表 (meetings) 和行动项表 (action_items)
- 支持添加、查询、更新、删除操作
- 自动关联会议与行动项

### 4. MeetingCLI (命令行界面)

位于 `cli.py`，提供用户交互界面：
- 支持多个子命令 (upload, list, actions, summary)
- 友好的错误提示和进度显示
- 简洁的输出格式

## 测试

### 运行单元测试

```bash
# 测试音频处理模块
python audio_processor.py

# 测试行动项提取模块
python action_extractor.py

# 测试数据库模块
python database.py
```

### 使用示例音频

项目包含一个示例音频文件 `example_meeting.mp3`，可用于快速测试系统功能：

```bash
python cli.py upload example_meeting.mp3 --title "示例会议"
```

## 配置选项

### Whisper模型大小

可以通过命令行参数指定模型大小：

```python
python cli.py --model-size tiny upload example_meeting.mp3 --title "示例会议"
```

- **tiny**: 最快，精度较低 (~1GB RAM)
- **base**: 平衡速度与精度 (~1GB RAM)
- **small**: 较好精度 (~2GB RAM)
- **medium**: 高精度 (~5GB RAM)
- **large**: 最高精度 (~10GB RAM)

### 数据库路径

默认数据库文件为项目目录下的 `data/meetings.db`，也可以通过参数或环境变量覆盖：

```python
python cli.py --db-path ./my_meetings.db list
```

### 行动项提取器

默认使用规则法：

```bash
python cli.py upload example_meeting.mp3 --title "示例会议"
```

使用本地 Ollama：

```bash
python cli.py --action-extractor ollama --action-model your-local-model upload example_meeting.mp3 --title "示例会议"
```

使用 OpenRouter：

```bash
python cli.py --action-extractor openrouter --action-model your-openrouter-model upload example_meeting.mp3 --title "示例会议"
```

常用环境变量：

```bash
MEETING_ACTION_EXTRACTOR=ollama
MEETING_ACTION_MODEL=your-local-model
OLLAMA_BASE_URL=http://localhost:11434/v1

OPENROUTER_API_KEY=your-key
MEETING_ACTION_EXTRACTOR=openrouter
MEETING_ACTION_MODEL=your-openrouter-model
```

## 故障排除

### 常见问题

1. **音频转写失败**
   - 检查FFmpeg是否安装: `ffmpeg -version`
   - 确保音频文件格式受支持
   - 尝试使用较小的Whisper模型 (tiny/base)

2. **依赖安装失败**
   - 确保使用 Python 3.10-3.12
   - 尝试升级pip: `pip install --upgrade pip`
   - 使用虚拟环境避免冲突

3. **行动项提取不准确**
   - 系统使用基于规则的方法，对于复杂表述可能需要调整规则
   - 可修改 `action_extractor.py` 中的触发词和匹配规则

### 获取帮助

```bash
# 查看所有命令
python cli.py --help

# 查看特定命令帮助
python cli.py upload --help
```

## 稳定性说明

- `list`、`actions`、`summary` 不再依赖 Whisper，可在未执行语音转写时单独使用
- 数据库默认写入 `data/` 目录，不会再随着当前工作目录漂移
- `test` 命令可用于快速验证提取器、数据库和可选的音频链路
- LLM 行动项提取失败时，默认会自动回退到规则模式；可通过 `--no-action-fallback` 关闭

## 后续开发计划

- [ ] 支持实时语音转写
- [ ] 集成更先进的NLP模型进行行动项提取
- [ ] 添加Web界面
- [ ] 支持多人协作和权限管理
- [ ] 集成日历系统自动创建提醒

## 许可证

本项目基于 MIT 许可证开源。

## 作者

sawyerxy huang - AI每日创意马拉松项目
