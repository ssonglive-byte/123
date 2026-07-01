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

## 주의사항

- YouTube Data API 키는 절대 저장소에 커밋하지 마세요. 환경변수로만 전달하세요.
- YouTube Data API의 일일 쿼터 제한이 있습니다 (기본 10,000 units/day).
