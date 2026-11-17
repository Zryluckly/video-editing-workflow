# 内容覆盖与来源

本清单区分仓库直接提供的判断方法、可复用代码，以及需要外部软件才能完成的执行能力。安装某个 Skill、软件可打开或脚本返回成功，都不能替代本片的实际声画验收。

## 自编内容的覆盖

| 来源与内容 | 公开位置 | 范围与处理 |
|---|---|---|
| 通用剪辑主流程 | [SKILL.md](../SKILL.md) | 保留接续、工具选择、阶段推进、内容与下游依赖、完成证据；原项目专用名称改为通用入口 |
| 选片、去重、安全切点、两轮气口与视觉边界 | [editing-and-qc.md](editing-and-qc.md) | 原有有效专业规则完整保留，不因公开化删成摘要 |
| 字幕、布局、MG、章节、声音和素材采用 | [packaging.md](packaging.md) | 保留可跨软件复用的判断；样式仅是可选起点，原项目身份与台词不作为默认值 |
| 返修真源、当前预览、颜色路径与交付 | [revision-checks.md](revision-checks.md) | 保留按改动选复验、保护手改、实际入口与版本证据规则 |
| 七个重录决策题及评分 | [cases.json](../evals/cases.json)、[grading.json](../evals/grading.json) | 构造文字题，覆盖完整性、质量差异、纠正与有意强调；不代替真实听验 |
| 十八个收尾返修题及评分 | [finishing-cases.json](../evals/finishing-cases.json)、[finishing-grading.json](../evals/finishing-grading.json) | 原自编案例的判断考点保留，台词、时间、数量及场景改写为中性虚构输入；含独立评测方法 |
| 旧项目中的通用失败机制 | [historical-failure-patterns.md](historical-failure-patterns.md) | 提取源时钟漂移、接口限制、模板运行、迁移等经验；不发布私有工程标识、账号、链接、会话或原台词 |
| 线性口播只读结构检查器 | [audit_edit.py](../scripts/audit_edit.py)、[test_audit_edit.py](../scripts/test_audit_edit.py) | 检查源范围、字幕字序/次数、策略和复查候选；不连接编辑器、不听声音、不审计任意多轨工程 |
| 通用字幕模板与应用脚本 | [portrait-caption.json](../assets/portrait-caption.json)、[apply_caption_template.py](../scripts/apply_caption_template.py) | 可编辑样式数据与对应操作，实际字体和输出显示仍需验证 |
| 可选包装风格配方 | [style-recipes.json](../assets/style-recipes.json) | 自编风格与组件规则；不宣称第三方模板已经成功导入 |
| 自编动态包装组件与示例 | [motion_pack.py](../scripts/motion_pack.py)、[build_motion_pack.py](../scripts/build_motion_pack.py)、[示例配置](../examples/motion/demo.json) | 提供重点、步骤、比较、关系、流程等9类图形及章节导航，生成可编辑 HTML 与 ASS；软件导入、合成和最终显示仍按目标工具验证 |
| 自编 OpenFilm 口播质量核对 | [OpenFilm QC](../integrations/openfilm-talking-head-qc/SKILL.md) | 补充资源引用存在性、当前工程加载、原生字幕与真实音轨路由核对；接口依照当前工具文档，不含 OpenFilm 软件或 SDK |
| 旧 `chatcut-talking-head-workflow` 名称 | [兼容入口](../integrations/chatcut-talking-head-workflow/SKILL.md) | 原目录只有转调规则、脚本和历史链接，没有另一套独有剪辑方法；保留名称及脚本转调，规则与资产指向本仓库唯一来源 |

自编内容适用根目录的 MIT 许可证。判断方法和脚本是不同交付：脚本能检查的结构事实不能覆盖文字方法中的语义、动作、听感和审美判断。评测JSON可解析只证明测试素材格式正确；决策效果仍需按[评测方法](../evals/run-evaluation.md)独立运行。

## 第三方 Skill 与工具

第三方方法包即使允许公开，也保留各自作者、许可证与来源。根目录 MIT 不重新授权它们的软件、素材或依赖；使用前读取对应集成目录说明。外部 Skill 中的安装、联网、自更新或云服务步骤不构成本次任务的自动授权。

| 对象 | 本次来源证据 | 仓库中的作用及边界 |
|---|---|---|
| `jianying-editor` | 安装包 README 指向 [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)，包内及官方许可页标注该作者的 MIT 许可 | [方法参考包](../integrations/jianying-editor/SKILL.md)含 16 份上游方法文件；剪映、JyWrapper、草稿 SDK 和本地环境不打包 |
| `video-shotcraft` | 插件元数据指向 [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)，作者 Wei Yihao，包内及官方仓库含 Apache-2.0 许可证 | [方法与镜头卡](../integrations/video-shotcraft/SKILL.md)含 139 份上游文档；保留来源与许可，Remotion、示例媒体和工作区依赖不打包 |
| HyperFrames 系列：`hyperframes`、`general-video`、`motion-graphics`、`media-use`及领域 Skill | 各入口明确由 HyperFrames 维护与分发，包含其自身更新和路由说明 | 本仓库使用它们时只按需调用；不将其整套第三方流程认作自编规则。当前选取文件缺少足以覆盖整包再分发的许可证证据，故不复制 |
| `talking-head-recut` | 包内 NOTICE 明示由 HyperFrames 改编自 [notedit/vtake-skills](https://github.com/notedit/vtake-skills)，保留上游 MIT 声明 | 卡片系统与 HyperFrames 流程存在来源层级；旧上游 MIT 声明不能单独证明全部现有改编及依赖的许可。此次不打包，且它“底片原样播放”的范围不等于本仓库的精剪 |
| `remotion-create`、`remotion-render`、`remotion-markup`、`remotion-captions` | 安装入口明确是 Remotion 创建、渲染和字幕领域 Skill | 外部执行工具链；本次未取得这些安装 Skill 完整的独立再分发许可，不复制。Remotion 软件许可另行适用 |
| `openfilm`、`earshot` | 分别是软件使用入口与音频分析工具说明 | 软件本体、模型和工具说明未随本仓库复制；本仓库仅提供自编选择方法、检查点和证据边界。Earshot 的模型分析不是亲自听过 |
| ChatCut 插件技能 | 插件工具和对应软件操作手册 | 使用可用工具完成剪辑、字幕、动效与导出；不复制账号、工具服务或未确认可再分发的插件包，也不靠本仓库补出接口 |

以上是本次对安装材料的归属核对，不代表上游当前版本的完整许可证审计。没有复制的第三方内容不影响本仓库自编方法、案例与检查器的完整公开；实际执行仍取决于使用者选择的软件与当前可用接口。

## 明确不随仓库发布的内容

- 原片、录音、成片、工程私有数据、账号凭证、私有链接、项目对白和个人路径。
- 编辑器、SDK、模型、安装器、依赖目录、缓存与编译字节码。
- 不能确定再分发权限的第三方模板、字体、音乐、音效和完整插件。
- 已由当前规则覆盖的旧重复快照；它们不会成为第二份独立维护来源。

这些排除项不被替换成虚构资源或虚假的完成证据。需要某项外部能力时先核对现有工具、来源与权限，再完成实际任务中的代表样本和对应验收。
