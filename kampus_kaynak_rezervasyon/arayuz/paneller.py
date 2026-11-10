"""Ekrandaki paneller: saat çubuğu, kullanıcı paneli, talep formu, ayrıntı şeridi, olay günlüğü.

Kural: hiçbir panel bir talebi kendisi engellemez veya kural uygulamaz.
Her eylem modülün ilgili metodunu çağırır, sonucu oturum.kaydet() ile günlüğe
yazar ve modülün cevabını eylemin yapıldığı yerin hemen yanında gösterir.
"""
import json

from PySide6.QtCore import QDate, QDateTime, Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox, QDateEdit, QDateTimeEdit,
                               QFrame, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QProgressBar,
                               QPushButton, QRadioButton, QSplitter, QTableWidget, QTableWidgetItem,
                               QToolButton, QVBoxLayout, QWidget)

from . import tema

SAATLER = [f"{dk // 60:02d}:{dk % 60:02d}" for dk in range(8 * 60, 22 * 60 + 1, 15)]


# ---------------------------------------------------------------------------
# Küçük yardımcılar
# ---------------------------------------------------------------------------
def kart(baslik=None):
    """Beyaz kenarlıklı kutu ve içindeki dikey düzen."""
    cerceve = QFrame()
    cerceve.setObjectName("kart")
    duzen = QVBoxLayout(cerceve)
    duzen.setContentsMargins(10, 8, 10, 8)
    duzen.setSpacing(6)
    if baslik:
        etiket = QLabel(baslik)
        etiket.setObjectName("baslik")
        duzen.addWidget(etiket)
    return cerceve, duzen


def tarih_saat(t: str) -> str:
    """'2027-03-08T11:15' → '08.03 11:15'"""
    return f"{t[8:10]}.{t[5:7]} {t[11:16]}"


def olay_metni(o: dict) -> str:
    z = tarih_saat(o["zaman"])
    if o["tur"] in ("GELMEDI", "TAMAMLANDI"):
        return f'{z} {o["tur"]} {o["rezervasyon"]} ({o["kullanici"]} → güven {o["guvenilirlik"]})'
    if o["tur"] == "OTOMATIK_ATAMA":
        return (f'{z} OTOMATİK ATAMA {o["bekleme"]} → {o["rezervasyon"]} '
                f'({o["kullanici"]}, {o["ucret"]} KP, bakiye {o["bakiye"]})')
    return f'{z} {o["tur"].replace("_", " ")}'


def red_metni(sistem, kod: str) -> str:
    return f'<span style="color:{tema.HATA}"><b>✗ {kod}</b> — {sistem.aciklama(kod)}</span>'


def basari_metni(metin: str) -> str:
    return f'<span style="color:{tema.BASARI}"><b>✓</b> {metin}</span>'


def olaylar_html(olaylar) -> str:
    return "".join(f"<br>• {olay_metni(o)}" for o in olaylar)


def tablo(sutunlar):
    t = QTableWidget(0, len(sutunlar))
    t.setHorizontalHeaderLabels(sutunlar)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.verticalHeader().setDefaultSectionSize(22)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def hucre(metin, renk=None):
    oge = QTableWidgetItem(str(metin))
    if renk:
        oge.setForeground(QColor(renk))
    return oge


