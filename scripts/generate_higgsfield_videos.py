#!/usr/bin/env python3
"""
Use the Higgsfield API to auto-generate a short video for each collected
YouTube Shorts entry (data/top10_shorts.json), using the video's thumbnail
as the source image and an auto-written prompt that matches the title's mood.

Higgsfield's public video model (dop) is image-to-video, so this script
feeds it the thumbnail already collected by fetch_shorts_top10.py plus a
generated prompt, rather than generating from text alone.

Requires the official Higgsfield Python SDK and API credentials:

    pip install higgsfield-client
    export HF_API_KEY="your-api-key"
    export HF_API_SECRET="your-api-secret"
    python3 scripts/generate_higgsfield_videos.py --limit 3

Use --dry-run to preview the generated prompts without spending API credits.

NOTE: Higgsfield's public REST API is less consistently documented than
YouTube's. This script follows the endpoint/parameter shape shown
in the official SDKs (higgsfield-ai/higgsfield-client, higgsfield-ai/higgsfield-js)
as of this writing. If Higgsfield changes their model catalog or parameter
names, update MODEL_ID / VIDEO_ENDPOINT / build_arguments() below to match
your dashboard's current API reference.
"""

import argparse
import json
import os
import sys

VIDEO_ENDPOINT = "/v1/image2video/dop"
MODEL_ID = "dop-turbo"

# Keyword -> (visual style, mood) used to auto-write a prompt matching the
# title's vibe. Checked in order; first match wins.
MOOD_RULES = [
    (("메이크업", "레드립", "뷰티", "스킨", "화장품", "립스틱"),
     "glamorous close-up beauty shot, soft flattering lighting, elegant confident mood"),
    (("행주", "주방", "살림", "건조대", "청소", "세탁", "옷장", "정리"),
     "cozy tidy home lifestyle scene, bright clean lighting, satisfying product demo, warm friendly tone"),
    (("인테리어", "냉풍기", "가전", "가구"),
     "modern minimal interior styling, calm satisfying before-after transformation"),
    (("여행", "캠핑", "아웃도어"),
     "vibrant sunny travel vlog energy, adventurous upbeat mood"),
]
DEFAULT_MOOD = "engaging satisfying product showcase, energetic short-form vertical video pacing"


def pick_mood(title: str) -> str:
    for trigger_words, mood in MOOD_RULES:
        if any(word in title for word in trigger_words):
            return mood
    return DEFAULT_MOOD


def build_prompt(video: dict) -> str:
    mood = pick_mood(video["title"])
    return (
        f"{mood}, vertical 9:16 short-form video inspired by the Korean YouTube "
        f'Shorts titled "{video["title"]}", smooth natural motion'
    )


def generate_video(client, model: str, prompt: str, thumbnail_url: str) -> dict:
    request_controller = client.submit(
        VIDEO_ENDPOINT,
        arguments={
            "model": model,
            "prompt": prompt,
            "input_images": [{"type": "image_url", "image_url": thumbnail_url}],
        },
    )
    for status in request_controller.poll_request_status():
        pass  # block until terminal status
    return request_controller.get()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "top10_shorts.json"),
    )
    parser.add_argument("--output", default=None, help="Output path (default: overwrite --input)")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N videos")
    parser.add_argument("--model", default=MODEL_ID, help=f"Higgsfield model id (default: {MODEL_ID})")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print generated prompts without calling the API"
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    if args.limit:
        videos = videos[: args.limit]

    if args.dry_run:
        for video in videos:
            print(f"- {video['title']}")
            print(f"  prompt: {build_prompt(video)}")
            print(f"  source image: {video['thumbnail_url']}")
        return

    try:
        import higgsfield_client
    except ImportError:
        print("Error: run `pip install higgsfield-client` first.", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("HF_API_KEY")
    api_secret = os.environ.get("HF_API_SECRET")
    if not api_key or not api_secret:
        print("Error: set HF_API_KEY and HF_API_SECRET environment variables first.", file=sys.stderr)
        sys.exit(1)

    for video in videos:
        prompt = build_prompt(video)
        print(f"Generating video for: {video['title']}\n  prompt: {prompt}")
        result = generate_video(higgsfield_client, args.model, prompt, video["thumbnail_url"])
        video["higgsfield_video"] = {
            "model": args.model,
            "prompt": prompt,
            "video_url": (result.get("video") or {}).get("url"),
            "raw_result": result,
        }

    output_path = os.path.abspath(args.output) if args.output else input_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Updated {len(videos)} videos with Higgsfield video data -> {output_path}")


if __name__ == "__main__":
    main()
