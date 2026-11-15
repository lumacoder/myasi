# myasi 设计说明

> 一个 GitHub 仓库管理常用的 skills、MCP 配置和 CLI 清单，按裸名同步到 Codex、Claude Code、pi、DeepSeek Harness（dsh）和 deepseek TUI。
> 标注：【已验证】查过官方文档或源码；【未验证】需要实测。

## 1. 结论

- **一个总仓库**（monorepo）。不拆成一个 skill 一个仓库，也不用 git submodule。
- **skills 只保留一份**：`skills/<name>/SKILL.md`，遵循 Agent Skills 开放标准。安装时用链接（Windows 用 junction）挂到 `~/.agents/skills`；Codex、pi、dsh、deepseek TUI 都读这个目录，Claude Code 不读，所以再挂一份到 `~/.claude/skills`。
- **按名获取**：用户只说裸名，`myasi get <name>` 只拉这一个目录；`npx skills`、Claude 插件市场也能按名装。
- **MCP 只有一个配置源**：`mcp/servers.yaml`，由 `myasi mcp apply` 生成各端格式，密钥只写 `${ENV}` 引用。
- **CLI 用清单管理**：`winget import`、`brew bundle`、npm / uv 全局清单。

## 2. 各端 skill 目录【已验证】

| 端 | 用户级目录 | 读 `~/.agents/skills`？ | 备注 |
|---|---|---|---|
| Claude Code | `~/.claude/skills` | 不读（anthropics/claude-code#56193） | 支持符号链接；插件市场 `.claude-plugin/marketplace.json` |
| Codex | `~/.agents/skills` | 读 | `~/.codex/skills` 是旧路径；可选 `agents/openai.yaml` |
| pi | `~/.pi/agent/skills` | 读 | `/skill:name` 强制调用 |
| DeepSeek Harness `dsh` | `~/.dsh/skills` | 读 | `customSkillDirs` 可加目录 |
| deepseek TUI（社区） | `~/.deepseek/skills` | 读（也读 `~/.claude/skills`） | MCP 在 `~/.deepseek/mcp.json` |

`doctor` 会检查旧路径（`~/.codex/skills`、`~/.pi/agent/skills`、`~/.deepseek/skills`、`~/.dsh/skills`）里和 `~/.agents/skills` 同名的 skill，避免同一个 skill 被读到两次。

## 3. 名字解析

- `scripts/build_registry.py` 扫描 `skills/*/SKILL.md`、`skill.json`、`profiles/`、`catalog/external.yaml`，生成 `registry.json` 和 `.claude-plugin/marketplace.json`。CI 用 `--check` 保证它们是最新的。
- 裸名是唯一键；`skill.json` 的 `aliases` 用于改名后兼容旧名。名字和别名都不区分大小写。
- 找不到时用 difflib 给出最接近的 3 个名字，并且**在动磁盘之前**解析完全部名字，拼错一个就什么都不装。

## 4. 只拉一个目录

| 情况 | 做法 |
|---|---|
| 有 git | `git clone --depth 1 --filter=blob:none --sparse`，再 `git sparse-checkout add skills/<name>`。只下载根目录文件和这个目录的内容。缓存在 `~/.myasi/cache/`，删除最后一个 skill 时缓存一并删除。 |
| 没有 git | 下载 codeload tarball（一次运行只下载一次），只解压 `skills/<name>/`；跳过链接成员和 `..` 路径。 |
| 本地克隆 / `file://` | 直接链接或拷贝，开发时用 `--source .`。 |

私有仓库：git 路径用系统凭据，或者 `GITHUB_TOKEN` / `GH_TOKEN` 通过环境变量传给 git（不进 argv，不写 `.git/config`），HTTP 只把 token 发给 GitHub 域名。

安装记录 `~/.myasi/state.json`：每个 skill 的目标路径、模式（link/copy）、端、版本、来源（`source_spec`）。`update` 回到记录的来源；`remove` 只删 myasi 装的东西，拷贝模式还会核对 SKILL.md 的 name。

## 5. MCP 生成

| 端 | 目标 | 说明 |
|---|---|---|
| codex | `~/.codex/config.toml` | 只替换 `# >>> managed-by: myasi` 区块；同名的非托管表直接报错。`${VAR}` 转为 `env_vars` / `bearer_token_env_var` / `env_http_headers`。 |
| claude | `claude mcp add-json <name> '<json>' -s user` | `--write` 时执行，需要 `claude` 在 PATH。 |
| deepseek / cursor / gemini | `~/.deepseek/mcp.json`、`~/.cursor/mcp.json`、`~/.gemini/settings.json` | 合并进 `mcpServers`，其他键保留。Cursor 用 `${env:VAR}`，Gemini 的 HTTP 用 `httpUrl`。 |
| dsh / pi | — | 格式【未验证】，只打印中性 JSON，不写文件。 |

`verified: false` 的条目默认跳过，`--include-unverified` 才输出。默认 dry-run，`--write` 才写。

## 6. 不做什么

- 不复制第三方 skill：`catalog/external.yaml` 只记来源，安装前要 `--yes`。
- 不保存任何密钥；不管理全局 AGENTS.md / CLAUDE.md（以后可以考虑 chezmoi 或 rulesync）。
- 不删除用户自己放进各端目录的 skill。

## 7. 待定

- dsh、pi 的 MCP 配置格式需要实测后再支持 `--write`。
- 大素材（> 5MB）的存放方式：GitHub Release 或外部存储。
- 可选兼容层：rulesync（生成各端规则）、1mcp（MCP 聚合）。

## 来源

- Agent Skills 规范：https://agentskills.io/specification
- Claude Code skills：https://code.claude.com/docs/en/skills ；插件市场：https://code.claude.com/docs/en/plugins/marketplace-reference
- Codex skills：https://developers.openai.com/codex/skills
- pi：https://github.com/earendil-works/pi
- DeepSeek Harness：https://github.com/deepseek-ai/deepseek-harness
- git sparse-checkout：https://git-scm.com/docs/git-sparse-checkout
- 相关工具：https://github.com/vercel-labs/skills ，https://github.com/dyoshikawa/rulesync