# ---------------------------------------------------------------------------
# Üst çubuk: dosya, simüle saat, saat ilerletme, son olaylar
# ---------------------------------------------------------------------------
class SaatCubugu(QFrame):
    dosya_sec = Signal()
    ilerledi = Signal(str, str)        # eski saat, yeni saat

    def __init__(self, oturum):
        super().__init__()
        self.setObjectName("kart")
        self.oturum = oturum
        self.dosya = QPushButton("📂")
        self.dosya.setToolTip("Başka bir başlangıç dosyası seç (tüm durum sıfırlanır)")
        self.dosya.clicked.connect(self.dosya_sec)
        self.saat = QLabel()
        self.saat.setObjectName("saat")
        self.hedef = QDateTimeEdit()
        self.hedef.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.hedef.setCalendarPopup(True)
        ilerlet = QPushButton("İlerlet")
        ilerlet.setObjectName("birincil")
        ilerlet.clicked.connect(lambda: self.ilerlet(self.hedef.dateTime().toString("yyyy-MM-ddTHH:mm")))
        self.olaylar = QLabel()
        self.olaylar.setWordWrap(True)
        self.olaylar.setTextFormat(Qt.RichText)

        ust = QHBoxLayout()
        ust.addWidget(self.dosya)
        ust.addSpacing(8)
        ust.addWidget(QLabel("⏱"))
        ust.addWidget(self.saat)
        ust.addStretch()
        for etiket, dk in (("+15 dk", 15), ("+1 sa", 60), ("+1 gün", 24 * 60)):
            d = QPushButton(etiket)
            d.clicked.connect(lambda _=False, dk=dk: self.ilerlet(self._simdi().addSecs(dk * 60)
                                                                  .toString("yyyy-MM-ddTHH:mm")))
            ust.addWidget(d)
        ust.addSpacing(8)
        ust.addWidget(self.hedef)
        ust.addWidget(ilerlet)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 6, 10, 6)
        duzen.addLayout(ust)
        duzen.addWidget(self.olaylar)

    def _simdi(self) -> QDateTime:
        return QDateTime.fromString(self.oturum.sistem.simdi(), "yyyy-MM-ddTHH:mm")

    def yenile(self):
        simdi = self._simdi()
        gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        self.saat.setText(f'{gunler[simdi.date().dayOfWeek() - 1]} {simdi.toString("dd.MM.yyyy  HH:mm")}')
        self.hedef.setDateTime(simdi)
        self.dosya.setText(f"📂 {self.oturum.dosya.replace(chr(92), '/').split('/')[-1]}")

    def sifirla(self):
        self.olaylar.setText(f'<span style="color:{tema.SOLUK_YAZI}">Saat ilerletildiğinde oluşan olaylar '
                             f'burada listelenir.</span>')

    def ilerlet(self, zaman: str):
        s = self.oturum.sistem
        eski = s.simdi()
        sonuc = self.oturum.kaydet({"komut": "saat", "zaman": zaman}, s.saat_ilerlet(zaman))
        if sonuc["durum"] == "RED":
            self.olaylar.setText(red_metni(s, sonuc["kod"]))
            return
        if sonuc["olaylar"]:
            self.olaylar.setText(f"<b>Son ilerletmede {len(sonuc['olaylar'])} olay:</b> "
                                 + " &nbsp;·&nbsp; ".join(olay_metni(o) for o in sonuc["olaylar"]))
        else:
            self.olaylar.setText(f'<span style="color:{tema.SOLUK_YAZI}">Son ilerletmede olay yok.</span>')
        self.ilerledi.emit(eski, s.simdi())


