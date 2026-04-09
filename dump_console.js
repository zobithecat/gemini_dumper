/*
 * Gemini 세션 백업 스니펫
 * 사용법:
 *   1) 백업할 Gemini 대화 탭을 연다
 *   2) DevTools (Cmd+Opt+I) → Console
 *   3) 이 파일 내용 전체를 붙여넣고 Enter
 *   4) 끝나면 자동으로 JSON + Markdown 파일이 다운로드됨
 *
 * 전제: infinite-scroller.chat-history 컨테이너에서 위로 스크롤하면
 *       과거 턴들이 지연 로드됨. 더 이상 새 턴이 안 나올 때까지 반복.
 */
(async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  const scroller =
    document.querySelector('infinite-scroller.chat-history') ||
    document.querySelector('[data-test-id="chat-history-container"]') ||
    document.querySelector('infinite-scroller');
  if (!scroller) { alert('chat-history scroller not found'); return; }

  console.log('[dump] scroller:', scroller);

  // 1) 맨 위까지 반복 스크롤 — 높이가 더 이상 증가하지 않을 때까지
  let lastCount = -1, stable = 0, iter = 0;
  while (stable < 4 && iter < 2000) {
    scroller.scrollTop = 0;
    await sleep(350);
    const count = document.querySelectorAll('user-query, model-response').length;
    if (count === lastCount) stable++; else { stable = 0; lastCount = count; }
    if (iter % 10 === 0) console.log(`[dump] iter=${iter} turns=${count} stable=${stable}`);
    iter++;
  }
  console.log(`[dump] scroll done. total turn elements = ${lastCount}`);

  // 2) 순서대로 user/model 턴 수집 (DOM 순서 = 대화 순서)
  const nodes = Array.from(document.querySelectorAll('user-query, model-response'));
  const turns = nodes.map((n, i) => {
    const isUser = n.tagName.toLowerCase() === 'user-query';
    let textEl, html, text;
    if (isUser) {
      textEl = n.querySelector('.query-text') || n;
      text = textEl.innerText.trim();
      html = textEl.innerHTML;
    } else {
      textEl = n.querySelector('.markdown.markdown-main-panel')
            || n.querySelector('.markdown')
            || n.querySelector('message-content')
            || n;
      text = textEl.innerText.trim();
      html = textEl.innerHTML;
    }
    return { index: i, role: isUser ? 'user' : 'model', text, html };
  }).filter(t => t.text.length > 0);

  console.log(`[dump] collected ${turns.length} turns`);

  // 3) 파일 다운로드
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const download = (name, content, mime) => {
    const blob = new Blob([content], { type: mime });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
  };

  download(`gemini-${stamp}.json`, JSON.stringify(turns, null, 2), 'application/json');

  const md = turns.map(t =>
    `## ${t.role === 'user' ? '🧑 User' : '🤖 Gemini'} (#${t.index})\n\n${t.text}\n`
  ).join('\n---\n\n');
  download(`gemini-${stamp}.md`, md, 'text/markdown');

  const htmlDoc = `<!doctype html><meta charset="utf-8"><title>Gemini backup ${stamp}</title>
<style>body{font-family:system-ui;max-width:860px;margin:2em auto;padding:0 1em}
.turn{padding:1em;margin:1em 0;border-radius:8px}
.user{background:#e8f0fe}.model{background:#f5f5f5}
h3{margin:0 0 .5em;font-size:.9em;color:#555}</style>
${turns.map(t => `<div class="turn ${t.role}"><h3>${t.role==='user'?'User':'Gemini'} #${t.index}</h3>${t.html}</div>`).join('\n')}`;
  download(`gemini-${stamp}.html`, htmlDoc, 'text/html');

  console.log(`[dump] DONE. ${turns.length} turns saved.`);
  alert(`Gemini 백업 완료: ${turns.length} turns\nJSON/MD/HTML 3개 파일 다운로드됨`);
})();
