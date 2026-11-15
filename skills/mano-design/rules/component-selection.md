# 组件选型决策（核心）
先回答 4 个问题，再选组件；完整规则用 `python3 scripts/rules.py --category component --format table`。

1. **数据形态**：二值？N 选 1？N 选多？连续数值？日期？自由文本？
2. **生效时机**：立即生效，还是点「保存」后生效？
3. **关系**：选项/视图之间是同级并列、先后顺序，还是可以同时展开？
4. **数量与空间**：选项几个？屏幕放得下吗？

| 场景（信号） | 正确组件 | 典型错误（不合格） | 规则 |
|---|---|---|---|
| 二值设置、立即生效 | Switch | 下拉「开/关」 | cs.binary-select（critical） |
| 二值、需保存后生效 | Checkbox | 开关 + 保存按钮 | cs.toggle-deferred |
| 2—6 个同级视图，一次看一个 | 水平 Tabs / Segmented | 纵向 Accordion/details 堆叠 | cs.peer-views-accordion（critical） |
| 有先后顺序的步骤 | Stepper / 向导 | Tabs | cs.tabs-for-sequence |
| 2—5 种视图模式 | Segmented Control | 下拉 | cs.segmented-for-mode |
| 互斥 3—5 项 | Radio / Segmented | Select | cs.few-options-select |
| 互斥 >7 项 | Select；>15 项可搜索 Combobox | 平铺 radio / 长下拉 | cs.many-radios / cs.long-select-no-search |
| 多选 ≤7 项 | Checkbox 组 | select multiple | cs.multi-select-native |
| 连续数值 | Slider + 数字输入 | 0%…100% 下拉 | cs.numeric-select |
| 小范围整数 | Stepper（−/+） | 下拉 1..99 | cs.stepper-for-number |
| 日期 | Date Picker（可键盘输入） | 文本框 YYYY-MM-DD | cs.date-as-text |
| 危险/不可逆 | AlertDialog（按钮写动作）或撤销 | 直接执行 / 只写「确定」 | cs.destructive-no-confirm / cs.dialog-vague-buttons |
| 非阻断通知 | Toast / 内联提示 | 模态弹窗 | cs.modal-for-info |
| 字段 >12 | fieldset 分组或分步 | 一屏平铺 | cs.long-form-ungrouped |
| 动作 / 导航 | button / a href | div onclick / 按钮跳页 | cs.clickable-div / cs.button-as-link |
| 可同时展开的长内容（FAQ、筛选分面） | Accordion | — | （合理用法，检查器不报） |

默认实现映射：shadcn/ui `Switch`、`Tabs`、`ToggleGroup`、`RadioGroup`、`Checkbox`、`Slider`、`Calendar/DatePicker`、`AlertDialog`、`Command+Popover`（Combobox）、`Sonner`（Toast）。项目已有组件库时沿用现有库的同类组件。
