# 考我一下

微信里最快的可溯源读后自测：只根据用户提供的内容出题，约 3 分钟完成一关，每道题都能回到原文，之后只复测错题。

口号：**把刚读的，考明白。**

进入仓库的 Agent 与开发者请先读 [`AGENTS.md`](./AGENTS.md)，产品范围以 [`需求分析.md`](./需求分析.md) 为准，页面以 [`UI原型图.md`](./UI原型图.md) 为准。

## 当前状态

本地可跑通 P0+P1：

1. 粘贴文本或公开网页链接
2. AI 生成 5–7 道单选 / 判断题
3. 每题绑定原文依据 `source_span`
4. 即时正误反馈、结果页、错题复测
5. 记录、额度、隐私删除

尚未接入：微信云托管、正式登录、分享落地、订阅提醒、MySQL、PDF / 拍照解析。

## 仓库结构

```text
backend/          FastAPI + LangGraph + DeepSeek
miniprogram/      微信原生小程序（TypeScript）
contracts/        OpenAPI 契约
prototypes/       正式 HTML 原型（Codex）与早期参考稿
docs/             设计规范、实施计划、原型总览图
```

## 本地启动

### 0. 一键安装（推荐）

```bash
make setup    # 创建后端 venv + 安装后端与小程序依赖
```

之后常用命令：

```bash
make test     # 全部测试（后端 + 契约漂移 + 原型 + TS 类型检查）
make dev      # 启动后端 127.0.0.1:8000
make proto    # 启动 HTML 原型 127.0.0.1:4173
make help     # 列出全部目标
```

### 1. 后端

（手工方式；等价于 `make setup && make dev`）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

在 `.env` 填入 `DEEPSEEK_API_KEY`。没有 Key 时后端会走限源 Fixture 模型，题目能出但不走真实 DeepSeek。

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

健康检查：<http://127.0.0.1:8000/health>

**不要把 `.env` 提交到 Git。** 根目录与 `backend/.gitignore` 都已忽略它。

本地数据库默认落在 `backend/local.db`（路径锚定 backend/ 目录，与启动时的工作目录无关）；`DATABASE_URL` 环境变量可覆盖。

DeepSeek V4 Flash 默认开思考模式，结构化出题必须关闭思考：

```text
extra_body={"thinking": {"type": "disabled"}}
```

适配器里已经这样配置。开发期用户识别请求头：`X-Dev-Openid`。

### 2. 微信小程序

1. 打开微信开发者工具
2. 导入本仓库根目录，或导入 `miniprogram/`
3. AppID 可用测试号 / `touristappid`
4. 详情 → 本地设置 → 勾选「不校验合法域名」
5. 用**模拟器**编译，不要用真机预览（真机访问不了 `127.0.0.1`）

小程序请求 `http://127.0.0.1:8000`。每日生成额度 3 次（Asia/Shanghai）。

### 3. HTML 原型

```bash
python3 -m http.server 4173
```

打开 `prototypes/codex-core-flow.html`。不要把早期 `prototypes/core-flow.html` 当成正式视觉规范。

## 测试

```bash
make test        # 一键全部：后端 + 契约漂移 + 原型 + TS 类型检查
make verify      # make test + git diff --check（提交前必跑）
```

等价的手工命令：

```bash
cd backend && pytest tests/ -q              # 后端单元测试 + 契约漂移检测
python3 -m unittest tests/test_prototypes.py -v
cd miniprogram && npx tsc --noEmit
```

后端单元测试强制使用 Fixture 模型，不会消耗 DeepSeek 额度。`backend/tests/test_contract.py` 会把 `contracts/openapi.yaml` 与 FastAPI 运行时 schema 逐接口比对，改接口时必须同步更新契约。

每次 push 到 `main` 和每个 PR 都会在 GitHub Actions 上自动跑同一套检查（`.github/workflows/ci.yml`）。

## 产品原则（摘要）

- 严格限源，不用材料外知识补答案
- 每题必须能回到原文
- 材料不适合时少出题或拒绝，不凑数
- 不宣称「掌握」「学会」「零幻觉」
- 禁止分享解锁 / 分享奖励
- 材料默认私有、短期保存，用户可删除

## 已知限制

- 出题目前在生成接口内同步完成；长文本 + 真实模型可能接近小程序 60 秒超时，生产环境需要后台任务
- 本地 SQLite，尚未接云托管与 MySQL
- 结果页「分享结果」仅提示「分享稍后开放」
