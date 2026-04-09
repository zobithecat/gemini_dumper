# Gemini 세션 덤퍼

쿼터 소진 등으로 응답이 막힌 Gemini 대화 세션의 **모든 메시지를 스크롤하여 백업**합니다.

## 방법 A — 콘솔 붙여넣기 (권장, 설치 불필요)

세션을 건드리지 않고 가장 안전합니다.

1. 백업할 Gemini 대화 탭을 연다
2. DevTools 열기: `Cmd + Opt + I` → **Console** 탭
3. `dump_console.js` 파일 내용 전체를 복사해 콘솔에 붙여넣고 Enter
4. 자동으로 위쪽으로 끝까지 스크롤 → 모든 턴 수집 → **JSON / Markdown / HTML 3개 파일 다운로드**

> 콘솔이 "이런 코드 붙여넣기 위험" 경고를 띄우면, 지시에 따라 `allow pasting` 입력.

## 방법 B — Playwright CDP Attach

```bash
# 1) 기존 Chrome 종료 후 디버그 포트로 재실행 (기존 로그인 유지)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/Library/Application Support/Google/Chrome"

# 2) Gemini 대화 탭을 연 상태에서
pip install playwright
python dump_playwright.py
```

결과: `gemini-YYYYMMDD-HHMMSS.json` / `.md`

## 변환 — JSON → Markdown / Text

`dump_console.js`로 받은 JSON을 일반 텍스트나 마크다운으로 변환:

```bash
python3 convert.py gemini-2026-04-09T11-17-06-694Z.json              # md + txt 둘 다
python3 convert.py gemini-2026-04-09T11-17-06-694Z.json --format md  # md만
python3 convert.py gemini-2026-04-09T11-17-06-694Z.json --format txt # txt만
```

- `.md`: `## 🧑 User #N` / `## 🤖 Gemini #N` 섹션 헤더 + 본문
- `.txt`: `====` 구분선 + `[NNNN] USER/GEMINI` 헤더
- Gemini UI의 "말씀하신 내용" 프리픽스 자동 제거

## 동작 원리

- 컨테이너: `infinite-scroller.chat-history` (또는 `[data-test-id="chat-history-container"]`)
- 가상 스크롤이므로 `scrollTop = 0`을 반복 호출 → 350ms 대기 → 새 턴이 4회 연속 증가하지 않으면 종료
- 턴 수집: `user-query` (내부 `.query-text`) + `model-response` (내부 `.markdown.markdown-main-panel`)
- DOM 순서 = 대화 시간순

## 검증 (QA)

백업 완료 후:
1. 다운로드된 JSON의 `turns.length`가 콘솔 로그와 일치하는지 확인
2. 첫 번째 user 메시지가 실제 세션의 최초 질문과 같은지 육안 확인
3. 마지막 model 응답이 쿼터 에러 직전 마지막 응답과 같은지 확인
4. 중간에 누락된 이미지/첨부는 `html` 필드로 확인 (텍스트만 저장되는 경우가 있음)
