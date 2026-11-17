"""Self-contained portrait motion graphics. Copyright (c) 2026 Zryluckly, MIT.

All intervals are half-open frame ranges. Labels are plain text, never HTML.
No assets, fonts, footage, network access or external Python packages required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
from math import ceil
from pathlib import Path
import json
import unicodedata


WIDTH, HEIGHT = 1080, 1920
LEFT, RIGHT = 72, 954
NAV_TOP, CARD_TOP = 220, 346
FONT = "Microsoft YaHei"
NAVY = "#142938"
INK = "#193443"
IVORY = "#FAF6E9"
AQUA = "#9CDBD1"
GOLD = "#F4DE91"
MUTED = "#C2CBCB"
RAIL = "#52717C"
SUBTITLE_TOP = 1150
KINDS = {"steps", "compare", "chain", "focus", "active_steps",
         "network", "loop", "timeline", "question"}

STYLE_FORMAT = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
)
EVENT_FORMAT = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"


@dataclass(frozen=True)
class Sprite:
    start: int
    end: int
    layer: int
    x: int
    y: int
    color: str
    opacity: float = 1.0
    width: int = 0
    height: int = 0
    radius: int = 0
    text: str = ""
    font: int = 38
    center: bool = False
    enter: int = 0
    leave: int = 0
    slide: int = 0
    grow: bool = False
    path: str = ""


def _range(record: dict) -> tuple[int, int]:
    if not isinstance(record, dict):
        raise ValueError("Each chapter/card must be an object")
    start, end = record.get("start"), record.get("end")
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError(f"Invalid frame range {start!r}–{end!r}")
    return start, end


def _layout(chapters: list[dict], cards: list[dict], fps: int, duration_frames: int | None):
    if type(fps) is not int or fps < 1 or fps > 100:
        raise ValueError("fps must be an integer from 1 to 100")
    if not isinstance(chapters, list) or not isinstance(cards, list):
        raise ValueError("chapters and cards must be arrays")
    last_chapter_frame = _range(chapters[-1])[1] if chapters else 0
    last_card_frame = max((_range(card)[1] for card in cards), default=0)
    end = max(last_chapter_frame, last_card_frame) if duration_frames is None else duration_frames
    if type(end) is not int or end <= 0 or end < max(last_chapter_frame, last_card_frame):
        raise ValueError("duration_frames must cover the graphics timeline")
    if chapters:
        expected_start = 0
        for chapter in chapters:
            start, stop = _range(chapter)
            if start != expected_start or not isinstance(chapter.get("label"), str) or not chapter["label"].strip():
                raise ValueError("Chapters must use contiguous ranges and nonempty labels")
            expected_start = stop
        if expected_start != end:
            raise ValueError("Chapter ranges must cover the full duration")
    previous_end = 0
    for card in sorted(cards, key=lambda card: _range(card)[0]):
        start, stop = _range(card)
        if start < previous_end:
            raise ValueError("Cards must not overlap; combine related items in one card")
        if stop - start < 4:
            raise ValueError("A card must last at least four frames")
        previous_end = stop
    sprites = sorted(_navigation(chapters, end) + _cards(cards, fps), key=lambda sprite: sprite.layer)
    for sprite in sprites:
        if sprite.text:
            half_height = sprite.font * 1.15 * len(sprite.text.split("\n")) / 2
            text_width = _text_width(sprite.text) * sprite.font
            x = sprite.x - (text_width / 2 if sprite.center else 0)
            y, right, bottom = sprite.y - half_height, x + text_width, sprite.y + half_height + sprite.slide
        else:
            x, y, right, bottom = sprite.x, sprite.y, sprite.x + sprite.width, sprite.y + sprite.height + sprite.slide
        if x < LEFT or right > RIGHT or y < NAV_TOP or bottom > SUBTITLE_TOP:
            raise ValueError("Graphic exceeds the safe bounds (x 72..954, y 220..1150)")
    return end, sprites


def _text_width(text: str) -> float:
    return max(sum(1.04 if unicodedata.east_asian_width(ch) in "FWA" else 0.65 for ch in line)
               for line in text.split("\n"))


def _plain_text(value, name: str, lines: int = 1) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.split("\n")) > lines:
        raise ValueError(f"{name} must contain one to {lines} nonempty lines")
    if any(not line.strip() for line in value.split("\n")) or any(ord(ch) < 32 and ch != "\n" for ch in value):
        raise ValueError(f"{name} contains blank lines or unsupported control characters")
    return value


def _font_size(text: str, available: int, preferred: int, minimum: int) -> int:
    size = min(preferred, int(available / max(1, _text_width(text))))
    if size < minimum:
        raise ValueError(f"Text does not fit. Shorten or split it across lines: {text!r}")
    return size


def _navigation(chapters: list[dict], end: int) -> list[Sprite]:
    if not chapters:
        return []
    gap, padding = 7, 9
    width = RIGHT - LEFT
    inner = width - 2 * padding - gap * (len(chapters) - 1)
    minimum_widths = [max(62, ceil(_text_width(chapter["label"]) * 29 + 14)) for chapter in chapters]
    if sum(minimum_widths) > inner:
        raise ValueError("Chapter labels do not fit at readable size. Shorten or consolidate chapters.")
    extra = inner - sum(minimum_widths)
    sprites = [Sprite(0, end, 0, LEFT, NAV_TOP, NAVY, .94, width, 82, 18)]
    x = LEFT + padding
    for index, (chapter, minimum) in enumerate(zip(chapters, minimum_widths)):
        size = minimum + extra * (index + 1) // len(chapters) - extra * index // len(chapters)
        start, stop = _range(chapter)
        label = _plain_text(chapter["label"], "Chapter label")
        if "\n" in label:
            raise ValueError("Chapter labels must use one line")
        font = _font_size(label, size - 14, 32, 29)
        sprites.append(Sprite(start, stop, 1, x, NAV_TOP + 9, INK, 1.0, size, 62, 13))
        sprites.append(Sprite(0, end, 2, x + 10, NAV_TOP + 65, RAIL, 1.0, size - 20, 5, 2))
        sprites.append(Sprite(start, stop, 3, x + 10, NAV_TOP + 65, GOLD, 1.0, size - 20, 5, 2, grow=True))
        if stop < end:
            sprites.append(Sprite(stop, end, 3, x + 10, NAV_TOP + 65, AQUA, 1.0, size - 20, 5, 2))
        for begin, last, color in [(0, start, MUTED), (start, stop, GOLD), (stop, end, IVORY)]:
            if begin < last:
                sprites.append(Sprite(begin, last, 4, x + size // 2, NAV_TOP + 35, color,
                                      text=label, font=font, center=True))
        x += size + gap
    return sprites


def _cards(cards: list[dict], fps: int) -> list[Sprite]:
    sprites = []
    for record in cards:
        start, end = _range(record)
        title = _plain_text(record.get("title"), "Card title")
        items = record.get("items", [])
        kind = record.get("kind", "steps")
        if kind not in KINDS:
            raise ValueError(f"Unknown card kind: {kind}")
        if not isinstance(items, list):
            raise ValueError("items must be an array")
        if kind in {"network", "loop", "timeline", "question"}:
            sprites.extend(_diagram(record, fps))
            continue
        if (kind == "compare" and not 2 <= len(items) <= 3) or len(items) > 4:
            raise ValueError("A comparison needs two or three items. Other cards allow up to four.")
        if kind == "focus" and items:
            raise ValueError("A focus card only uses its title")
        if kind != "focus" and not items:
            raise ValueError("This card needs at least one item")
        top = record.get("top", CARD_TOP)
        if type(top) is not int or top < NAV_TOP + 98:
            raise ValueError("Card top must leave space below the chapter rail")
        entrance = max(1, min(round(fps * .23), (end - start) // 4))
        exit_duration = max(1, min(round(fps * .17), (end - start) // 5))
        width = RIGHT - LEFT
        strip_width = min(width, max(258, round(_text_width(title) * 49 + 90)))
        title_size = _font_size(title, strip_width - 90, 46, 34)
        sprites.extend([
            Sprite(start, end, 8, LEFT, top, NAVY, .96, strip_width, 76, 18,
                   enter=entrance, leave=exit_duration, slide=14),
            Sprite(start, end, 9, LEFT + 20, top + 19, AQUA, 1.0, 7, 38, 3,
                   enter=entrance, leave=exit_duration, slide=14),
            Sprite(start, end, 10, LEFT + 47, top + 37, IVORY, text=title,
                   font=title_size, enter=entrance, leave=exit_duration, slide=14),
        ])
        y = top + 89
        previous_reveal = start
        for index, item in enumerate(items):
            latest_reveal = end - exit_duration - 1
            default_reveal = min(latest_reveal, start + entrance + round(index * .58 * fps))
            reveal = item.get("frame", default_reveal) if isinstance(item, dict) else default_reveal
            text = _plain_text(item.get("text") if isinstance(item, dict) else item, "Item", 2)
            if type(reveal) is not int or not previous_reveal <= reveal <= latest_reveal:
                raise ValueError(f"Invalid reveal order / out-of-range reveal for {text!r}")
            previous_reveal = reveal
            rise = max(1, min(round(fps * .22), (end - reveal) // 4))
            if kind == "compare":
                gap = 13
                cell = (width - gap * (len(items) - 1)) // len(items)
                x = LEFT + (cell + gap) * index
                height = 112
                color = IVORY if index % 2 == 0 else AQUA
                sprites.extend([
                    Sprite(reveal, end, 8, x, y, color, .98, cell, height, 17,
                           enter=rise, leave=exit_duration, slide=12),
                    Sprite(reveal, end, 10, x + cell // 2, y + height // 2, INK,
                           text=text, font=_font_size(text, cell - 36, 39, 28), center=True,
                           enter=rise, leave=exit_duration, slide=12),
                ])
                continue
            height = 70 if "\n" not in text else 104
            prefix = 93 if kind in {"steps", "active_steps"} else 45
            row_width = min(width, max(360, round(_text_width(text) * 43 + prefix + 35)))
            sprites.extend([
                Sprite(reveal, end, 8, LEFT, y, IVORY, .97, row_width, height, 15,
                       enter=rise, leave=exit_duration, slide=12),
                Sprite(reveal, end, 10, LEFT + prefix, y + height // 2, INK,
                       text=text, font=_font_size(text, row_width - prefix - 26, 39, 30),
                       enter=rise, leave=exit_duration, slide=12),
            ])
            if kind in {"steps", "active_steps"}:
                sprites.extend([
                    Sprite(reveal, end, 9, LEFT + 19, y + (height - 42) // 2, AQUA, 1.0, 51, 42, 10,
                           enter=rise, leave=exit_duration, slide=12),
                    Sprite(reveal, end, 10, LEFT + 44, y + height // 2, INK, text=str(index + 1),
                           font=30, center=True, enter=rise, leave=exit_duration, slide=12),
                ])
                if kind == "active_steps":
                    if index + 1 < len(items):
                        next_item = items[index + 1]
                        next_default = min(latest_reveal, start + entrance + round((index + 1) * .58 * fps))
                        active_end = next_item.get("frame", next_default) if isinstance(next_item, dict) else next_default
                    else:
                        active_end = end
                    if type(active_end) is not int or active_end <= reveal:
                        raise ValueError("active_steps requires strictly increasing item frames")
                    sprites.append(Sprite(reveal, active_end, 9, LEFT + 7, y + 8, GOLD,
                                          width=5, height=height - 16, radius=2,
                                          enter=rise, leave=exit_duration if active_end == end else 0))
            else:
                sprites.append(Sprite(reveal, end, 9, LEFT + 19, y + (height - 31) // 2, INK,
                                      1.0, 5, 31, 2, enter=rise, leave=exit_duration, slide=12))
                if index:
                    sprites.append(Sprite(reveal, end, 9, LEFT + 30, y - 16, AQUA,
                                          text="↓", font=31, center=True, enter=rise,
                                          leave=exit_duration, slide=8))
            y += height + (32 if kind == "chain" else 12)
    if any(sprite.layer >= 8 and sprite.y + sprite.height + sprite.slide > SUBTITLE_TOP for sprite in sprites):
        raise ValueError("Card extends into the subtitle region. Raise its top or use fewer items.")
    return sprites


def _diagram(record: dict, fps: int) -> list[Sprite]:
    """Compact relation, cycle, timeline and worked-question layouts.

    These layouts generalize the project's original hand-authored diagram pages;
    all geometry and animation remain editable and share the HTML/ASS renderer.
    """
    start, end = _range(record)
    kind, items = record["kind"], record.get("items", [])
    title = _plain_text(record.get("title"), "Card title")
    top = record.get("top", CARD_TOP)
    if type(top) is not int or top < NAV_TOP + 98:
        raise ValueError("Card top must leave space below the chapter rail")
    limits = {"network": (3, 5), "loop": (3, 3), "timeline": (2, 3), "question": (2, 4)}
    low, high = limits[kind]
    if not low <= len(items) <= high:
        raise ValueError(f"{kind} requires {low} to {high} items")
    enter = max(1, min(round(fps * .23), (end - start) // 4))
    leave = max(1, min(round(fps * .17), (end - start) // 5))
    latest = end - leave - 1
    parsed = []
    previous = start
    for index, item in enumerate(items):
        text = _plain_text(item.get("text") if isinstance(item, dict) else item, "Diagram item", 2)
        default = min(latest, start + enter + round(index * .7 * fps))
        reveal = item.get("frame", default) if isinstance(item, dict) else default
        if type(reveal) is not int or not previous <= reveal <= latest:
            raise ValueError("Diagram reveal frames must be ordered inside the card")
        parsed.append((text, reveal))
        previous = reveal
    sprites = []

    def rect(x, y, width, height, at, color=IVORY, radius=16, stop=end, layer=8, motion=True):
        sprites.append(Sprite(at, stop, layer, x, y, color, .98, width, height, radius,
                              enter=enter if motion else 0, leave=leave if stop == end else 0,
                              slide=12 if motion else 0))

    def label(text, x, y, width, at, color=INK, preferred=36, minimum=26, center=True):
        size = _font_size(text, width, preferred, minimum)
        sprites.append(Sprite(at, end, 10, x, y, color, text=text, font=size, center=center,
                              enter=enter, leave=leave, slide=12))

    def box(text, x, y, width, height, at, color=IVORY, radius=16):
        rect(x, y, width, height, at, color, radius)
        label(text, x + width // 2, y + height // 2, width - 32, at)

    def arrow(x1, y1, x2, y2, at, color=AQUA):
        # Filled polygon, identical coordinates in SVG and ASS drawing mode.
        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** .5
        if length < 16:
            raise ValueError("Diagram connector is too short")
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        base_x, base_y = x2 - 14 * ux, y2 - 14 * uy
        points = [(x1 + 3 * px, y1 + 3 * py), (base_x + 3 * px, base_y + 3 * py),
                  (base_x + 9 * px, base_y + 9 * py), (x2, y2),
                  (base_x - 9 * px, base_y - 9 * py), (base_x - 3 * px, base_y - 3 * py),
                  (x1 - 3 * px, y1 - 3 * py)]
        x, y = int(min(p[0] for p in points)), int(min(p[1] for p in points))
        width = ceil(max(p[0] for p in points)) - x
        height = ceil(max(p[1] for p in points)) - y
        coords = [(round(a - x), round(b - y)) for a, b in points]
        path = "m " + " l ".join(f"{a} {b}" for a, b in [*coords, coords[0]])
        sprites.append(Sprite(at, end, 7, x, y, color, width=width, height=height,
                              enter=enter, leave=leave, path=path))

    title_width = min(RIGHT - LEFT, max(300, round(_text_width(title) * 49 + 90)))
    rect(LEFT, top, title_width, 76, start, NAVY)
    rect(LEFT + 20, top + 19, 7, 38, start, AQUA, 3, layer=9)
    label(title, LEFT + 47, top + 37, title_width - 90, start, IVORY, 46, 34, False)

    if kind == "network":
        center_x, center_y, center_w = LEFT + 330, top + 160, 222
        text, at = parsed[0]
        box(text, center_x, center_y, center_w, 100, at, GOLD, 45)
        positions = [(LEFT, top + 96), (RIGHT - 240, top + 96),
                     (LEFT, top + 264), (RIGHT - 240, top + 264)]
        for (text, at), (x, y) in zip(parsed[1:], positions):
            left = x < center_x
            arrow(center_x if left else center_x + center_w, center_y + 50,
                  x + 248 if left else x - 8, y + 48, at)
            box(text, x, y, 240, 96, at, AQUA if left else IVORY)
    elif kind == "loop":
        xs = [LEFT, LEFT + 320, LEFT + 640]
        for index, ((text, at), x) in enumerate(zip(parsed, xs)):
            box(text, x, top + 114, 242, 100, at, [IVORY, AQUA, GOLD][index], 40)
            if index:
                arrow(xs[index - 1] + 250, top + 164, x - 8, top + 164, at)
        returned = record.get("return_frame", min(latest, parsed[-1][1] + round(.6 * fps)))
        if type(returned) is not int or not parsed[-1][1] <= returned <= latest:
            raise ValueError("return_frame must follow the last item and precede card exit")
        rect(xs[2] + 118, top + 224, 6, 80, returned, GOLD, 0, layer=7, motion=False)
        rect(xs[0] + 118, top + 300, 646, 6, returned, GOLD, 0, layer=7, motion=False)
        arrow(xs[0] + 121, top + 300, xs[0] + 121, top + 222, returned, GOLD)
    elif kind == "timeline":
        width = 262 if len(parsed) == 3 else 400
        gap = (RIGHT - LEFT - width * len(parsed)) // (len(parsed) - 1)
        for index, (text, at) in enumerate(parsed):
            x = LEFT + index * (width + gap)
            item = items[index]
            stamp = _plain_text(item.get("label", f"阶段 {index + 1}") if isinstance(item, dict)
                                else f"阶段 {index + 1}", "Timeline label")
            box(stamp, x, top + 105, width, 65, at, GOLD)
            box(text, x, top + 201, width, 110, at, IVORY)
            rect(x + width // 2 - 3, top + 177, 6, 17, at, AQUA, 2, layer=7, motion=False)
            if index:
                arrow(x - gap + 6, top + 255, x - 6, top + 255, at)
    else:
        prompt = _plain_text(record.get("prompt"), "Question prompt", 3)
        answer = record.get("answer")
        answer_frame = record.get("answer_frame")
        rationale = _plain_text(record.get("rationale"), "Rationale", 2)
        if type(answer) is not int or not 0 <= answer < len(parsed):
            raise ValueError("answer must be a zero-based option index")
        if type(answer_frame) is not int or not parsed[-1][1] < answer_frame <= latest:
            raise ValueError("answer_frame must follow all options and precede card exit")
        box(prompt, LEFT, top + 90, RIGHT - LEFT, 160, start + enter)
        for index, (text, at) in enumerate(parsed):
            x, y = LEFT + (index % 2) * 451, top + 268 + (index // 2) * 104
            rect(x, y, 431, 90, at, IVORY)
            if index == answer:
                rect(x, y, 431, 90, answer_frame, GOLD, layer=9, motion=False)
            label(f"{'ABCD'[index]}  {text}", x + 215, y + 45, 393, at, preferred=34)
        box(rationale, LEFT, top + 484, RIGHT - LEFT, 108, answer_frame, AQUA)
    return sprites


def _ctime(frame: int, fps: int) -> int:
    return frame * 100 // fps


def _stamp(centis: int) -> str:
    hours, cs = divmod(centis, 360_000)
    minutes, cs = divmod(cs, 6000)
    seconds, cs = divmod(cs, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"


def _ass_color(hex_color: str) -> str:
    return f"&H{hex_color[5:7]}{hex_color[3:5]}{hex_color[1:3]}&"


def _round_rectangle(width: int, height: int, radius: int) -> str:
    r = min(radius, width // 2, height // 2)
    c = round(r * .552285)
    return (
        f"m {r} 0 l {width-r} 0 b {width-r+c} 0 {width} {r-c} {width} {r} "
        f"l {width} {height-r} b {width} {height-r+c} {width-r+c} {height} {width-r} {height} "
        f"l {r} {height} b {r-c} {height} 0 {height-r+c} 0 {height-r} "
        f"l 0 {r} b 0 {r-c} {r-c} 0 {r} 0"
    )


def _dialogue(sprite: Sprite, fps: int) -> str:
    start, stop = _ctime(sprite.start, fps), _ctime(sprite.end, fps)
    length = (stop - start) * 10
    enter = round(sprite.enter * 1000 / fps)
    leave = round(sprite.leave * 1000 / fps)
    x, y = sprite.x, sprite.y
    align = (5 if sprite.center else 4) if sprite.text else 7
    tags = rf"\an{align}\1c{_ass_color(sprite.color)}\1a&H{round((1-sprite.opacity)*255):02X}&"
    if sprite.slide:
        tags += rf"\move({x},{y+sprite.slide},{x},{y},0,{enter})"
    else:
        tags += rf"\pos({x},{y})"
    if enter or leave:
        tags += rf"\fad({enter},{leave})"
    if sprite.grow:
        tags += rf"\clip({x},{y},{x},{y+sprite.height})\t(0,{length},\clip({x},{y},{x+sprite.width},{y+sprite.height}))"
    if sprite.text:
        tags += rf"\fs{sprite.font}\b1\q2"
        body = sprite.text.replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", r"\N")
    else:
        tags += r"\p1"
        body = sprite.path or _round_rectangle(sprite.width, sprite.height, sprite.radius)
    return f"Dialogue: {sprite.layer},{_stamp(start)},{_stamp(stop)},MG,,0,0,0,,{{{tags}}}{body}"


def ass_sections(chapters: list[dict], cards: list[dict], *, fps: int = 30, duration_frames: int | None = None):
    """Return style and dialogue lines for a 1080 × 1920 ASS document."""
    _, sprites = _layout(chapters, cards, fps, duration_frames)
    style = f"Style: MG,{FONT},38,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1"
    return [style], [_dialogue(sprite, fps) for sprite in sprites]


def write_ass(path: Path, chapters: list[dict], cards: list[dict], *, fps: int = 30, duration_frames: int | None = None):
    """Write a standalone overlay track. Each timeline range is half-open, in frames."""
    styles, events = ass_sections(chapters, cards, fps=fps, duration_frames=duration_frames)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {WIDTH}", f"PlayResY: {HEIGHT}",
        "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "", "[V4+ Styles]", STYLE_FORMAT, *styles,
        "", "[Events]", EVENT_FORMAT, *events, "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8-sig")


def _svg(index: int, sprite: Sprite) -> str:
    if sprite.path:
        # The generated path uses only m/l coordinates, shared with ASS drawing mode.
        return (f'<path id="mg{index}" d="{sprite.path.upper()}" '
                f'transform="translate({sprite.x} {sprite.y})" fill="{sprite.color}"/>')
    if not sprite.text:
        return (f'<rect id="mg{index}" x="{sprite.x}" y="{sprite.y}" width="{sprite.width}" '
                f'height="{sprite.height}" rx="{sprite.radius}" fill="{sprite.color}"/>')
    baseline = sprite.y + sprite.font * .371
    lines = sprite.text.split("\n")
    leading = sprite.font * 1.15
    line_nodes = "".join(
        f'<tspan x="{sprite.x}" y="{baseline + (n-(len(lines)-1)/2)*leading:.2f}">{escape(line)}</tspan>'
        for n, line in enumerate(lines)
    )
    anchor = "middle" if sprite.center else "start"
    return (f'<text id="mg{index}" text-anchor="{anchor}" font-size="{sprite.font}" '
            f'fill="{sprite.color}">{line_nodes}</text>')


def write_html(path: Path, chapters: list[dict], cards: list[dict], *, fps: int = 30, duration_frames: int | None = None):
    """Write a transparent OpenFilm child page driven by its parent frame clock."""
    duration, sprites = _layout(chapters, cards, fps, duration_frames)
    artwork = "\n".join(_svg(index, sprite) for index, sprite in enumerate(sprites))
    keyframes = [{key: value for key, value in asdict(sprite).items()
                  if key in {"start", "end", "opacity", "enter", "leave", "slide", "grow", "width"}}
                 for sprite in sprites]
    payload = json.dumps(keyframes, ensure_ascii=False, separators=(",", ":"))
    document = f'''<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>Motion overlay</title>
<style>html,body{{margin:0;background:transparent;overflow:hidden}}svg{{display:block;font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;font-weight:700}}</style>
<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">
{artwork}
</svg>
<script>
const fps = {fps};
const duration = {duration} / fps;
const sprites = {payload};
const nodes = sprites.map((_, index) => document.getElementById(`mg${{index}}`));
const clamp = value => Math.max(0, Math.min(1, value));
function frame(time) {{
  if (!Number.isFinite(time)) throw new TypeError('frame(time) needs finite seconds');
  const now = Math.floor(time * fps + 1e-6);
  sprites.forEach((sprite, index) => {{
    const node = nodes[index];
    const visible = now >= sprite.start && now < sprite.end;
    node.style.display = visible ? '' : 'none';
    const age = now - sprite.start;
    const arrival = sprite.enter ? clamp(age / sprite.enter) : 1;
    const departure = sprite.leave ? clamp((sprite.end - now) / sprite.leave) : 1;
    node.setAttribute('opacity', sprite.opacity * arrival * departure);
    if (sprite.slide) node.setAttribute('transform', `translate(0 ${{(1-arrival)*sprite.slide}})`);
    if (sprite.grow) node.setAttribute('width', sprite.width * clamp(age / (sprite.end - sprite.start)));
  }});
}}
window.film = {{width:{WIDTH}, height:{HEIGHT}, fps, duration, ready:document.fonts.ready, frame}};
frame(0);
</script>
</html>
'''
    Path(path).write_text(document, encoding="utf-8")
