"""Apply the portrait caption preset to a timed, single-track plain-text WebVTT."""

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from html import escape, unescape
import json
from pathlib import Path
import re
import subprocess
import tempfile

PROFILE = Path(__file__).resolve().parents[1] / "assets" / "portrait-caption.json"
STAMP = r"(?:\d{2,}:)?[0-5]\d:[0-5]\d\.\d{3}"
TIMING = re.compile(rf"({STAMP})[ \t]+-->[ \t]+({STAMP})(?:[ \t]+.*)?")
INK_THRESHOLD = bytes(value if value > 130 else 0 for value in range(256))


@dataclass(frozen=True)
class Cue:
    start: str
    end: str
    lines: tuple[str, ...]


def milliseconds(timestamp):
    hours, minutes, seconds = ("00:" + timestamp if timestamp.count(":") == 1 else timestamp).split(":")
    whole, fraction = seconds.split(".")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(whole)) * 1000 + int(fraction)


def read_vtt(path):
    blocks = re.split(r"\n[ \t]*\n", path.read_text(encoding="utf-8-sig").strip("\n"))
    if not re.match(r"^WEBVTT(?:[ \t].*|\n.*|$)", blocks[0]):
        raise ValueError("Expected a WebVTT input file with a WEBVTT header")
    cues = []
    last_end = 0
    for block in blocks[1:]:
        rows = block.splitlines()
        if not rows or re.match(r"^(STYLE|REGION|NOTE)(?:[ \t].*)?$", rows[0]):
            continue
        time_index = 0 if "-->" in rows[0] else 1
        match = TIMING.fullmatch(rows[time_index]) if len(rows) > time_index else None
        raw_lines = rows[time_index + 1:]
        if not match or not 1 <= len(raw_lines) <= 2 or any(not row.strip() for row in raw_lines):
            raise ValueError(f"Expected timed, one- or two-line cue at {rows[0]!r}")
        if any(re.search(r"<[^>]*>", row) for row in raw_lines):
            raise ValueError(f"Expected plain text without cue tags at {match[1]}")
        start, end = match.groups()
        if not last_end <= milliseconds(start) < milliseconds(end):
            raise ValueError(f"Cues must be ordered and nonoverlapping at {start}")
        cues.append(Cue(start, end, tuple(map(unescape, raw_lines))))
        last_end = milliseconds(end)
    if not cues:
        raise ValueError("No subtitle cues found")
    return cues


class GlyphWidth(ctypes.Structure):
    _fields_ = [(name, ctypes.c_float) for name in ("left", "ink", "right")]


def glyph_metrics(cues, family, weight, size):
    gdi = ctypes.WinDLL("gdi32", use_last_error=True)
    gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi.CreateCompatibleDC.restype = wintypes.HDC
    gdi.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
    gdi.CreateFontW.restype = wintypes.HFONT
    gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi.SelectObject.restype = wintypes.HGDIOBJ
    gdi.GetCharABCWidthsFloatW.argtypes = [wintypes.HDC, wintypes.UINT, wintypes.UINT, ctypes.POINTER(GlyphWidth)]
    gdi.GetCharABCWidthsFloatW.restype = wintypes.BOOL
    gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi.DeleteDC.argtypes = [wintypes.HDC]
    dc = gdi.CreateCompatibleDC(None)
    if not dc:
        raise ctypes.WinError(ctypes.get_last_error())
    font = gdi.CreateFontW(-size, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 0, 0, family)
    if not font:
        gdi.DeleteDC(dc)
        raise ctypes.WinError(ctypes.get_last_error())
    previous = gdi.SelectObject(dc, font)
    widths = {}
    try:
        for char in set("".join(line for cue in cues for line in cue.lines)):
            result = GlyphWidth()
            if ord(char) > 0xFFFF or not gdi.GetCharABCWidthsFloatW(dc, ord(char), ord(char), ctypes.byref(result)):
                raise ValueError(f"Could not measure OpenFilm glyph {char!r} with {family}")
            widths[char] = (result.left, result.ink, result.right)
    finally:
        if previous:
            gdi.SelectObject(dc, previous)
        gdi.DeleteObject(font)
        gdi.DeleteDC(dc)
    return widths


def centered_ink(lines, metrics):
    left_edges = []
    right_edges = []
    widest = 0
    for line in lines:
        advance = 0
        edges = []
        for char in line:
            left, ink, right = metrics[char]
            if ink > 0:
                edges.append((advance + left, advance + left + ink))
            advance += left + ink + right
        if edges:
            left_edges.append(min(edge[0] for edge in edges) - advance / 2)
            right_edges.append(max(edge[1] for edge in edges) - advance / 2)
        widest = max(widest, advance)
    if not left_edges:
        raise ValueError(f"No visible text in cue {lines!r}")
    return min(left_edges), max(right_edges), widest


