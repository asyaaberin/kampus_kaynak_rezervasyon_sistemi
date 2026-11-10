"""Kaynak takvimi: kaynaklar satır, yatay eksen 08:00-22:00, 15 dakikalık ızgara.

Yalnızca çizim ve fare etkileşimi yapar; gösterdiği veri modülün gun_gorunumu()
fonksiyonundan gelir. Boş alana sürüklemek bir aralık seçer (talep formunu doldurur),
kutuya tıklamak rezervasyonu seçer.
"""
from PySide6.QtCore import QRectF, Qt, Signal, QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from . import tema

GUN_BAS_DK, GUN_DK = 8 * 60, 14 * 60   # görünür eksen: 08:00 + 840 dk
SOL, SAG = 120, 10                    # sol etiket sütunu ve sağ boşluk (piksel)
SATIR_PAY = 6                         # satır yükseklikleri yazı tipinden hesaplanır (yüksek DPI)


def dakika(zaman: str, gun: str) -> int:
    """'YYYY-AA-GGTSS:DD' → gösterilen günün 08:00'inden itibaren dakika (eksene kırpılır)."""
    if zaman[:10] < gun:
        return 0
    if zaman[:10] > gun:
        return GUN_DK
    dk = int(zaman[11:13]) * 60 + int(zaman[14:16]) - GUN_BAS_DK
    return max(0, min(GUN_DK, dk))


def ss_dd(dk: int) -> str:
    dk += GUN_BAS_DK
    return f"{dk // 60:02d}:{dk % 60:02d}"


def seritlere_dagit(rezervasyonlar):
    """Kutuları üst üste binmeyecek şekilde şeritlere yerleştirir.
    Etkin kutular (ONAYLI/KULLANIMDA/TAMAMLANDI) önce yerleşir ve ana şeridi alır;
    onlarla çakışan IPTAL/GELMEDI kutuları alt şeritlere iner."""
    seritler, atama = [], {}
    sirali = sorted(rezervasyonlar, key=lambda r: (r["durum"] in tema.SOLUK_DURUMLAR,
                                                    r["baslangic"], int(r["id"][1:])))
    for r in sirali:
        b, e = r["baslangic"], r["hazirlik_bitis"] or r["bitis"]
        for i, serit in enumerate(seritler):
            if all(e <= b2 or b >= e2 for b2, e2 in serit):
                serit.append((b, e))
                atama[r["id"]] = i
                break
        else:
            seritler.append([(b, e)])
            atama[r["id"]] = len(seritler) - 1
    return atama, max(1, len(seritler))


