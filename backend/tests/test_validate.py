from app.graphs.validate import GeneratedQuestion, span_in_source, validate_question

SOURCE = (
    "研究者认为，人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。"
    "这种短期情绪修复，会带来更大的长期压力。"
)


def test_span_must_be_real_substring():
    assert span_in_source("暂时逃避任务引发的焦虑", SOURCE) is True
    assert span_in_source("拖延其实是基因决定的", SOURCE) is False


def test_fullwidth_and_whitespace_normalize():
    assert span_in_source("暂时逃避任务引发的焦虑", "暂时  逃避任务引发的焦虑") is True
    assert span_in_source("暂时逃避任务引发的焦虑", "暂时逃避任务引发的焦虑") is True


def test_validate_question_rejects_missing_span():
    q = GeneratedQuestion(
        knowledge_point="情绪",
        question_type="single",
        stem="拖延最常见诱因是？",
        options=["时间管理不足", "对负面情绪的即时逃避", "没有目标"],
        answer_index=1,
        source_span="这段话完全不在原文里",
        explanation="x",
    )
    assert "span_not_in_source" in validate_question(q, SOURCE)


def test_validate_question_accepts_supported_item():
    q = GeneratedQuestion(
        knowledge_point="情绪调节",
        question_type="single",
        stem="文章认为人们拖延常常是为了什么？",
        options=["提高效率", "暂时逃避任务引发的焦虑", "增加长期压力"],
        answer_index=1,
        source_span="人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑",
        explanation="原文把拖延描述为短期情绪修复。",
    )
    assert validate_question(q, SOURCE) == []


def test_validate_rejects_out_of_range_answer():
    q = GeneratedQuestion(
        knowledge_point="情绪",
        question_type="single",
        stem="拖延最常见诱因是什么？",
        options=["A", "B", "C"],
        answer_index=3,
        source_span="人们常常通过拖延来暂时逃避任务引发的焦虑",
        explanation="x",
    )
    assert "answer_index_out_of_range" in validate_question(q, SOURCE)


def test_validate_rejects_stem_leaking_answer():
    q = GeneratedQuestion(
        knowledge_point="情绪",
        question_type="single",
        stem="人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑，对吗？答案是暂时逃避任务引发的焦虑、无聊或自我怀疑",
        options=["时间管理", "暂时逃避任务引发的焦虑、无聊或自我怀疑", "没有目标"],
        answer_index=1,
        source_span="人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑",
        explanation="x",
    )
    assert "stem_leaks_answer" in validate_question(q, SOURCE)
