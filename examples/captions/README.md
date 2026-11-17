# 字幕模板示例

`input.vtt` 是专为演示构造的四条台词，不含项目原声或原稿。`openfilm.vtt` 和 `captions.ass` 为同一模板的两种输出，实际时间都来自输入字幕；句末不加标点。

模板采用 1080×1920、白字加紧贴字面的深色底框。单行和双行预览分别见 `single-line.png`、`two-lines.png`。字体文件不随仓库分发；示例使用本机微软雅黑。其他字体需要重新量字和看实际成片，不能保证仅改字体名称后视觉相同。

在仓库根目录重新生成到新路径：

```text
python scripts/apply_caption_template.py examples/captions/input.vtt --openfilm-vtt preview.vtt --ass preview.ass
```

OpenFilm 原生 VTT 需要 Windows 字体测量接口。ASS 生成需要可调用的 FFmpeg/libass。脚本拒绝覆盖既有输出。FFmpeg 示例（在仓库根目录执行，按当前版本检查字体与滤镜支持）：

```text
ffmpeg -i source.mp4 -vf subtitles=preview.ass -c:v libx264 -crf 18 -c:a copy captioned.mp4
```

这里仅示范字幕叠加，不替代原片颜色、帧率和音频处理方案。模板是可选参考，优先沿用当前用户已确认的样式。
