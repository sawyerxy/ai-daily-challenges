from __future__ import annotations

import json
import re
from typing import Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app_paths import (
    DEFAULT_ACTION_API_KEY,
    DEFAULT_ACTION_EXTRACTOR,
    DEFAULT_ACTION_FALLBACK,
    DEFAULT_ACTION_LLM_MODEL,
    DEFAULT_ACTION_TIMEOUT,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENROUTER_BASE_URL,
    DEFAULT_OPENROUTER_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_SITE_URL,
)


class RuleBasedActionItemExtractor:
    """行动项提取模块，基于规则匹配提取会议中的行动项。"""

    def __init__(self):
        self.action_trigger_words = [
            "需要", "要", "必须", "得", "应该", "应当",
            "完成", "准备", "安排", "负责", "处理", "解决",
            "提交", "发送", "整理", "汇总", "制定", "编写",
        ]
        self.owner_keywords = [
            "由", "负责", "责任人", "指派", "交给", "归属",
            "小张", "小李", "小王", "小明", "张三", "李四",
        ]
        self.owner_patterns = [
            r"由(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})负责",
            r"(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})负责",
            r"(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})需要",
            r"(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})要",
            r"(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})应当",
            r"(?P<owner>[\u4e00-\u9fffA-Za-z]{2,8})应该",
        ]
        self.invalid_owner_values = {
            "我们", "大家", "项目", "项目组", "团队", "会议", "今天", "今天的",
        }
        self.deadline_keywords = [
            "之前", "前", "截止", "期限", "deadline",
            "今天", "明天", "本周", "下周", "月底", "年底",
        ]
        self.date_patterns = [
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{1,2}月\d{1,2}日",
            r"\d{1,2}日",
            r"\d{1,2}月\d{1,2}号",
            r"\d{1,2}号",
            r"\d{1,2}-\d{1,2}",
            r"\d{1,2}/\d{1,2}",
        ]

    def extract_action_items(self, text: str) -> List[Dict]:
        action_items = []
        sentences = re.split(r"[。！？；.!?;\n]", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue

            if not any(word in sentence for word in self.action_trigger_words):
                continue

            action_item = self._parse_sentence(sentence)
            if action_item:
                action_items.append(action_item)

        return action_items

    def _parse_sentence(self, sentence: str) -> Optional[Dict]:
        action_item = {
            "description": sentence,
            "owner": None,
            "deadline": None,
            "priority": "medium",
        }

        owner = self._extract_owner(sentence)
        if owner:
            action_item["owner"] = owner

        deadline = self._extract_deadline(sentence)
        if deadline:
            action_item["deadline"] = deadline

        if owner or deadline:
            return action_item
        if any(word in sentence for word in self.action_trigger_words):
            return action_item

        return None

    def _extract_owner(self, sentence: str) -> Optional[str]:
        for pattern in self.owner_patterns:
            match = re.search(pattern, sentence)
            if match:
                owner = match.group("owner").strip(" ，,：:()（）")
                if owner and owner not in self.invalid_owner_values:
                    return owner

        for keyword in self.owner_keywords:
            if keyword in sentence:
                idx = sentence.find(keyword)
                if idx >= 0:
                    after_keyword = sentence[idx + len(keyword):idx + len(keyword) + 6]
                    after_keyword = after_keyword.strip(" ，,：:()（）")
                    if after_keyword and after_keyword not in self.invalid_owner_values:
                        return after_keyword

        common_names = ["小张", "小李", "小王", "小明", "张三", "李四", "王五", "赵六"]
        for name in common_names:
            if name in sentence:
                return name

        return None

    def _extract_deadline(self, sentence: str) -> Optional[str]:
        for pattern in self.date_patterns:
            matches = re.findall(pattern, sentence)
            if matches:
                return matches[0]

        for keyword in self.deadline_keywords:
            if keyword in sentence:
                idx = sentence.find(keyword)
                start = max(0, idx - 10)
                end = min(len(sentence), idx + len(keyword) + 10)
                return sentence[start:end]

        return None

    def summarize_action_items(self, action_items: List[Dict]) -> str:
        if not action_items:
            return "未发现明确的行动项"

        summary = f"发现 {len(action_items)} 个行动项:\n\n"
        for index, item in enumerate(action_items, 1):
            summary += f"{index}. {item['description']}\n"
            if item["owner"]:
                summary += f"   负责人: {item['owner']}\n"
            if item["deadline"]:
                summary += f"   截止时间: {item['deadline']}\n"
            summary += "\n"

        return summary


class LLMActionItemExtractor:
    """基于 OpenAI 兼容 Chat Completions 接口的 LLM 行动项提取器。"""

    def __init__(
        self,
        provider: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_ACTION_TIMEOUT,
        completion_caller: Optional[Callable[[Dict, str, Dict[str, str], int], Dict]] = None,
    ):
        provider = provider.lower()
        if provider not in {"ollama", "openrouter"}:
            raise ValueError(f"不支持的 LLM 提取器类型: {provider}")

        self.provider = provider
        self.model = model or self._resolve_default_model(provider)
        self.base_url = base_url or self._resolve_default_base_url(provider)
        self.api_key = api_key or self._resolve_default_api_key(provider)
        self.timeout = timeout
        self.completion_caller = completion_caller or self._default_completion_caller

        if not self.model:
            raise ValueError(
                f"{provider} 模式需要指定模型名称。请使用 --action-model，或设置相应环境变量。"
            )

        if provider == "openrouter" and not self.api_key:
            raise ValueError("OpenRouter 模式需要 OPENROUTER_API_KEY，或通过 --action-api-key 传入。")

    def extract_action_items(self, text: str) -> List[Dict]:
        if not text.strip():
            return []

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(text)},
            ],
        }
        response = self.completion_caller(payload, self._request_url(), self._headers(), self.timeout)
        content = self._extract_response_content(response)
        data = self._extract_json_payload(content)
        return self._normalize_action_items(data.get("action_items", []))

    def _resolve_default_model(self, provider: str) -> Optional[str]:
        if provider == "ollama":
            return DEFAULT_OLLAMA_MODEL or DEFAULT_ACTION_LLM_MODEL
        return DEFAULT_OPENROUTER_MODEL or DEFAULT_ACTION_LLM_MODEL

    def _resolve_default_base_url(self, provider: str) -> str:
        if provider == "ollama":
            return DEFAULT_OLLAMA_BASE_URL
        return DEFAULT_OPENROUTER_BASE_URL

    def _resolve_default_api_key(self, provider: str) -> Optional[str]:
        if provider == "openrouter":
            return OPENROUTER_API_KEY or DEFAULT_ACTION_API_KEY
        return DEFAULT_ACTION_API_KEY

    def _request_url(self) -> str:
        request_url = self.base_url.rstrip("/")
        if request_url.endswith("/chat/completions"):
            return request_url
        return f"{request_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.provider == "openrouter":
            headers["Authorization"] = f"Bearer {self.api_key}"
            if OPENROUTER_SITE_URL:
                headers["HTTP-Referer"] = OPENROUTER_SITE_URL
            if OPENROUTER_APP_NAME:
                headers["X-Title"] = OPENROUTER_APP_NAME
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_system_prompt(self) -> str:
        return (
            "你是一个会议行动项抽取器。"
            "请从会议转写中抽取明确、可执行、应该被跟踪的任务。"
            "只返回严格 JSON，不要输出 markdown，不要解释。"
            '输出格式必须是 {"action_items":[{"description":"...","owner":"...或null","deadline":"...或null","priority":"high|medium|low"}]}。'
            "规则："
            "1. 只保留明确待办，不要保留背景介绍、泛泛提醒、纯讨论内容。"
            "2. description 请用简洁中文概括任务。"
            "3. owner 未明确时填 null。"
            "4. deadline 未明确时填 null。"
            "5. priority 只能是 high、medium、low，无法判断时填 medium。"
            '6. 如果没有行动项，返回 {"action_items":[]}。'
        )

    def _build_user_prompt(self, text: str) -> str:
        return f"请从下面会议转写中抽取行动项：\n\n<<<TRANSCRIPT>>>\n{text}\n<<<END>>>"

    def _default_completion_caller(self, payload: Dict, request_url: str, headers: Dict[str, str], timeout: int) -> Dict:
        request = Request(
            request_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM 请求失败: HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"LLM 请求失败: {exc.reason}") from exc

    def _extract_response_content(self, response: Dict) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise ValueError("LLM 响应中没有 choices。")

        message = choices[0].get("message") or {}
        content = message.get("content", "")

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = "".join(text_parts)

        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM 响应内容为空。")

        return content.strip()

    def _extract_json_payload(self, content: str) -> Dict:
        content = content.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
        if fenced_match:
            content = fenced_match.group(1)
        else:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end >= start:
                content = content[start:end + 1]

        return json.loads(content)

    def _normalize_action_items(self, action_items: List[Dict]) -> List[Dict]:
        normalized = []
        seen_descriptions = set()

        for item in action_items:
            if not isinstance(item, dict):
                continue

            description = str(
                item.get("description")
                or item.get("task")
                or item.get("action")
                or ""
            ).strip()
            if not description or description in seen_descriptions:
                continue

            owner = item.get("owner") or item.get("assignee")
            deadline = item.get("deadline") or item.get("due_date") or item.get("due")
            priority = str(item.get("priority") or "medium").strip().lower()
            if priority not in {"high", "medium", "low"}:
                priority = "medium"

            normalized.append(
                {
                    "description": description,
                    "owner": self._normalize_nullable_text(owner),
                    "deadline": self._normalize_nullable_text(deadline),
                    "priority": priority,
                }
            )
            seen_descriptions.add(description)

        return normalized

    @staticmethod
    def _normalize_nullable_text(value) -> Optional[str]:
        if value is None:
            return None

        text = str(value).strip()
        if not text or text.lower() in {"null", "none", "unknown", "未指定", "未知"}:
            return None
        return text


