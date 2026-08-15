# 考我一下 —— 一键开发/验证入口
# 用法：make help 查看全部目标；make setup 一次装好全部依赖。

PY := backend/.venv/bin/python

.PHONY: setup test test-backend test-contract test-prototypes test-miniprogram test-types verify dev proto clean help

setup: ## 创建后端 venv + 安装后端/小程序依赖
	python3 -m venv backend/.venv
	$(PY) -m pip install -e "backend[dev]"
	cd miniprogram && npm install

test: test-backend test-prototypes test-miniprogram ## 运行全部测试套件

test-backend: ## 后端测试（含契约漂移检测，强制 Fixture 模型）
	cd backend && .venv/bin/python -m pytest tests/ -q

test-contract: ## 只跑契约漂移检测
	cd backend && .venv/bin/python -m pytest tests/test_contract.py -q

test-prototypes: ## HTML 原型验证
	$(PY) -m unittest tests/test_miniprogram_ui.py tests/test_prototypes.py -v

test-miniprogram: ## 小程序状态测试与 TypeScript 类型检查
	cd miniprogram && npm test && npm run typecheck

test-types: ## 小程序 TypeScript 类型检查
	cd miniprogram && npm run typecheck

verify: test ## 全部测试 + 空白错误检查（提交前必跑）
	git diff --check

dev: ## 启动后端 http://127.0.0.1:8000
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

proto: ## 启动 HTML 原型 http://127.0.0.1:4173
	python3 -m http.server 4173

clean: ## 删除本地虚拟环境与 node_modules
	rm -rf backend/.venv miniprogram/node_modules

help: ## 列出全部目标
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'
