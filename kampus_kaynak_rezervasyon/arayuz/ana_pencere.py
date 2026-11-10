"""Ana pencere: tüm panelleri tek ekranda birleştirir ve yenilemeyi yönetir.

Düzen: üstte saat çubuğu; solda takvim + seçili rezervasyon şeridi + olay günlüğü;
sağda kullanıcı paneli + talep formu. Durumu değiştiren her işlemden sonra
oturum 'degisti' sinyalini yayar ve yenile() her şeyi günceller.
"""
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QDateEdit, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QScrollArea, QSplitter, QToolButton, QVBoxLayout, QWidget)

from . import tema
from .diyaloglar import KaynakEklePenceresi, KullaniciEklePenceresi
from .oturum import Oturum
from .paneller import DetaySeridi, KullaniciPaneli, OlayGunlugu, SaatCubugu, TalepFormu, kart
from .takvim import Takvim

ORNEK_KLASOR = Path(__file__).resolve().parent.parent / "ornek"


def renk_ornegi(renk: str, etiket: str) -> QLabel:
    """Takvim başlığındaki küçük renk açıklaması."""
    kutu = QLabel(f"■ {etiket}")
    kutu.setStyleSheet(f"color: {renk}; font-size: 9pt;")
    return kutu


class AnaPencere(QMainWindow):
    def __init__(self, oturum: Oturum):
        super().__init__()
        self.oturum = oturum
        self.setWindowTitle("Kampüs Kaynak Rezervasyon")
        self.secili_rez = None

        # --- bileşenler
        self.saat_cubugu = SaatCubugu(oturum)
        self.takvim = Takvim()
        self.detay = DetaySeridi(oturum)
        self.gunluk = OlayGunlugu(oturum)
        self.kullanici = KullaniciPaneli(oturum)
        self.form = TalepFormu(oturum)

        # --- takvim kartı: gün gezinme + açıklama + kaydırılabilir takvim
        takvim_karti, takvim_duzen = kart()
        ust = QHBoxLayout()
        geri, ileri = QToolButton(), QToolButton()
        geri.setText("◀")
        ileri.setText("▶")
        self.gun = QDateEdit()
        self.gun.setDisplayFormat("dddd, dd.MM.yyyy")
        self.gun.setCalendarPopup(True)
        bugun = QPushButton("Simüle gün")
        bugun.setToolTip("Takvimi simüle saatin gününe getir")
        kaynak_ekle = QPushButton("+ Kaynak")
        geri.clicked.connect(lambda: self.gun.setDate(self.gun.date().addDays(-1)))
        ileri.clicked.connect(lambda: self.gun.setDate(self.gun.date().addDays(1)))
        bugun.clicked.connect(self._simule_gune_git)
        kaynak_ekle.clicked.connect(self._kaynak_ekle)
        self.gun.dateChanged.connect(self._gun_degisti)
        for w in (geri, self.gun, ileri, bugun):
            ust.addWidget(w)
        ust.addSpacing(12)
        for durum in ("ONAYLI", "KULLANIMDA", "TAMAMLANDI", "IPTAL", "GELMEDI"):
            ust.addWidget(renk_ornegi(tema.DURUM_RENK[durum][1], durum))
        aciklama = QLabel("▨ hazırlık  ▧ bakım  │ simüle saat")
        aciklama.setObjectName("soluk")
        ust.addWidget(aciklama)
        ust.addStretch()
        ust.addWidget(kaynak_ekle)
        takvim_duzen.addLayout(ust)
        kaydirma = QScrollArea()
        kaydirma.setWidget(self.takvim)
        kaydirma.setWidgetResizable(True)
        kaydirma.setFrameShape(QScrollArea.NoFrame)
        takvim_duzen.addWidget(kaydirma)

        # --- yerleşim
        sol = QSplitter(Qt.Vertical)
        ust_sol = QWidget()
        ust_sol_duzen = QVBoxLayout(ust_sol)
        ust_sol_duzen.setContentsMargins(0, 0, 0, 0)
        ust_sol_duzen.setSpacing(6)
        ust_sol_duzen.addWidget(takvim_karti, 1)
        ust_sol_duzen.addWidget(self.detay)
        sol.addWidget(ust_sol)
        sol.addWidget(self.gunluk)
        sol.setSizes([560, 240])
        sag = QSplitter(Qt.Vertical)
        sag.addWidget(self.kullanici)
        sag.addWidget(self.form)
        sag.setSizes([380, 420])
        ana = QSplitter()
        ana.addWidget(sol)
        ana.addWidget(sag)
        ana.setStretchFactor(0, 1)
        ana.setSizes([1000, 420])
        kok = QWidget()
        kok.setObjectName("kok")
        kok_duzen = QVBoxLayout(kok)
        kok_duzen.setContentsMargins(8, 8, 8, 8)
        kok_duzen.setSpacing(6)
        kok_duzen.addWidget(self.saat_cubugu)
        kok_duzen.addWidget(ana, 1)
        self.setCentralWidget(kok)

        # --- bağlantılar
        oturum.degisti.connect(self.yenile)
        oturum.gunluk_degisti.connect(self.gunluk.yenile)
        oturum.yuklendi.connect(self._yuklendi)
        self.saat_cubugu.dosya_sec.connect(self.dosya_sec)
        self.saat_cubugu.ilerledi.connect(self._saat_ilerledi)
        self.takvim.rezervasyon_secildi.connect(self._rez_sec)
        self.takvim.aralik_secildi.connect(
            lambda k, b, e: self.form.aralik_ayarla(k, self.gun.date().toString("yyyy-MM-dd"), b, e))
        self.kullanici.kullanici_degisti.connect(self.form.kullanici_ayarla)
        self.kullanici.kullanici_ekle.connect(self._kullanici_ekle)
        self.kullanici.rezervasyon_secildi.connect(self._rez_ve_gun_sec)
        self.form.rezervasyon_olustu.connect(self._rez_sec)

    # ------------------------------------------------------------------ dosya
    def dosya_sec(self, ilk=False):
        yol, _ = QFileDialog.getOpenFileName(self, "Başlangıç dosyası seç", str(ORNEK_KLASOR),
                                             "JSON dosyaları (*.json)")
        if not yol:
            if ilk and (ORNEK_KLASOR / "baslangic.json").exists():
                yol = str(ORNEK_KLASOR / "baslangic.json")
            else:
                return False
        return self.yukle(yol)

    def yukle(self, yol):
        try:
            self.oturum.yukle(yol)
            return True
        except (OSError, ValueError, KeyError) as hata:
            QMessageBox.warning(self, "Dosya okunamadı", f"{yol}\n\n{hata}")
            return False

    def _yuklendi(self):
        """Yeni dosya: seçimler ve sonuçlar sıfırlanır, takvim simüle güne gelir."""
        self.secili_rez = None
        self.detay.sec(None)
        self.saat_cubugu.sifirla()
        self.kullanici.yenile()
        self.form.kullanici_ayarla(self.kullanici.secili())
        self.form.sifirla()
        self._simule_gune_git()

    # ------------------------------------------------------------------ yenileme
    def yenile(self):
        s = self.oturum.sistem
        if not s:
            return
        gun = self.gun.date().toString("yyyy-MM-dd")
        self.takvim.veri_ayarla(s.gun_gorunumu(gun), gun, s.simdi(), self.secili_rez)
        self.saat_cubugu.yenile()
        self.kullanici.yenile()
        self.form.yenile()
        self.detay.yenile()

    def _gun_degisti(self):
        self.form.gun_ayarla(self.gun.date().toString("yyyy-MM-dd"))
        self.yenile()

    def _simule_gune_git(self):
        gun = QDate.fromString(self.oturum.sistem.simdi()[:10], "yyyy-MM-dd")
        if self.gun.date() != gun:
            self.gun.setDate(gun)          # _gun_degisti → yenile
        else:
            self._gun_degisti()

    def _saat_ilerledi(self, eski, yeni):
        # Takvim simüle günü gösteriyorsa yeni güne de eşlik etsin.
        if self.gun.date().toString("yyyy-MM-dd") == eski[:10] and eski[:10] != yeni[:10]:
            self._simule_gune_git()

    # ------------------------------------------------------------------ seçim
    def _rez_sec(self, rid):
        self.secili_rez = rid
        self.takvim.secimi_ayarla(rid)
        self.detay.sec(rid)

    def _rez_ve_gun_sec(self, rid, gun):
        self.secili_rez = rid
        self.gun.setDate(QDate.fromString(gun, "yyyy-MM-dd"))
        self._rez_sec(rid)

    # ------------------------------------------------------------------ ekleme
    def _kullanici_ekle(self):
        pencere = KullaniciEklePenceresi(self, self.oturum)
        if pencere.exec() and pencere.eklenen_id:
            self.kullanici.sec(pencere.eklenen_id)

    def _kaynak_ekle(self):
        KaynakEklePenceresi(self, self.oturum).exec()
