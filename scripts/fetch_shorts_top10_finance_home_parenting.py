#!/usr/bin/env python3
"""
Fetch today's most popular YouTube Shorts filtered to the
'재테크' (personal finance), '살림' (household management), and
'육아' (parenting) categories, and save the top 10 by view count.

Requires a YouTube Data API v3 key, e.g.:

    export YOUTUBE_API_KEY="your-api-key-here"
    python scripts/fetch_shorts_top10_finance_home_parenting.py

Output is written to data/top10_shorts_finance_home_parenting.json
(title, view count, thumbnail URL for each video), plus a printed
summary table.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API_BASE = "https://www.googleapis.com/youtube/v3"
CATEGORY_KEYWORDS = {
    "재테크": ["재테크", "부업", "짠테크"],
    "살림": ["살림", "살림꿀팁", "집안일"],
    "육아": ["육아", "육아꿀팁", "육아템"],
}
SHORTS_MAX_SECONDS = 60  # YouTube Shorts are <= 60s
DEFAULT_REGION = "KR"


def http_get(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}") as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_videos(api_key: str, keyword: str, published_after: str, region_code: str) -> list:
    params = {
        "key": api_key,
        "part": "snippet",
        "type": "video",
        "q": keyword,
        "videoDuration": "short",  # <4 min; narrowed to <=60s below via contentDetails
        "order": "viewCount",
        "publishedAfter": published_after,
        "regionCode": region_code,
        "maxResults": 50,
    }
    data = http_get(f"{API_BASE}/search", params)
    return [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item.get("id", {})]


def parse_iso8601_duration_seconds(duration: str) -> int:
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def fetch_video_details(api_key: str, video_ids: list) -> list:
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        params = {
            "key": api_key,
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
        }
        data = http_get(f"{API_BASE}/videos", params)
        videos.extend(data.get("items", []))
    return videos


def is_shorts_video(video: dict) -> bool:
    duration = video.get("contentDetails", {}).get("duration", "")
    return parse_iso8601_duration_seconds(duration) <= SHORTS_MAX_SECONDS


def matched_category(video: dict, category_keywords: dict) -> str:
    title = video.get("snippet", {}).get("title", "")
    description = video.get("snippet", {}).get("description", "")
    text = f"{title} {description}"
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    return ""


def best_thumbnail_url(video: dict) -> str:
    thumbnails = video.get("snippet", {}).get("thumbnails", {})
    for size in ("maxres", "standard", "high", "medium", "default"):
        if size in thumbnails:
            return thumbnails[size]["url"]
    return ""


def fetch_top10(api_key: str, category_keywords: dict, region_code: str = DEFAULT_REGION) -> list:
    today_start = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    published_after = today_start.isoformat().replace("+00:00", "Z")

    video_ids = set()
    for keywords in category_keywords.values():
        for keyword in keywords:
            video_ids.update(search_videos(api_key, keyword, published_after, region_code))

    if not video_ids:
        return []

    videos = fetch_video_details(api_key, list(video_ids))

    filtered = []
    for video in videos:
        if not is_shorts_video(video):
            continue
        category = matched_category(video, category_keywords)
        if category:
            filtered.append((video, category))

    filtered.sort(key=lambda pair: int(pair[0].get("statistics", {}).get("viewCount", 0)), reverse=True)

    top10 = []
    for video, category in filtered[:10]:
        top10.append(
            {
                "title": video["snippet"]["title"],
                "view_count": int(video.get("statistics", {}).get("viewCount", 0)),
                "thumbnail_url": best_thumbnail_url(video),
                "category": category,
                "video_id": video["id"],
                "url": f"https://www.youtube.com/shorts/{video['id']}",
            }
        )
    return top10


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(__file__), "..", "data", "top10_shorts_finance_home_parenting.json"
        ),
        help="Path to write the JSON results (default: data/top10_shorts_finance_home_parenting.json)",
    )
    parser.add_argument("--region", default=DEFAULT_REGION, help="YouTube regionCode (default: KR)")
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: set the YOUTUBE_API_KEY environment variable first.", file=sys.stderr)
        sys.exit(1)

    top10 = fetch_top10(api_key, CATEGORY_KEYWORDS, region_code=args.region)

    result = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "categories": {category: keywords for category, keywords in CATEGORY_KEYWORDS.items()},
        "region": args.region,
        "videos": top10,
    }

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(top10)} videos to {output_path}\n")
    for i, video in enumerate(top10, start=1):
        print(f"{i}. [{video['category']}] {video['title']} — {video['view_count']:,} views")
        print(f"   {video['thumbnail_url']}")


if __name__ == "__main__":
    main()
