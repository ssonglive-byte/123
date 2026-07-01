#!/usr/bin/env python3
"""
Fetch AdPick's (애드픽) "쇼핑메이트" recommended-product JSON feed and
attach the top 3 keyword-matching products (name, price, link) to each
video in the collected YouTube Shorts data.

Unlike Coupang Partners' /products/search, AdPick's SDK endpoint
(https://adpick.co.kr/apis/sdk_shopping.php) takes no search keyword —
it only accepts `affid` and always returns the same AdPick-curated list
of currently promotable products. This script fetches that list once,
then matches products locally against each video's extracted keywords
(title hashtags/nouns). Since the list isn't tailored to any category,
videos with no keyword overlap against the current AdPick catalog will
end up with fewer than 3 (or zero) matched products.

Requires an AdPick affid (from https://adpick.co.kr, 광고툴/API >
쇼핑메이트 추천 제품 JSON API page, shown in your personal API URL):

    export ADPICK_AFFID="a919d3"
    python3 scripts/enrich_adpick_products.py
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from enrich_coupang_products import extract_keywords  # noqa: E402

API_URL = "https://adpick.co.kr/apis/sdk_shopping.php"
PRODUCTS_PER_VIDEO = 3


def fetch_products(affid: str) -> list:
    query = f"affid={urllib.parse.quote(affid)}"
    with urllib.request.urlopen(f"{API_URL}?{query}") as resp:
        themes = json.loads(resp.read().decode("utf-8"))

    products = []
    for theme in themes:
        for item in theme.get("list", []):
            products.append(item)
    return products


def parse_price(price_str) -> int:
    if price_str is None:
        return 0
    digits = str(price_str).replace(",", "").strip()
    return int(digits) if digits.isdigit() else 0


def score_product(product: dict, keywords: list) -> int:
    text = f"{product.get('product_name', '')} {product.get('mall_name', '')}"
    return sum(1 for keyword in keywords if keyword in text)


def match_top_products(products: list, keywords: list, limit: int = PRODUCTS_PER_VIDEO) -> list:
    scored = [(score_product(p, keywords), p) for p in products]
    scored = [(score, p) for score, p in scored if score > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    matches = []
    for _, product in scored[:limit]:
        matches.append(
            {
                "product_name": product.get("product_name"),
                "price": parse_price(product.get("price_sale")),
                "product_url": product.get("buyurl"),
            }
        )
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=os.path.join(
            os.path.dirname(__file__), "..", "data", "top10_shorts_finance_home_parenting.json"
        ),
        help="Path to the collected videos JSON",
    )
    parser.add_argument("--output", default=None, help="Output path (default: overwrite --input)")
    args = parser.parse_args()

    affid = os.environ.get("ADPICK_AFFID")
    if not affid:
        print("Error: set the ADPICK_AFFID environment variable first.", file=sys.stderr)
        sys.exit(1)

    input_path = os.path.abspath(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    products = fetch_products(affid)
    print(f"Fetched {len(products)} AdPick products for affid={affid}")

    matched_count = 0
    for video in data.get("videos", []):
        keywords = video.get("keywords") or extract_keywords(video["title"])
        video["keywords"] = keywords
        video["adpick_products"] = match_top_products(products, keywords)
        if video["adpick_products"]:
            matched_count += 1

    output_path = os.path.abspath(args.output) if args.output else input_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Updated {len(data.get('videos', []))} videos "
        f"({matched_count} with at least one AdPick match) -> {output_path}"
    )


if __name__ == "__main__":
    main()
