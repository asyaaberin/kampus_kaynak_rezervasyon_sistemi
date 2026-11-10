"""Çıktı ile beklenen sonucu satır satır ve alan alan karşılaştırır.

Kullanım: python testler/karsilastir.py cikti.jsonl beklenen.jsonl

Gizli testlerdeki kural: fazladan alan serbesttir (iç içe sözlüklerde de),
eksik veya farklı alan hatadır. Listelerde uzunluk ve sıra aynı olmalıdır.
"""
import json
import sys


def farklar(gercek, beklenen, yol=""):
    """Beklenen değerdeki her alanı gerçek değerde arar; farkları liste olarak döndürür."""
    if isinstance(beklenen, dict):
        if not isinstance(gercek, dict):
            return [f"{yol or '.'}: sözlük bekleniyordu, gelen {gercek!r}"]
        sonuc = []
        for anahtar, deger in beklenen.items():
            alt_yol = f"{yol}.{anahtar}" if yol else anahtar
            if anahtar not in gercek:
                sonuc.append(f"{alt_yol}: EKSİK (beklenen {deger!r})")
            else:
                sonuc += farklar(gercek[anahtar], deger, alt_yol)
        return sonuc
    if isinstance(beklenen, list):
        if not isinstance(gercek, list):
            return [f"{yol}: liste bekleniyordu, gelen {gercek!r}"]
        if len(gercek) != len(beklenen):
            return [f"{yol}: uzunluk {len(gercek)}, beklenen {len(beklenen)}\n"
                    f"      gelen   : {json.dumps(gercek, ensure_ascii=False)}\n"
                    f"      beklenen: {json.dumps(beklenen, ensure_ascii=False)}"]
        sonuc = []
        for i, (g, b) in enumerate(zip(gercek, beklenen)):
            sonuc += farklar(g, b, f"{yol}[{i}]")
        return sonuc
    # bool ile int'i ayır (True == 1 sayılmasın)
    if gercek != beklenen or (type(gercek) is bool) != (type(beklenen) is bool):
        return [f"{yol}: gelen {gercek!r}, beklenen {beklenen!r}"]
    return []


def oku(yol):
    with open(yol, encoding="utf-8-sig") as f:
        return [json.loads(s) for s in f if s.strip()]


def karsilastir(cikti_yolu, beklenen_yolu, sessiz=False):
    """(geçen, toplam) döndürür ve farkları ekrana yazar."""
    cikti, beklenen = oku(cikti_yolu), oku(beklenen_yolu)
    gecen = 0
    for i, b in enumerate(beklenen):
        g = cikti[i] if i < len(cikti) else None
        hatalar = ["satır yok"] if g is None else farklar(g, b)
        if hatalar:
            print(f"  ✗ satır {i + 1} ({b.get('komut')}):")
            for h in hatalar:
                print(f"      {h}")
        else:
            gecen += 1
    if len(cikti) > len(beklenen):
        print(f"  ✗ çıktıda {len(cikti) - len(beklenen)} fazla satır var")
    if not sessiz:
        print(f"{gecen}/{len(beklenen)} satır geçti")
    return gecen, len(beklenen)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    g, t = karsilastir(sys.argv[1], sys.argv[2])
    sys.exit(0 if g == t else 1)
