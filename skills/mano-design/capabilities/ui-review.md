# 评审已有 UI（代码、URL 或截图）
1. **定范围**：一个页面或一个组件；写下目标用户与核心任务（一句话）。
2. **确定性检查**：
   - 代码：`python3 scripts/ui_lint.py <files> --format text`
   - 运行中的页面：`python3 scripts/browser_check.py http://localhost:5173 --viewport 390x844`，以及 1280x800
   - 可选第二检测器：`npx impeccable detect --json <dir或URL>`；`npx lighthouse <url> --only-categories=accessibility --output=json`
3. **语义评审**：`rsi/rubric.md`（只评静态检查看不出的问题）。
4. **合并**：同一元素同一问题去重；按 critical → major → minor 排序；每条带规则 id、证据、修复（具体组件/参数）。
5. **修复**：先修 top3；每修一处重跑检查；不为了过检查加 `aria-hidden`、删内容或改阈值。
6. **沉淀**：漏报/误报写入 RSI 失败日志（`rsi/README.md`）。

输出模板：
```text
结论：PASS/FAIL（critical x / major y / minor z）
Top3：1) <规则id> <元素> → <修复>  2) …  3) …
已运行：ui_lint ✓ / browser_check ✓|跳过(原因) / rubric ✓
未验证：<动效手感、真实数据量、读屏实测…>
```
