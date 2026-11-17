---
name: cli-tools
description: CLI tools for diagnostics, draft inspection, search, and export.
metadata:
  tags: cli, diagnostics, drafts, export
---

> 分发说明：本文件为上游方法文档快照；本次仅将未收录资源的 Markdown 链接指向上游。文中命令、`scripts/`、`assets/`、`demos/` 等路径按完整上游安装解释，本仓库不包含这些软件与资源。不要把原文中的历史验收声明当成本分发已测试。


# CLI Tools

Prefer these scripts for command-line workflows.

## 1) Draft Inspector (Recommended)

Use `draft_inspector.py` to inspect local drafts quickly.

```bash
# list drafts
python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20

# summary by draft name
python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"

# show full draft JSON
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind content --json
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind meta --json
```

Notes:

- `--root` can override drafts root.
- `--path` can inspect by absolute draft path.
- `--json` returns machine-readable payload.

## 2) Diagnostics

```bash
python <SKILL_ROOT>/scripts/api_validator.py --json
```

## 3) Asset Search

```bash
python <SKILL_ROOT>/scripts/asset_search.py "复古" -c filters
python <SKILL_ROOT>/scripts/asset_search.py "雾化" -c transitions
```

## 4) Export

```bash
python <SKILL_ROOT>/scripts/auto_exporter.py "DraftName" "output.mp4" --res 1080 --fps 60
```

## 5) CLI Output Contract

For scripts supporting `--json`, prefer:

```json
{
  "ok": true,
  "code": "ok",
  "reason": "",
  "data": {}
}
```
