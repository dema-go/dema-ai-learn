# 「考我一下」MVP 后端 + 小程序实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付可本地跑通的 P0+P1 闭环：粘贴文本/公开网页 → 后台任务生成 5–7 道限源题 → 逐题作答与原文依据 → 结果与错题复测 → 记录/额度/隐私删除；小程序视觉 1:1 对齐正式 HTML 原型。

**Architecture:** FastAPI 负责任务状态与业务 API；LangGraph `StateGraph` + `Send` 并行出题，`validate` 做三层校验，不配 checkpointer、不用 `create_agent`。模型经 `QuizModel` 接口注入，测试用 `FakeQuizModel`，有 `DEEPSEEK_API_KEY` 时走 `ChatDeepSeek.with_structured_output(..., method="function_calling", strict=True)`。微信小程序原生 TypeScript 页面按 `prototypes/codex-styles.css` 与画板移植，开发期 `wx.request` 访问本机 `127.0.0.1:8000`。

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy 2 / SQLite（测试与本地默认）/ LangGraph 1.2.11 / LangChain 1.3.15 / langchain-deepseek 1.1.0 / pytest / 微信原生小程序 + TypeScript。

## Global Constraints

- 范围仅 P0+P1。P2（结果卡、分享落地、好友挑战、订阅、次日召回、头像昵称授权）不做；结果页「分享结果」按钮可点，toast「分享稍后开放」。
- 拍照/文件入口禁用并标「敬请期待」，不做解析。
- 严格限源：禁止用材料外知识补答案；`source_span` 必须是原文真实连续子串（归一化空白与全半角后再比）。
- 文本上限 8000 字，超限 400 拒绝，不得静默截断。
- 每日生成额度 3 次（Asia/Shanghai 自然日）；同用户 `content_hash` 命中缓存不扣额度、不重新生成。
- 材料保留 7 天，到期删除 `raw_text`；用户删除则材料/题目/答题/错题级联删除。
- 缓存去重仅限同一用户，禁止跨用户共享原文。
- 任务状态：`pending` → `extracting` → `planning` → `generating` → `validating` → `succeeded` | `degraded` | `failed`。
- 进度文案只用：「正在理解原文」「正在抓住重点」「正在生成第 N 题」「正在检查答案」。
- 不宣称「掌握」「学会」「零幻觉」。题目/解析/结果页必须有 AI 标识。
- 正误除颜色外必须有图标和文字。选中后需用户点「确定答案」才提交。
- 开发期用户识别：请求头 `X-Dev-Openid`；缺省为 `dev-local-user`。
- 测试默认不打真实模型、不连生产库。本地默认 SQLite；`DATABASE_URL` 可切 MySQL。
- 不在 `main` 上写业务代码。后端 worktree：`.worktrees/backend` 分支 `agent/backend`。小程序 worktree：`.worktrees/miniprogram` 分支 `agent/miniprogram`。
- 实现 LangGraph / DeepSeek / FastAPI 前用 Context7 或官方文档核对该节点最新 API。
- 后端每个行为先写失败测试，再写最小实现（TDD）。

## File Structure

```text
contracts/openapi.yaml
backend/
  pyproject.toml
  .env.example
  app/
    main.py
    config.py
    db.py
    deps.py
    models/tables.py
    schemas/api.py
    schemas/quiz.py
    api/home.py
    api/quiz.py
    api/material.py
    api/feedback.py
    api/events.py
    services/users.py
    services/materials.py
    services/quota.py
    services/tasks.py
    services/attempts.py
    services/home.py
    services/events.py
    services/moderation.py
    graphs/state.py
    graphs/quiz_graph.py
    graphs/validate.py
    adapters/quiz_model.py
    adapters/url_extract.py
  tests/
    conftest.py
    test_health.py
    test_materials.py
    test_quota.py
    test_tasks.py
    test_validate.py
    test_graph.py
    test_quiz_api.py
    test_retest.py
    test_home.py
    test_feedback.py
    test_delete.py
    test_events.py
miniprogram/
  app.ts / app.json / app.wxss / sitemap.json / project.config.json / tsconfig.json
  services/api.ts
  services/auth.ts
  styles/tokens.wxss
  components/kaokao/ kaokao.ts wxml wxss json
  components/ai-notice/
  components/choice-card/
  components/primary-button/
  pages/home/ input-picker/ text-input/ url-input/ generation/ preview/
        quiz/ report/ result/ retest/ records/ record-detail/ wrong-book/
        quota/ profile/ privacy/ delete-confirm/ help/
```

