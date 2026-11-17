---
name: chatcut-talking-head-workflow
description: 旧版口播剪辑 Skill 的兼容入口。旧名称转到本仓库的通用剪辑标准，不要求使用 ChatCut，也不独立维护规则。
---

# 旧名称兼容入口

读取[通用视频剪辑与包装](../../SKILL.md)并按当前任务继续。用户指定的软件、交付物和已确认范围优先；此入口名称本身不选择编辑器。

这个目录保留自编旧入口的名称与脚本调用能力，适用仓库根目录的 MIT 许可证。它不含 ChatCut 插件、软件代码、账号或服务接口。保留本仓库目录结构使用，不要把此子目录单独搬走后期待相对路径仍可工作。

- 剪点、重复、气口与验证统一在[剪点与检查](../../references/editing-and-qc.md)维护。
- 字幕、布局、章节与配声统一在[包装规则](../../references/packaging.md)维护。
- 风格数据使用[通用配方](../../assets/style-recipes.json)，不再复制旧快照。
- 可公开的旧项目经验见[历史失败机制](../../references/historical-failure-patterns.md)，其中不携带原项目内容或参数。

旧脚本入口仅调用根目录中的同一份只读检查器：

```text
python integrations/chatcut-talking-head-workflow/scripts/audit_edit.py --help
python integrations/chatcut-talking-head-workflow/scripts/test_audit_edit.py
```

从仓库根目录运行，其他目录使用实际绝对路径。脚本不连接 ChatCut，不修改工程，也不证明听感或画面已经通过。
