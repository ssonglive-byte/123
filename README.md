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

## Higgsfield 영상 자동 생성

`scripts/generate_higgsfield_videos.py`는 수집된 각 영상의 썸네일을 원본
이미지로 사용하고, 제목의 분위기를 자동 분석한 프롬프트로 Higgsfield API를
호출해 짧은 영상을 생성합니다 (image-to-video). 결과는 각 영상 항목에
`higgsfield_video`(model, prompt, video_url) 필드로 추가됩니다.

```bash
pip install higgsfield-client
export HF_API_KEY="your-api-key"
export HF_API_SECRET="your-api-secret"
python3 scripts/generate_higgsfield_videos.py --limit 3   # 먼저 소량으로 테스트 권장
```

- `--dry-run`: API를 호출하지 않고 자동 생성된 프롬프트만 미리 확인 (크레딧 소모 없음)
- `--model` (기본값 `dop-turbo`): 사용할 Higgsfield 모델 ID
- `--limit`: 앞에서부터 N개 영상만 처리 (크레딧 절약)
- 프롬프트 분위기는 제목의 키워드(메이크업/뷰티, 살림/청소, 인테리어, 여행 등)에 따라
  자동으로 톤을 다르게 생성합니다. 매칭되는 규칙이 없으면 기본 톤을 사용합니다.

Higgsfield API 키는 https://cloud.higgsfield.ai 대시보드에서 발급받습니다.
Higgsfield의 공개 REST API는 YouTube/Coupang API보다 문서화가 덜 정리되어
있어, 공식 SDK(`higgsfield-ai/higgsfield-client`, `higgsfield-ai/higgsfield-js`)
예제를 기준으로 작성했습니다. 모델 카탈로그나 파라미터명이 바뀌면 스크립트
상단의 `VIDEO_ENDPOINT`/`MODEL_ID`/`build_prompt()`를 대시보드 최신 문서에
맞게 조정하세요.

## 주의사항

- YouTube Data API 키, Coupang Partners ACCESS_KEY/SECRET_KEY, Higgsfield API 키는
  절대 저장소에 커밋하지 마세요. 환경변수로만 전달하세요.
- YouTube Data API의 일일 쿼터 제한이 있습니다 (기본 10,000 units/day).
- Coupang Partners API로 얻은 링크로 발생한 수익은 발급받은 계정의 파트너스 ID에 귀속되므로, 본인 계정의 키만 사용하세요.
- Higgsfield 영상 생성은 크레딧을 소모합니다. `--dry-run`으로 프롬프트를 먼저 확인한 뒤 `--limit`으로 소량 테스트를 권장합니다.