## API Contract (权威，前后端共用)

基础 URL：`http://127.0.0.1:8000`

公共请求头：`X-Dev-Openid: string`

错误体：`{"error":{"code":"TEXT_TOO_LONG","message":"超过 8000 字，请截取重点段落后再试"}}`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| GET | `/api/home` | 额度 + 主任务（retest>continue>create）+ 最近 5 条 |
| POST | `/api/quiz/generate` | `{source_type:text\|url, text?, url?, channel?}` → `{task_id, status}` |
| GET | `/api/quiz/task/{task_id}` | `{task_id,status,progress,stage,quiz_id?,error?,question_count?}` |
| GET | `/api/quiz/{quiz_id}` | 完整题目（含 options、source_span、explanation） |
| POST | `/api/quiz/{quiz_id}/answer` | `{attempt_id?, question_id, chosen_index}` |
| POST | `/api/quiz/{quiz_id}/retest` | 基于最近一次 attempt 的错题生成新 quiz |
| GET | `/api/quiz/recent` | 最近闯关 |
| POST | `/api/question/{question_id}/feedback` | `{error_type: no_evidence\|wrong_answer\|ambiguous\|too_easy}` |
| DELETE | `/api/material/{material_id}` | 级联删除 |
| POST | `/api/events` | `{name, payload}` |
| GET | `/api/me` | 匿名统计：连续天数、星星、完成次数 |

题目对象：

```text
question_id, question_type(single|true_false), stem, options[],
answer_index, explanation, source_span, quality_status(passed|degraded)
```

作答响应：`{is_correct, correct_index, explanation, source_span, attempt_id, next_question_id, finished, result?}`

---

### Task 1: OpenAPI 契约

**Files:**
- Create: `contracts/openapi.yaml`

**Interfaces:**
- Produces: 上文 API 表的完整 OpenAPI 3.1 文档，供前后端共用。
- Consumes: 无

- [ ] **Step 1: 写入 OpenAPI 文件**

在 `contracts/openapi.yaml` 中定义 `HealthResponse`、`GenerateRequest`、`TaskResponse`、`QuizResponse`、`Question`、`AnswerRequest`、`AnswerResponse`、`HomeResponse`、`ErrorBody`。`GenerateRequest` 用 `source_type` 区分 text/url；`text` 超过 8000 由服务端拒绝。状态枚举必须包含 `pending, extracting, planning, generating, validating, succeeded, degraded, failed`。

- [ ] **Step 2: 校验 YAML 可解析**

```bash
python3 -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('contracts/openapi.yaml').read_text()); print('ok')"
```

若环境无 PyYAML：`python3 -c "import pathlib; t=pathlib.Path('contracts/openapi.yaml').read_text(); assert 'openapi:' in t and '/api/quiz/generate' in t; print('ok')"`

Expected: `ok`

- [ ] **Step 3: Commit**（仅当用户要求提交时执行；默认跳过）

---

### Task 2: 后端骨架与健康检查

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI`；`GET /health` 返回 `{"status":"ok"}`
- Consumes: 无

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: 运行确认失败**

```bash
cd backend && python -m pytest tests/test_health.py -v
```

Expected: FAIL `ModuleNotFoundError` 或 `create_app` 未定义

- [ ] **Step 3: 最小实现**

`pyproject.toml` 依赖锁定：

```toml
[project]
name = "kaowoyixia-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy>=2.0",
  "pydantic-settings>=2.4",
  "httpx>=0.27",
  "trafilatura>=2.0",
  "langgraph==1.2.11",
  "langchain==1.3.15",
  "langchain-deepseek==1.1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```python
# backend/app/main.py
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="考我一下")
    @app.get("/health")
    def health():
        return {"status": "ok"}
    return app

app = create_app()
```

`.env.example`：

```
DATABASE_URL=sqlite:///./local.db
DEEPSEEK_API_KEY=
DEFAULT_OPENID=dev-local-user
DAILY_GENERATE_LIMIT=3
MATERIAL_TTL_DAYS=7
TIMEZONE=Asia/Shanghai
```

- [ ] **Step 4: 安装并跑通**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/test_health.py -v
```

Expected: PASS

---

### Task 3: 数据库表与测试夹具

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/tables.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Produces: SQLAlchemy 模型 `User, Material, Task, Quiz, Question, Attempt, Answer, Feedback, Event`；`get_engine()` / `get_session()` / `init_db()`
- Consumes: `Settings.database_url`

