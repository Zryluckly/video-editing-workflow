---
name: generative-workflow
description: Thinking process for generative editing and AI prompts.
metadata:
  tags: chain_of_thought, generative, logic, prompt
---

> 分发说明：本文件为上游方法文档快照；本次仅将未收录资源的 Markdown 链接指向上游。文中命令、`scripts/`、`assets/`、`demos/` 等路径按完整上游安装解释，本仓库不包含这些软件与资源。不要把原文中的历史验收声明当成本分发已测试。


# Generative Editing Workflow

Do not only fill templates. Build an executable editing plan.

## Chain of Thought

When user intent is vague (for example "做赛博朋克风"), follow:

1. Deconstruct style into concrete elements:
   neon, glitch, pace, typography, transitions, sound design.
2. Retrieve assets:
   use `scripts/asset_search.py` against relevant libraries.
3. Compose implementation:
   convert style plan into deterministic API calls.

## Time Precision Rules

- Use seconds as float values for AI-generated timelines.
- Keep 2-3 decimal digits for stable microsecond conversion.
- Avoid HH:MM:SS and frame-count outputs in model JSON.

## Movie Commentary / Viral Summary

For long-video commentary tasks:

1. Read prompt template: `prompts/movie_commentary.md`.
2. Optimize media before analysis:
   keep <= 30 minutes, prefer 360p for model input.
3. Generate storyboard/timeline JSON via LLM.
4. Execute with existing implementation:
   `scripts/movie_commentary_builder.py`.

Example:

```bash
python <SKILL_ROOT>/scripts/movie_commentary_builder.py --video "video.mp4" --json "storyboard.json"
```

Reference implementation:

- `scripts/movie_commentary_builder.py`
- `prompts/movie_commentary.md`
