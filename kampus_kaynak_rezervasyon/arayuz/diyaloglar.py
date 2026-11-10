"""Yeni kullanıcı ve yeni kaynak ekleme pencereleri.

Rol, tür, sertifika ve izinli roller başlangıç dosyasındaki değerlerden seçilir.
Pencere hiçbir değeri kendisi reddetmez; kararı modül verir ve sonuç pencerenin
içinde gösterilir. Başarılı olursa pencere kapanır.
"""
import re

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from . import tema


def sonraki_id(mevcut, on_ek):
    """Öneri: 'u' önekli en büyük numaranın bir fazlası (kullanıcı değiştirebilir)."""
    sayilar = [int(m.group(1)) for i in mevcut if (m := re.fullmatch(re.escape(on_ek) + r"(\d+)", i))]
    return f"{on_ek}{max(sayilar, default=0) + 1}"


def onay_kutulari(degerler, isaretli):
    kutu = QWidget()
    duzen = QHBoxLayout(kutu)
    duzen.setContentsMargins(0, 0, 0, 0)
    kutular = {}
    for d in degerler:
        k = QCheckBox(d)
        k.setChecked(isaretli)
        duzen.addWidget(k)
        kutular[d] = k
    duzen.addStretch()
    return kutu, kutular


class EklemePenceresi(QDialog):
    """Ortak iskelet: form + sonuç satırı + Ekle düğmesi."""

    def __init__(self, ust, oturum, baslik):
        super().__init__(ust)
        self.oturum = oturum
        self.eklenen_id = None
        self.setWindowTitle(baslik)
        self.form = QFormLayout()
        self.sonuc = QLabel()
        self.sonuc.setWordWrap(True)
        ekle = QPushButton("Ekle")
        ekle.setObjectName("birincil")
        ekle.setDefault(True)
        ekle.clicked.connect(self.gonder)
        duzen = QVBoxLayout(self)
        duzen.addLayout(self.form)
        alt = QHBoxLayout()
        alt.addWidget(self.sonuc, 1)
        alt.addWidget(ekle)
        duzen.addLayout(alt)

    def sonuc_goster(self, sonuc, kimlik):
        if sonuc["durum"] == "TAMAM":
            self.eklenen_id = kimlik
            self.accept()
        else:
            aciklama = self.oturum.sistem.aciklama(sonuc["kod"])
            self.sonuc.setText(f'<span style="color:{tema.HATA}"><b>✗ {sonuc["kod"]}</b> — {aciklama}</span>')


class KullaniciEklePenceresi(EklemePenceresi):
    def __init__(self, ust, oturum):
        super().__init__(ust, oturum, "Yeni kullanıcı")
        s = oturum.sistem
        self.secenek = s.secenekler()
        self.kimlik = QLineEdit(sonraki_id([u["id"] for u in s.kullanici_listesi()], "u"))
        self.ad = QLineEdit()
        self.rol = QComboBox()
        self.rol.addItems(self.secenek["roller"])
        sertifika_kutusu, self.sertifikalar = onay_kutulari(self.secenek["sertifikalar"], False)
        self.bakiye = QSpinBox()
        self.bakiye.setRange(-100000, 100000)      # arayüz sınırlamaz; modül denetler
        self.guven = QSpinBox()
        self.guven.setRange(-1000, 1000)
        self.guven.setValue(80)                    # örnek senaryodaki değer
        self.rol.currentTextChanged.connect(self._rol_degisti)
        self._rol_degisti(self.rol.currentText())
        for etiket, alan in (("Kimlik", self.kimlik), ("Ad", self.ad), ("Rol", self.rol),
                             ("Sertifikalar", sertifika_kutusu), ("Bakiye (KP)", self.bakiye),
                             ("Güvenilirlik", self.guven)):
            self.form.addRow(etiket, alan)
        self.ad.setFocus()

    def _rol_degisti(self, rol):
        # Anlamlı varsayılan: yeni üye haftalık kotasıyla başlar.
        self.bakiye.setValue(self.secenek["kotalar"].get(rol, 0))

    def gonder(self):
        komut = {"komut": "kullanici_ekle", "id": self.kimlik.text().strip(), "ad": self.ad.text().strip(),
                 "rol": self.rol.currentText(),
                 "sertifikalar": [s for s, k in self.sertifikalar.items() if k.isChecked()],
                 "bakiye": self.bakiye.value(), "guvenilirlik": self.guven.value()}
        sonuc = self.oturum.sistem.kullanici_ekle(komut["id"], komut["ad"], komut["rol"],
                                                  komut["sertifikalar"], komut["bakiye"], komut["guvenilirlik"])
        self.oturum.kaydet(komut, sonuc)
        self.sonuc_goster(sonuc, komut["id"])


class KaynakEklePenceresi(EklemePenceresi):
    def __init__(self, ust, oturum):
        super().__init__(ust, oturum, "Yeni kaynak")
        secenek = oturum.sistem.secenekler()
        self.kimlik = QLineEdit()
        self.ad = QLineEdit()
        self.tur = QComboBox()
        self.tur.addItems(secenek["turler"])
        rol_kutusu, self.roller = onay_kutulari(secenek["roller"], True)
        for etiket, alan in (("Kimlik", self.kimlik), ("Ad", self.ad), ("Tür", self.tur),
                             ("İzinli roller", rol_kutusu)):
            self.form.addRow(etiket, alan)
        self.kimlik.setFocus()

    def gonder(self):
        komut = {"komut": "kaynak_ekle", "id": self.kimlik.text().strip(), "ad": self.ad.text().strip(),
                 "tur": self.tur.currentText(),
                 "izinli_roller": [r for r, k in self.roller.items() if k.isChecked()]}
        sonuc = self.oturum.sistem.kaynak_ekle(komut["id"], komut["ad"], komut["tur"], komut["izinli_roller"])
        self.oturum.kaydet(komut, sonuc)
        self.sonuc_goster(sonuc, komut["id"])