表字段按 `技术方案.md` §5.5，并补：

- `User`: `id, openid, channel, created_at, streak_days, stars`
- `Material`: `id, user_id, source_type, source_url, title, content_hash, raw_text, expire_at, created_at`
- `Task`: `id, user_id, material_id, status, progress, stage, retry_count, error, quiz_id, created_at, updated_at`
- `Quiz`: `id, material_id, user_id, question_count, is_degraded, is_retest, parent_quiz_id, created_at`
- `Question`: `id, quiz_id, ordinal, question_type, stem, options_json, answer_index, source_span, explanation, quality_status, knowledge_point`
- `Attempt`: `id, quiz_id, user_id, started_at, completed_at, score, current_ordinal`
- `Answer`: `id, attempt_id, question_id, chosen_index, is_correct, created_at`
- `Feedback`: `id, question_id, user_id, error_type, created_at`
- `Event`: `id, user_id, name, payload_json, created_at`

- [ ] **Step 1: 写失败测试**

```python
def test_init_db_creates_user_table(db_session):
    from app.models.tables import User
    user = User(openid="o1", channel="dev")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
```

- [ ] **Step 2: 运行确认失败**

Expected: `User` 未定义

- [ ] **Step 3: 实现模型与内存 SQLite 夹具**

`conftest.py` 使用 `sqlite:///:memory:` + `StaticPool`，每个测试 `create_all` / `drop_all`，并通过 `app.dependency_overrides` 注入 session。

- [ ] **Step 4: 测试通过**

---

### Task 4: 用户识别与首页空状态

**Files:**
- Create: `backend/app/deps.py`
- Create: `backend/app/services/users.py`
- Create: `backend/app/api/home.py`
- Create: `backend/tests/test_home.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `X-Dev-Openid` header
- Produces: `get_current_user(session, openid) -> User`（不存在则创建）；`GET /api/home` 无数据时：

```json
{
  "quota": {"used": 0, "limit": 3, "reset_at": "2026-08-14T16:00:00+00:00"},
  "primary_task": {"type": "create"},
  "recent": [],
  "me": {"streak_days": 0, "stars": 0, "completed_count": 0}
}
```

- [ ] **Step 1: 写失败测试**

```python
def test_home_creates_user_and_returns_create_task(client):
    res = client.get("/api/home", headers={"X-Dev-Openid": "user-a"})
    assert res.status_code == 200
    body = res.json()
    assert body["primary_task"]["type"] == "create"
    assert body["quota"]["limit"] == 3
    assert body["quota"]["used"] == 0
    assert body["recent"] == []
