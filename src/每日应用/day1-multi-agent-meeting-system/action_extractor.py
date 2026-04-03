import re
from typing import List, Dict, Optional

class ActionItemExtractor:
    """行动项提取模块，基于规则匹配提取会议中的行动项"""
    
    def __init__(self):
        # 行动项触发词
        self.action_trigger_words = [
            "需要", "要", "必须", "得", "应该", "应当",
            "完成", "准备", "安排", "负责", "处理", "解决",
            "提交", "发送", "整理", "汇总", "制定", "编写"
        ]
        
        # 负责人关键词
        self.owner_keywords = [
            "由", "负责", "责任人", "指派", "交给", "归属",
            "小张", "小李", "小王", "小明", "张三", "李四"  # 示例人名
        ]
        
        # 截止时间关键词
        self.deadline_keywords = [
            "之前", "前", "截止", "期限", "deadline",
            "今天", "明天", "本周", "下周", "月底", "年底"
        ]
        
        # 时间模式正则表达式
        self.date_patterns = [
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{1,2}月\d{1,2}日",
            r"\d{1,2}日",
            r"\d{1,2}月\d{1,2}号",
            r"\d{1,2}号",
            r"\d{1,2}-\d{1,2}",
            r"\d{1,2}/\d{1,2}"
        ]
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """
        从文本中提取行动项
        
        Args:
            text: 会议转写文本
            
        Returns:
            List[Dict]: 行动项列表，每个行动项包含描述、负责人、截止时间
        """
        action_items = []
        
        # 按句号、问号、感叹号分割文本
        sentences = re.split(r'[。！？；\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue
            
            # 检查是否包含行动项触发词
            has_action = any(word in sentence for word in self.action_trigger_words)
            if not has_action:
                continue
            
            # 提取行动项信息
            action_item = self._parse_sentence(sentence)
            if action_item:
                action_items.append(action_item)
        
        return action_items
    
    def _parse_sentence(self, sentence: str) -> Optional[Dict]:
        """解析单个句子，提取行动项信息"""
        
        # 基础信息
        action_item = {
            "description": sentence,
            "owner": None,
            "deadline": None,
            "priority": "medium"
        }
        
        # 提取负责人
        owner = self._extract_owner(sentence)
        if owner:
            action_item["owner"] = owner
        
        # 提取截止时间
        deadline = self._extract_deadline(sentence)
        if deadline:
            action_item["deadline"] = deadline
        
        # 如果既没有负责人也没有截止时间，但确实是行动项，仍然保留
        if owner or deadline:
            return action_item
        elif any(word in sentence for word in self.action_trigger_words):
            # 有行动触发词但无具体信息，仍然作为行动项
            return action_item
        
        return None
    
    def _extract_owner(self, sentence: str) -> Optional[str]:
        """从句子中提取负责人"""
        # 简单模式：关键词后的人名或称谓
        for keyword in self.owner_keywords:
            if keyword in sentence:
                # 提取关键词后的2-4个字符
                idx = sentence.find(keyword)
                if idx >= 0:
                    # 获取关键词后的内容
                    after_keyword = sentence[idx + len(keyword):idx + len(keyword) + 6]
                    after_keyword = after_keyword.strip()
                    if after_keyword:
                        return after_keyword
        
        # 如果没找到，尝试匹配常见人名
        common_names = ["小张", "小李", "小王", "小明", "张三", "李四", "王五", "赵六"]
        for name in common_names:
            if name in sentence:
                return name
        
        return None
    
    def _extract_deadline(self, sentence: str) -> Optional[str]:
        """从句子中提取截止时间"""
        # 匹配日期模式
        for pattern in self.date_patterns:
            matches = re.findall(pattern, sentence)
            if matches:
                return matches[0]
        
        # 匹配关键词相关的时间
        for keyword in self.deadline_keywords:
            if keyword in sentence:
                # 提取关键词前后的内容
                idx = sentence.find(keyword)
                start = max(0, idx - 10)
                end = min(len(sentence), idx + len(keyword) + 10)
                context = sentence[start:end]
                return context
        
        return None
    
    def summarize_action_items(self, action_items: List[Dict]) -> str:
        """生成行动项摘要"""
        if not action_items:
            return "未发现明确的行动项"
        
        summary = f"发现 {len(action_items)} 个行动项:\n\n"
        for i, item in enumerate(action_items, 1):
            summary += f"{i}. {item['description']}\n"
            if item['owner']:
                summary += f"   负责人: {item['owner']}\n"
            if item['deadline']:
                summary += f"   截止时间: {item['deadline']}\n"
            summary += "\n"
        
        return summary


def test_extraction():
    """测试提取功能"""
    extractor = ActionItemExtractor()
    
    # 测试文本
    test_text = """
    今天的会议我们需要讨论项目进展。
    小张需要在本周五前完成需求文档。
    小李负责整理用户反馈，下周一提交。
    王五要处理技术难题，月底前解决。
    另外，大家记得明天提交周报。
    """
    
    action_items = extractor.extract_action_items(test_text)
    print(f"提取到 {len(action_items)} 个行动项:")
    
    for i, item in enumerate(action_items, 1):
        print(f"{i}. 描述: {item['description']}")
        print(f"   负责人: {item.get('owner', '未指定')}")
        print(f"   截止时间: {item.get('deadline', '未指定')}")
        print()
    
    # 生成摘要
    summary = extractor.summarize_action_items(action_items)
    print("摘要:")
    print(summary)


if __name__ == "__main__":
    test_extraction()