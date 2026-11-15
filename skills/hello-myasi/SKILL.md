---
name: hello-myasi
description: 示例 / 模板 skill（不是真实工具）。只在用户明确说 hello-myasi、要演示或测试 myasi 的 get / update / remove 流程时使用；新建自己的 skill 时可以照着它的结构写，或直接运行 myasi new <name>。
disable-model-invocation: true
---
# hello-myasi（示例）

这是 myasi 自带的**示例 skill**，用来演示按名获取，也供 CI 冒烟测试使用。它不做任何实际工作，可以随时 `myasi remove hello-myasi`。

## 被调用时
1. 回复一句：`hello from myasi — skill 已按名安装成功`。
2. 告诉用户它装在哪个目录（`~/.agents/skills/hello-myasi` 或 `~/.claude/skills/hello-myasi`），以及用 `myasi remove hello-myasi` 删除。

## 一个 skill 目录的最小结构
```
skills/<name>/
├── SKILL.md              # 必需：frontmatter 的 name 等于目录名，description 写清楚何时使用
├── skill.json            # 可选：version / tags / aliases / clients / license
└── agents/openai.yaml    # 可选：Codex 界面元数据
```
