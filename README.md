https://github.com/hegelty/AUK-Android
https://play.google.com/store/apps/details?id=com.unrevr.auk&pcampaignid=web_share


## 일별 학습 점수

`POST /upload_score`는 기존 앱과 같은 폼 필드 `id`와 `score`(0–100)를 받습니다. 한국 시간으로 같은 날 같은 설치에서 다시 보내면 한 행을 갱신합니다. 저장 성공은 HTTP 200과 `success`, 잘못된 입력은 400, DB 오류는 503입니다.

기본 DB 파일은 서버 작업 디렉터리의 `score.db`입니다. 서버 이전 시 기존 DB의 일관된 백업을 가져와 같은 경로에 배치합니다. 첫 쓰기에서 기존 표를 `score_legacy`로 보존하고, 날짜·설치별 마지막 유효 점수를 `score`에 이관합니다. 시간대가 없는 과거 수신 시각은 기록된 날짜를 그대로 사용합니다. 통계는 `score`에서 조회하고, 사용자 기록 삭제 요청은 보존된 `score_legacy`에도 적용합니다.