def rgb(color):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"Expected a six-digit hex color, got {color!r}")
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def openfilm_vtt(cues, profile):
    canvas = profile["canvas"]
    font = profile["font"]
    position = profile["position"]
    settings = profile["openfilm"]
    gdi_size = settings["gdi_font_px"]
    padding = profile["horizontal_padding_px"]
    pad_em = padding / gdi_size
    metrics = glyph_metrics(cues, font["family"], font["weight"], gdi_size)
    red, green, blue = rgb(settings["box_color"])
    rules = [
        f'::cue {{ font: {font["weight"]} {settings["font_cqmin"]}cqmin/{settings["line_height"]} "{font["family"]}", sans-serif; '
        f'color: {settings["text_color"]}; background: transparent; display: inline-block; box-sizing: border-box; '
        f'max-width: 100%; padding: {settings["pad_top_em"]}em {pad_em:.5f}em {settings["pad_bottom_em"]}em; '
        'position: relative; isolation: isolate; '
        f'-webkit-text-stroke: {settings["stroke_width_em"]}em {settings["stroke_color"]}; paint-order: stroke fill; }}',
        '::cue::before { content: ""; position: absolute; z-index: -1; '
        'inset: 0 var(--caption-ink-right,0em) 0 var(--caption-ink-left,0em); '
        f'background: rgba({red}, {green}, {blue}, {settings["box_opacity"]}); border-radius: {settings["box_radius_em"]}em; }}',
    ]
    line_pct = position["y_px"] / canvas["height"] * 100
    x_pct = position["x_px"] / canvas["width"] * 100
    positioning = f'line:{line_pct:.4f}%,center size:{settings["max_width_pct"]}% align:{position["align"]}'
    if x_pct != 50:
        positioning += f" position:{x_pct:.4f}%"
    blocks = []
    for index, cue in enumerate(cues, 1):
        left, right, widest = centered_ink(cue.lines, metrics)
        if widest + 2 * padding > canvas["width"] * settings["max_width_pct"] / 100:
            raise ValueError(f"Caption at {cue.start} is too wide for this template; adjust its line break")
        rules.append(
            f'::cue(#{index}) {{ --caption-ink-left: {(widest / 2 + left) / gdi_size:.5f}em; '
            f'--caption-ink-right: {(widest / 2 - right) / gdi_size:.5f}em; }}'
        )
        blocks.append("\n".join([str(index), f"{cue.start} --> {cue.end} {positioning}", *map(escape, cue.lines)]))
    return "\n\n".join(["WEBVTT", "STYLE\n" + "\n".join(rules), *blocks]) + "\n"


def ass_timestamp(ms):
    cs = ms // 10
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_bgr(rgb_value):
    return "".join(f"{channel:02X}" for channel in reversed(rgb(rgb_value)))


def color_with_alpha(value, alpha=0):
    return f"&H{alpha:02X}{ass_bgr(value)}"


def ass_document(profile, events):
    canvas, font, settings = (profile[key] for key in ("canvas", "font", "ass"))
    color = color_with_alpha(settings["foreground"])
    outline = color_with_alpha(settings["outline_color"])
    bold = -1 if font["weight"] >= 700 else 0
    return "\n".join([
        "[Script Info]", "ScriptType: v4.00+", f'PlayResX: {canvas["width"]}', f'PlayResY: {canvas["height"]}',
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f'Style: Caption,{font["family"]},{settings["font_size"]},{color},{color},{outline},&H00000000,'
        f'{bold},0,0,0,100,100,0,0,1,{settings["outline_px"]},0,5,0,0,0,1',
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text", *events, "",
    ])


def dialogue(layer, start, end, text):
    return f"Dialogue: {layer},{start},{end},Caption,,0,0,0,,{text}"


def words(text, position):
    return rf'{{\an5\pos({position["x_px"]},{position["y_px"]})}}{text}'


def ass_ink_bounds(cues, texts, profile):
    canvas, position = profile["canvas"], profile["position"]
    width, height = canvas["width"], canvas["height"]
    strip_height = 180
    strip_top = (position["y_px"] - strip_height // 2) // 2 * 2
    # Give each measurement frame its own centisecond event.
    events = [
        dialogue(21, ass_timestamp(index * 40), ass_timestamp((index + 1) * 40), words(text, position))
        for index, text in enumerate(texts)
    ]
    with tempfile.TemporaryDirectory(prefix="portrait-caption-") as directory:
        (Path(directory) / "metrics.ass").write_text(ass_document(profile, events), encoding="utf-8-sig")
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i", f"color=black:s={width}x{height}:r=25",
            "-vf", f"ass=metrics.ass,crop={width}:{strip_height}:0:{strip_top},format=gray", "-frames:v", str(len(cues)),
            "-c:v", "rawvideo", "-threads", "1", "-f", "rawvideo", "-",
        ], cwd=directory, check=True, capture_output=True)
    stride = width * strip_height
    if len(result.stdout) != len(cues) * stride:
        raise ValueError("FFmpeg returned an unexpected number of caption measurement frames")
    bounds = []
    for idx, cue in enumerate(cues):
        frame = result.stdout[idx * stride:(idx + 1) * stride].translate(INK_THRESHOLD)
        empty_row = bytes(width)
        top, bottom, left, right = strip_height, 0, width, 0
        for row_index in range(strip_height):
            row = frame[row_index * width:(row_index + 1) * width]
            if row != empty_row:
                first = len(row) - len(row.lstrip(b"\0"))
                last = len(row.rstrip(b"\0"))
                left, right = min(left, first), max(right, last)
                top, bottom = min(top, row_index), row_index + 1
        if bottom == 0 or top == 0 or bottom == strip_height or left == 0 or right == width:
            raise ValueError(f"Could not measure complete glyphs at {cue.start}")
        bounds.append((left, right, strip_top + top, strip_top + bottom))
    return bounds


