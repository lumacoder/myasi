# AGENTS.md — myasi

## 用户按名提到 skill 时
用户只说裸名（如“用 hello-myasi”），不要让用户给路径。
1. 先查本机：`~/.agents/skills/<name>/SKILL.md`（Codex/pi/dsh/deepseek TUI）或 `~/.claude/skills/<name>/SKILL.md`（Claude Code）。已装就读取并执行。
2. 未装：`myasi info <name>`（按 `registry.json` 的 name/aliases 解析，如 hello → hello-myasi），再 `myasi get <name> --agent <当前端>`，然后加载它的 SKILL.md。没有 myasi 时用 `npx skills add lumacoder/myasi --skill <name> -g -y`。
3. 找不到：`myasi search <词>` 列出最接近的 3 个，不要猜路径。
4. 第三方 skill（kind=ext）先说明来源和许可证，用户同意后才 `--yes`。
5. MCP 先 `myasi mcp apply --agent <端>` 预览，确认后才 `--write`；不写明文密钥。

## 在本仓库里开发
- 新建 skill：`python scripts/myasi.py new <name> -d "<何时使用>"`（规范布局：`SKILL.md`、`skill.json`、`agents/openai.yaml`，按需配 `README.md` 与 `CHANGELOG.md`）。
- 顶层文档分工：`README.md`（门面概览）、`docs/GUIDE.md`（完整 CLI/MCP/开发手册）、`docs/DESIGN.md`（架构设计），勿重复堆砌。
- 新增或修改 skill 后运行：`python scripts/build_registry.py && python scripts/validate.py && python -m unittest discover -s tests`。
- `registry.json` 和 `.claude-plugin/marketplace.json` 由脚本生成，不要手改。
- 只用 Python 标准库，兼容 3.8；单个 skill ≤ 5MB；不提交 zip、构建产物、备份、`.env`、`__pycache__`。
- 测试用临时 HOME 和 `--source .`，结束后删除临时目录。
