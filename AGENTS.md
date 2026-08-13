# AGENTS.md

本文档是所有进入本仓库的 AI Agent、开发者和自动化工具的项目入口说明。开始任何非平凡工作前，请先完整阅读本文，再按“权威资料”章节读取与任务相关的文档。

## 1. 项目背景

项目暂名 **「考我一下」**，目标是开发一个微信 AI 闯关学习小程序。

一句话定位：**微信里最快的可溯源读后自测——只根据用户提供的内容出题，约 3 分钟完成一关，每道题都能回到原文，之后只复测错题。**

核心流程：

```text
粘贴文本或公开网页链接
  → AI 理解材料并生成 5–7 道题
  → 自动校验题目质量
  → 用户逐题作答并获得即时反馈
  → 查看原文依据
  → 通关结果与错题复测
  → 再次提交新材料
```

首批用户是 18 岁以上的泛知识自学者，优先关注职业技能、产品技术、行业资料和考证补充阅读。

首版只支持：

- 粘贴文本，最多 8,000 个中文字符；
- 无需登录、付费或验证码的公开网页链接；
- 单选题和判断题；
- 每题绑定原文依据 `source_span`；
- 即时正误反馈、题目纠错、结果页和错题复测。

首版明确不做：全网搜索、知识库 RAG、PDF/Word/PPT 实际解析、图片 OCR、视频音频、多人 PK、排行榜、复杂 VIP、企业后台。原型中拍照和文件入口可以出现，但必须禁用并标记“敬请期待”。

## 2. 核心产品原则

所有实现和设计决策都应服务以下原则：

1. **严格限源**：不得使用材料外知识补充答案。
2. **完成优先**：默认一局 5–7 题、约 3 分钟，不堆参数和工具入口。
3. **证据优先**：每题都能查看最短、直接支持答案的原文片段。
4. **拒绝优先**：材料不适合时少出题或拒绝，不生成凑数题。
5. **复用优先**：通关后的第一行动是错题复测或再考一篇，不是分享。
6. **分享自愿**：禁止分享解锁、分享奖励和其他诱导分享设计。
7. **不夸大效果**：不得宣称用户已经“掌握”“学会”或系统“零幻觉”。
8. **隐私默认**：材料默认私有、短期保存、用户可主动删除。

## 3. 权威资料与阅读顺序

根据任务类型阅读以下文件：

1. `需求分析.md`：产品范围、核心流程、MVP、风险、指标和明确不做事项。产品决策以此为基础。
2. `技术方案.md`：微信原生小程序、FastAPI、LangGraph、模型、任务轮询、数据表与部署方案。
3. `UI原型图.md`：32 个正式 UI 画板总览、页面锚点、状态说明、开发映射、实施优先级与验收清单。开始 UI、前端或接口联调工作时必须阅读。
4. `docs/superpowers/specs/2026-08-13-ai-quest-miniapp-ui-design.md`：已由用户确认的正式 UI 原型规范。
5. `docs/superpowers/plans/2026-08-13-ai-quest-html-prototypes.md`：Codex HTML 原型实施计划。
6. `UI竞品设计调研.md`：AI 学习和游戏化学习产品的 UI 调研。
7. `竞品调研资料.md`：产品、市场、学习科学、合规与单位经济性证据。

若文档间存在冲突，使用以下优先级：

```text
用户最新明确决定
  > 本 AGENTS.md 中记录的已确认决策
  > UI原型图.md
  > ai-quest-miniapp-ui-design.md
  > 需求分析.md
  > 技术方案.md
  > 旧设计稿或参考原型
```

发现仍无法解决的实质冲突时，不要自行选择会改变产品范围的方案；列出冲突和影响后询问用户。

## 4. 已确认的 UI 与品牌方向

- 临时产品名：**考我一下**。
- 口号：**把刚读的，考明白。**
- 原创角色：**考考**，定位为会陪用户犯错、核查证据的学习搭档，不是老师。
- 风格：大胆卡通的“爆笑练习册”，面向仍有童心的成年人。
- 视觉原则：**界面负责阅读，SVG 负责卡通。**
- 主色系统：暖纸底 `#FBF7EE`、珊瑚红 `#DE5848`、薄荷青 `#78CDBF`、奖励黄 `#FFD45A`、正文深灰 `#24292D`。
- 字体：高可读系统无衬线中文字体；不得用楷体、仿宋或手写字体承载标题、题干、正文、选项和按钮。
- 可使用原创内联 SVG 绘制“考考”的不同表情和动作。
- 不得复制《阿衰》的角色外形、服装、姓名、标志性构图、台词或封面字体。

首页采用“任务优先型”：

