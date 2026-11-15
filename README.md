# myasi

> **寓意：我的超级人工智能（My ASI）。** 一个仓库管理工作中常用的 skills、MCP 配置和 CLI 清单，按名同步到 Codex、Claude Code、pi、DeepSeek Harness（dsh）和 deepseek TUI，换电脑、换终端都能复用。

- **一个总仓库**：skills、MCP、CLI 放在一起，不是一个 skill 一个仓库。
- **只说名字**：用户和 agent 只用裸名，比如 `hello-myasi`；`skills/<name>/` 只是内部存放位置。
- **按需只拉一个目录**：有 git 时用局部克隆 + 稀疏检出，没有 git 时下载 tarball 只解压这一个目录。
- **零依赖**：`myasi` 是 Python 3.8+ 标准库单文件，Windows（`py`）、Linux、macOS 都能跑。
- **不碰密钥**：MCP 配置只写 `${ENV}` 引用；myasi 只删除自己装的东西。

> 现在仓库里有三个 skill：`myasi`（教 agent 按名找 skill 的元 skill）、`hello-myasi`（最小示例 / 模板）和 `mano-asi`（真实案例：全栈研发，别名 `devasi`，在 example profile 里）。自己的 skill 按下面「如何添加你自己的 skill」加进来。

## 快速开始

PowerShell（Windows）：
```powershell
irm https://raw.githubusercontent.com/lumacoder/myasi/main/scripts/install.ps1 | iex
myasi get hello-myasi
```

bash / zsh（Linux、macOS、Git Bash）：
```bash
curl -fsSL https://raw.githubusercontent.com/lumacoder/myasi/main/scripts/install.sh | sh
export PATH="$HOME/.myasi/bin:$PATH"    # 写进 ~/.bashrc 或 ~/.zshrc 永久生效
myasi get hello-myasi
```

安装脚本只下载 `myasi.py` 和包装脚本到 `~/.myasi/bin`，不克隆整个仓库；PowerShell 版会把它加进用户 PATH。仓库改为私有后，先设置只读 token：`$env:GITHUB_TOKEN="..."`（PowerShell）或 `export GITHUB_TOKEN=...`（bash）；git 路径也可以直接用本机的 Git Credential Manager。下载慢时可用 `MYASI_RAW_URL` 指向镜像。

不用 myasi 也能按名装：
```bash
npx skills add lumacoder/myasi --skill hello-myasi -g -a codex -y   # vercel-labs/skills
/plugin marketplace add lumacoder/myasi                              # Claude Code
/plugin install hello-myasi@myasi
```

## 按名获取

```bash
myasi list [--tag example] [--profile core] [--installed] [--json]
myasi search 示例                      # 按名字、别名、标签、简介搜索
myasi info hello-myasi                 # 也接受别名：myasi info hello
myasi get hello-myasi                  # 默认装到全部端：~/.agents/skills + ~/.claude/skills
myasi get hello-myasi --agent codex    # codex | claude | pi | dsh | deepseek | all，可逗号组合
myasi get hello-myasi --copy           # 默认 --link（指向 ~/.myasi/cache），--copy 为独立拷贝
myasi get --profile core,example       # 按 profile 批量装
myasi get <第三方名> --yes             # 第三方 skill（catalog/external.yaml）需 --yes 确认
myasi update [name]                    # 从当初安装的来源更新，只拉取已检出的目录
myasi remove hello-myasi [--agent claude]
myasi sync [--prune]                   # 按 profiles/clients.yaml 给每个端装齐，幂等
myasi doctor [--strict]                # 失效链接、同名重复、安装状态
myasi mcp apply --agent codex          # 预览 MCP 配置；确认后加 --write
myasi cli [--run] [--os windows]       # 按 cli/ 清单安装 CLI，默认只打印
myasi new <name>                       # 在本地克隆里新建 skill 骨架（见下文）
```

名字解析：`registry.json` 以裸名为唯一键，记录简介、标签、版本、路径、适用端、profile 和别名（例如 `hello → hello-myasi`）。找不到时给出最接近的 3 个名字，并且一个都不装。

来源默认是 `lumacoder/myasi`；可用 `--source` 或环境变量 `MYASI_SOURCE` 指向别的仓库（`owner/name`）、git URL、`file://` URL、本地裸仓库或本地克隆（在克隆里直接运行 `bin/myasi` 时自动使用该克隆）。`--ref` / `MYASI_REF` 选分支或标签，`MYASI_AGENT` 设默认端。安装记录在 `~/.myasi/state.json`（含来源，`update` 会回到同一来源）。

