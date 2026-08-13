from app.adapters.deepseek_model import DeepSeekQuizModel
from app.adapters.quiz_model import KnowledgePlan
from app.graphs.validate import GeneratedQuestion


class _FakeStructured:
    def __init__(self, value):
        self.value = value

    def invoke(self, _messages):
        return self.value


def test_deepseek_adapter_uses_structured_output(monkeypatch):
    plan = KnowledgePlan(title="拖延", points=["a", "b", "c", "d", "e"])
    question = GeneratedQuestion(
        knowledge_point="a",
        question_type="true_false",
        stem="材料是否提到拖延？",
        options=["正确", "错误"],
        answer_index=0,
        source_span="人们常常通过拖延来暂时逃避任务引发的焦虑",
        explanation="依据材料。",
    )

    class FakeChat:
        def __init__(self, **kwargs):
            assert kwargs["model"] == "deepseek-v4-flash"
            assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}

        def with_structured_output(self, schema, method, strict):
            assert method == "function_calling"
            assert strict is True
            if schema is KnowledgePlan:
                return _FakeStructured(plan)
            return _FakeStructured(question)

    monkeypatch.setattr("app.adapters.deepseek_model.ChatDeepSeek", FakeChat)
    model = DeepSeekQuizModel(api_key="test")
    assert model.plan("材料").points == plan.points
    generated = model.generate_question("材料", "a")
    assert generated.stem == question.stem


def test_deepseek_generate_retries_empty_structured_output(monkeypatch):
    question = GeneratedQuestion(
        knowledge_point="a",
        question_type="true_false",
        stem="材料是否提到拖延？",
        options=["正确", "错误"],
        answer_index=0,
        source_span="人们常常通过拖延来暂时逃避任务引发的焦虑",
        explanation="依据材料。",
    )

    class _ThenValue:
        def __init__(self):
            self.calls = 0

        def invoke(self, _messages):
            self.calls += 1
            if self.calls == 1:
                return None
            return question

    generator = _ThenValue()

    class FakeChat:
        def __init__(self, **kwargs):
            assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}

        def with_structured_output(self, schema, method, strict):
            if schema is KnowledgePlan:
                return _FakeStructured(
                    KnowledgePlan(title="拖延", points=["a", "b", "c", "d", "e"])
                )
            return generator

    monkeypatch.setattr("app.adapters.deepseek_model.ChatDeepSeek", FakeChat)
    model = DeepSeekQuizModel(api_key="test")
    generated = model.generate_question("材料", "a")
    assert generated.stem == question.stem
    assert generator.calls == 2
