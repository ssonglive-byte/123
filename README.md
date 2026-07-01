# YouTube Shorts TOP 10 (꿀템 / 쿠팡파트너스)

YouTube Data API v3로 오늘 업로드된 인기 Shorts 중 "꿀템" / "쿠팡파트너스" 키워드가
포함된 영상을 조회수 기준 TOP 10으로 뽑아 `data/top10_shorts.json`에 저장하는 스크립트입니다.

## 사용법

```bash
export YOUTUBE_API_KEY="your-api-key-here"
python3 scripts/fetch_shorts_top10.py
```

- `--region` (기본값 `KR`): 검색 지역 코드
- `--output` (기본값 `data/top10_shorts.json`): 결과 저장 경로

## 필터링 기준

- 제목/설명에 "꿀템" 또는 "쿠팡파트너스"가 포함된 영상
- 영상 길이 60초 이하 (YouTube Shorts 기준)
- 오늘(UTC 기준 자정 이후) 업로드된 영상
- 조회수 내림차순 정렬 후 상위 10개

## 저장 항목

각 영상마다 다음 정보를 저장합니다.

- `title`: 영상 제목
- `view_count`: 조회수
- `thumbnail_url`: 썸네일 URL
- `video_id`, `url`: 참고용 영상 ID/링크

## 쿠팡파트너스 상품 매칭

`scripts/enrich_coupang_products.py`는 위 결과 파일의 영상 제목에서 키워드를
추출해 Coupang Partners Open API로 관련 상품을 검색하고, 각 영상에
`keywords`, `coupang_products`(상품명 `product_name`, 가격 `price`,
상품 URL `product_url`) 필드를 추가합니다.

```bash
export COUPANG_ACCESS_KEY="your-access-key"
export COUPANG_SECRET_KEY="your-secret-key"
python3 scripts/enrich_coupang_products.py
```

- Coupang Partners Open API 키는 https://partners.coupang.com (마이페이지 > Open API 발급)에서 발급받습니다.
- 키워드 추출은 정식 형태소 분석기 없이 해시태그/명사 후보를 휴리스틱으로 뽑는 방식이라 일부 부정확할 수 있습니다.
- `--input`, `--output`으로 대상 JSON 경로를 지정할 수 있습니다 (기본은 같은 파일에 덮어씁니다).

## 주의사항

- YouTube Data API 키, Coupang Partners ACCESS_KEY/SECRET_KEY는 절대 저장소에 커밋하지 마세요. 환경변수로만 전달하세요.
- YouTube Data API의 일일 쿼터 제한이 있습니다 (기본 10,000 units/day).
- Coupang Partners API로 얻은 링크로 발생한 수익은 발급받은 계정의 파트너스 ID에 귀속되므로, 본인 계정의 키만 사용하세요.
