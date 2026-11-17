#!/usr/bin/env python3
"""Build offline HTML, ASS and a seekable preview from a motion-pack JSON file."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re

from motion_pack import HEIGHT, WIDTH, _layout, write_ass, write_html


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("The config root must be an object")
    allowed = {"fps", "duration_frames", "chapters", "cards", "demo_notice"}
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown))}")
    config.setdefault("fps", 30)
    config.setdefault("chapters", [])
    config.setdefault("cards", [])
    if isinstance(config["cards"], list):
        for card in config["cards"]:
            if isinstance(card, dict):
                card.setdefault("kind", "steps")
    duration, _ = _layout(config["chapters"], config["cards"], config["fps"], config.get("duration_frames"))
    config["duration_frames"] = duration
    return config


def write_preview(path: Path, overlay: str, config: dict):
    fps, frames = config["fps"], config["duration_frames"]
    options = "".join(f'<option value="{card["start"]}">{escape(card["kind"])} · {escape(card["title"])}</option>'
                      for card in config["cards"])
    notice = str(config.get("demo_notice", "离线无声预览；按播放或拖动时间轴查看。"))
    page = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion pack · 可拖动预览</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0c1b24;color:#faf6e9;font:15px system-ui,sans-serif}
main{max-width:960px;margin:24px auto;padding:0 20px;display:flex;gap:28px;align-items:flex-start}
.viewport{position:relative;width:min(70vw,360px);aspect-ratio:9/16;flex:none;overflow:hidden;border-radius:18px;background:linear-gradient(155deg,#345260,#162e3b 65%,#0a1b25);box-shadow:0 10px 40px #0005}
.canvas{position:absolute;width:1080px;height:1920px;transform-origin:top left}iframe{position:absolute;border:0;width:1080px;height:1920px}
.guide{position:absolute;left:72px;width:882px;border:2px dashed #92d9ce90;pointer-events:none;color:#92d9ce;opacity:.6;font:27px sans-serif;padding:14px}
.top{top:220px;height:930px;font-size:0}.top:before{content:'MG 安全区 · 220–1150';position:absolute;top:-42px;left:0;font:27px sans-serif}.sub{top:1260px;height:340px;color:#f4de91;border-color:#f4de9190}
.note{position:absolute;left:72px;top:1700px;width:882px;font:28px sans-serif;color:#c2cbcb;opacity:.6;text-align:center}
.controls{min-width:0;flex:1}h1{font-size:25px;margin:5px 0 14px}p{line-height:1.6;color:#c2cbcb}.control{margin:22px 0}input[type=range]{width:100%;accent-color:#9cdbd1}button,select{border:1px solid #52717c;border-radius:8px;background:#193443;color:#faf6e9;padding:10px;font:inherit}select{max-width:100%;width:100%}button{cursor:pointer}output{display:block;font-variant-numeric:tabular-nums;margin-top:8px}label{line-height:1.7}a{color:#9cdbd1}small{color:#c2cbcb;line-height:1.6;display:block}
@media(max-width:640px){main{display:block}.viewport{width:min(84vw,320px);margin:auto}.controls{margin-top:24px}}
</style></head><body><main>
<div class="viewport"><div class="canvas"><iframe title="Motion overlay" srcdoc="__OVERLAY__"></iframe>
<div class="guide top"></div><div class="guide sub">字幕区示意 · 仅预览显示</div><div class="note">预览底色 · 不含原片或音频</div></div></div>
<section class="controls"><h1>Motion pack</h1><p>__NOTICE__</p>
<div class="control"><label for="scene">跳到模板</label><select id="scene">__OPTIONS__</select></div>
<div class="control"><button id="play" type="button">播放</button> <button id="reset" type="button">回到开头</button></div>
<div class="control"><label for="seek">帧时间轴</label><input id="seek" type="range" min="0" max="__MAXFRAME__" step="1" value="0"><output id="time"></output></div>
<label><input id="guides" type="checkbox" checked>显示安全区参考线</label>
<p><a href="overlay.html">透明 HTML</a> · <a href="overlay.ass" download>ASS 叠加轨</a> · <a href="demo.json">参数文件</a></p>
<small>生成内容无外链、无音频、无自动播放。透明 HTML 由 window.film.frame(秒) 驱动。ASS 使用相同布局；字体随系统配置变化。</small>
</section></main><script>
const fps=__FPS__,total=__FRAMES__,seek=document.querySelector('#seek'),readout=document.querySelector('#time');
const iframe=document.querySelector('iframe'),play=document.querySelector('#play'),viewport=document.querySelector('.viewport');
let playing=false,current=0,last=0;
function show(value){current=Math.max(0,Math.min(total,Number(value)));seek.value=Math.floor(current);readout.textContent=`${(current/fps).toFixed(2)} s · ${Math.floor(current)} / ${total} 帧`;if(iframe.contentWindow.film)iframe.contentWindow.film.frame(current/fps);}
function stop(){playing=false;play.textContent='播放';}
iframe.addEventListener('load',()=>show(current));
seek.addEventListener('input',()=>{stop();show(seek.value);});
document.querySelector('#scene').addEventListener('change',event=>{stop();show(event.target.value);});
document.querySelector('#reset').addEventListener('click',()=>{stop();show(0);});
document.querySelector('#guides').addEventListener('change',event=>{document.querySelectorAll('.guide,.note').forEach(node=>node.hidden=!event.target.checked);});
play.addEventListener('click',()=>{if(playing){stop();return;}if(current>=total)show(0);playing=true;play.textContent='暂停';last=performance.now();requestAnimationFrame(tick);});
function tick(now){if(!playing)return;show(current+(now-last)*fps/1000);last=now;if(current>=total)stop();else requestAnimationFrame(tick);}
new ResizeObserver(()=>{document.querySelector('.canvas').style.transform=`scale(${viewport.clientWidth/1080})`;}).observe(viewport);
show(0);
</script></body></html>
'''
    replacements = {"__OVERLAY__": escape(overlay, quote=True), "__NOTICE__": escape(notice),
                    "__OPTIONS__": options, "__MAXFRAME__": str(frames),
                    "__FPS__": str(fps), "__FRAMES__": str(frames)}
    # Single-pass replacement keeps user text from being treated as a placeholder.
    page = re.sub(r"__(?:OVERLAY|NOTICE|OPTIONS|MAXFRAME|FPS|FRAMES)__",
                  lambda match: replacements[match.group()], page)
    path.write_text(page, encoding="utf-8")


def build(config_path: Path, out: Path) -> dict:
    config = load_config(config_path)
    out.mkdir(parents=True, exist_ok=True)
    kwargs = {"fps": config["fps"], "duration_frames": config["duration_frames"]}
    write_html(out / "overlay.html", config["chapters"], config["cards"], **kwargs)
    write_ass(out / "overlay.ass", config["chapters"], config["cards"], **kwargs)
    write_preview(out / "preview.html", (out / "overlay.html").read_text(encoding="utf-8"), config)
    (out / "demo.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"canvas": {"width": WIDTH, "height": HEIGHT}, "fps": config["fps"],
                "duration_frames": config["duration_frames"], "card_count": len(config["cards"]),
                "templates": sorted({card["kind"] for card in config["cards"]}),
                "files": ["overlay.html", "overlay.ass", "preview.html", "demo.json"],
                "external_assets": [], "notice": "Constructed examples are not factual claims."}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON containing fps, chapters and cards")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    try:
        manifest = build(args.config, args.out)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Motion pack input error: {exc}\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