# ---------------------------------------------------------------------------
# Kullanıcı paneli
# ---------------------------------------------------------------------------
class KullaniciPaneli(QFrame):
    kullanici_degisti = Signal(str)
    rezervasyon_secildi = Signal(str, str)     # rezervasyon id, gün
    kullanici_ekle = Signal()

    def __init__(self, oturum):
        super().__init__()
        self.setObjectName("kart")
        self.oturum = oturum
        self.secim = QComboBox()
        self.secim.currentIndexChanged.connect(self._secim_degisti)
        ekle = QToolButton()
        ekle.setText("+")
        ekle.setToolTip("Yeni kullanıcı ekle")
        ekle.clicked.connect(self.kullanici_ekle)
        sorgula = QPushButton("Sorgula")
        sorgula.setToolTip("sorgu komutunu çalıştırır ve sonucu olay günlüğüne yazar")
        sorgula.clicked.connect(self.sorgula)
        self.bakiye = QProgressBar()
        self.bakiye.setStyleSheet("QProgressBar::chunk { background: #3b82f6; }")
        self.guven = QProgressBar()
        self.guven.setRange(0, 100)
        self.guven.setStyleSheet("QProgressBar::chunk { background: #8b5cf6; }")
        self.rezler = tablo(["No", "Kaynak", "Tarih", "Aralık", "Durum", "KP"])
        self.rezler.cellClicked.connect(self._rez_tiklandi)
        self.beklemeler = tablo(["No", "Kaynak", "Tarih", "Aralık"])
        self.beklemeler.setMaximumHeight(90)

        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 8, 10, 8)
        ust = QHBoxLayout()
        baslik = QLabel("Kullanıcı")
        baslik.setObjectName("baslik")
        ust.addWidget(baslik)
        ust.addWidget(self.secim, 1)
        ust.addWidget(ekle)
        ust.addWidget(sorgula)
        duzen.addLayout(ust)
        for etiket, cubuk in (("Bakiye", self.bakiye), ("Güven", self.guven)):
            satir = QHBoxLayout()
            e = QLabel(etiket)
            e.setFixedWidth(48)
            satir.addWidget(e)
            satir.addWidget(cubuk)
            duzen.addLayout(satir)
        duzen.addWidget(self.rezler, 1)
        e = QLabel("Bekleme kayıtları")
        e.setObjectName("soluk")
        duzen.addWidget(e)
        duzen.addWidget(self.beklemeler)

    def secili(self):
        return self.secim.currentData()

    def sec(self, kimlik):
        i = self.secim.findData(kimlik)
        if i >= 0:
            self.secim.setCurrentIndex(i)

    def _secim_degisti(self):
        if self.secili():
            self._bilgileri_doldur()
            self.kullanici_degisti.emit(self.secili())

    def yenile(self):
        onceki = self.secili()
        self.secim.blockSignals(True)
        self.secim.clear()
        for u in self.oturum.sistem.kullanici_listesi():
            self.secim.addItem(f'{u["id"]} · {u["ad"]}  ({u["rol"]})', u["id"])
        i = self.secim.findData(onceki)
        self.secim.setCurrentIndex(i if i >= 0 else 0)
        self.secim.blockSignals(False)
        self._bilgileri_doldur()
        if self.secili() != onceki:
            self.kullanici_degisti.emit(self.secili())

    def _bilgileri_doldur(self):
        """Panel modülün sorgu sonucunu gösterir (yenilemeler günlüğe yazılmaz)."""
        s, kimlik = self.oturum.sistem, self.secili()
        if not kimlik:
            return
        bilgi = s.sorgu("kullanici", kimlik)
        kota = next(u["kota"] for u in s.kullanici_listesi() if u["id"] == kimlik)
        self.bakiye.setRange(0, max(1, kota))
        self.bakiye.setValue(max(0, min(kota, bilgi["bakiye"])))
        self.bakiye.setFormat(f'{bilgi["bakiye"]} / {kota} KP')
        self.guven.setValue(bilgi["guvenilirlik"])
        self.guven.setFormat(f'{bilgi["guvenilirlik"]}')
        self.rezler.setRowCount(0)
        for r in bilgi["rezervasyonlar"]:
            i = self.rezler.rowCount()
            self.rezler.insertRow(i)
            renk = tema.DURUM_RENK[r["durum"]][1]
            for j, metin in enumerate((r["id"], r["kaynak"], tarih_saat(r["baslangic"])[:5],
                                       f'{r["baslangic"][11:]}–{r["bitis"][11:]}', r["durum"], r["ucret"])):
                self.rezler.setItem(i, j, hucre(metin, renk if j == 4 else None))
            self.rezler.item(i, 0).setData(Qt.UserRole, r["baslangic"][:10])
        self.beklemeler.setRowCount(0)
        for b in bilgi.get("beklemeler", []):
            i = self.beklemeler.rowCount()
            self.beklemeler.insertRow(i)
            for j, metin in enumerate((b["id"], b["kaynak"], tarih_saat(b["baslangic"])[:5],
                                       f'{b["baslangic"][11:]}–{b["bitis"][11:]}')):
                self.beklemeler.setItem(i, j, hucre(metin))

    def _rez_tiklandi(self, satir, _):
        oge = self.rezler.item(satir, 0)
        self.rezervasyon_secildi.emit(oge.text(), oge.data(Qt.UserRole))

    def sorgula(self):
        kimlik = self.secili()
        self.oturum.kaydet({"komut": "sorgu", "tur": "kullanici", "id": kimlik},
                           self.oturum.sistem.sorgu("kullanici", kimlik))