1. 有错题时优先显示错题复测；
2. 否则有未完成任务时显示继续闯关；
3. 否则显示创建新闯关。

用户识别采用静默 `openid`。昵称、头像和订阅提醒只在需要时显式授权，均可跳过。

## 5. 原型文件来源，禁止混淆

`prototypes/` 中存在两套不同来源的原型。

### Claude Code 早期参考稿

以下文件由 Claude Code 生成，只作为历史参考保留：

- `prototypes/core-flow.html`
- `prototypes/extended-features.html`
- `prototypes/states-compliance.html`
- `prototypes/styles.css`

不要把其中的“读后闯关 / 小衰 / 活力橙”当作正式品牌与视觉规范，也不要直接覆盖这些文件。

### Codex 正式原型

正式原型已通过 GitHub PR #1 合入 `main`；原开发分支为 `codex/html-prototypes`：

- `UI原型图.md`
- `prototypes/codex-core-flow.html`
- `prototypes/codex-records-share.html`
- `prototypes/codex-settings-future.html`
- `prototypes/codex-styles.css`
- `prototypes/codex-app.js`
- `docs/assets/ui-prototypes/core-flow.png`
- `docs/assets/ui-prototypes/records-share.png`
- `docs/assets/ui-prototypes/settings-future.png`
- `tests/test_prototypes.py`
- `docs/prototype-verification.md`

`UI原型图.md` 是后续开发的统一页面索引。实现页面、设计接口或拆分任务时，必须使用其中的画板 ID 和业务状态，不要只凭截图猜测功能。

主目录的 `main` 工作树现在可以直接查看和启动这些正式文件。历史功能分支与 worktree 仅用于追溯，不应作为后续开发基线。

## 6. Git 与 Worktree 开发规范

### 6.1 基本原则

- `main` 始终保持可验证、可集成状态，不直接承载未完成开发。
- 每项独立功能使用独立分支和独立 worktree。
- 一个分支不能同时被两个 worktree 检出。
- `.worktrees/` 已被 Git 忽略，所有项目本地 worktree 默认放在这里。
- 禁止使用 `git reset --hard`、`git checkout --` 等破坏性命令清理不属于自己的改动。
- 不得覆盖、删除或顺手提交其他 Agent 的未完成修改。
- 开发前检查 `git status -sb`、当前分支和现有 worktree。

### 6.2 创建 worktree

先更新 `main`，再创建语义明确的功能分支：

```bash
cd /path/to/dema-ai-learn
git status -sb
git pull --ff-only origin main
git worktree add .worktrees/backend -b agent/backend main
```

推荐命名：

```text
.worktrees/miniprogram/    agent/miniprogram
.worktrees/backend/        agent/backend
.worktrees/integration/    agent/integration
```

若同名分支或目录已经存在，先运行 `git worktree list` 和 `git branch -avv` 查明归属，不要强制覆盖。

### 6.3 Worktree 的隔离范围

Worktree 隔离的是：

- 工作目录文件；
- 当前检出的分支；
- 未提交修改和索引状态。

Worktree 不隔离：

- Git 对象和提交历史；
- 本机网络与端口；
- 系统进程；
- 外部数据库、缓存或云资源。

因此，前端 worktree 看不到后端分支尚未合入的源文件，但前端进程仍可通过 `localhost` 访问后端 worktree 启动的服务。

### 6.4 多 Agent 并行开发

建议结构：

```text
main
 ├─ agent/miniprogram    微信小程序前端
 ├─ agent/backend        FastAPI + LangGraph 后端
 └─ agent/integration    合并前后端进行联调
```

Agent 只能修改自己任务范围内的 worktree。涉及共享 API 时，先约定接口契约，优先使用：

- `openapi.json` 或 OpenAPI 文档；
- 固定的请求/响应示例；
- 共享 TypeScript/Pydantic 类型；
- 前端 mock 数据与后端契约测试。

不要为了临时联调把对方所有未完成代码合入自己的功能分支。需要统一文件视图时，创建 `agent/integration` 分支，将前后端功能分支合入后再联调。

## 7. 前后端同时启动与资源隔离

### 7.1 分别从不同 worktree 启动

示例：

```bash
# 终端 A：后端 worktree
cd .worktrees/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 B：前端 worktree
cd .worktrees/miniprogram
npm run dev -- --port 3000
```

前端访问 `http://127.0.0.1:8000` 即可。代码不需要处于同一目录。

微信小程序正式联调时，还需遵守微信开发者工具、合法域名和云托管约束；本地 HTML 原型可用静态服务器：

```bash
cd .worktrees/codex-html-prototypes
python3 -m http.server 4173
```

### 7.2 端口约定

默认建议：

