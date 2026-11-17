# 第三方内容与分发范围

根目录 MIT 适用于本项目原创内容。下列文件按其原有许可分发，署名与许可随文件保留，不因放入本仓库而改变。

| 目录 | 来源与许可 | 本次范围 |
|---|---|---|
| `assets/sfx/cc0/` | Freesound；CC0-1.0 | 官方 HQ 预览及已有用途明确的处理版本，逐条记录作者和作品页 |
| `assets/sfx/generated/` | 本地 Earshot 生成；生成器 MIT 声明随包保留 | 2 个既有合成音效；不是录自广告成片的人声或配乐 |
| `assets/motion-templates/kinetic-tech-zh.motion` | [MotionGit 官方作品](https://motiongit.com/adunext/385712) | 原样公开包；代码/纹理 MIT、字体 OFL、品牌素材仅按包内声明原样随模板再分发 |
| `integrations/jianying-editor/` | [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)，[MIT 及原声明](integrations/jianying-editor/LICENSE) | 方法文档快照；不含编辑器、JyWrapper、SDK、云素材或原演示媒体 |
| `integrations/video-shotcraft/` | [Wei Yihao / Video Shotcraft](https://github.com/Vincentwei1021/video-shotcraft)，[Apache-2.0](integrations/video-shotcraft/LICENSE) | 方法文档、镜头卡、模板说明；不含 Remotion 运行库、品牌图、示例录屏或 BGM |

音效和 `.motion` 的精确文件清单、许可依据、文件指纹及排除项在 [ASSET_SOURCES.json](ASSET_SOURCES.json)。许可正文或声明副本在 [LICENSES/third-party-assets](LICENSES/third-party-assets)。第三方方法文件保留原文归属，本分发补充说明并将未打包资源的 Markdown 链接指向上游；对应来源和分发文件指纹写在各目录的 `SOURCE_FILES.json`。

`.motion` 为避免大文件上传通道错误而分卷保存，运行还原脚本后字节与原包完全一致，未解密、删改模板或移除许可。

字幕与本项目 MG 示例依赖系统字体，但未附带微软雅黑等商业字体文件。品牌素材不能从 `.motion` 拿出后视为任意可用的图标库。没有再分发依据的个人授权模板、Mixkit 音效、剪映缓存素材、抽取的参考视频音轨和私人项目文件均未收录。
