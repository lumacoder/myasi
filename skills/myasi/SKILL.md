---
name: myasi
description: 当用户按名字提到一个本机没有的 skill（如“用 xxx skill”“装上 xxx”“有没有做某事的 skill”），或要同步、更新、删除 skill，或要把 MCP/CLI 配置同步到 Codex、Claude Code、pi、DeepSeek（dsh / deepseek TUI）时使用；通过 myasi 仓库的 registry.json 按裸名解析并安装，然后加载对应 SKILL.md。
---
# myasi｜按名获取 skill

用户只说**裸名**（如 `hello-myasi`），`skills/<name>/` 只是仓库内部存放位置，不要让用户提供路径。

## 规则
1. 先看本机是否已装：`~/.agents/skills/<name>/SKILL.md`（Codex / pi / dsh / deepseek TUI）或 `~/.claude/skills/<name>/SKILL.md`（Claude Code）。已装就直接读取并执行。
2. 没装：`myasi info <name>` 解析名字/别名（例如 `hello` → `hello-myasi`），再 `myasi get <name> --agent <当前端>`，装好后读取它的 SKILL.md 执行。
   - 当前端：Codex=`codex`，Claude Code=`claude`，pi=`pi`，DeepSeek Harness=`dsh`，deepseek TUI=`deepseek`。
   - 没有 `myasi` 命令时：`npx skills add lumacoder/myasi --skill <name> -g -y`。
3. 找不到：运行 `myasi search <关键词>`，列出最接近的 3 个让用户选，**不要猜路径**。
4. 第三方 skill（`myasi list` 中 kind=ext）需要用户同意后才加 `--yes` 安装，并说明许可证。
5. 删除只用 `myasi remove <name>`，它只删 myasi 自己装的；不要手动删用户目录。
6. MCP 先 `myasi mcp apply --agent <端>` 预览，用户确认后才加 `--write`；密钥只用 `${ENV}` 引用，绝不写明文。
7. 用户要新建自己的 skill：在 myasi 克隆里运行 `myasi new <name> -d "<何时使用>"`，再 `python scripts/validate.py`。

## 常用命令
```
myasi list [--tag example] [--profile core]   myasi search 示例
myasi info hello-myasi                         myasi get hello-myasi --agent codex
myasi update [name]                            myasi remove hello-myasi
myasi sync [--prune]                           myasi doctor
myasi mcp apply --agent codex [--write]        myasi cli [--run]
myasi new <name> -d "<何时使用>"
```