class ActionItemExtractor:
    """行动项提取统一入口，支持规则法、Ollama 和 OpenRouter。"""

    def __init__(
        self,
        extractor_type: str = DEFAULT_ACTION_EXTRACTOR,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_ACTION_TIMEOUT,
        fallback_to_rules: bool = DEFAULT_ACTION_FALLBACK,
        completion_caller: Optional[Callable[[Dict, str, Dict[str, str], int], Dict]] = None,
    ):
        extractor_type = (extractor_type or "rules").lower()
        self.extractor_type = extractor_type
        self.fallback_to_rules = fallback_to_rules
        self.rule_extractor = RuleBasedActionItemExtractor()
        self.llm_extractor = None

        if extractor_type != "rules":
            self.llm_extractor = LLMActionItemExtractor(
                provider=extractor_type,
                model=model,
                base_url=base_url,
                api_key=api_key,
                timeout=timeout,
                completion_caller=completion_caller,
            )

    def extract_action_items(self, text: str) -> List[Dict]:
        if self.extractor_type == "rules":
            return self.rule_extractor.extract_action_items(text)

        try:
            return self.llm_extractor.extract_action_items(text)
        except Exception as exc:
            if not self.fallback_to_rules:
                raise
            print(f"LLM 行动项提取失败，已回退到规则模式: {exc}")
            return self.rule_extractor.extract_action_items(text)

    def summarize_action_items(self, action_items: List[Dict]) -> str:
        return self.rule_extractor.summarize_action_items(action_items)


def test_extraction():
    extractor = ActionItemExtractor()
    test_text = """
    今天的会议我们讨论项目进展。
    小张需要在本周五前完成需求文档。
    小李负责整理用户反馈，下周一提交。
    王五要处理技术难题，月底前解决。
    另外，大家记得明天提交周报。
    """

    action_items = extractor.extract_action_items(test_text)
    print(f"提取到 {len(action_items)} 个行动项:")

    for index, item in enumerate(action_items, 1):
        print(f"{index}. 描述: {item['description']}")
        print(f"   负责人: {item.get('owner', '未指定')}")
        print(f"   截止时间: {item.get('deadline', '未指定')}")
        print()

    summary = extractor.summarize_action_items(action_items)
    print("摘要:")
    print(summary)


if __name__ == "__main__":
    test_extraction()
