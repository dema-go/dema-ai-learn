# UI 原型图资产

本目录存放 `UI原型图.md` 使用的正式 HTML 原型总览图。

截图来源：

| 文件 | 来源页面 | 画板 |
| --- | --- | ---: |
| `core-flow.png` | `prototypes/codex-core-flow.html` | 13 |
| `records-share.png` | `prototypes/codex-records-share.html` | 9 |
| `settings-future.png` | `prototypes/codex-settings-future.html` | 10 |

重新生成时，在正式原型 worktree 根目录启动静态服务：

```bash
python3 -m http.server 4173
```

再使用 Chromium 以 1440 px 宽度截取对应页面的完整高度。若页面布局发生变化，必须重新确认实际 `scrollHeight`，不要沿用旧高度。

这些 PNG 是文档预览资产；交互和细节评审仍以对应 HTML 为准。