# ---------------------------------------------------------------------------
# Talep formu (tek rezervasyon veya paket)
# ---------------------------------------------------------------------------
class KalemSatiri(QWidget):
    degisti = Signal()
    sil = Signal(object)
    odaklandi = Signal(object)

    def __init__(self):
        super().__init__()
        self.kaynak = QComboBox()
        self.kaynak.setMinimumWidth(80)
        self.tarih = QDateEdit()
        self.tarih.setDisplayFormat("dd.MM.yy")
        self.tarih.setCalendarPopup(True)
        self.bas, self.bit = QComboBox(), QComboBox()
        for c in (self.bas, self.bit):
            c.setEditable(True)            # 13:10 gibi geçersiz saat de yazılabilir; modül reddeder
            c.addItems(SAATLER)
            c.setMaxVisibleItems(16)
            c.setMinimumWidth(64)
        self.bas.setCurrentText("10:00")
        self.bit.setCurrentText("11:00")
        self.kaldir = QToolButton()
        self.kaldir.setText("×")
        self.kaldir.setToolTip("Kalemi çıkar")
        self.kaldir.clicked.connect(lambda: self.sil.emit(self))
        self.fiyat = QLabel()
        self.fiyat.setMinimumWidth(60)
        self.sonuc = QLabel()

        ust = QHBoxLayout()
        ust.setContentsMargins(0, 0, 0, 0)
        for w, esneme in ((self.kaynak, 2), (self.tarih, 0), (self.bas, 1), (self.bit, 1), (self.kaldir, 0)):
            ust.addWidget(w, esneme)
        alt = QHBoxLayout()
        alt.setContentsMargins(2, 0, 0, 0)
        alt.addWidget(self.fiyat)
        alt.addWidget(self.sonuc, 1)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 2)
        duzen.setSpacing(1)
        duzen.addLayout(ust)
        duzen.addLayout(alt)

        self.kaynak.currentIndexChanged.connect(self._kullanici_degistirdi)
        self.tarih.dateChanged.connect(self._kullanici_degistirdi)
        self.bas.currentTextChanged.connect(self._kullanici_degistirdi)
        self.bit.currentTextChanged.connect(self._kullanici_degistirdi)

    def _kullanici_degistirdi(self, *_):
        self.sonuc.clear()
        self.odaklandi.emit(self)
        self.degisti.emit()

    def kaynaklari_ayarla(self, kaynaklar):
        onceki = self.kaynak.currentData()
        self.kaynak.blockSignals(True)
        self.kaynak.clear()
        for k in kaynaklar:
            self.kaynak.addItem(f'{k["id"]} · {k["ad"]}', k["id"])
        i = self.kaynak.findData(onceki)
        self.kaynak.setCurrentIndex(i if i >= 0 else 0)
        self.kaynak.blockSignals(False)

    def ayarla(self, kaynak=None, tarih=None, bas=None, bit=None):
        for w in (self.kaynak, self.tarih, self.bas, self.bit):
            w.blockSignals(True)
        if kaynak:
            self.kaynak.setCurrentIndex(self.kaynak.findData(kaynak))
        if tarih:
            self.tarih.setDate(QDate.fromString(tarih, "yyyy-MM-dd"))
        if bas:
            self.bas.setCurrentText(bas)
        if bit:
            self.bit.setCurrentText(bit)
        for w in (self.kaynak, self.tarih, self.bas, self.bit):
            w.blockSignals(False)
        self.sonuc.clear()

    def talep(self) -> dict:
        """Modüle gidecek alanlar; hiçbir denetim yapılmaz."""
        gun = self.tarih.date().toString("yyyy-MM-dd")
        return {"kaynak": self.kaynak.currentData(), "baslangic": f"{gun}T{self.bas.currentText().strip()}",
                "bitis": f"{gun}T{self.bit.currentText().strip()}"}


