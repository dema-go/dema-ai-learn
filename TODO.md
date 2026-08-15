# TODO

用于记录项目后续待完成的工作项。完成后请勾选对应条目，并补充关联提交或 PR。

## UI 优化

- [ ] 优化选项宽度和按钮之间的距离，统一不同页面的视觉间距，并检查手机端的可读性与可点击性。（进行中：分支 `codex/ui-spacing-redesign`）

## 工程基建（P1/P2 候选项）

- [ ] 锁文件：后端依赖固定版本（或 uv/requirements.lock），小程序生成 package-lock.json
- [ ] lint/格式门禁：后端 ruff + mypy，小程序 prettier/eslint，pre-commit 钩子
- [ ] 交接物模板：`docs/handoffs/` 固定格式 + 每个 worktree 的 STATUS.md
- [ ] AGENTS.md「当前仓库与协作状态」改为命令式获取，避免静态快照过期
- [ ] 轻量 ADR：`docs/adr/` 记录已否决方案（Skyline、Taro、LangGraph Platform 等）
- [ ] 拆分 `backend/AGENTS.md` 与 `miniprogram/AGENTS.md`，根文件只留入口
- [ ] 隐私清理任务：定期物理删除过期 material 与 event 行（当前只在读取时判断 expire_at）
- [ ] 依赖更新提醒（renovate/dependabot），触发 AGENTS.md「版本变化需重新核验」