| 服务 | 端口 |
| --- | --- |
| HTML 原型 | `4173` |
| Web/小程序辅助前端 | `3000` |
| FastAPI 后端 | `8000` |
| 前端 mock API | `8001` |

启动前检查端口是否被占用。多个 Agent 同时启动同类服务时，必须分配不同端口并在交接说明中记录。

### 7.3 环境与数据

- `.env`、模型密钥、数据库密码不得提交到 Git。
- 每个 worktree 通常拥有独立的 `node_modules`、Python 虚拟环境和本地构建产物。
- 可维护无敏感信息的 `.env.example` 说明变量名。
- 并行测试共享数据库时，使用不同数据库名、schema 或测试前缀，防止数据互相污染。
- 不要让测试默认连接生产数据库、生产模型额度或真实微信用户数据。

## 8. 技术方向

当前技术方案的目标架构：

- 微信小程序原生 + TypeScript；
- TDesign 小程序组件库；
- 首版 WebView 渲染；
- Python 3.11+；
- FastAPI；
- LangGraph + LangChain；
- 主力模型 DeepSeek strict tool calling，备用 GLM；
- MySQL；
- 微信云托管；
- 生成流程采用后台任务 + 轮询，不依赖 SSE。

模型和第三方依赖版本、价格、平台规则可能变化。涉及这些时必须重新核验官方资料，不要仅凭本文中的历史结论升级或替换。

## 9. 开发、测试与提交规范

### 9.1 开发前

1. 阅读本文件和任务相关的权威文档。
   UI、微信小程序前端或前后端联调任务还必须阅读 `UI原型图.md`。
2. 检查 `git status -sb`、当前分支和 worktree。
3. 明确本次任务的文件范围和验收标准。
4. 先确认是否已有测试、实施计划或未完成 PR。
5. 若发现用户或其他 Agent 的未提交改动，保留并避开；无法避开时停止并说明。

### 9.2 实现中

- 新功能或修复优先采用测试先行：先写会因缺少行为而失败的测试，再实现最小正确行为。
- 不为通过测试而缩减用户明确要求的范围。
- 交互原型必须在真实浏览器中检查，而不仅是静态搜索 HTML。
- 所有 AI 题目、解释和结果页面必须保留 AI 生成提示与原文依据入口。
- 正误状态除颜色外还需图标和文字提示。
- 支持键盘焦点和 `prefers-reduced-motion`。

### 9.3 提交前

至少执行与改动匹配的验证：

```bash
git diff --check
git status -sb
```

当前 HTML 原型测试：

```bash
python3 -m unittest tests/test_prototypes.py -v
```

未来后端和小程序建立正式测试命令后，应在此补充，并优先运行项目统一入口。

浏览器 UI 改动至少验证：

- 页面不是空白页；
- 控制台无相关错误；
- 主流程交互真实改变 UI 状态；
- 桌面和移动端无横向溢出、遮挡或不可点击元素；
- 错误态和空状态具有明确下一步。

### 9.4 提交与 PR

- 提交只包含当前任务范围内的文件。
- 使用清晰的小提交，例如：`feat: add quiz generation task API`。
- 推送功能分支后创建面向 `main` 的 PR。
- PR 描述需说明：改了什么、为什么、用户影响、验证命令和已知限制。
- 默认保留 worktree 以便处理 PR 反馈；合并且验证后再删除。
- 不得在未获得用户授权时自行合并、强推或删除远程分支。

## 10. 当前仓库与协作状态

- GitHub：`dema-go/dema-ai-learn`，私有仓库。
- 默认分支：`main`。
- 正式 HTML 原型已合入默认分支 `main`。
- 历史开发分支：`codex/html-prototypes`。
- 已完成的正式 HTML 原型 PR：`https://github.com/dema-go/dema-ai-learn/pull/1`。
- 正式原型共 3 组、32 个画板，统一索引为 `UI原型图.md`。
- 正式原型已完成 8 项契约测试、3 张 1440 px 总览图和 1440 / 900 / 390 px 浏览器验证。

开始新任务前必须重新运行 `git status`、`git worktree list` 和远程 PR 检查；本节记录的是编写本文时的状态，可能已经变化。

## 11. Agent 交接清单

结束任务前，在回复或项目文档中交代：

1. 使用的 worktree 路径和分支；
2. 创建、修改和删除的文件；
3. 已运行的测试及结果；
4. 启动命令、端口和必要环境变量；
5. 未解决问题与已知限制；
6. 提交哈希、远程分支和 PR 地址；
7. 是否仍有后台服务运行；
8. 是否存在需要下一个 Agent 避开的用户改动。

不要仅回复“已完成”。后续 Agent 应能仅依靠仓库、提交记录和交接信息恢复上下文并继续工作。
