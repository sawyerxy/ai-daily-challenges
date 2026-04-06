from __future__ import annotations

from pathlib import Path

class AudioProcessor:
    """音频处理模块，使用OpenAI Whisper进行语音转写"""
    
    def __init__(self, model_size="tiny", language=None):
        """
        初始化Whisper模型
        
        Args:
            model_size: Whisper模型大小，可选 "tiny", "base", "small", "medium", "large"
        """
        self.model_size = model_size
        self.language = language
        self.model = None

    def _load_model(self):
        """按需加载Whisper，避免只读命令也依赖语音模型。"""
        if self.model is None:
            try:
                import whisper
            except ImportError as exc:
                raise RuntimeError(
                    "未安装 openai-whisper。请确认使用 Python 3.10-3.12，并重新执行 `pip install -r requirements.txt`。"
                ) from exc

            print(f"正在加载Whisper {self.model_size}模型...")
            self.model = whisper.load_model(self.model_size)
            print("模型加载完成")

        return self.model
    
    def transcribe_audio(self, audio_path):
        """
        转录音频文件为文本
        
        Args:
            audio_path: 音频文件路径（支持mp3, wav等格式）
            
        Returns:
            dict: 包含转写文本和分段信息的字典
        """
        try:
            audio_file = Path(audio_path).expanduser().resolve()

            if not audio_file.exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_file}")

            print(f"正在转录音频: {audio_file}")
            transcribe_kwargs = {}
            if self.language:
                transcribe_kwargs["language"] = self.language

            result = self._load_model().transcribe(str(audio_file), **transcribe_kwargs)
            
            # 返回结果
            return {
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "zh")
            }
            
        except Exception as e:
            print(f"音频转写失败: {e}")
            raise
    
    def transcribe_to_text(self, audio_path):
        """
        简化版转写，只返回文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            str: 转写文本
        """
        result = self.transcribe_audio(audio_path)
        return result["text"]

    def get_audio_duration_seconds(self, audio_path):
        """使用 pydub 获取音频时长。"""
        from pydub import AudioSegment

        audio_file = Path(audio_path).expanduser().resolve()
        audio = AudioSegment.from_file(audio_file)
        return int(round(len(audio) / 1000))


def test_transcription():
    """测试函数"""
    processor = AudioProcessor(model_size="tiny")
    
    # 如果没有测试音频，创建一个临时文件并提示
    test_audio = "test_audio.mp3"
    if not os.path.exists(test_audio):
        print(f"测试音频不存在，请将音频文件放在: {test_audio}")
        return
    
    try:
        result = processor.transcribe_audio(test_audio)
        print("转写成功！")
        print(f"文本长度: {len(result['text'])} 字符")
        print(f"前500字符: {result['text'][:500]}...")
        return result
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_transcription()
