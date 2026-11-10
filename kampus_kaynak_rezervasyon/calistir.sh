#!/usr/bin/env sh
# Kullanım: ./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
DIZIN="$(cd "$(dirname "$0")" && pwd)"
# Gerçekten çalışan ilk Python yorumlayıcısını seç (python3, python, py).
for PY in python3 python py; do
    if "$PY" --version >/dev/null 2>&1; then
        exec "$PY" "$DIZIN/calistir.py" "$@"
    fi
done
echo "Python bulunamadı (3.11+ gerekli)." >&2
exit 1
