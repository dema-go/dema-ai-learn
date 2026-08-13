from collections import defaultdict

from app.adapters.quiz_model import FakeQuizModel, KnowledgePlan
from app.graphs.quiz_graph import build_quiz_graph
from app.graphs.validate import GeneratedQuestion, span_in_source

SOURCE = (
    "研究者认为，人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。"
    "这种短期情绪修复，会带来更大的长期压力。"
    "拖延并不总是时间管理问题，它也可能是一种回避策略。"
    "短期轻松之后，任务压力往往会变得更大。"
    "理解诱因，有助于把注意力从自责转向调节情绪。"
    "因此读完材料后，用几道题检查自己是否抓住了核心观点。"
)


def _ok_question(point: str, span: str) -> GeneratedQuestion:
    return GeneratedQuestion(
        knowledge_point=point,
        question_type="single",
        stem=f"关于「{point}」，材料更支持哪一项？",
        options=["与材料无关的外部知识", span[:18], "完全相反的结论"],
        answer_index=1,
        source_span=span,
        explanation="依据原文片段。",
    )


def test_graph_keeps_only_valid_questions():
    points = ["逃避焦虑", "短期修复", "不是时间管理", "压力变大", "转向情绪"]
    spans = [
        "人们常常通过拖延来暂时逃避任务引发的焦虑",
        "这种短期情绪修复，会带来更大的长期压力",
        "拖延并不总是时间管理问题",
        "任务压力往往会变得更大",
        "把注意力从自责转向调节情绪",
    ]
    model = FakeQuizModel(
        plan=KnowledgePlan(title="拖延", points=points),
        questions={point: _ok_question(point, span) for point, span in zip(points, spans)},
    )
    graph = build_quiz_graph(model)
    out = graph.invoke({"source_text": SOURCE, "retry_count": 0})
    assert out["status"] in {"succeeded", "degraded"}
    assert 5 <= len(out["valid_questions"]) <= 7
    for question in out["valid_questions"]:
        assert span_in_source(question.source_span, SOURCE)


def test_graph_retries_only_failed_item():
    points = ["好知识点", "坏知识点", "稳定点一", "稳定点二", "稳定点三"]
    good_span = "人们常常通过拖延来暂时逃避任务引发的焦虑"
    questions = {
        "好知识点": _ok_question("好知识点", good_span),
        "稳定点一": _ok_question("稳定点一", "拖延并不总是时间管理问题"),
        "稳定点二": _ok_question("稳定点二", "任务压力往往会变得更大"),
        "稳定点三": _ok_question("稳定点三", "把注意力从自责转向调节情绪"),
        "坏知识点": [
            GeneratedQuestion(
                knowledge_point="坏知识点",
                question_type="single",
                stem="这题没有依据？",
                options=["A", "B", "C"],
                answer_index=0,
                source_span="这段话完全不在原文里",
                explanation="x",
            ),
            _ok_question("坏知识点", "这种短期情绪修复，会带来更大的长期压力"),
        ],
    }
    model = FakeQuizModel(
        plan=KnowledgePlan(title="拖延", points=points),
        questions=questions,
    )
    graph = build_quiz_graph(model)
    out = graph.invoke({"source_text": SOURCE, "retry_count": 0})
    assert model.generate_calls["坏知识点"] == 2
    assert any(item.knowledge_point == "坏知识点" for item in out["valid_questions"])
