# 资源卫生
- 截图、录屏、browser_check 产物写到系统临时目录或项目 `.gitignore` 目录，评审完删除；不提交 zip、`__pycache__`、venv。
- 自己启动的 dev server / 浏览器在验收后关闭；交付时列出仍在运行的服务。
- RSI 失败日志入库后删除原日志（内容已进 fixtures/manifest）；不复制 `v1/ final/` 目录，迭代靠 git 与 CHANGELOG。
- 交付附一行：清理：删除 <路径/类别>；保留 <最终产物>；仍在运行 <服务:端口 / 无>。
