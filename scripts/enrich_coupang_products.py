#!/usr/bin/env python3
"""
Extract keywords from the collected YouTube Shorts titles
(data/top10_shorts.json), search matching products on Coupang Partners,
and attach product name / price to each video entry.

Requires Coupang Partners Open API credentials:

    export COUPANG_ACCESS_KEY="your-access-key"
    export COUPANG_SECRET_KEY="your-secret-key"
    python3 scripts/enrich_coupang_products.py

Credentials are issued at https://partners.coupang.com (마이페이지 > Open API 발급).
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API_HOST = "https://api-gateway.coupang.com"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
PRODUCTS_PER_KEYWORD = 3
KEYWORDS_PER_VIDEO = 2

# Generic hashtags/words that don't describe an actual product and should
# not be used as a Coupang search term.
STOPWORDS = {
    "꿀템", "꿀팁", "생활꿀템", "생활꿀팁", "살림템", "살림팁", "살림꿀템",
    "살림초보", "생활용품", "주방템추천", "주방꿀템", "가성비추천", "추천",
    "꿀템추천", "쿠팡", "쿠팡파트너스", "쿠팡템", "shorts", "tip_zip", "팁집",
    "lifehacks", "hack", "tips", "diy", "이슈", "뷰티", "왓츠인마이백",
    "정말", "쉬워요", "이유", "이렇게", "그냥", "왜", "실제로",
    "쓸만할까요", "유명한", "미친", "번", "이걸로", "이걸", "하니", "매년",
    "실제", "진짜", "완전", "바로", "여기", "지금", "오늘", "매번",
}

# Common trailing particles (조사) stripped from plain (non-hashtag) words
# to approximate a noun stem without a full morphological analyzer.
PARTICLE_SUFFIXES = ["으로는", "에서는", "이라고", "이에요", "예요", "으로", "에서", "부터",
                     "까지", "처럼", "보다", "이랑", "하고", "이나", "만큼", "에게",
                     "한테", "이", "가", "은", "는", "을", "를", "의", "에", "와",
                     "과", "도", "만", "랑", "로"]


# Endings typical of conjugated verbs/adjectives rather than nouns, used to
# filter out words like "줄여버린"/"쓰세요"/"막으세요" from keyword candidates.
VERB_SUFFIXES = (
    "세요", "니다", "어요", "아요", "네요", "군요", "잖아요", "버린", "할까요",
    "같아요", "이에요", "예요", "해요", "했어요", "됩니다", "됐어요", "봤어요",
)


def looks_like_verb(word: str) -> bool:
    return word.endswith(VERB_SUFFIXES)


def strip_particle(word: str) -> str:
    for suffix in sorted(PARTICLE_SUFFIXES, key=len, reverse=True):
        if len(word) > len(suffix) + 1 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def extract_keywords(title: str, limit: int = KEYWORDS_PER_VIDEO) -> list:
    hashtags = re.findall(r"#([\w가-힣]+)", title)
    plain_text = re.sub(r"#[\w가-힣]+", "", title)
    plain_words = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", plain_text)
    plain_words = [w for w in plain_words if not looks_like_verb(w)]

    # Longer compounds are more likely to be the actual product noun than
    # short modifiers/adjectives (e.g. "건조대" over "슬림"/"미니").
    hashtags = sorted(hashtags, key=len, reverse=True)
    stemmed_words = sorted({strip_particle(w) for w in plain_words}, key=len, reverse=True)

    candidates = []
    for tag in hashtags:
        if tag not in STOPWORDS and tag not in candidates:
            candidates.append(tag)
    for word in stemmed_words:
        if word not in STOPWORDS and len(word) >= 2 and word not in candidates:
            candidates.append(word)

    return candidates[:limit]


def sign_request(method: str, path: str, query: str, access_key: str, secret_key: str) -> tuple:
    signed_date = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%dT%H%M%SZ")
    message = signed_date + method + path + query
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, "
        f"signed-date={signed_date}, signature={signature}"
    )
    return authorization


def coupang_search(keyword: str, access_key: str, secret_key: str, limit: int) -> list:
    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    authorization = sign_request("GET", SEARCH_PATH, query, access_key, secret_key)

    request = urllib.request.Request(
        f"{API_HOST}{SEARCH_PATH}?{query}",
        headers={"Authorization": authorization, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    products = []
    for item in body.get("data", {}).get("productData", []):
        products.append(
            {
                "product_name": item.get("productName"),
                "price": item.get("productPrice"),
                "product_url": item.get("productUrl"),
                "product_image": item.get("productImage"),
            }
        )
    return products


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "top10_shorts.json"),
        help="Path to the collected videos JSON (default: data/top10_shorts.json)",
    )
    parser.add_argument("--output", default=None, help="Output path (default: overwrite --input)")
    args = parser.parse_args()

    access_key = os.environ.get("COUPANG_ACCESS_KEY")
    secret_key = os.environ.get("COUPANG_SECRET_KEY")
    if not access_key or not secret_key:
        print(
            "Error: set COUPANG_ACCESS_KEY and COUPANG_SECRET_KEY environment variables first.",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = os.path.abspath(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keyword_cache = {}
    for video in data.get("videos", []):
        keywords = extract_keywords(video["title"])
        video["keywords"] = keywords

        products = []
        seen_names = set()
        for keyword in keywords:
            if keyword not in keyword_cache:
                keyword_cache[keyword] = coupang_search(
                    keyword, access_key, secret_key, PRODUCTS_PER_KEYWORD
                )
            for product in keyword_cache[keyword]:
                if product["product_name"] not in seen_names:
                    products.append(product)
                    seen_names.add(product["product_name"])
        video["coupang_products"] = products[:PRODUCTS_PER_KEYWORD]

    output_path = os.path.abspath(args.output) if args.output else input_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Updated {len(data.get('videos', []))} videos with Coupang product data -> {output_path}")


if __name__ == "__main__":
    main()
