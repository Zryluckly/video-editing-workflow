# 通用视频剪辑与包装 Skill

用于口播、访谈和教学视频的 Codex Skill。把原片取舍、两轮气口复查、字幕、章节进度、动态包装和交付检查连在一起。现包含可运行的动态图形模板、字幕模板、音效和允许再分发的 `.motion` 包；剪辑和导出由使用者选定的编辑器完成。

## 已收录的内容

| 内容 | 入口与使用方式 |
|---|---|
| 剪辑流程、两轮气口、语义去重、颜色、字幕和交付检查 | [SKILL.md](SKILL.md)，按任务选择参考章节 |
| 竖屏字幕模板、实际单行/双行预览、VTT 与 ASS 示例 | [字幕示例](examples/captions/README.md) |
| 章节进度和动态图解：重点、步骤、对比、关系链等 | [可运行 MG 示例](examples/motion/README.md)，支持生成 HTML/ASS |
| 13 个音效文件 | [音效目录](assets/sfx/README.md)，按具体动作选用并重新混音 |
| 完整科技风 `.motion` 模板 | [分卷与还原命令](assets/motion-templates/README.md)，保留包内各项许可 |
| 选片与返修决策案例、检查脚本 | [维护评测](evals/run-evaluation.md) |
| OpenFilm 核对、旧入口兼容及许可明确的第三方方法文档 | [Skill 覆盖清单](references/skill-coverage.md)，按需查阅 |

素材的作者、出处、许可、处理说明和文件指纹见 [ASSET_SOURCES.json](ASSET_SOURCES.json)。第三方方法包括剪映自动化操作参考与 Video Shotcraft 镜头配方文档；它们是方法参考库，不包含对应软件和运行环境。未把其他全部已安装 Skill 改标为本项目原创。

未收录原始视频、私人项目、账号或授权密钥、软件安装器、禁止单独再分发的音效，以及未核实来源的素材。个人授权 `.motion` 封套和 Mixkit 原音效未上传；这不改变已有成片。详见来源清单的排除记录。

## 使用

在 PowerShell 中可将整个仓库克隆到 Codex 的个人 Skill 目录。已安装同名 Skill 时，先将仓库克隆到其他位置查看，再决定如何接入。

```powershell
git clone https://github.com/Zryluckly/video-editing-workflow.git "$env:USERPROFILE/.codex/skills/video-editing-workflow"
```

在 Codex 里提供素材位置和交付要求，例如：

> 用 $video-editing-workflow 剪这条竖屏教学口播，保留内容与原声，检查重复表达和气口。完成基础剪辑后做字幕和包装，交付前核对实际导出文件。

- [Skill 入口](SKILL.md) 定义剪辑阶段和交付边界。
- [剪点与复查](references/editing-and-qc.md) 涵盖语义去重、停顿、剪口、同步和闪帧。
- [包装与字幕](references/packaging.md) 涵盖字幕样式、章节导航、动态图解和音效。
- [开工与交付检查](references/revision-checks.md#开工与交付检查) 帮助把确认过的要求逐项核对到成片。

## 可选工具

结构检查器使用 Python 3.10 或以上版本，根据导出的源范围、字幕和已确认台词检查连续性、字序及句末标点。自然听感和显示效果仍需观看实际成片。 [数据格式与命令](references/editing-and-qc.md#检查器输入)

竖屏字幕模板适用于 1080×1920、已分为一至两行且条目不重叠的纯文本 WebVTT。OpenFilm 输出使用 Windows 字体测量接口。ASS 输出使用可调用的 FFmpeg/libass。两种输出都需要本机可用的微软雅黑字体。 [模板说明](references/packaging.md#竖屏口播字幕模板)

```text
python scripts/apply_caption_template.py input.vtt --openfilm-vtt captions.vtt --ass captions.ass
```

## 验证

在仓库根目录执行：

```text
python -B -m unittest discover -s scripts -p 'test_*.py'
python -B scripts/verify_bundle.py
```

仓库提供了合成选片与返修用例，便于检查规则修改。 [评测说明](evals/run-evaluation.md)

已对公开版 MG 示例做生成、时序与代表画面检查，对音效做完整解码检查。第三方 `.motion` 只核对许可、完整性与资源指纹，未在本次重新渲染；参考方法文档不代表其外部软件已安装或已验证。实际人声混音、整片听感、目标平台裁切仍需针对使用者的成片验收。

## 许可证

本项目原创工作流、脚本与示例采用 [MIT 许可证](LICENSE)。第三方内容保留各自许可：CC0 音效、Apache-2.0 方法文档，以及 `.motion` 内的 MIT/OFL 和品牌随包分发声明等，不能统一改称 MIT。许可与范围见 [第三方声明](THIRD_PARTY_NOTICES.md)；使用自己的视频、字体、音效和第三方模板时，仍需遵循各自授权。
