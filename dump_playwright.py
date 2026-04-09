"""
Gemini 세션 백업 — Playwright CDP attach 버전

사전 준비 (기존 로그인 세션 유지):
    1) 현재 Chrome을 완전 종료
    2) 디버그 포트로 재실행:
       /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
           --remote-debugging-port=9222 \\
           --user-data-dir="$HOME/Library/Application Support/Google/Chrome"
    3) 백업하려는 Gemini 대화 탭을 연다
    4) python dump_playwright.py

설치: pip install playwright && playwright install chromium (CDP-attach는 브라우저 설치 불필요)
"""
import json, pathlib, datetime, sys
from playwright.sync_api import sync_playwright

CDP = "http://localhost:9222"
OUT = pathlib.Path(__file__).parent

JS = (OUT / "dump_console.js").read_text()

# 콘솔 스니펫은 다운로드를 트리거하지만, playwright에서는 직접 turns를 반환시키자.
EVAL_JS = r"""
async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const scroller = document.querySelector('infinite-scroller.chat-history')
    || document.querySelector('[data-test-id="chat-history-container"]')
    || document.querySelector('infinite-scroller');
  if (!scroller) throw new Error('scroller not found');
  let last = -1, stable = 0, iter = 0;
  while (stable < 4 && iter < 2000) {
    scroller.scrollTop = 0;
    await sleep(350);
    const c = document.querySelectorAll('user-query, model-response').length;
    if (c === last) stable++; else { stable = 0; last = c; }
    iter++;
  }
  const nodes = Array.from(document.querySelectorAll('user-query, model-response'));
  return nodes.map((n, i) => {
    const isUser = n.tagName.toLowerCase() === 'user-query';
    const el = isUser
      ? (n.querySelector('.query-text') || n)
      : (n.querySelector('.markdown.markdown-main-panel') || n.querySelector('.markdown') || n);
    return { index: i, role: isUser ? 'user' : 'model',
             text: el.innerText.trim(), html: el.innerHTML };
  }).filter(t => t.text.length > 0);
}
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "gemini.google.com" in pg.url:
                page = pg; break
        if not page:
            print("❌ gemini.google.com 탭을 찾지 못함", file=sys.stderr); sys.exit(1)
        print(f"▶ attached: {page.url}")
        turns = page.evaluate(EVAL_JS)
        print(f"▶ collected {len(turns)} turns")

        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        (OUT / f"gemini-{stamp}.json").write_text(json.dumps(turns, ensure_ascii=False, indent=2))
        md = "\n---\n\n".join(
            f"## {'🧑 User' if t['role']=='user' else '🤖 Gemini'} (#{t['index']})\n\n{t['text']}\n"
            for t in turns
        )
        (OUT / f"gemini-{stamp}.md").write_text(md)
        print(f"✅ saved gemini-{stamp}.json / .md  ({len(turns)} turns)")

if __name__ == "__main__":
    main()
