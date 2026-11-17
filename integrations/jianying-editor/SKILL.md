---
name: jianying-editor-reference
description: 剪映草稿自动化的方法文档参考。仅在使用者选择剪映并已安装上游 JyWrapper 环境时查阅；不包含编辑器或运行软件。
---

# 剪映自动化方法参考

这里保留上游 Skill、11 份操作规则、API 与执行检查方法，方便离线查阅。它不是 `jianying-editor` 的完整软件安装目录；不要在本目录直接运行原文中的软件命令。

- 总入口：[上游 Skill 文档](upstream/METHOD.md)
- 执行与验收：[Agent playbook](upstream/docs/agent-playbook.md)
- 操作规则：[核心操作](upstream/rules/core.md)
- 来源：[luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)
- 许可：[MIT 与原第三方声明](LICENSE)

只有当前任务选定剪映时才接入；不能因为包含此参考库而改用剪映、安装软件、覆盖草稿、调用云配音或发布视频。按实际已安装版本核对 API。现用草稿先复制；上游示例中的 `overwrite=True` 不构成覆盖用户工程的授权。

本快照取自本地安装的上游 1.7.0 方法文档，去除本机安装信息；保留原作者版权和原有说明。文档中的外部资源链接已指向上游，软件、云素材索引、示例音视频、SDK 和虚拟环境未打包。源文件指纹见 [SOURCE_FILES.json](SOURCE_FILES.json)。