def drawing_box(x, y, width, height, radius, color, alpha):
    # The original confirmed box uses two cubic control points near each corner.
    r = min(radius, width // 2, height // 2)
    curve = round(r * 0.375)
    box = rf"{{\an7\bord0\shad0\1c&H{color}&\1a&H{alpha:02X}&\pos({x},{y})\p1}}"
    drawing = (
        f"m {r} 0 l {width-r} 0 b {width} 0 {width} {curve} {width} {r} "
        f"l {width} {height-r} b {width} {height} {width-curve} {height} {width-r} {height} "
        f"l {r} {height} b 0 {height} 0 {height-curve} 0 {height-r} "
        f"l 0 {r} b 0 0 {curve} 0 {r} 0"
    )
    return box + drawing


def ass_captions(cues, profile):
    settings = profile["ass"]
    position = profile["position"]
    canvas = profile["canvas"]
    horizontal = profile["horizontal_padding_px"]
    vertical = settings["vertical_padding_px"]
    box_color = ass_bgr(settings["box_color"])
    raw_alpha = settings["box_alpha"]
    alpha = int(raw_alpha, 0) if isinstance(raw_alpha, str) else int(raw_alpha)
    if not 0 <= alpha <= 255:
        raise ValueError("ASS transparency byte must be between 0 and 255")
    for cue in cues:
        if any(re.search(r"[{}\\]", line) for line in cue.lines):
            raise ValueError(f"ASS text requires plain characters without braces or backslashes at {cue.start}")
        if milliseconds(cue.start) // 10 == milliseconds(cue.end) // 10:
            raise ValueError(f"Caption at {cue.start} is too brief for ASS timing precision")
    texts = [r"\N".join(cue.lines) for cue in cues]
    events = []
    for cue, text, (left, right, top, bottom) in zip(cues, texts, ass_ink_bounds(cues, texts, profile), strict=True):
        start, end = (ass_timestamp(milliseconds(time)) for time in (cue.start, cue.end))
        x, y = left - horizontal, top - vertical
        width, height = right - left + 2 * horizontal, bottom - top + 2 * vertical
        if x < 0 or y < 0 or x + width > canvas["width"] or y + height > canvas["height"]:
            raise ValueError(f"Caption at {cue.start} extends beyond the template canvas")
        box = drawing_box(x, y, width, height, settings["box_radius_px"], box_color, alpha)
        events.append(dialogue(20, start, end, box))
        events.append(dialogue(21, start, end, words(text, position)))
    return ass_document(profile, events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Existing plain-text .vtt with one or two lines per cue")
    parser.add_argument("--openfilm-vtt", type=Path, help="New OpenFilm .vtt output")
    parser.add_argument("--ass", type=Path, help="New burn-in .ass output")
    args = parser.parse_args()
    targets = [path.resolve() for path in (args.openfilm_vtt, args.ass) if path is not None]
    if not targets:
        parser.error("choose at least one output")
    if len(set(targets)) != len(targets) or args.input.resolve() in targets:
        parser.error("input and output paths must be distinct")
    if any(path.exists() for path in targets):
        parser.error("choose output paths that do not already exist")
    if any(not path.parent.is_dir() for path in targets):
        parser.error("output folders must already exist")
    try:
        profile = json.loads(PROFILE.read_text(encoding="utf-8-sig"))
        cues = read_vtt(args.input)
        rendered = []
        if args.openfilm_vtt is not None:
            rendered.append((args.openfilm_vtt, openfilm_vtt(cues, profile), "utf-8"))
        if args.ass is not None:
            rendered.append((args.ass, ass_captions(cues, profile), "utf-8-sig"))
        for path, content, encoding in rendered:
            with path.open("x", encoding=encoding) as stream:
                stream.write(content)
    except subprocess.CalledProcessError as error:
        parser.exit(1, f'Caption rendering failed: {error.stderr.decode("utf-8", "replace").strip()}\n')
    except (OSError, AttributeError, ValueError, KeyError) as error:
        parser.exit(1, f"Caption template: {error}\n")
    print(f"Styled {len(cues)} caption cues")


if __name__ == "__main__":
    main()
