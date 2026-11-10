"""Tüm senaryoları çalıştırır: py testler/hepsini_calistir.py

Önce örnek senaryo (ornek/), sonra testler/senaryolar/ altındaki her klasör çalışır.
Her klasörde komutlar.jsonl ve beklenen.jsonl (resmi örnekte sonuclar.jsonl) bulunur. baslangic.json yoksa
testler/baslangic_test.json kullanılır. Komutlar gerçek CLI (calistir.py) üzerinden
çalıştırılır; böylece gizli testlerle aynı yol sınanmış olur.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from karsilastir import karsilastir

KOK = Path(__file__).resolve().parent.parent
TESTLER = KOK / "testler"


def senaryo_calistir(klasor: Path, varsayilan_baslangic: Path):
    baslangic = klasor / "baslangic.json"
    if not baslangic.exists():
        baslangic = varsayilan_baslangic
    sonuc = subprocess.run([sys.executable, str(KOK / "calistir.py"), str(baslangic),
                            str(klasor / "komutlar.jsonl")],
                           capture_output=True, text=True, encoding="utf-8")
    if sonuc.returncode != 0:
        print(f"  ✗ CLI hata verdi:\n{sonuc.stderr}")
        return 0, 1
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(sonuc.stdout)
        cikti = f.name
    try:
        # Resmi örnekte beklenen dosyanın adı sonuclar.jsonl; kendi senaryolarımızda beklenen.jsonl.
        beklenen = klasor / "sonuclar.jsonl"
        if not beklenen.exists():
            beklenen = klasor / "beklenen.jsonl"
        return karsilastir(cikti, beklenen, sessiz=True)
    finally:
        Path(cikti).unlink()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    klasorler = [(KOK / "ornek", KOK / "ornek" / "baslangic.json")]
    klasorler += [(k, TESTLER / "baslangic_test.json")
                  for k in sorted((TESTLER / "senaryolar").iterdir()) if k.is_dir()]
    toplam_gecen = toplam_satir = basarisiz = 0
    for klasor, varsayilan in klasorler:
        print(f"{klasor.name}:")
        gecen, satir = senaryo_calistir(klasor, varsayilan)
        print(f"  {'✓' if gecen == satir else '✗'} {gecen}/{satir}")
        toplam_gecen += gecen
        toplam_satir += satir
        basarisiz += gecen != satir
    print(f"\nTOPLAM: {toplam_gecen}/{toplam_satir} satır, "
          f"{len(klasorler) - basarisiz}/{len(klasorler)} senaryo geçti")
    return 0 if basarisiz == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
