"""Komut satırı: python calistir.py baslangic.json komutlar.jsonl > sonuclar.jsonl

Her komut satırı modülün isle() metoduna verilir; sonuç JSONL olarak stdout'a yazılır.
"""
import json
import sys

from rezervasyon import RezervasyonSistemi


def main(argv):
    if len(argv) != 3:
        print("Kullanım: calistir baslangic.json komutlar.jsonl", file=sys.stderr)
        return 2
    # Çıktı: UTF-8 ve yalnızca '\n' satır sonu (Windows'ta da \r\n'ye çevrilmesin).
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sistem = RezervasyonSistemi.dosyadan(argv[1])
    with open(argv[2], encoding="utf-8-sig") as f:
        satirlar = [s for s in f if s.strip()]
    for no, satir in enumerate(satirlar, start=1):
        komut = json.loads(satir)
        sonuc = sistem.isle(komut)
        # Satır sırası: no, komut, durum, ardından ek alanlar.
        cikti = {"no": no, "komut": komut.get("komut"), **sonuc}
        sys.stdout.write(json.dumps(cikti, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
