#!/usr/bin/env bash
# تنزيل خطوط Noto العربية — متعدد المصادر (raw.githubusercontent قد يكون محجوباً في بعض البيئات)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
dl() { # $1=remote_path $2=local
  if curl -sSL --max-time 60 -o "$2" "https://github.com/notofonts/notofonts.github.io/raw/main/$1" && [ -s "$2" ]; then
    echo "OK(raw): $2"; return 0
  fi
  echo "raw فشل — أجرّب GitHub API…"
  python3 - "$1" "$2" <<'EOF'
import sys, json, base64, urllib.request
path, out = sys.argv[1], sys.argv[2]
d = json.load(urllib.request.urlopen(
  f"https://api.github.com/repos/notofonts/notofonts.github.io/contents/{path}", timeout=60))
open(out, "wb").write(base64.b64decode(d["content"]))
print(f"OK(api): {out}")
EOF
}
dl "fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Bold.ttf" NotoNaskhArabic-Bold.ttf
dl "fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Bold.ttf"   NotoSansArabic-Bold.ttf
# ملاحظة: config يشير إلى NotoNaskhArabic.ttf (بدون Bold) — انسخه إن لزم:
[ -f NotoNaskhArabic.ttf ] || cp NotoNaskhArabic-Bold.ttf NotoNaskhArabic.ttf
ls -la
# لاتيني: /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf (موجود غالباً)
