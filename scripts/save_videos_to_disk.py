#!/usr/bin/env python3
"""
Download each generated Higgsfield video (from data/top10_shorts.json's
`higgsfield_video.video_url`, produced by generate_higgsfield_videos.py)
and save it to a local folder together with a text file containing the
title and the prompt/"script" used to generate it.

This must be run on the machine where the target drive is actually
mounted — a cloud/remote session has no access to a local D:\ drive.
Run it on your own Windows PC after generating the videos:

    python3 scripts/save_videos_to_disk.py --save-dir "D:\\youtube_shorts"

On macOS/Linux, use a normal path instead, e.g. --save-dir ~/youtube_shorts
"""

import argparse
import json
import os
import re
import urllib.request


def sanitize_filename(text: str, max_length: int = 60) -> str:
    text = re.sub(r'[\\/:*?"<>|\r\n\t]', "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text[:max_length] or "video"


def download_file(url: str, path: str) -> None:
    with urllib.request.urlopen(url) as resp, open(path, "wb") as f:
        f.write(resp.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "top10_shorts.json"),
    )
    parser.add_argument(
        "--save-dir",
        required=True,
        help=r'Destination folder, e.g. "D:\youtube_shorts" (Windows) or ~/youtube_shorts (macOS/Linux)',
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List what would be saved without downloading"
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    save_dir = args.save_dir
    if not args.dry_run:
        os.makedirs(save_dir, exist_ok=True)

    saved = 0
    for i, video in enumerate(videos, start=1):
        higgsfield_video = video.get("higgsfield_video") or {}
        video_url = higgsfield_video.get("video_url")
        if not video_url:
            print(f"[skip] no generated video for: {video['title']}")
            continue

        base_name = f"{i:02d}_{sanitize_filename(video['title'])}"
        video_path = os.path.join(save_dir, f"{base_name}.mp4")
        script_path = os.path.join(save_dir, f"{base_name}.txt")

        if args.dry_run:
            print(f"[dry-run] would save {video_path} and {script_path}")
            continue

        print(f"Downloading: {video['title']} -> {video_path}")
        download_file(video_url, video_path)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(f"제목: {video['title']}\n")
            f.write(f"조회수: {video.get('view_count', 'N/A')}\n")
            f.write(f"원본 영상: {video.get('url', 'N/A')}\n")
            f.write(f"생성 모델: {higgsfield_video.get('model', 'N/A')}\n")
            f.write(f"프롬프트(스크립트): {higgsfield_video.get('prompt', 'N/A')}\n")

        saved += 1

    if not args.dry_run:
        print(f"Saved {saved} video(s) to {os.path.abspath(save_dir)}")


if __name__ == "__main__":
    main()