class TalepFormu(QFrame):
    rezervasyon_olustu = Signal(str)     # takvimde seçilecek rezervasyon

    def __init__(self, oturum):
        super().__init__()
        self.setObjectName("kart")
        self.oturum = oturum
        self.kullanici = None
        self.son_talep = None             # tek tıkla bekleme için reddedilen talep
        self.satirlar: list[KalemSatiri] = []
        self.aktif = None                 # takvimden sürüklenen aralığın yazılacağı satır
        self.gun = None

        self.tek, self.paket = QRadioButton("Tek"), QRadioButton("Paket")
        self.tek.setChecked(True)
        grup = QButtonGroup(self)
        grup.addButton(self.tek)
        grup.addButton(self.paket)
        self.paket.toggled.connect(self._mod_degisti)
        self.kalem_ekle = QPushButton("+ Kalem")
        self.kalem_ekle.clicked.connect(lambda: self._satir_ekle(kopyala=True))
        self.gonder = QPushButton("Rezervasyon yap")
        self.gonder.setObjectName("birincil")
        self.gonder.clicked.connect(self._gonder)
        self.beklemeye = QPushButton("Beklemeye yazıl")
        self.beklemeye.setToolTip("Bu aralık için doğrudan bekleme kaydı açtırır")
        self.beklemeye.clicked.connect(lambda: self._bekleme_ac(self.satirlar[0].talep()))
        self.toplam = QLabel()
        self.sonuc = QLabel()
        self.sonuc.setWordWrap(True)
        self.sonuc.setTextFormat(Qt.RichText)
        self.bekleme_ac = QPushButton("Bekleme aç")
        self.bekleme_ac.setToolTip("Reddedilen aynı talep için bekleme kaydı aç")
        self.bekleme_ac.clicked.connect(lambda: self._bekleme_ac(self.son_talep))
        self.bekleme_ac.hide()

        self.fiyat_zamanlayici = QTimer(self)
        self.fiyat_zamanlayici.setSingleShot(True)
        self.fiyat_zamanlayici.setInterval(250)
        self.fiyat_zamanlayici.timeout.connect(lambda: self.fiyat_hesapla(gunluge=True))

        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 8, 10, 8)
        ust = QHBoxLayout()
        baslik = QLabel("Talep")
        baslik.setObjectName("baslik")
        ust.addWidget(baslik)
        ust.addStretch()
        ust.addWidget(self.tek)
        ust.addWidget(self.paket)
        duzen.addLayout(ust)
        ipucu = QLabel("Kaynak · tarih · başlangıç · bitiş  (takvimde sürükleyerek de doldurulur)")
        ipucu.setObjectName("soluk")
        duzen.addWidget(ipucu)
        self.satir_kutusu = QVBoxLayout()
        self.satir_kutusu.setSpacing(2)
        duzen.addLayout(self.satir_kutusu)
        orta = QHBoxLayout()
        orta.addWidget(self.kalem_ekle)
        orta.addStretch()
        orta.addWidget(self.toplam)
        duzen.addLayout(orta)
        dugmeler = QHBoxLayout()
        dugmeler.addWidget(self.gonder, 1)
        dugmeler.addWidget(self.beklemeye)
        duzen.addLayout(dugmeler)
        sonuc = QHBoxLayout()
        sonuc.addWidget(self.sonuc, 1)
        sonuc.addWidget(self.bekleme_ac, 0, Qt.AlignTop)
        duzen.addLayout(sonuc)
        duzen.addStretch()
        self._satir_ekle()
        self._mod_degisti()

    # --- satır yönetimi
    def _satir_ekle(self, kopyala=False):
        satir = KalemSatiri()
        satir.kaynaklari_ayarla(self.oturum.sistem.kaynak_listesi() if self.oturum.sistem else [])
        if kopyala and self.satirlar:
            onceki = self.satirlar[-1].talep()
            satir.ayarla(tarih=onceki["baslangic"][:10], bas=onceki["baslangic"][11:], bit=onceki["bitis"][11:])
        elif self.gun:
            satir.ayarla(tarih=self.gun)
        satir.degisti.connect(self._form_degisti)
        satir.sil.connect(self._satir_sil)
        satir.odaklandi.connect(lambda s: setattr(self, "aktif", s))
        self.satirlar.append(satir)
        self.satir_kutusu.addWidget(satir)
        self._gorunumu_guncelle()
        self._form_degisti()

    def _satir_sil(self, satir):
        if len(self.satirlar) <= 1:
            return
        self.satirlar.remove(satir)
        satir.deleteLater()
        if self.aktif is satir:
            self.aktif = None
        self._gorunumu_guncelle()
        self._form_degisti()

    def _mod_degisti(self):
        paket = self.paket.isChecked()
        # Paket modu iki kalemle başlar (anlamlı varsayılan); kalem sayısını modül denetler.
        if paket and len(self.satirlar) == 1:
            self._satir_ekle(kopyala=True)
        while not paket and len(self.satirlar) > 1:
            self.satirlar.pop().deleteLater()
        self.gonder.setText("Paketi gönder" if paket else "Rezervasyon yap")
        self._sonucu_temizle()
        self._gorunumu_guncelle()
        self._form_degisti()

    def _gorunumu_guncelle(self):
        paket = self.paket.isChecked()
        self.kalem_ekle.setVisible(paket)
        self.beklemeye.setVisible(not paket)
        self.toplam.setVisible(paket)
        for s in self.satirlar:
            s.kaldir.setVisible(paket)

    # --- dışarıdan gelen ayarlar
    def kullanici_ayarla(self, kimlik):
        self.kullanici = kimlik
        self._form_degisti()

    def gun_ayarla(self, gun):
        self.gun = gun
        for s in self.satirlar:
            s.ayarla(tarih=gun)
        self.fiyat_hesapla(gunluge=False)

    def aralik_ayarla(self, kaynak, gun, bas, bit):
        satir = self.aktif if self.aktif in self.satirlar else self.satirlar[0]
        satir.ayarla(kaynak, gun, bas, bit)
        self._form_degisti()

    def yenile(self):
        """Durum değişince: kaynak listesi ve fiyatlar güncellenir (günlüğe yazmadan)."""
        kaynaklar = self.oturum.sistem.kaynak_listesi()
        for s in self.satirlar:
            s.kaynaklari_ayarla(kaynaklar)
        self.fiyat_hesapla(gunluge=False)

    def sifirla(self):
        self.tek.setChecked(True)
        self._sonucu_temizle()
        self.yenile()

    # --- fiyat
    def _form_degisti(self):
        self.fiyat_zamanlayici.start()

    def fiyat_hesapla(self, gunluge: bool):
        """Her kalem için modülün fiyat fonksiyonu çağrılır (bakiye dışındaki tüm kontroller).
        Yalnız tek talepte ve kullanıcı formu değiştirdiğinde günlüğe yazılır."""
        s = self.oturum.sistem
        if not s or not self.kullanici:
            return
        toplam, hepsi_tamam = 0, True
        for satir in self.satirlar:
            t = satir.talep()
            sonuc = s.fiyat(self.kullanici, t["kaynak"], t["baslangic"], t["bitis"])
            if gunluge and self.tek.isChecked():
                self.oturum.kaydet({"komut": "fiyat", "kullanici": self.kullanici, **t}, sonuc)
            if sonuc["durum"] == "TAMAM":
                satir.fiyat.setText(f'<b>{sonuc["ucret"]} KP</b>')
                satir.fiyat.setToolTip("")
                toplam += sonuc["ucret"]
            else:
                hepsi_tamam = False
                satir.fiyat.setText(f'<span style="color:{tema.SOLUK_YAZI}">— {sonuc["kod"]}</span>')
                satir.fiyat.setToolTip(s.aciklama(sonuc["kod"]))
        self.toplam.setText(f"Toplam: <b>{toplam} KP</b>" if hepsi_tamam else "Toplam: —")

    # --- gönderme
    def _sonucu_temizle(self):
        self.sonuc.clear()
        self.bekleme_ac.hide()
        for satir in self.satirlar:
            satir.sonuc.clear()

    def _bekleyen_fiyati_yaz(self):
        """Gönderimden önce bekleyen canlı fiyat hesabı hemen yapılır;
        böylece günlükte sıra her zaman 'fiyat → talep' olur."""
        if self.fiyat_zamanlayici.isActive():
            self.fiyat_zamanlayici.stop()
            self.fiyat_hesapla(gunluge=True)

    def _gonder(self):
        self._bekleyen_fiyati_yaz()
        self._sonucu_temizle()
        s, u = self.oturum.sistem, self.kullanici
        if self.tek.isChecked():
            t = self.satirlar[0].talep()
            sonuc = s.rezervasyon(u, t["kaynak"], t["baslangic"], t["bitis"])
            self.oturum.kaydet({"komut": "rezervasyon", "kullanici": u, **t}, sonuc)
            if sonuc["durum"] == "TAMAM":
                self.sonuc.setText(basari_metni(f'<b>{sonuc["rezervasyon_id"]}</b> alındı · '
                                                f'{sonuc["ucret"]} KP · yeni bakiye {sonuc["bakiye"]}'))
                self.rezervasyon_olustu.emit(sonuc["rezervasyon_id"])
            else:
                self.sonuc.setText(red_metni(s, sonuc["kod"]))
                # K9: yalnız bu iki kodda aynı talep için bekleme önerilir (kod modülden gelir).
                if sonuc["kod"] in ("KESISME", "HAZIRLIK_IHLALI"):
                    self.son_talep = t
                    self.bekleme_ac.show()
            return
        kalemler = [satir.talep() for satir in self.satirlar]
        sonuc = s.paket(u, kalemler)
        self.oturum.kaydet({"komut": "paket", "kullanici": u, "kalemler": kalemler}, sonuc)
        if sonuc["durum"] == "TAMAM":
            self.sonuc.setText(basari_metni(f'<b>{sonuc["paket_id"]}</b> alındı: {", ".join(sonuc["rezervasyonlar"])}'
                                            f' · toplam {sonuc["toplam"]} KP · yeni bakiye {sonuc["bakiye"]}'))
            for satir, rid, ucret in zip(self.satirlar, sonuc["rezervasyonlar"], sonuc["ucretler"]):
                satir.sonuc.setText(basari_metni(f"{rid} · {ucret} KP"))
            self.rezervasyon_olustu.emit(sonuc["rezervasyonlar"][0])
            return
        self.sonuc.setText(red_metni(s, sonuc["kod"]))
        # PAKET_RED: her kalemin sonucu kendi satırında
        for k in sonuc.get("kalemler", []):
            if k["sira"] < len(self.satirlar):
                satir = self.satirlar[k["sira"]]
                satir.sonuc.setText(basari_metni("geçti") if k["durum"] == "TAMAM"
                                    else red_metni(s, k["kod"]))

    def _bekleme_ac(self, t):
        if not t:
            return
        self._bekleyen_fiyati_yaz()
        self._sonucu_temizle()
        s, u = self.oturum.sistem, self.kullanici
        sonuc = s.bekleme(u, t["kaynak"], t["baslangic"], t["bitis"])
        self.oturum.kaydet({"komut": "bekleme", "kullanici": u, **t}, sonuc)
        if sonuc["durum"] == "TAMAM":
            self.sonuc.setText(basari_metni(f'Bekleme kaydı <b>{sonuc["bekleme_id"]}</b> açıldı · '
                                            f'{t["kaynak"]} listesinde sıra {sonuc["sira"]}'))
        else:
            self.sonuc.setText(red_metni(s, sonuc["kod"]))


