# myasi 使用与开发指南

> 导航：[首页](../README.md) · **使用与开发指南** · [架构与协议设计](DESIGN.md)

---

## 1. Skill 管理命令

```bash
# 检索与查看
myasi list [--tag web] [--profile core] [--installed] [--json]
myasi search 滚动                      # 按名称、别名、标签、简介搜索
myasi info devasi                      # 支持别名解析（devasi → mano-asi）

# 安装与更新
myasi get mano-asi                     # 默认链接安装到 ~/.agents/skills + ~/.claude/skills
myasi get mano-asi --agent codex       # codex | claude | pi | dsh | deepseek | all（支持逗号组合）
myasi get mano-asi --copy              # 独立拷贝（默认 --link 指向 ~/.myasi/cache）
myasi get --profile core,example       # 按 profile 批量安装
myasi get <第三方名> --yes             # 第三方 skill（catalog/external.yaml）需 --yes 确认许可
myasi update [name]                    # 回到 ~/.myasi/state.json 记录的 source_spec 拉取更新

# 同步、诊断与卸载
myasi sync [--prune]                   # 按 profiles/clients.yaml 幂等对齐（--prune 清理多余托管项）
myasi doctor [--strict]                # 检查失效链接、旧路径同名冲突与安装状态
myasi remove mano-asi [--agent claude] # 仅删除 myasi 自己安装的目录/链接
```

### 切换来源、分支与私有仓库

| 环境变量 / 参数 | 用途 | 示例 |
|---|---|---|
| `--source` / `MYASI_SOURCE` | 指定仓库（`owner/name`、Git URL、`file://`、本地路径） | `myasi get mano-asi --source .` |
| `--ref` / `MYASI_REF` | 指定分支或标签 | `myasi get my-skill --ref dev` |
| `MYASI_AGENT` | 默认目标端 | `export MYASI_AGENT=claude` |
| `GITHUB_TOKEN` / `GH_TOKEN` | 私有仓库只读凭据（不写入仓库或 URL） | `$env:GITHUB_TOKEN="github_pat_..."` |
| `MYASI_RAW_URL` | 安装脚本/镜像源前缀 | `export MYASI_RAW_URL=https://...` |

> 在本地克隆目录中直接运行 `bin/myasi`（或 `python scripts/myasi.py`）时，自动使用当前克隆作为来源；安装记录保存在 `~/.myasi/state.json`。

---

## 2. MCP 与 CLI 同步

### MCP 配置（唯一真源：`mcp/servers.yaml`）

```bash
myasi mcp apply --agent codex          # 默认 dry-run 预览，不写入本机
myasi mcp apply --agent codex --write  # 确认后写入目标端配置
myasi mcp apply --agent all --include-unverified
```

- **密钥零落地**：`mcp/servers.yaml` 内所有凭据统一写成 `${ENV_VAR}` 占位符，由 `scripts/validate.py` 强制拦截明文密钥。
- **各端写入格式**：
  - **Codex**：只更新 `~/.codex/config.toml` 的 `# >>> managed-by: myasi` 区块，`${VAR}` 转为 `env_vars`。
  - **Claude Code**：`--write` 时调用 `claude mcp add-json <name> '<json>' -s user`。
  - **Cursor / Gemini / deepseek TUI**：合并进对应 `mcp.json` / `settings.json` 的 `mcpServers` 字段。
  - **pi / dsh**：当前仅打印中性 JSON（不自动写入）。

### CLI 装机清单（`cli/`）

```bash
myasi cli                              # 预览当前系统将执行的命令（dry-run）
myasi cli --os windows --run           # 实际执行安装
```

| 清单文件 | 对应工具 |
|---|---|
| `cli/windows/winget.json` | `winget import` |
| `cli/macos/Brewfile` | `brew bundle` |
| `cli/npm/global.txt` | `npm install -g` |
| `cli/uv/tools.txt` | `uv tool install` |

---

## 3. 添加或修改你自己的 Skill

1. **生成标准目录骨架**（会自动重生成 `registry.json` 与 `.claude-plugin/marketplace.json`）：
   ```bash
   python scripts/myasi.py new my-skill -d "什么时候用它（Agent 只看这句话决定是否加载）" --tags dev --alias old-name
   ```
   标准自有 Skill 结构：
   ```text
   skills/<name>/
   ├── SKILL.md            # 必填：YAML frontmatter（name = 目录名，description ≤ 1024 字符）
   ├── skill.json          # 推荐：version / tags / aliases / clients / license
   ├── agents/openai.yaml  # 推荐：Codex 界面显示名与默认提示词
   ├── README.md           # 可选：人类可读说明与运行命令
   └── CHANGELOG.md        # 可选：版本演进记录（避免把历史日志堆进 README）
   ```
2. **分配 Profile 或登记第三方 Skill**：
   - 需要随 `myasi sync` 默认安装时，将裸名写入 `profiles/core.txt` 或 `profiles/example.txt`（由 `profiles/clients.yaml` 映射各端）。
   - 第三方上游 skill 不拷贝源码，写入 `catalog/external.yaml` 并写明许可证。
3. **本地校验与试装**：
   ```bash
   python scripts/build_registry.py
   python scripts/validate.py
   python -m unittest discover -s tests
   ```
   > `registry.json` 与 `.claude-plugin/marketplace.json` 由脚本生成，切勿手改；单个 skill ≤ 5 MB，不提交 `.zip`、构建产物、`.env` 与 `__pycache__`。
4. **临时 `HOME` 冒烟验证**：用临时 `HOME` + `--source .` 试装，验证后删除临时目录再提交推送。
