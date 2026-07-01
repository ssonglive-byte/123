# YouTube Shorts TOP 10 (꿀템)

YouTube Data API v3로 오늘 업로드된 인기 Shorts 중 "꿀템" 키워드가
포함된 영상을 조회수 기준 TOP 10으로 뽑아 `data/top10_shorts.json`에 저장하는 스크립트입니다.

## 사용법

```bash
export YOUTUBE_API_KEY="your-api-key-here"
python3 scripts/fetch_shorts_top10.py
```

- `--region` (기본값 `KR`): 검색 지역 코드
- `--output` (기본값 `data/top10_shorts.json`): 결과 저장 경로

## 필터링 기준

- 제목/설명에 "꿀템"이 포함된 영상
- 영상 길이 60초 이하 (YouTube Shorts 기준)
- 오늘(UTC 기준 자정 이후) 업로드된 영상
- 조회수 내림차순 정렬 후 상위 10개

## 저장 항목

각 영상마다 다음 정보를 저장합니다.

- `title`: 영상 제목
- `view_count`: 조회수
- `thumbnail_url`: 썸네일 URL
- `video_id`, `url`: 참고용 영상 ID/링크

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
Higgsfield의 공개 REST API는 YouTube API보다 문서화가 덜 정리되어 있어,
공식 SDK(`higgsfield-ai/higgsfield-client`, `higgsfield-ai/higgsfield-js`)
예제를 기준으로 작성했습니다. 모델 카탈로그나 파라미터명이 바뀌면 스크립트
상단의 `VIDEO_ENDPOINT`/`MODEL_ID`/`build_prompt()`를 대시보드 최신 문서에
맞게 조정하세요.

## 생성된 영상 로컬(D 드라이브 등) 저장

`scripts/save_videos_to_disk.py`는 `higgsfield_video.video_url`이 채워진 영상들을
다운로드해서, 제목/프롬프트가 담긴 텍스트 파일과 함께 지정한 폴더에 저장합니다.

```bash
python3 scripts/save_videos_to_disk.py --save-dir "D:\youtube_shorts"
```

- 이 스크립트는 **저장 대상 드라이브가 실제로 연결된 컴퓨터에서 직접 실행**해야 합니다.
  (클라우드/원격 세션 컨테이너에는 로컬 D 드라이브가 없어서, Claude가 대신 이 작업을 수행할 수는 없습니다.)
- 파일당 두 개가 저장됩니다: `01_영상제목.mp4`(영상), `01_영상제목.txt`(제목/조회수/원본 링크/생성 프롬프트=스크립트)
- `--dry-run`으로 실제 다운로드 없이 저장될 파일 목록만 미리 확인할 수 있습니다.
- macOS/Linux에서는 `--save-dir ~/youtube_shorts`처럼 일반 경로를 사용하세요.

## 주의사항

- YouTube Data API 키, Higgsfield API 키는 절대 저장소에 커밋하지 마세요. 환경변수로만 전달하세요.
- YouTube Data API의 일일 쿼터 제한이 있습니다 (기본 10,000 units/day).
- Higgsfield 영상 생성은 크레딧을 소모합니다. `--dry-run`으로 프롬프트를 먼저 확인한 뒤 `--limit`으로 소량 테스트를 권장합니다.