## 各端支持

| 端 | skill 目录 | 调用方式 | MCP（`myasi mcp apply`） |
|---|---|---|---|
| Codex | `~/.agents/skills` | `$name`、`/skills` | ✅ 写入 `~/.codex/config.toml` 的 myasi 托管区块，密钥用 `env_vars` 转发 |
| Claude Code | `~/.claude/skills` | `/name` | ✅ 生成 `claude mcp add-json … -s user` 命令（`--write` 时执行） |
| pi | `~/.agents/skills` | `/skill:name` | ⏳ pi 需要扩展才支持 MCP，未验证，只打印中性 JSON |
| DeepSeek Harness（dsh） | `~/.agents/skills` | 自动加载 | ⏳ dsh-mcp-client 字段未验证，只打印中性 JSON |
| deepseek TUI | `~/.agents/skills`（也读 `~/.claude/skills`） | 自动加载 | ✅ `~/.deepseek/mcp.json` |
| Cursor / Gemini CLI（可选） | — | — | ✅ `~/.cursor/mcp.json`、`~/.gemini/settings.json` |

Windows 上链接用目录 junction（`mklink /J`，无需管理员），失败时自动改为拷贝；macOS / Linux 用符号链接。Codex、pi、dsh、deepseek TUI 共用 `~/.agents/skills`，所以同一个 skill 只装一份。

## 如何添加你自己的 skill

1. 克隆仓库，在仓库里新建骨架（会同时重新生成 `registry.json`）：
   ```bash
   git clone https://github.com/lumacoder/myasi && cd myasi
   python scripts/myasi.py new my-skill -d "什么时候用它（agent 只看这句话决定是否加载）" --tags dev --alias old-name
   ```
   生成 `skills/my-skill/SKILL.md`、`skill.json`（version / tags / aliases / clients / license）和 `agents/openai.yaml`（Codex 界面元数据）。也可以手动照着 `skills/hello-myasi`（最小模板）或 `skills/mano-asi`（真实案例，含 rules / scripts / 案例库）写：目录名用 kebab-case，frontmatter 的 `name` 必须等于目录名，`description` ≤ 1024 字符。
2. 编辑 `SKILL.md` 正文；需要默认安装就把名字加进 `profiles/<profile>.txt`（`clients.yaml` 决定每个端装哪些 profile）。第三方 skill 不拷贝，写进 `catalog/external.yaml`。
3. 重新生成索引、校验、跑测试：
   ```bash
   python scripts/build_registry.py && python scripts/validate.py && python -m unittest discover -s tests
   ```
4. 本地先试装：`python scripts/myasi.py get my-skill --source .`
5. 提交并推送；CI 通过后，各端执行 `myasi update` 或 `myasi sync`。

规矩：单个 skill 不超过 5MB，大素材放 Release 或外部存储；不提交 zip、构建产物、备份副本和 `.env`；密钥只用 `${ENV}`。`registry.json` 和 `.claude-plugin/marketplace.json` 由脚本生成，不要手改。

## 目录结构

```
myasi/
├── registry.json               # 名字 → 元数据索引（脚本生成，勿手改）
├── skills/<name>/SKILL.md      # 自有 skill，唯一真源；可选 skill.json、agents/openai.yaml
├── catalog/external.yaml       # 第三方 skill 只记来源（repo/path/license/install），不拷贝
├── profiles/*.txt              # 每行一个裸名；clients.yaml 定义每个端装哪些 profile
├── mcp/servers.yaml            # MCP 唯一真源，只含 ${ENV} 占位（现为示例条目）
├── cli/                        # winget.json、npm/uv 全局清单、Brewfile（现为示例）
├── .claude-plugin/marketplace.json  # Claude 插件市场：每个 skill 一个同名插件（脚本生成）
├── bin/                        # myasi（sh）、myasi.cmd（cmd / PowerShell）
├── scripts/                    # myasi.py、build_registry.py、validate.py、install.sh/ps1
├── tests/                      # 标准库单元测试和端到端测试
├── docs/DESIGN.md              # 设计说明
├── AGENTS.md / CLAUDE.md       # 给 agent 的按名解析规则
└── .github/workflows/ci.yml    # validate + 单测（3.8 / 3.12）+ gitleaks + 三平台冒烟
```

## 许可证

MIT。第三方 skill 以各自上游许可证为准（见 `catalog/external.yaml`）。
