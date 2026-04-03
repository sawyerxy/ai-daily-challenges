import whisper
import tempfile
import os
from pathlib import Path

class AudioProcessor:
    """音频处理模块，使用OpenAI Whisper进行语音转写"""
    
    def __init__(self, model_size="tiny"):
        """
        初始化Whisper模型
        
        Args:
            model_size: Whisper模型大小，可选 "tiny", "base", "small", "medium", "large"
        """
        print(f"正在加载Whisper {model_size}模型...")
        self.model = whisper.load_model(model_size)
        print("模型加载完成")
    
    def transcribe_audio(self, audio_path):
        """
        转录音频文件为文本
        
        Args:
            audio_path: 音频文件路径（支持mp3, wav等格式）
            
        Returns:
            dict: 包含转写文本和分段信息的字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 转录音频
            print(f"正在转录音频: {audio_path}")
            result = self.model.transcribe(audio_path)
            
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