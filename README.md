# 通用视频剪辑与包装 Skill

用于口播、访谈和教学视频的 Codex Skill。把原片取舍、两轮气口复查、字幕、章节进度、动态包装和交付检查连在一起。剪辑和导出由使用者选定的编辑器完成。

## 使用

在 PowerShell 中可 将整个仓库克隆到 Codex 的个人 Skill 目录。已安装同名 Skill 时，先将仓库克隆到其他位置查看，再决定如何接入。

```powershell
git clone https://github.com/Zryluckly/zry.git "$env:USERPROFILE/.codex/skills/video-editing-workflow"
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
```

仓库提供了合成选片用例，便于检查规则修改。 [评测说明](evals/run-evaluation.md)

## 许可证

本仓库采用 [MIT 许可证](LICENSE)。使用自己的视频、字体、音效和第三方模板时，请遵循相应素材的授权。
