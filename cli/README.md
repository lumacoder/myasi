# CLI 清单（示例）

| 文件 | 格式 | 执行的命令 |
|---|---|---|
| `windows/winget.json` | `winget export` 的格式 | `winget import -i cli/windows/winget.json` |
| `macos/Brewfile` | Homebrew Bundle | `brew bundle --file cli/macos/Brewfile` |
| `npm/global.txt` | 每行一个包 | `npm install -g <包>` |
| `uv/tools.txt` | 每行一个工具 | `uv tool install <工具>` |

现在的内容只是通用示例。换成自己的清单：Windows 上运行 `winget export -o cli/windows/winget.json`，再删掉不需要的条目；npm / uv 每行写一个包名。

`myasi cli` 只打印将执行的命令（dry-run），`myasi cli --run` 才执行；`--os windows|macos|linux` 可预览别的系统。Windows 上 `python` 可能指向某个虚拟环境，优先用 `py -3` 或 uv。
