"""
Gemini 덤프(JSON) → Markdown / Plain text 변환기

사용법:
    python convert.py gemini-2026-04-09T11-17-06-694Z.json
    python convert.py gemini-*.json --format md
    python convert.py gemini-*.json --format txt
    python convert.py gemini-*.json --format both   # 기본값

출력: 같은 폴더에 .md / .txt 생성
"""
import argparse, json, pathlib, sys, re

def to_md(turns: list[dict]) -> str:
    out = ["# Gemini 대화 백업", f"\n총 {len(turns)} turns\n", "---\n"]
    for t in turns:
        who = "🧑 User" if t["role"] == "user" else "🤖 Gemini"
        text = t["text"].strip()
        # "말씀하신 내용" 같은 Gemini UI 프리픽스 제거
        text = re.sub(r"^말씀하신 내용\s*\n+", "", text)
        out.append(f"## {who}  `#{t['index']}`\n")
        out.append(text + "\n")
        out.append("---\n")
    return "\n".join(out)

def to_txt(turns: list[dict]) -> str:
    lines = []
    bar = "=" * 70
    for t in turns:
        who = "USER" if t["role"] == "user" else "GEMINI"
        text = t["text"].strip()
        text = re.sub(r"^말씀하신 내용\s*\n+", "", text)
        lines.append(bar)
        lines.append(f"[{t['index']:04d}] {who}")
        lines.append(bar)
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file", type=pathlib.Path)
    ap.add_argument("--format", choices=["md", "txt", "both"], default="both")
    args = ap.parse_args()

    if not args.json_file.exists():
        print(f"❌ not found: {args.json_file}", file=sys.stderr); sys.exit(1)

    turns = json.loads(args.json_file.read_text(encoding="utf-8"))
    print(f"▶ loaded {len(turns)} turns from {args.json_file.name}")

    stem = args.json_file.with_suffix("")
    if args.format in ("md", "both"):
        out = stem.with_suffix(".md")
        out.write_text(to_md(turns), encoding="utf-8")
        print(f"✅ wrote {out.name} ({out.stat().st_size:,} bytes)")
    if args.format in ("txt", "both"):
        out = stem.with_suffix(".txt")
        out.write_text(to_txt(turns), encoding="utf-8")
        print(f"✅ wrote {out.name} ({out.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
