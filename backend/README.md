# 考我一下 · 后端

本地开发（默认 SQLite + 无 Key 时用限源 Fixture 模型）：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

测试：

```bash
pytest tests/ -v
```

有 `DEEPSEEK_API_KEY` 时会走 `deepseek-v4-flash` + strict function calling，并关闭思考模式（`thinking.type=disabled`）。
开发期用户识别请求头：`X-Dev-Openid`。
切勿提交 `.env`。
