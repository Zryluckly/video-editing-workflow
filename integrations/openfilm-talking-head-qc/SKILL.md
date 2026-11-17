---
name: openfilm-talking-head-qc
description: Verify or finish an OpenFilm Chinese talking-head edit when the request mentions full-source coverage, retakes, VTT captions, pause trimming, semantic repetition, or a complete listening deliverable.
argument-hint: "[project directory]"
user-invocable: false
---

# OpenFilm talking-head edit and QC

This is an optional QC method authored for this workflow, covered by the repository MIT license. It does not bundle OpenFilm, an SDK, media, models, or credentials. Read the current OpenFilm skill and available tool schemas before using any named API below; these names describe integration checkpoints, not a promise of current interface compatibility. Installing or updating external software is a separate action governed by the current task authorization.

Use the [main workflow](../../SKILL.md) for general editing decisions and the [delivery checks](../../references/revision-checks.md) for acceptance. Load this extension only for an OpenFilm project. The historical source used fixed command labels for execution; use the supported tools available in the current environment.

## When to use

Use for Chinese vertical talking-head edits in OpenFilm that require source inventory, retake selection, semantic cleanup, captions, or final acceptance. Do not use for a simple export-only request, an unrelated animation, or to claim human listening without it occurring.

## Inputs / context to gather

1. Confirm the project directory, all original source clips, destination editable project, and whether the user explicitly wants an MP4 render.
2. Read the current edit plan, source inventory, caption/VTT source, and prior QC receipt. Preserve source media and do not overwrite another project.
3. Identify the requested decision rule: full-source coverage, later complete retake, semantic-dedup rule, pause target, subtitle style, or feedback anchored to an exact spoken phrase.

## Procedure

1. Inventory every source clip and identify retake relationships before choosing material. Prefer the later complete take only when quality is comparable; preserve unique context, numbers, conditions, negations, examples, and endings.
2. Use ASR/VAD/waveform only to locate candidates. Treat token-start times as estimates, not cut-safe acoustic boundaries. Keep original ASR, documented corrections, and unresolved listening questions.
3. For semantic repetition, retain the later complete expression only when both passages mean the same thing. Do not delete wording that contributes unique context, a deadline, an example, or a parameter.
4. For pause cleanup, inspect the whole retained narration, including inside phrases and on both sides of cuts. The 0.1–0.3 second target is a guide, not permission to clip words or erase natural breath.
5. Rebuild captions from the post-edit speech. Verify VTT text and cue mapping against the intended spoken text; reuse approved visual style only, never other-project dialogue or branding.
6. Build an isolated editable OpenFilm project with film.html, assets, and .film. Use source #t=in,out cuts where applicable; do not transcode original material merely to assemble the edit.
7. Before acceptance, confirm every referenced src exists; reopen the current project; inspect actual readFilmFile/open output, meta.sounds, spans/cuts, and filmSubtitleAt behavior. Export complete voice/mix from actual meta.sounds -> audioClips -> mix without extra normalization only when required.
8. Report static/structural checks separately from real complete playback and human natural-listening review.

## Efficiency plan

- Do one source inventory and reuse it throughout; avoid rescanning source media.
- Stop early on missing project assets or an unloaded zero-duration Studio project: fix/open the current project before downstream QC.
- Use ASR and static verification to narrow review, not to substitute for the listening gate.
- Do not render MP4 unless the user asks; editable film.html + assets + .film is the default deliverable.

## Pitfalls and fixes

- graphics.html missing or Studio shows 0 tracks -> verify referenced src files, rebuild/open the intended current project, then inspect actual spans.
- BUILT, look, captionExact, or one successful mix command -> only a partial milestone; complete parsing, boundary/caption display, actual audio export, and playback/listening remain.
- ASR correction sounds fluent but changes the source -> retain original ASR and correction provenance; mark it for listening instead of silently rewriting.
- Feedback phrase is ambiguous -> confirm the full quote and map it to source time/frame and current cut before editing.

## Verification checklist

- [ ] All source clips and retake choices were reviewed; unique facts survived.
- [ ] Captions derive from the final edit and VTT/cue mapping is checked.
- [ ] Referenced assets exist and the current OpenFilm project opens with actual duration/tracks.
- [ ] Native spans/cuts, subtitles, and actual audio routing were checked.
- [ ] Static evidence, model analysis, and human listening/playback are reported separately.
