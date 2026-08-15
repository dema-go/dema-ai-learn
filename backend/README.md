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

## 数据库迁移

服务启动时会读取 `schema_migration` 的当前版本，并按版本执行轻量迁移。版本 1 为
`attempt(user_id, quiz_id)` 和 `answer(attempt_id, question_id)` 创建唯一索引，保证同一关的
首次作答与单题重试幂等；重复启动不会重复执行已记录的迁移。
若两个进程同时尝试同一版本，其中一方遇到重复 DDL 或版本写入冲突后，会重新核验版本号和
两个唯一索引；只有完整结构已由另一方提交时才继续启动。

迁移不会静默删除或合并历史作答。若旧数据库存在重复 attempt 或 answer 身份，启动会在
创建索引前失败，并列出最多 3 组冲突键。请先备份数据库，根据提示人工核对和清理重复行，
再重新启动。该失败路径不会改写旧业务数据，也不会把迁移版本标记为已完成。