class Takvim(QWidget):
    rezervasyon_secildi = Signal(str)          # rezervasyon id
    aralik_secildi = Signal(str, str, str)     # kaynak id, "SS:DD", "SS:DD"

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumWidth(720)
        self.gun, self.simdi, self.secili = "", "", None
        self.yerlesim = []        # çizim için hesaplanmış satırlar
        self.kutular = []         # (QRectF, rezervasyon) — tıklama/ipucu için
        self.surukle = None       # (kaynak id, başlangıç dk, bitiş dk)
        self._olculeri_hesapla()

    def _olculeri_hesapla(self):
        """Yükseklikler yazı tipinin gerçek ölçüsünden gelir; ekran ölçeği (%125, %150)
        büyüse de yazılar satırlara sığar."""
        normal = self.fontMetrics().height()
        kucuk = QFont(self.font())
        kucuk.setPointSizeF(self.font().pointSizeF() * 0.85)
        self.kucuk_h = QFontMetrics(kucuk).height()
        self.serit_h = max(24, self.kucuk_h + 10)          # bir kutu şeridi
        self.grup_h = self.kucuk_h + 6                     # tür başlığı satırı
        self.etiket_h = normal + self.kucuk_h + 8          # kaynak adı (iki satır)
        self.ust = self.kucuk_h + 14                       # saat etiketleri

    # ------------------------------------------------------------------ veri
    def veri_ayarla(self, satirlar, gun: str, simdi: str, secili):
        self.gun, self.simdi, self.secili = gun, simdi, secili
        self._olculeri_hesapla()
        self.yerlesim, y, onceki_tur = [], self.ust, None
        for s in satirlar:
            if s["tur"] != onceki_tur:      # tür değişince grup başlığı
                self.yerlesim.append({"grup": f'{s["tur"]}  ·  hazırlık {s["hazirlik_dk"]} dk',
                                      "y": y, "h": self.grup_h})
                y += self.grup_h
                onceki_tur = s["tur"]
            atama, serit_sayisi = seritlere_dagit(s["rezervasyonlar"])
            h = max(serit_sayisi * self.serit_h + SATIR_PAY, self.etiket_h)
            self.yerlesim.append({"satir": s, "y": y, "h": h, "atama": atama})
            y += h
        self.setMinimumHeight(y + 4)
        self.update()

    def secimi_ayarla(self, rid):
        self.secili = rid
        self.update()

    # ------------------------------------------------------------------ geometri
    def _x(self, dk: float) -> float:
        return SOL + dk / GUN_DK * (self.width() - SOL - SAG)

    def _dk(self, x: float) -> int:
        """Piksel → 15 dakikaya yuvarlanmış dakika."""
        oran = (x - SOL) / max(1, self.width() - SOL - SAG)
        return max(0, min(GUN_DK, round(oran * GUN_DK / 15) * 15))

    def _satir_bul(self, y):
        for ogeler in self.yerlesim:
            if "satir" in ogeler and ogeler["y"] <= y < ogeler["y"] + ogeler["h"]:
                return ogeler
        return None

    def _kutu_bul(self, nokta):
        for rect, r in reversed(self.kutular):
            if rect.contains(nokta):
                return r
        return None

    # ------------------------------------------------------------------ çizim
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#ffffff"))
        alt = self.yerlesim[-1]["y"] + self.yerlesim[-1]["h"] if self.yerlesim else self.ust
        self.kutular = []

        # Satır zeminleri ve etiketler
        kalin = QFont(self.font()); kalin.setBold(True)
        kucuk = QFont(self.font()); kucuk.setPointSizeF(self.font().pointSizeF() * 0.85)
        for i, o in enumerate(self.yerlesim):
            r = QRectF(0, o["y"], self.width(), o["h"])
            if "grup" in o:
                p.fillRect(r, tema.GRUP_ZEMIN)
                p.setPen(QColor("#334155")); p.setFont(kucuk)
                p.drawText(r.adjusted(8, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, o["grup"])
                continue
            if i % 2:
                p.fillRect(r, QColor("#fbfdff"))
            p.setPen(QColor("#e2e8f0")); p.drawLine(QPointF(0, r.bottom()), QPointF(self.width(), r.bottom()))
            p.setPen(QColor("#0f172a")); p.setFont(kalin)
            ust_satir = self.etiket_h - self.kucuk_h - 6
            p.drawText(QRectF(8, o["y"] + 3, SOL - 12, ust_satir), Qt.AlignLeft, o["satir"]["id"])
            p.setPen(QColor(tema.SOLUK_YAZI)); p.setFont(kucuk)
            p.drawText(QRectF(8, o["y"] + 3 + ust_satir, SOL - 12, self.kucuk_h), Qt.AlignLeft,
                       p.fontMetrics().elidedText(o["satir"]["ad"], Qt.ElideRight, SOL - 12))

        # Izgara: her saat koyu, her 15 dakika soluk çizgi; üstte saat etiketleri
        p.setFont(kucuk)
        for dk in range(0, GUN_DK + 1, 15):
            x = self._x(dk)
            saat_basi = dk % 60 == 0
            p.setPen(QPen(tema.IZGARA_SAAT if saat_basi else tema.IZGARA_CEYREK, 1))
            p.drawLine(QPointF(x, self.ust - (6 if saat_basi else 2)), QPointF(x, alt))
            if saat_basi:
                p.setPen(QColor("#475569"))
                p.drawText(QRectF(x - 20, 2, 40, self.ust - 8), Qt.AlignCenter, ss_dd(dk)[:2])

        # Bakım pencereleri, hazırlık kuyrukları ve rezervasyon kutuları
        p.setFont(kucuk)
        for o in self.yerlesim:
            if "satir" not in o:
                continue
            for b in o["satir"]["bakimlar"]:
                x1, x2 = self._x(dakika(b["baslangic"], self.gun)), self._x(dakika(b["bitis"], self.gun))
                if x2 <= x1:
                    continue
                r = QRectF(x1, o["y"] + 2, x2 - x1, o["h"] - 4)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#e2e8f0")); p.drawRect(r)
                p.setBrush(QBrush(tema.BAKIM_RENK, Qt.BDiagPattern)); p.drawRect(r)
                p.setPen(QColor("#1e293b"))
                p.drawText(r, Qt.AlignCenter, "BAKIM")
            for rez in o["satir"]["rezervasyonlar"]:
                self._kutu_ciz(p, rez, o["y"] + 3 + o["atama"][rez["id"]] * self.serit_h)

        # Simüle saat çizgisi (yalnız gösterilen gün simüle günse)
        if self.simdi[:10] == self.gun:
            dk = int(self.simdi[11:13]) * 60 + int(self.simdi[14:16]) - GUN_BAS_DK
            if 0 <= dk <= GUN_DK:
                x = self._x(dk)
                p.setPen(QPen(tema.SAAT_CIZGISI, 2))
                p.drawLine(QPointF(x, self.ust - 4), QPointF(x, alt))
                p.setBrush(tema.SAAT_CIZGISI); p.setPen(Qt.NoPen)
                p.drawPolygon([QPointF(x - 5, self.ust - 10), QPointF(x + 5, self.ust - 10), QPointF(x, self.ust - 3)])

        # Sürükleme ile seçilen aralık
        if self.surukle:
            o = next((o for o in self.yerlesim if "satir" in o and o["satir"]["id"] == self.surukle[0]), None)
            if o:
                b, e = sorted(self.surukle[1:])
                r = QRectF(self._x(b), o["y"] + 1, self._x(e) - self._x(b), o["h"] - 2)
                p.setPen(QPen(QColor("#2563eb"), 1, Qt.DashLine)); p.setBrush(tema.SURUKLE_ZEMIN)
                p.drawRect(r)
                p.setPen(QColor("#1d4ed8"))
                p.drawText(r, Qt.AlignCenter, f"{ss_dd(b)}–{ss_dd(e)}")
        p.end()

    def _kutu_ciz(self, p: QPainter, rez, y):
        dolgu, kenar, yazi = tema.DURUM_RENK[rez["durum"]]
        b, e = dakika(rez["baslangic"], self.gun), dakika(rez["bitis"], self.gun)
        x1, x2 = self._x(b), self._x(e)
        # Hazırlık kuyruğu (soğuma/havalandırma): kutunun ardında açık taralı alan
        if rez["hazirlik_bitis"]:
            hx = self._x(dakika(rez["hazirlik_bitis"], self.gun))
            if hx > x2:
                kuyruk = QRectF(x2, y + 3, hx - x2, self.serit_h - 8)
                renk = QColor(kenar); renk.setAlpha(110)
                p.setPen(Qt.NoPen); p.setBrush(QBrush(renk, Qt.FDiagPattern)); p.drawRect(kuyruk)
        r = QRectF(x1 + 1, y, max(3.0, x2 - x1 - 2), self.serit_h - 2)
        p.setPen(QPen(QColor(kenar), 1)); p.setBrush(QColor(dolgu))
        p.drawRoundedRect(r, 3, 3)
        if rez["durum"] in tema.SOLUK_DURUMLAR:
            tarama = QColor(kenar); tarama.setAlpha(70)
            p.setBrush(QBrush(tarama, Qt.BDiagPattern)); p.drawRoundedRect(r, 3, 3)
        if rez["id"] == self.secili:
            p.setPen(QPen(tema.SECIM_KENAR, 2.5)); p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(-1, -1, 1, 1), 3, 3)
        # Yazı: sığdığı kadar ayrıntı (yoğun günde okunabilirlik)
        p.setPen(QColor(yazi))
        fm = p.fontMetrics()
        for metin in (f'{rez["id"]} · {rez["kullanici"]} · {rez["ucret"]} KP', f'{rez["id"]} · {rez["kullanici"]}',
                      rez["id"]):
            if fm.horizontalAdvance(metin) <= r.width() - 6:
                p.drawText(r.adjusted(4, 0, -2, 0), Qt.AlignVCenter | Qt.AlignLeft, metin)
                break
        self.kutular.append((r, rez))

    # ------------------------------------------------------------------ fare
    def mousePressEvent(self, olay):
        if olay.button() != Qt.LeftButton:
            return
        rez = self._kutu_bul(olay.position())
        if rez:
            self.secimi_ayarla(rez["id"])
            self.rezervasyon_secildi.emit(rez["id"])
            return
        o = self._satir_bul(olay.position().y())
        if o and olay.position().x() > SOL:
            dk = self._dk(olay.position().x())
            self.surukle = [o["satir"]["id"], dk, dk]
            self.update()

    def mouseMoveEvent(self, olay):
        if self.surukle:
            self.surukle[2] = self._dk(olay.position().x())
            self.update()
        else:
            self.setCursor(Qt.PointingHandCursor if self._kutu_bul(olay.position()) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, olay):
        if not self.surukle:
            return
        kaynak, b, e = self.surukle
        b, e = sorted((b, e))
        if b == e:                      # tek tıklama: o saatten başlayan 1 saatlik aralık
            e = min(GUN_DK, b + 60)
        self.surukle = None
        self.update()
        if e > b:
            self.aralik_secildi.emit(kaynak, ss_dd(b), ss_dd(e))

    def event(self, olay):
        if olay.type() == olay.Type.ToolTip:
            rez = self._kutu_bul(QPointF(olay.pos()))
            if rez:
                paket = f'<br>Paket: {rez["paket"]}' if rez["paket"] else ""
                QToolTip.showText(olay.globalPos(),
                                  f'<b>{rez["id"]}</b> · {rez["durum"]}<br>{rez["kullanici"]} – {rez["kullanici_ad"]}'
                                  f'<br>{rez["baslangic"][11:]}–{rez["bitis"][11:]} · {rez["ucret"]} KP{paket}', self)
            else:
                QToolTip.hideText()
            return True
        return super().event(olay)
