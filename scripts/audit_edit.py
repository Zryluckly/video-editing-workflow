"""Read-only structural audit. No media decoding, listening, or project mutation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import math
from pathlib import Path
import sys
import unicodedata


CAPTION_END_PUNCTUATION_EXCEPTION_FIELD = 'captionEndPunctuationExceptionReason'
_CAPTION_END_MARKS = frozenset('.。．,，、?？!！;；:：…⋯')
_CAPTION_CLOSERS = frozenset('”’\"\'」』》〉】〕）］｝〗〙〛)]}')


def normalize(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalnum())


def _ending_punctuation(text: str) -> dict | None:
    """Return a visible terminal punctuation run, looking through closing marks."""
    tail = text.rstrip()
    closers = ''
    while tail and tail[-1] in _CAPTION_CLOSERS:
        closers = tail[-1] + closers
        tail = tail[:-1].rstrip()

    # A terminal dotted-letter abbreviation keeps its periods. Recognize the
    # form generically (U.S., U.K., e.g., i.e.) without an abbreviation dictionary.
    cursor = len(tail)
    letters = 0
    while (cursor >= 2 and tail[cursor - 1] == '.'
           and tail[cursor - 2].isascii() and tail[cursor - 2].isalpha()):
        letters += 1
        cursor -= 2
    has_boundary = cursor == 0 or not (tail[cursor - 1].isascii() and tail[cursor - 1].isalnum())
    if letters >= 2 and has_boundary:
        return {'punctuation': tail[cursor:], 'closingCharacters': closers,
                'protectedAbbreviation': tail[cursor:]}

    end = len(tail)
    start = end
    while start > 0 and tail[start - 1] in _CAPTION_END_MARKS:
        start -= 1
    if start == end:
        return None
    return {'punctuation': tail[start:end], 'closingCharacters': closers}


def _audit_caption_end_punctuation(cards: list[dict], policy: str | None) -> tuple[dict, list[dict]]:
    report = {
        'policy': policy,
        'status': 'NOT_ENABLED' if policy is None else 'PRESERVE',
        'checkedCards': 0,
        'exceptionField': CAPTION_END_PUNCTUATION_EXCEPTION_FIELD,
        'violations': [],
        'exceptions': [],
        'protectedAbbreviations': [],
    }
    errors = []
    if policy != 'omit':
        return report, errors

    report['checkedCards'] = len(cards)
    for index, card in enumerate(cards):
        ending = _ending_punctuation(card['text'])
        reason = card.get(CAPTION_END_PUNCTUATION_EXCEPTION_FIELD)
        has_reason = isinstance(reason, str) and bool(reason.strip())
        invalid_reason = CAPTION_END_PUNCTUATION_EXCEPTION_FIELD in card and not has_reason
        if invalid_reason:
            errors.append({'kind': 'caption_end_punctuation_exception_invalid', 'index': index,
                           'field': CAPTION_END_PUNCTUATION_EXCEPTION_FIELD})
        if ending and ending.get('protectedAbbreviation'):
            report['protectedAbbreviations'].append({
                'index': index, 'abbreviation': ending['protectedAbbreviation'],
                'text': card['text'], 'closingCharacters': ending['closingCharacters'],
                'reason': 'Terminal period is retained as part of the abbreviation.',
            })
        if has_reason and ending:
            report['exceptions'].append({
                'index': index, 'text': card['text'], 'punctuation': ending['punctuation'],
                'closingCharacters': ending['closingCharacters'], 'reason': reason.strip(),
            })
        elif has_reason and not ending:
            errors.append({'kind': 'caption_end_punctuation_exception_without_match', 'index': index,
                           'field': CAPTION_END_PUNCTUATION_EXCEPTION_FIELD,
                           'reason': reason.strip()})

        if ending and not ending.get('protectedAbbreviation') and not has_reason:
            violation = {'kind': 'caption_end_punctuation_present', 'index': index,
                         'text': card['text'], 'punctuation': ending['punctuation'],
                         'closingCharacters': ending['closingCharacters']}
            report['violations'].append(violation)
            errors.append(violation)

    report['status'] = 'OMIT_FAIL' if errors else 'OMIT_PASS'
    return report, errors


def adjacent_repeats(cards: list[dict]) -> list[dict]:
    """Locate short repeats across caption boundaries; never classify or delete speech."""
    units = [(char, index) for index, card in enumerate(cards)
             for char in normalize(card['text'])]
    text = ''.join(char for char, _ in units)
    found = []
    for offset in range(len(text)):
        # Longest match at this position avoids reporting both 这个 and 这.
        for size in range(4, 0, -1):
            word = text[offset:offset + size]
            if (len(word) == size and all(c.isalpha() for c in word)
                    and text[offset + size:offset + size * 2] == word):
                first, last = units[offset][1], units[offset + size * 2 - 1][1]
                found.append({'kind': 'adjacent_text_repeat', 'text': word,
                              'firstCard': first, 'lastCard': last,
                              'fromFrame': cards[first]['fromFrame'],
                              'toFrame': cards[last]['endFrame'],
                              'note': 'Review actual speech; natural reduplication and emphasis must remain. Caption times are not safe cut points.'})
                break
    return found


def frame(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or int(value) != value:
        raise ValueError(f'{label} must be a finite integer')
    return int(value)


def audit(run: list, captions: dict | list, target: str, fps: float, *,
          duration_frames: int | None = None, max_duration_seconds: float | None = None,
          baseline_run: list | None = None, source_tolerance_us: int = 2000,
          caption_gap_seconds: float = 0.3,
          caption_end_punctuation: str | None = None) -> dict:
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be positive and finite')
    if not isinstance(run, list) or not run:
        raise ValueError('run must be a non-empty list in final playback order')
    cards = captions.get('cards') if isinstance(captions, dict) else captions
    if not isinstance(cards, list) or not cards:
        raise ValueError('captions must be a non-empty cards list or {cards: [...]}')
    if not isinstance(target, str) or not normalize(target):
        raise ValueError('target must contain the approved spoken text')
    if caption_end_punctuation not in (None, 'omit', 'preserve'):
        raise ValueError("caption_end_punctuation must be 'omit', 'preserve', or None")
    if source_tolerance_us < 0 or not math.isfinite(caption_gap_seconds) or caption_gap_seconds < 0:
        raise ValueError('tolerances must be non-negative')
    if duration_frames is not None and frame(duration_frames, 'duration_frames') <= 0:
        raise ValueError('duration_frames must be positive')
    if max_duration_seconds is not None and (not math.isfinite(max_duration_seconds) or max_duration_seconds <= 0):
        raise ValueError('max_duration_seconds must be positive and finite')

    errors: list[dict] = []
    queue: list[dict] = []
    intervals: list[dict] = []
    expected_start = 0
    source_error_max = 0.0
    seen_sources: dict[tuple, int] = {}
    source_history: dict[str, list[tuple[int, int, int]]] = {}
    previous = None
    for index, row in enumerate(run):
        if not isinstance(row, dict):
            raise ValueError(f'run[{index}] must be an object')
        start = frame(row['fromFrame'], f'run[{index}].fromFrame')
        end = frame(row['endFrame'], f'run[{index}].endFrame')
        source_start = frame(row['sourceStartUs'], f'run[{index}].sourceStartUs')
        source_end = frame(row['sourceEndUs'], f'run[{index}].sourceEndUs')
        asset = row['assetId']
        if not isinstance(asset, str) or not asset:
            raise ValueError(f'run[{index}].assetId must be a non-empty string')
        speed = row.get('speed', 1.0)
        if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(speed) or speed <= 0:
            raise ValueError(f'run[{index}].speed must be positive and finite')
        if start < 0 or end <= start or source_start < 0 or source_end <= source_start:
            errors.append({'kind': 'invalid_range', 'index': index})
        if start != expected_start:
            errors.append({'kind': 'timeline_gap_or_overlap', 'index': index, 'expectedStart': expected_start, 'actualStart': start})
        if 'durationFrames' in row and frame(row['durationFrames'], 'durationFrames') != end - start:
            errors.append({'kind': 'duration_field_mismatch', 'index': index})
        delta = abs((source_end - source_start) / speed - (end - start) * 1e6 / fps)
        source_error_max = max(source_error_max, delta)
        if delta > source_tolerance_us:
            errors.append({'kind': 'source_timeline_duration_mismatch', 'index': index, 'errorUs': delta})
        if end - start < fps * 0.2:
            queue.append({'kind': 'short_voice_fragment', 'index': index, 'atSeconds': start / fps,
                          'note': 'Review complete phrase and motion; do not delete automatically.'})
        identity = (asset, source_start, source_end)
        if identity in seen_sources:
            queue.append({'kind': 'reused_exact_source_range', 'index': index, 'previousIndex': seen_sources[identity],
                          'note': 'May be intentional; check accidental duplicate restoration.'})
        seen_sources[identity] = index
        for earlier_index, earlier_start, earlier_end in source_history.get(asset, []):
            overlap_start = max(source_start, earlier_start)
            overlap_end = min(source_end, earlier_end)
            if earlier_index != index - 1 and overlap_end - overlap_start > source_tolerance_us:
                queue.append({'kind': 'nonadjacent_partial_source_overlap', 'index': index, 'previousIndex': earlier_index,
                              'assetId': asset, 'sourceOverlapStartUs': overlap_start, 'sourceOverlapEndUs': overlap_end,
                              'note': 'Review repeated source content across intervening clips; reuse may be intentional.'})
        source_history.setdefault(asset, []).append((index, source_start, source_end))
        if previous:
            same_asset = asset == previous['assetId']
            source_gap = source_start - previous['sourceEndUs'] if same_asset else None
            queue.append({'kind': 'join_to_listen_and_watch', 'leftIndex': index - 1, 'rightIndex': index,
                          'atSeconds': start / fps, 'sameAsset': same_asset, 'sourceGapUs': source_gap,
                          'reviewFromSeconds': max(0.0, start / fps - 1.5), 'reviewToSeconds': (start / fps + 1.5),
                          'note': 'No audio or motion judgment was made.'})
            if same_asset and source_gap is not None and source_gap < -source_tolerance_us:
                queue.append({'kind': 'adjacent_source_overlap_or_reorder', 'index': index, 'sourceGapUs': source_gap,
                              'note': 'Check duplicated syllable or intentional reorder against the approved edit.'})
        intervals.append({'assetId': asset, 'sourceStartUs': source_start, 'sourceEndUs': source_end,
                          'fromFrame': start, 'endFrame': end, 'speed': speed})
        previous = intervals[-1]
        expected_start = end

    end_frame = expected_start
    if duration_frames is not None and end_frame != duration_frames:
        errors.append({'kind': 'unexpected_total_duration', 'expectedFrames': duration_frames, 'actualFrames': end_frame})
    if max_duration_seconds is not None and end_frame / fps > max_duration_seconds + 1e-8:
        errors.append({'kind': 'hard_duration_limit', 'limitSeconds': max_duration_seconds, 'actualSeconds': end_frame / fps})
    if baseline_run is not None:
        def signature(rows: list) -> list:
            return [(r['assetId'], r['sourceStartUs'], r['sourceEndUs'], r['fromFrame'], r['endFrame'], r.get('speed', 1.0)) for r in rows]
        if signature(run) != signature(baseline_run):
            errors.append({'kind': 'unchanged_run_drift', 'note': 'A requested unchanged/no-op run altered source ranges, order, or timeline timing.'})

    texts = []
    last_end = 0
    last_start = -1
    gaps = []
    for index, card in enumerate(cards):
        if not isinstance(card, dict) or not isinstance(card.get('text'), str):
            raise ValueError(f'cards[{index}] must have string text')
        start = frame(card['fromFrame'], f'cards[{index}].fromFrame')
        end = frame(card['endFrame'], f'cards[{index}].endFrame')
        if start < 0 or end <= start or end > end_frame:
            errors.append({'kind': 'caption_invalid_or_outside_timeline', 'index': index})
        if start < last_start or start < last_end:
            errors.append({'kind': 'caption_order_or_overlap', 'index': index})
        if not normalize(card['text']):
            errors.append({'kind': 'empty_caption', 'index': index})
        gap = start - last_end
        if gap > 0:
            gaps.append(gap)
        if gap / fps > caption_gap_seconds:
            queue.append({'kind': 'caption_gap_not_audio_silence', 'beforeCard': index, 'fromFrame': last_end, 'toFrame': start,
                          'seconds': gap / fps, 'note': 'Check spoken-word coverage; never delete audio from this flag alone.'})
        if end - start < fps * 0.2:
            queue.append({'kind': 'short_caption', 'index': index, 'text': card['text'], 'atSeconds': start / fps})
        texts.append(card['text'])
        last_start, last_end = start, end
    if end_frame - last_end > fps * caption_gap_seconds:
        queue.append({'kind': 'caption_gap_not_audio_silence', 'afterCard': len(cards) - 1,
                      'fromFrame': last_end, 'toFrame': end_frame, 'seconds': (end_frame - last_end) / fps})
    queue.extend(adjacent_repeats(cards))
    actual_text = normalize(''.join(texts))
    wanted_text = normalize(target)
    mismatches = []
    if actual_text != wanted_text:
        matcher = difflib.SequenceMatcher(a=wanted_text, b=actual_text, autojunk=False)
        mismatches = [{'operation': op, 'expectedOffset': i, 'actualOffset': k,
                       'expected': wanted_text[i:j], 'actual': actual_text[k:l]}
                      for op, i, j, k, l in matcher.get_opcodes() if op != 'equal']
        errors.append({'kind': 'caption_spoken_text_mismatch', 'differences': mismatches})

    caption_punctuation_report, punctuation_errors = _audit_caption_end_punctuation(cards, caption_end_punctuation)
    errors.extend(punctuation_errors)

    return {'schema': 'chatcut-edit-audit-v1', 'status': 'STRUCTURAL_PASS' if not errors else 'STRUCTURAL_FAIL',
            'counts': {'voiceSegments': len(run), 'captionCards': len(cards), 'joins': len(run) - 1},
            'durationFrames': end_frame, 'durationSeconds': end_frame / fps, 'fps': fps,
            'sourceDurationMaxErrorUs': source_error_max,
            'captionText': {'normalization': 'NFKC + casefold + alphanumeric only; meaning and numeral spelling are not inferred',
                            'actualCharacters': len(actual_text), 'targetCharacters': len(wanted_text),
                            'exactOrderAndMultiplicityMatch': actual_text == wanted_text},
            'captionEndPunctuation': caption_punctuation_report,
            'largestCaptionGapSeconds': max(gaps, default=0) / fps,
            'audioVerified': False, 'motionVerified': False, 'actualSilenceMeasured': False,
            'limits': ['Structural pass does not prove words were spoken correctly.',
                       'Caption gaps are not audio silence.', 'All joins still require listening and continuous motion review.',
                       'Caption end-punctuation policy checks caption text only; it does not assess typography or listening quality.'],
            'errors': errors, 'reviewQueue': queue}


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--captions', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--fps', type=float, required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--duration-frames', type=int)
    parser.add_argument('--max-duration-seconds', type=float)
    parser.add_argument('--unchanged-from', help='Only for a promised unchanged/no-op run, not an intended recut')
    parser.add_argument('--source-tolerance-us', type=int, default=2000)
    parser.add_argument('--caption-gap-seconds', type=float, default=0.3)
    parser.add_argument('--caption-end-punctuation', choices=('omit', 'preserve'),
                        help='Optional caption-card ending punctuation check; omitted by default for compatibility.')
    args = parser.parse_args()
    try:
        output = Path(args.out).resolve()
        inputs = [Path(p).resolve() for p in (args.run, args.captions, args.target, args.unchanged_from) if p]
        if output in inputs:
            raise ValueError('Output must not overwrite an input')
        report = audit(read_json(args.run), read_json(args.captions), Path(args.target).read_text(encoding='utf-8-sig'), args.fps,
                       duration_frames=args.duration_frames, max_duration_seconds=args.max_duration_seconds,
                       baseline_run=read_json(args.unchanged_from) if args.unchanged_from else None,
                       source_tolerance_us=args.source_tolerance_us, caption_gap_seconds=args.caption_gap_seconds,
                       caption_end_punctuation=args.caption_end_punctuation)
        report['generatedAt'] = datetime.now(timezone.utc).isoformat()
        report['inputFiles'] = [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k: report[k] for k in ('status', 'counts', 'durationSeconds', 'captionText',
                                                  'captionEndPunctuation', 'audioVerified', 'motionVerified')}, ensure_ascii=False))
        print(f'Report: {output}')
        return 0 if not report['errors'] else 1
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'INPUT_OR_EXECUTION_ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