```

- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 `get_current_user` + `/api/home` 最小返回**
- [ ] **Step 4: 测试通过**

---

### Task 5: 材料校验（8000 字、空内容、URL 形态）

**Files:**
- Create: `backend/app/services/materials.py`
- Create: `backend/app/schemas/api.py`
- Create: `backend/tests/test_materials.py`
- Create: `backend/app/api/quiz.py`（先只接 generate 校验部分）

**Interfaces:**
- Produces: `count_chars(text) -> int`（按 Unicode 码点计数）；`validate_generate_input(source_type, text, url) -> None | raises DomainError`
- 错误码：`TEXT_EMPTY`, `TEXT_TOO_LONG`, `URL_INVALID`, `URL_REQUIRED`

- [ ] **Step 1: 写失败测试**

```python
def test_reject_text_over_8000(client):
    res = client.post("/api/quiz/generate", json={
        "source_type": "text",
        "text": "测" * 8001,
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "TEXT_TOO_LONG"
    assert "截取" in res.json()["error"]["message"]

def test_reject_empty_text(client):
    res = client.post("/api/quiz/generate", json={"source_type": "text", "text": "   "})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "TEXT_EMPTY"

def test_accept_text_8000(client):
    res = client.post("/api/quiz/generate", json={
        "source_type": "text",
        "text": "测" * 8000,
    })
    assert res.status_code == 200
    assert "task_id" in res.json()
```

- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现校验；超限不得截断后继续。此时 generate 可先创建 pending task 并立即返回，图可稍后挂接。**
- [ ] **Step 4: 测试通过**

---

### Task 6: 额度与同用户缓存

**Files:**
- Create: `backend/app/services/quota.py`
- Create: `backend/tests/test_quota.py`
- Modify: `backend/app/api/quiz.py`
- Modify: `backend/app/services/materials.py`

**Interfaces:**
- Produces: `hash_content(text) -> str`（sha256 hex）；`count_today_generations(session, user_id, now) -> int`；`assert_quota_available(...)`；缓存命中返回已有 `quiz` 对应的已完成 task 或新建 `succeeded` task 指向旧 quiz
- 额度满：HTTP 429，`code=QUOTA_EXCEEDED`，message 含恢复时间

- [ ] **Step 1: 写失败测试**

```python
def test_fourth_generate_is_rejected(client, make_text):
    payload = {"source_type": "text", "text": make_text(1)}
    for i in range(3):
        payload = {"source_type": "text", "text": f"材料{i}：" + "内容足够长的一段话。" * 20}
        assert client.post("/api/quiz/generate", json=payload).status_code == 200
    res = client.post("/api/quiz/generate", json={"source_type": "text", "text": "另一篇" + "内容足够长的一段话。" * 20})
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "QUOTA_EXCEEDED"

def test_same_hash_does_not_consume_quota(client):
    payload = {"source_type": "text", "text": "拖延是一种短期情绪调节策略。" * 30}
    first = client.post("/api/quiz/generate", json=payload)
    second = client.post("/api/quiz/generate", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    home = client.get("/api/home").json()
    assert home["quota"]["used"] == 1
```

说明：本任务测试可先在「generate 只建 task、Fake 图同步成功」的前提下跑；若图尚未接通，用测试夹具把 task 直接标 `succeeded` 并写入 quiz，再测额度计数以「非缓存的 generate 调用次数」为准。

- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现额度与 hash；跨用户相同 hash 不得复用 quiz/原文**
- [ ] **Step 4: 测试通过**

另加：

```python
def test_cache_not_shared_across_users(client):
    payload = {"source_type": "text", "text": "同一段公开资料内容。" * 40}
    a = client.post("/api/quiz/generate", json=payload, headers={"X-Dev-Openid": "u1"})
    b = client.post("/api/quiz/generate", json=payload, headers={"X-Dev-Openid": "u2"})
    assert a.json()["task_id"] != b.json()["task_id"]
```

---

### Task 7: 任务状态机与轮询

**Files:**
- Create: `backend/app/services/tasks.py`
- Create: `backend/tests/test_tasks.py`

**Interfaces:**
- Produces: `create_task(...)`；`update_task_progress(task, status, stage, progress_text)`；`get_task(task_id, user_id)`
- `GET /api/quiz/task/{task_id}` 只返回属于当前用户的任务，否则 404
- stage 与文案映射：

```python
STAGE_COPY = {
    "extracting": "正在理解原文",
    "planning": "正在抓住重点",
    "generating": "正在生成第 {n} 题",
    "validating": "正在检查答案",
}
```

- [ ] **Step 1: 写失败测试**

```python
def test_generate_returns_task_immediately(client):
    res = client.post("/api/quiz/generate", json={
        "source_type": "text",
        "text": "人们常常通过拖延来暂时逃避任务引发的焦虑。" * 20,
    })
    assert res.status_code == 200
    task_id = res.json()["task_id"]
    polled = client.get(f"/api/quiz/task/{task_id}")
    assert polled.status_code == 200
    assert polled.json()["status"] in {
        "pending", "extracting", "planning", "generating", "validating",
        "succeeded", "degraded", "failed",
    }
    assert polled.json()["progress"]

def test_task_not_visible_to_other_user(client):
    res = client.post("/api/quiz/generate", json={
        "source_type": "text", "text": "公开可测文本。" * 30,
    }, headers={"X-Dev-Openid": "owner"})
    task_id = res.json()["task_id"]
    other = client.get(f"/api/quiz/task/{task_id}", headers={"X-Dev-Openid": "intruder"})
    assert other.status_code == 404
```

- [ ] **Step 2–4: 红绿循环**

---

### Task 8: URL 抽取适配器（mock httpx/trafilatura）

**Files:**
- Create: `backend/app/adapters/url_extract.py`
- Create: `backend/app/services/moderation.py`
- Modify: `backend/tests/test_materials.py`

**Interfaces:**
- Produces: `ExtractResult(ok, title, text, error_code)`
- `error_code`: `URL_FETCH_FAILED` | `URL_LOGIN_WALL` | `URL_TOO_SHORT` | `URL_BLOCKED`
- 登录墙启发式：页面含 password 表单、或状态码 401/403、或正文 < 200 字
- 不绕过付费/验证码；失败 message：「这个网页没法读取，可能需要登录、付费或验证码。请改用粘贴文本。」
- `moderation.scan_text(text)` 本轮返回 `passed`；预留接口以便替换微信内容安全

- [ ] **Step 1: 写失败测试**

```python
from app.adapters.url_extract import extract_public_url

def test_extract_success(monkeypatch):
    monkeypatch.setattr("app.adapters.url_extract.fetch_html", lambda url: (
        200, "<article><h1>标题</h1><p>" + "正文内容" * 80 + "</p></article>"
    ))
    result = extract_public_url("https://example.com/a")
    assert result.ok is True
    assert result.title
    assert len(result.text) >= 200

def test_extract_login_wall(monkeypatch):
    monkeypatch.setattr("app.adapters.url_extract.fetch_html", lambda url: (401, "login"))
    result = extract_public_url("https://example.com/private")
    assert result.ok is False
    assert result.error_code == "URL_LOGIN_WALL"
```

- [ ] **Step 2–4: 红绿循环；generate 的 url 分支调用该适配器，失败则 task=`failed`**

---

### Task 9: source_span 与题目质量校验（纯函数）

**Files:**
- Create: `backend/app/graphs/validate.py`
- Create: `backend/app/schemas/quiz.py`
- Create: `backend/tests/test_validate.py`

**Interfaces:**

```python
class GeneratedQuestion(BaseModel):
    knowledge_point: str
    question_type: Literal["single", "true_false"]
    stem: str
    options: list[str] = Field(min_length=2, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    source_span: str
    explanation: str
    distractor_rationale: str = ""

def normalize_for_match(text: str) -> str: ...
def span_in_source(span: str, source: str) -> bool: ...
def validate_question(q: GeneratedQuestion, source: str) -> list[str]:
    """返回失败原因列表；空列表表示通过。"""
```

校验规则：

1. `span_in_source`：对 span 与 source 做 NFKC、全角转半角、空白折叠后，span 为 source 子串；span 长度 8–120 字。
2. `answer_index` 落在 `options` 范围内。
3. 判断题必须恰好 2 个选项，且为「正确/错误」或「对/错」或题干可判断的正反项。
4. 单选题 3–4 选项。
5. 题干不得完整包含正确选项原文（防泄答案，简单包含检查）。
6. `source_span` 必须能支持正确选项：正确选项的关键名词/短语至少有一个出现在 span 或题干+span 中；本层做启发式，失败则记原因 `unsupported_answer`。
7. 干扰项不得与 span 完全同义抄录正确事实到错误选项（若错误选项是 span 的连续子串且与正确答案不同，记 `distractor_conflicts`）。

- [ ] **Step 1: 写失败测试**

```python
SOURCE = "研究者认为，人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。这种短期情绪修复，会带来更大的长期压力。"

def test_span_must_be_real_substring():
    from app.graphs.validate import span_in_source
    assert span_in_source("暂时逃避任务引发的焦虑", SOURCE) is True
    assert span_in_source("拖延其实是基因决定的", SOURCE) is False

def test_fullwidth_and_whitespace_normalize():
    from app.graphs.validate import span_in_source
    assert span_in_source("暂时逃避任务引发的焦虑", "暂时  逃避任务引发的焦虑") is True

def test_validate_question_rejects_missing_span():
    from app.graphs.validate import GeneratedQuestion, validate_question
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
```

- [ ] **Step 2–4: 红绿循环**

---

### Task 10: QuizModel 接口与 FakeQuizModel

**Files:**
- Create: `backend/app/adapters/quiz_model.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**

```python
class KnowledgePlan(BaseModel):
    title: str
    points: list[str] = Field(min_length=5, max_length=7)

class QuizModel(Protocol):
    def plan(self, source: str) -> KnowledgePlan: ...
    def generate_question(self, source: str, point: str) -> GeneratedQuestion: ...

class FakeQuizModel:
    def __init__(self, plan: KnowledgePlan, questions: dict[str, GeneratedQuestion]): ...
```

`get_quiz_model()`：无 `DEEPSEEK_API_KEY` 时返回内置 `FixtureQuizModel`（从原文截取真实 span 造 5 道可用题，保证本地无 Key 也能闭环）；有 Key 时返回 `DeepSeekQuizModel`。

测试通过 `app.dependency_overrides` 或 `graph.set_model()` 注入 Fake，断言：

- Fake 返回的 span 均在给定原文中
- 调用 `generate_question` 次数等于 plan.points 数量

- [ ] **Step 1–4: 红绿循环；先不要接 DeepSeek**

---

### Task 11: LangGraph 出题图（Fake 模型）

**Files:**
- Create: `backend/app/graphs/state.py`
- Create: `backend/app/graphs/quiz_graph.py`
- Create: `backend/tests/test_graph.py`

**Interfaces:**

实现前用 Context7 复核 `StateGraph` / `Send` / `START` / `END`（官方：`from langgraph.graph import StateGraph, START, END`；`from langgraph.types import Send`）。

```python
class QuizGraphState(TypedDict):
    source_text: str
    title: str
    points: list[str]
    raw_questions: Annotated[list[GeneratedQuestion], operator.add]
    valid_questions: list[GeneratedQuestion]
    rejected: list[dict]
    retry_count: int
    status: str  # succeeded | degraded | failed
    progress_stage: str
    generate_index: int
```

图：

```text
extract(清洗/截断空白，不截 8000 已在入口完成)
 → plan(QuizModel.plan)
 → Send("generate", {point, source_text}) × N
 → validate
 → 若 rejected 非空且 retry_count < 2：只对 rejected 的 point 再 Send generate
 → 若 valid 5–7：succeeded；3–4：degraded；<3：failed
```

`compile(checkpointer=False)` 或不传 checkpointer。

- [ ] **Step 1: 写失败测试**

```python
def test_graph_keeps_only_valid_questions(fake_model, source):
    from app.graphs.quiz_graph import build_quiz_graph
    graph = build_quiz_graph(fake_model)
    out = graph.invoke({"source_text": source, "retry_count": 0})
    assert out["status"] in {"succeeded", "degraded"}
    assert 5 <= len(out["valid_questions"]) <= 7
    for q in out["valid_questions"]:
        assert q.source_span in source or span_in_source(q.source_span, source)

def test_graph_retries_only_failed_item(fake_model_one_bad):
    graph = build_quiz_graph(fake_model_one_bad)
    out = graph.invoke({"source_text": SOURCE, "retry_count": 0})
    assert fake_model_one_bad.generate_calls["坏知识点"] == 2  # 初试 + 1 次重试上限内
```

- [ ] **Step 2–4: 红绿循环。节点内更新 progress 可通过回调 `on_progress(stage, n)` 写 task 表。**

---

### Task 12: 后台执行 generate → 落库 quiz

**Files:**
- Modify: `backend/app/api/quiz.py`
- Modify: `backend/app/services/tasks.py`
- Create: `backend/tests/test_quiz_api.py`

**Interfaces:**
- `POST /api/quiz/generate` 创建 task 后 `BackgroundTasks.add_task(run_quiz_job, task_id)`
- job：extract/plan/generate/validate → 写 `Quiz`+`Question` → task.status=`succeeded|degraded|failed`
- `GET /api/quiz/{quiz_id}` 返回题目；**作答前也返回 `answer_index`**（小程序需要即时判题；生产可改为服务端判，但首版前后端都持有答案，与原型一致）
- 测试用 Fake 模型 + `TestClient` 的 `app.dependency_overrides`

- [ ] **Step 1: 写失败测试**

```python
def test_generate_completes_and_quiz_readable(client, monkeypatch):
    install_fake_model(monkeypatch)
    res = client.post("/api/quiz/generate", json={
        "source_type": "text",
        "text": SOURCE,
    })
    task_id = res.json()["task_id"]
    body = wait_task(client, task_id)
    assert body["status"] in {"succeeded", "degraded"}
    quiz = client.get(f"/api/quiz/{body['quiz_id']}").json()
    assert 5 <= len(quiz["questions"]) <= 7
    assert all(q["source_span"] for q in quiz["questions"])
    assert "AI 依据你的材料生成，可能有误" not in quiz["questions"][0]["stem"]
```

`wait_task`：循环 `GET /api/quiz/task/{id}` 最多 2 秒（Fake 应同步或极快）。

- [ ] **Step 2–4: 红绿循环；同时写 `generation_success` 事件**

---

### Task 13: 答题、续答、结果

**Files:**
- Create: `backend/app/services/attempts.py`
- Modify: `backend/app/api/quiz.py`
- Modify: `backend/tests/test_quiz_api.py`

**Interfaces:**
- `POST /api/quiz/{quiz_id}/answer`
  - 首次作答创建 `Attempt`
  - 同一题重复提交 409 `ALREADY_ANSWERED`
  - 返回 `is_correct, correct_index, explanation, source_span, finished`
  - `finished=true` 时附 `result: {correct, total, duration_seconds, wrong_question_ids}`
- 续答：`GET /api/quiz/{id}` 带 `attempt` 当前进度
- 事件：第一题 `quiz_started`，最后一题 `quiz_completed`

- [ ] **Step 1: 写失败测试**

```python
def test_answer_correct_and_wrong(client, ready_quiz):
    q0 = ready_quiz["questions"][0]
    res = client.post(f"/api/quiz/{ready_quiz['id']}/answer", json={
        "question_id": q0["question_id"],
        "chosen_index": q0["answer_index"],
    })
    assert res.status_code == 200
    assert res.json()["is_correct"] is True
    assert res.json()["explanation"]
    assert res.json()["source_span"]

def test_duplicate_answer_rejected(client, ready_quiz):
    q0 = ready_quiz["questions"][0]
    payload = {"question_id": q0["question_id"], "chosen_index": 0}
    client.post(f"/api/quiz/{ready_quiz['id']}/answer", json=payload)
    res = client.post(f"/api/quiz/{ready_quiz['id']}/answer", json=payload)
    assert res.status_code == 409
```

- [ ] **Step 2–4: 红绿循环**

---

### Task 14: 错题复测

**Files:**
- Modify: `backend/app/api/quiz.py`
- Create: `backend/tests/test_retest.py`

**Interfaces:**
- `POST /api/quiz/{quiz_id}/retest`：取该 quiz 最近一次已完成 attempt 的错题，复制题目到新 quiz（`is_retest=true`, `parent_quiz_id`），不调用模型
- 无错题：400 `NO_WRONG_ANSWERS`
- 事件 `retest_started`

- [ ] **Step 1: 写失败测试**

```python
def test_retest_contains_only_wrong_questions(client, answered_quiz_with_two_wrong):
    res = client.post(f"/api/quiz/{answered_quiz_with_two_wrong}/retest")
    assert res.status_code == 200
    quiz = client.get(f"/api/quiz/{res.json()['quiz_id']}").json()
    assert quiz["is_retest"] is True
    assert len(quiz["questions"]) == 2
```

- [ ] **Step 2–4: 红绿循环**

---

### Task 15: 纠错、删除、最近列表、首页优先级

**Files:**
- Create: `backend/app/api/feedback.py`
- Create: `backend/app/api/material.py`
- Create: `backend/app/services/home.py`
- Create: `backend/tests/test_feedback.py`
- Create: `backend/tests/test_delete.py`
- Modify: `backend/tests/test_home.py`

**Interfaces:**
- 纠错四类，重复提交同题同类型可 200 幂等
- DELETE material 后 GET quiz 404
- 首页 `primary_task.type`：有待复测错题 → `retest`；否则有未完成 attempt → `continue`；否则 `create`
- `GET /api/me` 与 home.me 一致
- `GET /api/quiz/recent` 支持 `?filter=all|active|retest`

- [ ] **Step 1–4: 各接口一条失败测试再实现**

首页优先级测试：

```python
def test_home_prefers_retest_over_continue(client, user_with_wrong_and_unfinished):
    body = client.get("/api/home").json()
    assert body["primary_task"]["type"] == "retest"
```

---

### Task 16: 埋点与 DeepSeek 适配器（无 Key 跳过集成测试）

**Files:**
- Create: `backend/app/api/events.py`
- Create: `backend/app/services/events.py`
- Create: `backend/tests/test_events.py`
- Modify: `backend/app/adapters/quiz_model.py`

**Interfaces:**
- `POST /api/events` 接受 `generation_success|quiz_started|quiz_completed|retest_started|question_error_reported|second_creation_7d`
- `DeepSeekQuizModel.plan/generate_question` 使用：

```python
from langchain_deepseek import ChatDeepSeek

model = ChatDeepSeek(model="deepseek-v4-flash", temperature=0)
structured = model.with_structured_output(
    GeneratedQuestion, method="function_calling", strict=True
)
```

外层最多 2 次捕获校验/解析异常后放弃该题。实现前再查 Context7：`ChatDeepSeek.with_structured_output`。

- [ ] **Step 1: 事件测试**
- [ ] **Step 2: `DeepSeekQuizModel` 单测用 monkeypatch 掉 `with_structured_output` 的 invoke**
- [ ] **Step 3: 若存在 `DEEPSEEK_API_KEY`，加 `@pytest.mark.integration` 的可选测试，默认不跑**

```bash
pytest tests/ -v
pytest tests/ -v -m integration   # 仅有 Key 时
```

Expected: 默认套件全绿

---

### Task 17: 小程序工程与设计系统

**Files:** 在 `.worktrees/miniprogram` 创建 `miniprogram/`（见 File Structure）

**Interfaces:**
- `services/api.ts`：封装上述 API，baseURL 可配置 `http://127.0.0.1:8000`
- `styles/tokens.wxss` 必须含：`#FBF7EE #FFFEFA #DE5848 #FBE2DD #78CDBF #D9F0EB #FFD45A #24292D #6F777E #D8D4CB #C9443A`
- 字体栈与原型一致；禁止楷体/仿宋
- `components/kaokao` 内联四套 SVG：happy/thinking/sweat/cheer，path 从 `prototypes/codex-core-flow.html` 原样复制
- `app.json`：`renderer` 不设 skyline；tabBar 三栏：闯关 / 记录 / 我的
- 文案对照 `UI原型图.md` 画板，不改口号与角色名

- [ ] **Step 1: 建原生 TS 项目结构与 token/组件**
- [ ] **Step 2: 对照原型 CSS 把 `.btn .card .choice-card .hero .ai-notice .tabs` 迁到 WXSS**
- [ ] **Step 3: 用开发者工具或截图确认 390px 无横向溢出（执行时在模拟器/浏览器核对）**

---

### Task 18: 小程序 P0 页面

按画板实现，状态与文案不得自行发挥：

| 页面 | 原型锚点 |
| --- | --- |
| pages/home | `#first-home` / `#return-home`（按 /api/home 切换） |
| pages/input-picker | `#input-picker` |
| pages/text-input | `#text-input` |
| pages/url-input | `#url-input` |
| pages/generation | `#generation` 每 1.5s 轮询 |
| pages/preview | `#generation-preview` |
| pages/quiz | `#quiz-question` `#quiz-correct` `#quiz-wrong` 原位切换 |
| pages/report | `#question-report` |
| pages/result | `#quiz-result`（分享 toast「分享稍后开放」） |
| pages/retest | `#wrong-retest` |

硬性：

- 选中选项后必须点「确定答案」
- 答错默认展开原文依据；答对可折叠展开
- 每页 AI 标识
- 生成可返回首页，任务继续

---

### Task 19: 小程序 P1 页面 + 本地联调

| 页面 | 原型锚点 |
| --- | --- |
| pages/records | `#recent-list` |
| pages/record-detail | `#record-detail` |
| pages/wrong-book | `#wrong-book` |
| pages/quota | `#quota-limit` |
| pages/profile | `#profile` |
| pages/privacy | `#privacy-data` |
| pages/delete-confirm | `#delete-confirm` |
| pages/help | `#help-feedback` |

联调：

```bash
# worktree backend
cd .worktrees/backend/backend && source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 微信开发者工具打开 .worktrees/miniprogram/miniprogram
# 关闭合法域名校验
```

验收：用一段 ≥200 字中文跑通 生成→答题→结果→复测；额度第 4 次触顶页；删除材料后记录消失。

---

### Task 20: 回归与交接

- [ ] `cd backend && pytest tests/ -v` 全绿
- [ ] `python3 -m unittest tests/test_prototypes.py -v` 原原型测试不被破坏
- [ ] `git diff --check` 与 `git status -sb`
- [ ] 交接：worktree 路径、启动命令、无 Key 时 Fake 模型行为、未做 P2、未接云托管
- [ ] 不自动 commit / 不自动开 PR

## Spec coverage

| 需求 | 任务 |
| --- | --- |
| M1 静默用户 | Task 4（开发头） |
| M2 输入 | Task 5, 8, 18 |
| M3 生成 5–7 题 | Task 10–12 |
| M4 质量自检 | Task 9, 11 |
| M5 答题 | Task 13, 18 |
| M6 原文依据 | Task 9, 13, 18 |
| M7 AI 标识 | Task 18–19 |
| M8 纠错 | Task 15, 18 |
| M9 结果页 | Task 13, 18（分享不做） |
| M10 复测 | Task 14, 18 |
| M11 最近列表 | Task 15, 19 |
| M12 隐私删除 | Task 15, 19（微信内容安全 mock） |
| M13 埋点 | Task 16 |
| M14 channel | GenerateRequest.channel → User.channel |
| 额度 | Task 6, 19 |
| P2 分享订阅 | 明确不做 |

## Type consistency

- 任务状态字符串与 OpenAPI / `Task.status` / 小程序轮询枚举一致
- 题目主键 API 字段名 `question_id`（表内 `Question.id`）
- 纠错 `error_type` 四值固定
- 首页 `primary_task.type` 仅 `retest|continue|create`