# ---------------------------------------------------------------------------
# Seçili rezervasyonun ayrıntı şeridi ve eylemleri (giriş / çıkış / iptal)
# ---------------------------------------------------------------------------
class DetaySeridi(QFrame):
    def __init__(self, oturum):
        super().__init__()
        self.setObjectName("kart")
        self.oturum = oturum
        self.rid = None
        self.bilgi = QLabel()
        self.bilgi.setTextFormat(Qt.RichText)
        self.sonuc = QLabel()
        self.sonuc.setWordWrap(True)
        self.sonuc.setTextFormat(Qt.RichText)
        self.dugmeler = []
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 6, 10, 6)
        ust = QHBoxLayout()
        ust.addWidget(self.bilgi, 1)
        # Düğmeler her durumda tıklanabilir: uygun olmayan durumda modül DURUM_HATASI döner.
        for etiket, komut in (("Giriş", "giris"), ("Çıkış", "cikis"), ("İptal", "iptal")):
            d = QPushButton(etiket)
            d.clicked.connect(lambda _=False, k=komut: self._eylem(k))
            ust.addWidget(d)
            self.dugmeler.append(d)
        duzen.addLayout(ust)
        duzen.addWidget(self.sonuc)
        self.sec(None)

    def sec(self, rid):
        self.rid = rid
        self.sonuc.clear()
        self.yenile()

    def yenile(self):
        bilgi = self.oturum.sistem.rezervasyon_bilgisi(self.rid) if self.rid and self.oturum.sistem else None
        for d in self.dugmeler:
            d.setEnabled(bilgi is not None)
        if not bilgi:
            self.bilgi.setText(f'<span style="color:{tema.SOLUK_YAZI}">Ayrıntı ve giriş/çıkış/iptal için '
                               f'takvimde bir rezervasyona tıklayın.</span>')
            return
        renk = tema.DURUM_RENK[bilgi["durum"]][1]
        paket = f' · paket {bilgi["paket"]}' if bilgi["paket"] else " · paket yok"
        self.bilgi.setText(
            f'<b>{bilgi["id"]}</b> · {bilgi["kullanici"]} {bilgi["kullanici_ad"]} · <b>{bilgi["kaynak"]}</b> · '
            f'{tarih_saat(bilgi["baslangic"])}–{bilgi["bitis"][11:]} · {bilgi["ucret"]} KP · '
            f'<span style="color:{renk}"><b>{bilgi["durum"]}</b></span>{paket}')

    def _eylem(self, komut):
        s = self.oturum.sistem
        sonuc = getattr(s, komut)(self.rid)        # s.giris / s.cikis / s.iptal
        self.oturum.kaydet({"komut": komut, "rezervasyon": self.rid}, sonuc)
        if sonuc["durum"] == "RED":
            self.sonuc.setText(red_metni(s, sonuc["kod"]))
        elif komut == "giris":
            self.sonuc.setText(basari_metni(f'Giriş yapıldı → {sonuc["yeni_durum"]}'))
        elif komut == "cikis":
            self.sonuc.setText(basari_metni(f'Çıkış yapıldı → {sonuc["yeni_durum"]} · güven {sonuc["guvenilirlik"]}')
                               + (olaylar_html(sonuc["olaylar"]) or " · bekleyen atama yok"))
        else:
            self.sonuc.setText(basari_metni(f'İptal edildi · iade {sonuc["iade"]} KP · bakiye {sonuc["bakiye"]} · '
                                            f'güven {sonuc["guvenilirlik"]}')
                               + (olaylar_html(sonuc["olaylar"]) or " · bekleyen atama yok"))


