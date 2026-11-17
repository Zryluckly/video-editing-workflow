# 可运行的竖屏 MG 模板

这里提供自编的实际绘图与动画模板。许可证沿用仓库 MIT；没有打包第三方代码、头像、原台词、品牌、音视频或字体文件。示例均为构造内容，不是事实陈述。

在仓库根目录执行，Python 3.10+ 即可生成，无需安装 Python 依赖：

```sh
python scripts/build_motion_pack.py examples/motion/demo.json --out output/motion
python scripts/test_motion_pack.py
```

用浏览器打开 `output/motion/preview.html`，点击播放、拖动帧时间轴或选择模板。预览不会自动播放，没有声音，不需要联网。已有可打开的示例在 [examples/motion](../../examples/motion/README.md)，索引在 [catalog.json](catalog.json)。

生成文件：

- `overlay.html`：1080×1920 透明 SVG 页面，`window.film.frame(seconds)` 按父级秒时钟绘制，`window.film.ready` 等待字体；它自身不启动播放。
- `overlay.ass`：相同几何布局、逐项时序与章节进度的 ASS 叠加轨。
- `preview.html`：带底色、播放、模板跳转和安全区开关的独立预览。
- `demo.json`、`manifest.json`：可编辑参数和本次生成清单。

| 类型 | 参数与内容 | 动态行为 |
| --- | --- | --- |
| `focus` | 标题，0 项 | 淡入上移、离场 |
| `steps` | 1–4 项 | 序号与内容逐项进入 |
| `compare` | 2–3 项 | 并排卡逐项进入 |
| `chain` | 1–4 项 | 纵向节点及箭头推进 |
| `active_steps` | 1–4 项，时间严格递增 | 当前步骤标记随时间切换 |
| `network` | 第一项为中心，再接 2–4 分支 | 分支及关系箭头逐项进入 |
| `loop` | 3 项，可指定 `return_frame` | 节点、连接与最后回路分段进入 |
| `timeline` | 2–3 项，可各带 `label` | 阶段/时间标签与事件依次进入 |
| `question` | 题干、2–4 选项、答案、解析 | 先读题再展示选项，指定帧高亮答案与解析 |

`chapters` 是独立的全程章节导航，可以与任意卡片搭配，也可以留空。章节必须从第 0 帧开始连续覆盖整个时长；每章有 `label`、`start`、`end`。当前章的进度条会真实增长，完成后保持填充。

卡片基础格式：

```json
{
  "kind": "steps",
  "start": 90,
  "end": 240,
  "title": "三步示意",
  "items": [
    {"text": "收集", "frame": 100},
    {"text": "整理", "frame": 140},
    {"text": "复核", "frame": 180}
  ]
}
```

所有 `start`、`end`、`frame`、`answer_frame`、`return_frame` 都是**整条输出时间轴上的绝对整数帧**，区间为 `[start, end)`；不是各卡片内的局部时间。`fps` 为 1–100 的整数。`items` 也可直接用字符串，生成器会默认错开出现；口播同步时请显式填写 `frame`。

`question` 另需 `prompt`（最多 3 行）、`answer`（从 0 开始的选项序号）、`answer_frame`（晚于全部选项）、`rationale`（最多 2 行）。`timeline.items` 可用 `label` 写阶段或时间。卡片标题为单行，普通项最多 2 行。文字会按可用宽度缩小，低于最低可读字号则报错，要求精简或换行。

画布沿用现有竖屏安全范围：左右 `72..954`，顶部从 `220` 起，内容不超过 `1150`，为人物及下方字幕留出空间。卡片默认 `top=346`，可向上或向下调整，但生成器会拒绝越界、卡片互相重叠、章节断档、倒序出现和范围外的出现帧。预览安全线不进入透明 HTML 或 ASS。接入具体原片后仍需检查人物位置和真实字幕位置是否冲突；这里没有包含原片。

HTML 与 ASS 共用同一布局和关键帧。ASS 时间精度为百分之一秒，在不能整除 100 的帧率下会向下量化，不保证与浏览器逐像素相同；字体回退也会影响字宽。默认请求 `Microsoft YaHei`，浏览器另回退到 `Noto Sans CJK SC`。不捆绑字体，接收端需自行提供可显示中文的字体。ASS 的 `\`、`{`、`}` 会替换为对应全角字符，防止作为控制标签执行；输入中的 HTML 按普通文字转义。

可选浏览器检查依赖本机已有的 Playwright 与 Chromium：

```sh
python scripts/test_motion_pack.py --browser
```

它检查实际逐项显示、时间回退后的状态、所有示例的字形安全边界、结束帧清空和预览跳转，并更新 `examples/motion/preview.png`。测试不安装浏览器，也不需要账号。ASS 可导入支持 ASS 绘图的宿主，或由带 libass 的 FFmpeg 合成；任意剪辑软件的原生模板导入、所有字体平台的一致性不在此模板包的承诺范围内。
