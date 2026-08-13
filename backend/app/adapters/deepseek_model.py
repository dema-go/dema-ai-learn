from langchain_deepseek import ChatDeepSeek

from app.adapters.quiz_model import KnowledgePlan
from app.graphs.validate import GeneratedQuestion

PLAN_PROMPT = (
    "你只根据用户提供的中文材料提取 5 到 7 个可出题知识点。"
    "禁止引入材料外知识。title 用材料主题，points 是短知识点名称。"
)
QUESTION_PROMPT = (
    "只根据给定材料出一道题。题型 single 或 true_false。"
    "source_span 必须是原文中真实存在的连续片段。"
    "只有一个正确答案。题干不要泄露答案。禁止材料外知识。"
)


class DeepSeekQuizModel:
    def __init__(self, api_key: str) -> None:
        self._model = ChatDeepSeek(
            model="deepseek-v4-flash",
            api_key=api_key,
            temperature=0,
            max_retries=2,
            extra_body={"thinking": {"type": "disabled"}},
        )
        self._planner = self._model.with_structured_output(
            KnowledgePlan, method="function_calling", strict=True
        )
        self._generator = self._model.with_structured_output(
            GeneratedQuestion, method="function_calling", strict=True
        )

    def plan(self, source: str) -> KnowledgePlan:
        result = self._planner.invoke(
            [
                ("system", PLAN_PROMPT),
                ("human", source[:8000]),
            ]
        )
        if result is None:
            raise ValueError("DeepSeek 规划返回空结果")
        return result

    def generate_question(self, source: str, point: str) -> GeneratedQuestion:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                result = self._generator.invoke(
                    [
                        ("system", QUESTION_PROMPT),
                        (
                            "human",
                            f"知识点：{point}\n\n材料：\n{source[:8000]}",
                        ),
                    ]
                )
                if result is None:
                    last_error = ValueError("DeepSeek 出题返回空结果")
                    continue
                return result
            except Exception as exc:  # noqa: BLE001 - 外层熔断，避免无限重试
                last_error = exc
        raise last_error or ValueError("DeepSeek 出题失败")
