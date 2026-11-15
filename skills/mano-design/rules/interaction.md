# 交互与状态
| 项目 | 规格（起点，品牌优先） | 规则 |
|---|---|---|
| 状态全集 | default / hover / focus-visible / active / disabled / loading / empty / error / success | st.no-hover-focus, st.missing-loading, st.missing-empty, st.missing-error |
| 焦点 | 不得 outline:none；:focus-visible 2px 实线 + 2px offset，对比 ≥3:1 | st.focus-removed |
| 加载 | >150ms 才显示，至少显示 300—500ms；按钮禁用+「保存中…」，保留原宽度；区域用骨架屏 | st.missing-loading |
| 空状态 | 说明原因 + 一个主操作；搜索无结果给「清除筛选」 | st.missing-empty, cs.search-filter-feedback |
| 错误 | 字段下内联、aria-describedby、提交后聚焦首个错误；不清空已输入内容 | st.missing-error, cp.vague-error |
| 动效 | 微交互 150—200ms，面板 200—300ms，>500ms 视为拖沓；只列具体属性；有 reduced-motion | st.slow-transition, st.transition-all, st.no-reduced-motion |
| 点击区 | ≥24×24（WCAG 2.5.8 AA），移动端 44×44；相邻目标间距 ≥8px | tt.small-target |
| 键盘 | 全流程可 Tab；Tabs 用左右键；对话框焦点循环、Esc 关闭、关闭后焦点回触发器 | a11y.keyboard-trap |
| 认知负荷 | 每屏 1 个主操作；选项 ≤7 平铺；渐进披露高级设置 | ly.hierarchy |
| 一致性 | 同类组件同 variant、同位置（危险按钮统一在右/左）、同术语 | ly.consistency |
| 深链 | Tabs、筛选、分页状态写进 URL；返回恢复滚动位置 | cs.pagination-vs-infinite |