# ---------------------------------------------------------------------------
# Olay günlüğü: tüm sonuçlar sırayla; seçili satırın komut ve sonuç JSON'u
# ---------------------------------------------------------------------------
def komut_ozeti(k: dict) -> str:
    ad = k["komut"]
    if ad in ("rezervasyon", "fiyat", "bekleme"):
        return f'{ad} {k["kullanici"]} {k["kaynak"]} {tarih_saat(k["baslangic"])}–{k["bitis"][11:]}'
    if ad == "paket":
        return f'paket {k["kullanici"]} ({len(k["kalemler"])} kalem)'
    if ad in ("iptal", "giris", "cikis"):
        return f'{ad} {k["rezervasyon"]}'
    if ad == "saat":
        return f'saat → {tarih_saat(k["zaman"])}'
    if ad == "sorgu":
        return f'sorgu {k["tur"]} {k["id"]}'
    return f'{ad} {k.get("id", "")}'


def sonuc_ozeti(s: dict) -> str:
    if s["durum"] == "RED":
        return s["kod"]
    ad = s["komut"]
    if ad == "rezervasyon":
        return f'{s["rezervasyon_id"]} · {s["ucret"]} KP · bakiye {s["bakiye"]}'
    if ad == "paket":
        return f'{s["paket_id"]} {s["rezervasyonlar"]} · toplam {s["toplam"]}'
    if ad == "fiyat":
        return f'{s["ucret"]} KP'
    if ad == "saat":
        return f'{len(s["olaylar"])} olay'
    if ad == "iptal":
        return f'iade {s["iade"]} · bakiye {s["bakiye"]} · {len(s["olaylar"])} atama'
    if ad in ("giris", "cikis"):
        return s["yeni_durum"]
    if ad == "bekleme":
        return f'{s["bekleme_id"]} · sıra {s["sira"]}'
    if ad == "sorgu":
        return f'bakiye {s["bakiye"]}' if "bakiye" in s else f'{len(s["doluluk"])} kayıt'
    return ""


