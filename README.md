# 考我一下

微信里最快的可溯源读后自测：只根据用户提供的内容出题，约 3 分钟完成一关，每道题都能回到原文，之后只复测错题。

口号：**把刚读的，考明白。**

进入仓库的 Agent 与开发者请先读 [`AGENTS.md`](./AGENTS.md)，产品范围以 [`需求分析.md`](./需求分析.md) 为准，页面以 [`UI原型图.md`](./UI原型图.md) 为准。

## 当前状态

本地可跑通 P0+P1：

1. 粘贴文本或公开网页链接
2. AI 生成 5–7 道单选 / 判断题
3. 每题绑定原文依据 `source_span`
4. 点选选项后立即判题，在选项原位显示勾 / 叉、正确答案与解释
5. 记录、额度、隐私删除

答题页选项接近屏幕全宽，选项间距为 `16px`；普通同组按钮间距为 `12px`，主行动组与次行动组间距为 `20px`。“下一题 / 查看结果”固定在底部，不需要为继续答题反复向下滚动。

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

### 1. 后端

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

微信基础库默认给普通 `button` 注入 `184px` 固定宽度和左右自动外边距，优先级高于单个类选择器。项目通过 `.screen .btn` 与 `.choice-list .choice-card` 覆盖该规则。调整按钮宽度或间距后，必须在开发者工具的 WXML 计算样式和手机模拟器中复核；仅检查源文件中的 `width: 100%` 不足以证明真实布局正确。

开发者工具导入项目时可能自动改写 `project.config.json` 或 `project.private.config.json`。验证结束前请检查 `git diff`，不要提交仅由本机工具产生的项目名、基础库版本或格式变化。

### 3. HTML 原型

```bash
python3 -m http.server 4173
```

打开 `prototypes/codex-core-flow.html`。不要把早期 `prototypes/core-flow.html` 当成正式视觉规范。

## 测试

```bash
python3 -m unittest tests/test_miniprogram_ui.py tests/test_prototypes.py -v
cd miniprogram && npm test
cd backend && pytest tests/ -q
```

小程序测试覆盖即时判题状态、丢失响应后的服务端选项恢复和关键布局契约。后端单元测试强制使用 Fixture 模型，不会消耗 DeepSeek 额度。

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
- 版本化轻量迁移可检测旧库重复答题身份并拒绝静默清理；两个进程同时初始化全新空数据库时，基础表 `create_all()` 的 DDL 仍未专门串行化
- 结果页「分享结果」仅提示「分享稍后开放」
