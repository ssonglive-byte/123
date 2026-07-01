# CLAUDE.md

This file gives Claude Code (claude.ai/code) the context needed to work in this repository.

## What this repo is

A small pipeline of standalone Python scripts (no package/build system) that:

1. Finds today's most-viewed Korean YouTube Shorts tagged "꿀템" (life-hack/deal finds).
2. Auto-generates a short AI video for each one via the Higgsfield API, using the video's thumbnail as the source image.
3. Downloads the generated videos to a local folder alongside a text file with the title/prompt.

There is no test suite, CI, linter config, or dependency manifest (`requirements.txt`/`pyproject.toml`). Each script only imports the stdlib except `generate_higgsfield_videos.py`, which lazily imports the optional `higgsfield-client` package.

## Repo layout

```
scripts/
  fetch_shorts_top10.py          # Step 1: YouTube Data API v3 -> data/top10_shorts.json
  generate_higgsfield_videos.py  # Step 2: Higgsfield image-to-video -> adds higgsfield_video field
  save_videos_to_disk.py         # Step 3: download videos + write title/prompt .txt files
data/
  top10_shorts.json              # pipeline's shared, evolving output file (committed)
README.md                        # Korean-language usage docs (source of truth for CLI flags)
```

## The pipeline, in order

Each script reads/writes `data/top10_shorts.json`, so they must run in this order:

```bash
export YOUTUBE_API_KEY="..."
python3 scripts/fetch_shorts_top10.py                     # writes data/top10_shorts.json

pip install higgsfield-client
export HF_API_KEY="..." HF_API_SECRET="..."
python3 scripts/generate_higgsfield_videos.py --dry-run    # preview prompts, no credits spent
python3 scripts/generate_higgsfield_videos.py --limit 3    # generate for a few videos first
                                                            # (overwrites data/top10_shorts.json in place)

python3 scripts/save_videos_to_disk.py --save-dir ~/youtube_shorts --dry-run
python3 scripts/save_videos_to_disk.py --save-dir ~/youtube_shorts
```

- `save_videos_to_disk.py` must be run on the machine where the destination drive is actually mounted (e.g. a Windows `D:\` drive). It cannot be run meaningfully from a cloud/remote Claude Code session — there is no local drive to write to.
- Every script supports `--input`/`--output` overrides and (except step 1) a `--dry-run` flag that avoids spending API credits.

## Data shape (`data/top10_shorts.json`)

```jsonc
{
  "fetched_at": "...", "keywords": ["꿀템"], "region": "KR",
  "videos": [
    {
      "title": "...", "view_count": 0, "thumbnail_url": "...",
      "video_id": "...", "url": "...",
      "higgsfield_video": { "model": "...", "prompt": "...", "video_url": "...", "raw_result": {...} }
    }
  ]
}
```

`higgsfield_video` is only present after step 2 has run for that entry.

## Conventions

- **Language**: code/identifiers in English; user-facing strings (README, saved `.txt` sidecar files, error messages) are Korean where the existing script already uses Korean — match the surrounding style rather than converting everything to English.
- **Style**: stdlib-only, `argparse` CLIs with defaults pointing at `data/top10_shorts.json`, `#!/usr/bin/env python3` shebang, module docstring explaining usage at the top of each script.
- **Secrets**: never commit API keys. `YOUTUBE_API_KEY`, `HF_API_KEY`, `HF_API_SECRET` are read from environment variables only; `.gitignore` already excludes `.env` and `*.key`.
- **External API fragility**: `generate_higgsfield_videos.py`'s header comment warns that Higgsfield's public REST API is under-documented and may change shape. If it breaks, update `VIDEO_ENDPOINT` / `MODEL_ID` / `build_prompt()` to match Higgsfield's current dashboard docs rather than guessing.
- **Mood/prompt rules**: `MOOD_RULES` in `generate_higgsfield_videos.py` is an ordered keyword→style list (first match wins) that drives the auto-generated video prompt from the title's Korean keywords. Add new categories by prepending/inserting tuples, keeping `DEFAULT_MOOD` as the fallback.
- **README is the spec for CLI flags** — when changing a script's arguments or output fields, update `README.md` in the same change.

## Working in this repo

- There's no build/test/lint command to run. Validate changes by running the relevant script with `--dry-run` (steps 2–3) or against real API keys if available.
- Since `data/top10_shorts.json` is both a script output and a committed data file, treat unexpected diffs there as generated content (fine to overwrite) rather than manual edits worth preserving.
