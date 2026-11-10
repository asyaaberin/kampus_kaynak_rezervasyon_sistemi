"""Masaüstü uygulamasını başlatır.

Kullanım:  python -m arayuz                (açılışta dosya seçilir)
           python -m arayuz baslangic.json  (doğrudan bu dosyayla açılır)
"""
import sys

from PySide6.QtWidgets import QApplication

from .ana_pencere import AnaPencere
from .oturum import Oturum
from . import tema


def main():
    uygulama = QApplication(sys.argv)
    tema.uygulamayi_hazirla(uygulama)
    pencere = AnaPencere(Oturum())
    yuklendi = pencere.yukle(sys.argv[1]) if len(sys.argv) > 1 else pencere.dosya_sec(ilk=True)
    if not yuklendi:
        return 1
    pencere.resize(1480, 900)
    pencere.show()
    return uygulama.exec()


if __name__ == "__main__":
    sys.exit(main())