class OlayGunlugu(QFrame):
    def __init__(self, oturum):
        super().__init__()
        self.setObjectName("kart")
        self.oturum = oturum
        self.tablo = tablo(["No", "Komut", "Durum", "Sonuç"])
        self.tablo.currentCellChanged.connect(lambda satir, *_: self._goster(satir))
        self.komut_json = QPlainTextEdit()
        self.sonuc_json = QPlainTextEdit()
        for w in (self.komut_json, self.sonuc_json):
            w.setReadOnly(True)
            w.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        sag = QWidget()
        sag_duzen = QVBoxLayout(sag)
        sag_duzen.setContentsMargins(0, 0, 0, 0)
        for etiket, alan in (("Komut", self.komut_json), ("Sonuç", self.sonuc_json)):
            e = QLabel(etiket)
            e.setObjectName("soluk")
            sag_duzen.addWidget(e)
            sag_duzen.addWidget(alan)
        bolucu = QSplitter()
        bolucu.addWidget(self.tablo)
        bolucu.addWidget(sag)
        bolucu.setSizes([520, 380])
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 8, 10, 8)
        baslik = QLabel("Olay günlüğü")
        baslik.setObjectName("baslik")
        duzen.addWidget(baslik)
        duzen.addWidget(bolucu)

    def yenile(self):
        g = self.oturum.gunluk
        self.tablo.blockSignals(True)
        self.tablo.setRowCount(len(g))
        for i, kayit in enumerate(g):
            k, s = kayit["komut"], kayit["sonuc"]
            renk = tema.BASARI if s["durum"] == "TAMAM" else tema.HATA
            for j, metin in enumerate((s["no"], komut_ozeti(k), s["durum"], sonuc_ozeti(s))):
                self.tablo.setItem(i, j, hucre(metin, renk if j == 2 else None))
        self.tablo.blockSignals(False)
        if g:                                   # en son işlem seçili gelir
            self.tablo.setCurrentCell(len(g) - 1, 0)
            self.tablo.scrollToBottom()
            self._goster(len(g) - 1)
        else:
            self.komut_json.clear()
            self.sonuc_json.clear()

    def _goster(self, satir):
        if 0 <= satir < len(self.oturum.gunluk):
            kayit = self.oturum.gunluk[satir]
            # Bölüm 5 biçimi: komut dosyası satırı ve sonuç dosyası satırı (JSON Lines)
            self.komut_json.setPlainText(json.dumps(kayit["komut"], ensure_ascii=False, separators=(",", ":")))
            self.sonuc_json.setPlainText(json.dumps(kayit["sonuc"], ensure_ascii=False, separators=(",", ":")))
