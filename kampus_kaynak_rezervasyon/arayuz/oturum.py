"""Oturum: modülü (RezervasyonSistemi) ve olay günlüğünü tutar.

Arayüz bileşenleri modülün metotlarını doğrudan çağırır, ardından sonucu
kaydet() ile günlüğe yazar. Durum değişince 'degisti' sinyali bütün
görünümleri yeniler (takvim, kullanıcı paneli, saat).
"""
from PySide6.QtCore import QObject, Signal

from rezervasyon import RezervasyonSistemi

# Durumu değiştirmeyen komutlar (sonrasında yenileme gerekmez).
SALT_OKUNUR = {"fiyat", "sorgu"}


class Oturum(QObject):
    yuklendi = Signal()          # yeni başlangıç dosyası yüklendi
    degisti = Signal()           # modülün durumu değişti → her şey yenilenir
    gunluk_degisti = Signal()    # günlüğe satır eklendi / değişti

    def __init__(self):
        super().__init__()
        self.sistem: RezervasyonSistemi | None = None
        self.dosya = None
        self.gunluk = []         # [{"komut": {...}, "sonuc": {...}}]

    def yukle(self, yol: str):
        """Yeni dosya seçildiğinde tüm durum bu dosyaya göre yeniden kurulur."""
        self.sistem = RezervasyonSistemi.dosyadan(yol)
        self.dosya = yol
        self.gunluk = []
        self.yuklendi.emit()
        self.gunluk_degisti.emit()
        self.degisti.emit()

    def kaydet(self, komut: dict, sonuc: dict) -> dict:
        """Komutu ve modülün sonucunu Bölüm 5 biçiminde günlüğe ekler.
        Arka arkaya gelen fiyat satırları birleştirilir (canlı fiyat günlüğü doldurmasın)."""
        if komut["komut"] == "fiyat" and self.gunluk and self.gunluk[-1]["komut"]["komut"] == "fiyat":
            self.gunluk.pop()
        satir = {"no": len(self.gunluk) + 1, "komut": komut["komut"], **sonuc}
        self.gunluk.append({"komut": komut, "sonuc": satir})
        self.gunluk_degisti.emit()
        if komut["komut"] not in SALT_OKUNUR:
            self.degisti.emit()
        return sonuc
