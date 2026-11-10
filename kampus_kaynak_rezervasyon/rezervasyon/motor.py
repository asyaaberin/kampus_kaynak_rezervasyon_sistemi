"""Rezervasyon motoru: tüm iş kuralları (K1-K11) bu dosyadadır.

Başlangıç dosyasındaki değerler (türler, roller, ücretler, kotalar...) koda
yazılmaz; hepsi çalışma anında sözlüklerden okunur. Aşağıdaki sabitler ise
PDF'teki kuralların kendisidir (dosyada yer almazlar).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from fractions import Fraction
from math import floor

# ---------------------------------------------------------------------------
# Kural sabitleri (PDF'ten)
# ---------------------------------------------------------------------------
ZAMAN_BICIMI = "%Y-%m-%dT%H:%M"
ADIM_DK = 15                          # K1: 15 dakikalık adımlar
ACILIS, KAPANIS = time(8, 0), time(22, 0)   # K1: 08:00-22:00
EN_AZ_SURE_DK = 30                    # K1: en az 30 dakika
ARDISIK_BOSLUK = timedelta(minutes=60)  # K4: aynı kişi, aynı kaynak, 60 dk
BANT_SAAT = 2                         # K5: 2 saatlik bantlar (08-10, 10-12, ...)
BANT_DK = BANT_SAAT * 60              # K5: payda için 120
PIK_BAS, PIK_BIT = time(10, 0), time(16, 0)  # K5: pik saatler
PIK_CARPANI = Fraction(3, 2)          # K5: enerji yoğun türlerde 1,5
GIRIS_ONCE = timedelta(minutes=10)    # K8: başlangıçtan 10 dk önce
GIRIS_SONRA = timedelta(minutes=15)   # K8: başlangıçtan 15 dk sonra (GELMEDI anı)
GUVEN_GELMEDI, GUVEN_GEC_IPTAL, GUVEN_TAMAM = -15, -5, +2  # K8
GUVEN_ESIGI = 50                      # K8: altında ileri tarih 1 gün, paket yok
DUSUK_GUVEN_ILERI_GUN = 1             # K8
PAKET_EN_AZ, PAKET_EN_COK = 2, 4      # K7

# K3/K9/K10: hangi durumlar hangi kontrolde sayılır
KESISME_DURUMLARI = {"ONAYLI", "KULLANIMDA"}               # KESISME ve doluluk
HAZIRLIK_DURUMLARI = {"ONAYLI", "KULLANIMDA", "TAMAMLANDI"}  # HAZIRLIK ve ARDISIK

# Hata kodlarının Türkçe açıklamaları (arayüz bunları gösterir).
HATA_ACIKLAMALARI = {
    "BULUNAMADI": "Kullanıcı, kaynak veya rezervasyon bulunamadı.",
    "ZAMAN_ADIMI_HATASI": "Saatler 15 dakikalık adımlara oturmuyor ya da bitiş başlangıçtan sonra değil.",
    "GECMIS_ZAMAN": "Başlangıç simüle saatten önce olamaz.",
    "CALISMA_SAATI_DISI": "Rezervasyon aynı gün içinde 08:00-22:00 arasında kalmalıdır.",
    "SURE_SINIRI": "Süre 30 dakikadan kısa veya rolün azami süresinden uzun.",
    "ILERI_TARIH_SINIRI": "Rolün ileri tarih sınırı aşıldı (güvenilirlik 50'nin altındaysa 1 gün).",
    "ROL_IZNI_YOK": "Kullanıcının rolü bu kaynağı rezerve edemez.",
    "SERTIFIKA_YOK": "Bu kaynak türü için gereken sertifika kullanıcıda yok.",
    "BAKIM": "İstenen aralık bir bakım penceresiyle kesişiyor.",
    "KESISME": "İstenen aralık başka bir rezervasyonla kesişiyor.",
    "HAZIRLIK_IHLALI": "Kaynağın hazırlık süresi (soğuma/havalandırma) ihlal ediliyor.",
    "ARDISIK_KULLANIM": "Aynı kaynaktaki iki rezervasyonunuz arasında en az 60 dakika olmalı.",
    "BAKIYE_YETERSIZ": "Bakiye ücreti karşılamıyor.",
    "PAKET_BOYUTU": "Paket 2 ile 4 arasında kalem içermelidir.",
    "GUVENILIRLIK_DUSUK": "Güvenilirlik 50'nin altındayken paket yapılamaz.",
    "PAKET_RED": "Paketteki en az bir kalem doğrulamadan geçemedi.",
    "PAKET_ICI_KESISME": "Paketteki aynı kaynağa ait kalemler kesişiyor veya aralarında yeterli boşluk yok.",
    "DURUM_HATASI": "Rezervasyon bu işlem için uygun durumda değil.",
    "GIRIS_PENCERESI_DISI": "Giriş yalnızca başlangıçtan 10 dk önce ile 15 dk sonra arasında yapılabilir.",
    "BEKLEME_GEREKSIZ": "Talep zaten geçerli; doğrudan rezervasyon yapılabilir.",
    "SAAT_GERI": "Simüle saat geri alınamaz.",
    "ID_MEVCUT": "Bu kimlikle bir kayıt zaten var.",
    "TANIMSIZ_DEGER": "Rol, tür veya izinli rollerden biri başlangıç dosyasında tanımlı değil.",
    "GECERSIZ_DEGER": "Bakiye 0 ile haftalık kota arasında, güvenilirlik 0-100 arası tam sayı olmalı.",
    "BILINMEYEN_KOMUT": "Komut tanınmadı.",
}


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------
def zaman_oku(deger):
    """'YYYY-AA-GGTSS:DD' metnini datetime'a çevirir; hatalıysa None döner."""
    if isinstance(deger, datetime):
        return deger
    try:
        return datetime.strptime(deger, ZAMAN_BICIMI)
    except (TypeError, ValueError):
        return None


def zaman_yaz(dt: datetime) -> str:
    return dt.strftime(ZAMAN_BICIMI)


def adima_oturur(dt: datetime) -> bool:
    """K1: dakika :00, :15, :30 veya :45 olmalı."""
    return dt.minute % ADIM_DK == 0 and dt.second == 0


def kesisir(b, e, b2, e2) -> bool:
    """Yarı açık aralıklar [b,e) ve [b2,e2) kesişiyor mu? (K3: b < e' ve e > b')"""
    return b < e2 and e > b2


def bosluk_az(b, e, b2, e2, h: timedelta) -> bool:
    """K3 simetrik hazırlık formülü: b < e' + h ve e + h > b'.
    K4'te aynı formül h = 60 dk ile kullanılır."""
    return b < e2 + h and e + h > b2


def no_al(kimlik: str) -> int:
    """'r12' -> 12 (sıralamada b2 < b10 olması için)."""
    return int(kimlik[1:])


# ---------------------------------------------------------------------------
# Veri modeli (PDF Bölüm 3)
# ---------------------------------------------------------------------------
@dataclass
class Kullanici:
    id: str
    ad: str
    rol: str
    sertifikalar: list
    bakiye: int
    guvenilirlik: int


@dataclass
class Kaynak:
    id: str
    ad: str
    tur: str
    izinli_roller: list


@dataclass
class Bakim:
    kaynak: str
    baslangic: datetime
    bitis: datetime


@dataclass
class Rezervasyon:
    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    ucret: int
    durum: str = "ONAYLI"
    paket: str | None = None


@dataclass
class Bekleme:
    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    kayit_saati: datetime


def tamam(**ek) -> dict:
    return {"durum": "TAMAM", **ek}


def red(kod: str, **ek) -> dict:
    return {"durum": "RED", "kod": kod, **ek}


# ---------------------------------------------------------------------------
# Ana sınıf
# ---------------------------------------------------------------------------
class RezervasyonSistemi:
    """Bütün durum bellekte tutulur. Her işlem bir sonuç sözlüğü döndürür."""

    def __init__(self, baslangic: dict):
        self.saat: datetime = zaman_oku(baslangic["saat"])
        self.turler: dict = baslangic["kaynak_turleri"]   # tür -> parametreler
        self.roller: dict = baslangic["roller"]           # rol -> parametreler
        self.kaynaklar: dict[str, Kaynak] = {}
        for k in baslangic.get("kaynaklar", []):
            self.kaynaklar[k["id"]] = Kaynak(k["id"], k["ad"], k["tur"], list(k["izinli_roller"]))
        self.bakimlar = [Bakim(b["kaynak"], zaman_oku(b["baslangic"]), zaman_oku(b["bitis"]))
                         for b in baslangic.get("bakim_pencereleri", [])]
        self.kullanicilar: dict[str, Kullanici] = {}
        for u in baslangic.get("kullanicilar", []):
            self.kullanicilar[u["id"]] = Kullanici(u["id"], u["ad"], u["rol"], list(u["sertifikalar"]),
                                                   u["bakiye"], u["guvenilirlik"])
        # Sözlükler ekleme sırasını korur; bu da oluşturulma (numara) sırasıdır.
        self.rezervasyonlar: dict[str, Rezervasyon] = {}
        self.beklemeler: dict[str, Bekleme] = {}
        self.paketler: dict[str, list] = {}
        self._sayac = {"r": 0, "p": 0, "b": 0}  # reddedilen talepler numara tüketmez

    @classmethod
    def dosyadan(cls, yol: str) -> "RezervasyonSistemi":
        with open(yol, encoding="utf-8") as f:
            return cls(json.load(f))

    # ------------------------------------------------------------------ yardımcılar
    def _yeni_id(self, on_ek: str) -> str:
        self._sayac[on_ek] += 1
        return f"{on_ek}{self._sayac[on_ek]}"

    def _kota(self, kullanici: Kullanici) -> int:
        return self.roller[kullanici.rol]["haftalik_kota"]

    def _guven_degistir(self, kullanici: Kullanici, fark: int):
        """K8: güvenilirlik 0-100 arasında tutulur."""
        kullanici.guvenilirlik = max(0, min(100, kullanici.guvenilirlik + fark))

    def _iade_et(self, kullanici: Kullanici, miktar: int) -> int:
        """K6: iade bakiyeyi kotanın üstüne çıkaramaz. Gerçekte eklenen miktarı döndürür."""
        eklenen = max(0, min(miktar, self._kota(kullanici) - kullanici.bakiye))
        kullanici.bakiye += eklenen
        return eklenen

    def _beklemeleri_temizle(self):
        """K9: başlangıcı simüle saatten önceye düşen bekleme kayıtları silinir."""
        for bid in [b.id for b in self.beklemeler.values() if b.baslangic < self.saat]:
            del self.beklemeler[bid]

    def _bekleme_sirasi(self, kaynak_id: str) -> list:
        """K9: güvenilirlik yüksekten düşüğe, sonra kayıt saati, sonra numara."""
        kayitlar = [b for b in self.beklemeler.values() if b.kaynak == kaynak_id]
        return sorted(kayitlar, key=lambda b: (-self.kullanicilar[b.kullanici].guvenilirlik,
                                               b.kayit_saati, no_al(b.id)))

    # ------------------------------------------------------------------ K5 ücret
    def _ucret_hesapla(self, tur: str, b: datetime, e: datetime) -> int:
        """K5: 15 dakikalık dilimlerin toplamı; kesirli ara değerler için Fraction."""
        tur_bilgi = self.turler[tur]
        temel = Fraction(str(tur_bilgi["temel_ucret"]))
        # Türdeki kaynak sayısı talep anındaki sayıdır (kaynak_ekle hemen sayılır).
        kaynak_sayisi = sum(1 for k in self.kaynaklar.values() if k.tur == tur)
        ayni_tur = [r for r in self.rezervasyonlar.values()
                    if r.durum in KESISME_DURUMLARI and self.kaynaklar[r.kaynak].tur == tur]

        bant_carpanlari = {}   # bant başlangıcı -> çarpan (her bant bir kez hesaplanır)
        toplam = Fraction(0)
        t = b
        while t < e:
            bant_bas = t.replace(hour=t.hour - t.hour % BANT_SAAT, minute=0)
            if bant_bas not in bant_carpanlari:
                bant_son = bant_bas + timedelta(minutes=BANT_DK)
                # Aynı gün ve bant içinde kalan dolu dakikalar (talebin kendisi sayılmaz).
                dolu = 0
                for r in ayni_tur:
                    ortak = min(r.bitis, bant_son) - max(r.baslangic, bant_bas)
                    if ortak > timedelta(0):
                        dolu += ortak // timedelta(minutes=1)
                doluluk = Fraction(dolu, kaynak_sayisi * BANT_DK)
                # Bant çarpanı = 1 + 0,25 × ⌊4 × doluluk⌋  (tam 0,25 -> 1,25)
                bant_carpanlari[bant_bas] = 1 + Fraction(1, 4) * floor(4 * doluluk)
            # Pik çarpanı yalnız enerji yoğun türlerde, 10:00-16:00 dilimlerinde.
            pik = PIK_CARPANI if tur_bilgi["enerji_yogun"] and PIK_BAS <= t.time() < PIK_BIT else 1
            toplam += temel * Fraction(1, 4) * bant_carpanlari[bant_bas] * pik
            t += timedelta(minutes=ADIM_DK)
        # Yuvarlama: en yakın tam sayı, tam 0,5 yukarı. (round() banker yuvarlaması yapar!)
        return floor(toplam + Fraction(1, 2))

    # ------------------------------------------------------------------ K10 doğrulama
    def _dogrula(self, kullanici_id, kaynak_id, baslangic, bitis, bakiye_kontrol=True):
        """K10 doğrulama sırası. İlk başarısız adımın kodunu döndürür.
        Dönüş: (kod, ucret). Talep geçerliyse kod None, ucret hesaplanmış olur."""
        kullanici = self.kullanicilar.get(kullanici_id)
        kaynak = self.kaynaklar.get(kaynak_id)
        # 1) BULUNAMADI
        if kullanici is None or kaynak is None:
            return "BULUNAMADI", None
        b, e = zaman_oku(baslangic), zaman_oku(bitis)
        # 2) ZAMAN_ADIMI_HATASI (K1: 15 dk adım, bitiş başlangıçtan sonra)
        if b is None or e is None or not adima_oturur(b) or not adima_oturur(e) or e <= b:
            return "ZAMAN_ADIMI_HATASI", None
        # 3) GECMIS_ZAMAN
        if b < self.saat:
            return "GECMIS_ZAMAN", None
        # 4) CALISMA_SAATI_DISI (aynı gün, 08:00-22:00)
        if b.date() != e.date() or b.time() < ACILIS or e.time() > KAPANIS:
            return "CALISMA_SAATI_DISI", None
        # 5) SURE_SINIRI (en az 30 dk, en fazla rolün azami_sure_dk değeri)
        rol = self.roller[kullanici.rol]
        sure_dk = (e - b) // timedelta(minutes=1)
        if sure_dk < EN_AZ_SURE_DK or sure_dk > rol["azami_sure_dk"]:
            return "SURE_SINIRI", None
        # 6) ILERI_TARIH_SINIRI (K8: güvenilirlik < 50 ise 1 gün)
        ileri_gun = DUSUK_GUVEN_ILERI_GUN if kullanici.guvenilirlik < GUVEN_ESIGI else rol["ileri_gun"]
        if b > self.saat + timedelta(hours=24 * ileri_gun):
            return "ILERI_TARIH_SINIRI", None
        # 7) ROL_IZNI_YOK
        if kullanici.rol not in kaynak.izinli_roller:
            return "ROL_IZNI_YOK", None
        # 8) SERTIFIKA_YOK
        tur = self.turler[kaynak.tur]
        if tur["sertifika"] and tur["sertifika"] not in kullanici.sertifikalar:
            return "SERTIFIKA_YOK", None
        # 9) BAKIM (K2: bakımdan sonra hazırlık uygulanmaz, yalnızca kesişme bakılır)
        for bk in self.bakimlar:
            if bk.kaynak == kaynak.id and kesisir(b, e, bk.baslangic, bk.bitis):
                return "BAKIM", None

        ayni_kaynak = [r for r in self.rezervasyonlar.values() if r.kaynak == kaynak.id]
        # 10) KESISME (K3: yalnız ONAYLI ve KULLANIMDA)
        for r in ayni_kaynak:
            if r.durum in KESISME_DURUMLARI and kesisir(b, e, r.baslangic, r.bitis):
                return "KESISME", None
        # 11) HAZIRLIK_IHLALI (K3: ONAYLI, KULLANIMDA, TAMAMLANDI; simetrik formül)
        h = timedelta(minutes=tur["hazirlik_dk"])
        for r in ayni_kaynak:
            if r.durum in HAZIRLIK_DURUMLARI and bosluk_az(b, e, r.baslangic, r.bitis, h):
                return "HAZIRLIK_IHLALI", None
        # 12) ARDISIK_KULLANIM (K4: aynı kullanıcı, aynı kaynak, 60 dk)
        for r in ayni_kaynak:
            if (r.kullanici == kullanici.id and r.durum in HAZIRLIK_DURUMLARI
                    and bosluk_az(b, e, r.baslangic, r.bitis, ARDISIK_BOSLUK)):
                return "ARDISIK_KULLANIM", None

        ucret = self._ucret_hesapla(kaynak.tur, b, e)
        # 13) BAKIYE_YETERSIZ (K6)
        if bakiye_kontrol and ucret > kullanici.bakiye:
            return "BAKIYE_YETERSIZ", ucret
        return None, ucret

    def _rezervasyon_olustur(self, kullanici_id, kaynak_id, b, e, ucret, paket=None) -> Rezervasyon:
        r = Rezervasyon(self._yeni_id("r"), kullanici_id, kaynak_id, zaman_oku(b), zaman_oku(e),
                        ucret, "ONAYLI", paket)
        self.rezervasyonlar[r.id] = r
        self.kullanicilar[kullanici_id].bakiye -= ucret   # K6: ücret rezervasyon anında düşer
        return r

    # ------------------------------------------------------------------ K9 tarama
    def _bekleme_tara(self, kaynak_id: str) -> list:
        """K9: yer boşalınca o kaynağın bekleme kayıtları sırayla tam K10 kontrolünden
        geçirilir; geçen kayıt rezervasyona dönüşür. Tarama listenin sonuna kadar sürer."""
        self._beklemeleri_temizle()
        olaylar = []
        for bk in self._bekleme_sirasi(kaynak_id):
            kod, ucret = self._dogrula(bk.kullanici, bk.kaynak, bk.baslangic, bk.bitis)
            if kod is not None:
                continue   # geçemeyen kayıt listede kalır
            r = self._rezervasyon_olustur(bk.kullanici, bk.kaynak, bk.baslangic, bk.bitis, ucret)
            del self.beklemeler[bk.id]
            olaylar.append({"zaman": zaman_yaz(self.saat), "tur": "OTOMATIK_ATAMA",
                            "bekleme": bk.id, "rezervasyon": r.id, "kullanici": bk.kullanici,
                            "ucret": ucret, "bakiye": self.kullanicilar[bk.kullanici].bakiye})
        return olaylar

    # ================================================================== KOMUTLAR
    def rezervasyon(self, kullanici, kaynak, baslangic, bitis) -> dict:
        kod, ucret = self._dogrula(kullanici, kaynak, baslangic, bitis)
        if kod:
            return red(kod)
        r = self._rezervasyon_olustur(kullanici, kaynak, baslangic, bitis, ucret)
        return tamam(rezervasyon_id=r.id, ucret=ucret, bakiye=self.kullanicilar[kullanici].bakiye)

    def fiyat(self, kullanici, kaynak, baslangic, bitis) -> dict:
        """Bakiye dışındaki tüm kontroller; durum değişmez, numara tüketmez."""
        kod, ucret = self._dogrula(kullanici, kaynak, baslangic, bitis, bakiye_kontrol=False)
        return red(kod) if kod else tamam(ucret=ucret)

    def paket(self, kullanici, kalemler) -> dict:
        """K7: ya hep ya hiç. Kendi denetim sırası vardır."""
        kalemler = kalemler if isinstance(kalemler, list) else []
        u = self.kullanicilar.get(kullanici)
        # 1) BULUNAMADI: kullanıcı yok
        if u is None:
            return red("BULUNAMADI", kalemler=[])
        # 2) PAKET_BOYUTU
        if not PAKET_EN_AZ <= len(kalemler) <= PAKET_EN_COK:
            return red("PAKET_BOYUTU", kalemler=[])
        # 3) GUVENILIRLIK_DUSUK
        if u.guvenilirlik < GUVEN_ESIGI:
            return red("GUVENILIRLIK_DUSUK", kalemler=[])
        # 4) PAKET_RED: her kalem paket öncesi duruma göre, bakiye hariç K10 ile doğrulanır.
        #    Hiçbir kalem eklenmediği için kalemler birbirinin doluluğuna katılmaz.
        sonuclar, ucretler = [], []
        for i, k in enumerate(kalemler):
            kod, ucret = self._dogrula(kullanici, k.get("kaynak"), k.get("baslangic"),
                                       k.get("bitis"), bakiye_kontrol=False)
            sonuclar.append({"sira": i, "durum": "RED", "kod": kod} if kod else {"sira": i, "durum": "TAMAM"})
            ucretler.append(ucret)
        if any(s["durum"] == "RED" for s in sonuclar):
            return red("PAKET_RED", kalemler=sonuclar)
        # 5) PAKET_ICI_KESISME: aynı kaynaktaki kalemler kesişme / hazırlık / ardışık.
        #    (Kesişme, h >= 0 olduğundan bosluk_az formülünün içinde zaten vardır.)
        for i in range(len(kalemler)):
            for j in range(i + 1, len(kalemler)):
                a, c = kalemler[i], kalemler[j]
                if a["kaynak"] != c["kaynak"]:
                    continue
                h = timedelta(minutes=self.turler[self.kaynaklar[a["kaynak"]].tur]["hazirlik_dk"])
                ab, ae, cb, ce = (zaman_oku(a["baslangic"]), zaman_oku(a["bitis"]),
                                  zaman_oku(c["baslangic"]), zaman_oku(c["bitis"]))
                if bosluk_az(ab, ae, cb, ce, h) or bosluk_az(ab, ae, cb, ce, ARDISIK_BOSLUK):
                    return red("PAKET_ICI_KESISME", kalemler=sonuclar)
        # 6) BAKIYE_YETERSIZ: toplam ücret bakiyeyi aşıyor
        toplam = sum(ucretler)
        if toplam > u.bakiye:
            return red("BAKIYE_YETERSIZ", kalemler=sonuclar)
        pid = self._yeni_id("p")
        rids = [self._rezervasyon_olustur(kullanici, k["kaynak"], k["baslangic"], k["bitis"], ucret, pid).id
                for k, ucret in zip(kalemler, ucretler)]
        self.paketler[pid] = rids
        return tamam(paket_id=pid, rezervasyonlar=rids, ucretler=ucretler, toplam=toplam, bakiye=u.bakiye)

    def giris(self, rezervasyon) -> dict:
        """K8: ONAYLI -> KULLANIMDA, pencere [b-10, b+15]."""
        r = self.rezervasyonlar.get(rezervasyon)
        if r is None:
            return red("BULUNAMADI")
        if r.durum != "ONAYLI":
            return red("DURUM_HATASI")
        if not r.baslangic - GIRIS_ONCE <= self.saat <= r.baslangic + GIRIS_SONRA:
            return red("GIRIS_PENCERESI_DISI")
        r.durum = "KULLANIMDA"
        return tamam(yeni_durum=r.durum)

    def cikis(self, rezervasyon) -> dict:
        """K8: erken çıkış. Bitiş çıkış saatine çekilir, iade yok, güvenilirlik değişmez.
        K9: yer boşaldığı için bekleme taraması yapılır."""
        r = self.rezervasyonlar.get(rezervasyon)
        if r is None:
            return red("BULUNAMADI")
        if r.durum != "KULLANIMDA":
            return red("DURUM_HATASI")
        # Başlangıçtan önce çıkış yapılırsa bitiş başlangıca eşitlenir (bizim yorumumuz).
        r.bitis = max(self.saat, r.baslangic)
        r.durum = "TAMAMLANDI"
        olaylar = self._bekleme_tara(r.kaynak)
        return tamam(yeni_durum=r.durum, guvenilirlik=self.kullanicilar[r.kullanici].guvenilirlik,
                     olaylar=olaylar)

    def iptal(self, rezervasyon) -> dict:
        """K8: ONAYLI -> IPTAL. İade başlangıca kalan süreye göre."""
        r = self.rezervasyonlar.get(rezervasyon)
        if r is None:
            return red("BULUNAMADI")
        if r.durum != "ONAYLI":
            return red("DURUM_HATASI")
        u = self.kullanicilar[r.kullanici]
        kalan = r.baslangic - self.saat
        if kalan >= timedelta(hours=24):
            iade = r.ucret                 # %100
        elif kalan >= timedelta(hours=2):
            iade = r.ucret // 2            # %50, aşağı yuvarlanır
        else:
            iade = 0                       # %0 ve güvenilirlik -5 (başlangıç geçmiş dahil)
            self._guven_degistir(u, GUVEN_GEC_IPTAL)
        r.durum = "IPTAL"
        iade = self._iade_et(u, iade)      # K6: kotayı aşan kısım iade edilmez
        bakiye, guven = u.bakiye, u.guvenilirlik
        olaylar = self._bekleme_tara(r.kaynak)
        return tamam(iade=iade, bakiye=bakiye, guvenilirlik=guven, olaylar=olaylar)

    def bekleme(self, kullanici, kaynak, baslangic, bitis) -> dict:
        """K9: yalnız KESISME veya HAZIRLIK_IHLALI ile reddedilen talep için kayıt açılır.
        Bakiye kontrol edilmez."""
        self._beklemeleri_temizle()
        kod, _ = self._dogrula(kullanici, kaynak, baslangic, bitis, bakiye_kontrol=False)
        if kod is None:
            return red("BEKLEME_GEREKSIZ")
        if kod not in ("KESISME", "HAZIRLIK_IHLALI"):
            return red(kod)
        bk = Bekleme(self._yeni_id("b"), kullanici, kaynak, zaman_oku(baslangic), zaman_oku(bitis), self.saat)
        self.beklemeler[bk.id] = bk
        sira = [x.id for x in self._bekleme_sirasi(kaynak)].index(bk.id) + 1
        return tamam(bekleme_id=bk.id, sira=sira)

    def sorgu(self, tur, id, gun=None) -> dict:
        if tur == "kullanici":
            u = self.kullanicilar.get(id)
            if u is None:
                return red("BULUNAMADI")
            liste = sorted((r for r in self.rezervasyonlar.values() if r.kullanici == id),
                           key=lambda r: (r.baslangic, no_al(r.id)))
            # 'beklemeler' arayüz için ek alandır (fazladan alan hata sayılmaz).
            beklemeler = sorted((b for b in self.beklemeler.values() if b.kullanici == id),
                                key=lambda b: no_al(b.id))
            return tamam(
                bakiye=u.bakiye, guvenilirlik=u.guvenilirlik,
                rezervasyonlar=[{"id": r.id, "kaynak": r.kaynak, "baslangic": zaman_yaz(r.baslangic),
                                 "bitis": zaman_yaz(r.bitis), "durum": r.durum, "ucret": r.ucret}
                                for r in liste],
                beklemeler=[{"id": b.id, "kaynak": b.kaynak, "baslangic": zaman_yaz(b.baslangic),
                             "bitis": zaman_yaz(b.bitis), "kayit_saati": zaman_yaz(b.kayit_saati)}
                            for b in beklemeler])
        if tur == "kaynak":
            if id not in self.kaynaklar:
                return red("BULUNAMADI")
            gun_bas = zaman_oku(f"{gun}T00:00")
            if gun_bas is None:
                return red("GECERSIZ_DEGER")
            gun_son = gun_bas + timedelta(days=1)
            # (sıralama anahtarı, satır) çiftleri; yalnız ONAYLI/KULLANIMDA ve bakımlar
            satirlar = []
            for r in self.rezervasyonlar.values():
                if r.kaynak == id and r.durum in KESISME_DURUMLARI and kesisir(r.baslangic, r.bitis, gun_bas, gun_son):
                    satirlar.append(((r.baslangic, 1, no_al(r.id)),
                                     {"baslangic": zaman_yaz(r.baslangic), "bitis": zaman_yaz(r.bitis),
                                      "tur": "REZERVASYON", "rezervasyon": r.id}))
            for bk in self.bakimlar:
                if bk.kaynak == id and kesisir(bk.baslangic, bk.bitis, gun_bas, gun_son):
                    satirlar.append(((bk.baslangic, 0, 0),
                                     {"baslangic": zaman_yaz(bk.baslangic), "bitis": zaman_yaz(bk.bitis),
                                      "tur": "BAKIM"}))
            satirlar.sort(key=lambda s: s[0])
            return tamam(doluluk=[s[1] for s in satirlar])
        return red("GECERSIZ_DEGER")

    def saat_ilerlet(self, zaman) -> dict:
        """K11: (eski saat, yeni saat] aralığındaki olaylar zaman sırasıyla işlenir.
        Her olay anında simüle saat o ana ayarlanır."""
        hedef = zaman_oku(zaman)
        if hedef is None:
            return red("GECERSIZ_DEGER")
        if hedef < self.saat:
            return red("SAAT_GERI")
        olaylar = []
        while True:
            t = self._sonraki_olay_ani()
            if t is None or t > hedef:
                break
            self.saat = t
            self._beklemeleri_temizle()
            olaylar.extend(self._an_isle(t))
        self.saat = hedef
        self._beklemeleri_temizle()
        return tamam(olaylar=olaylar)

    def _sonraki_pazartesi(self) -> datetime:
        """Simüle saatten kesin olarak sonraki ilk Pazartesi 00:00."""
        gun = datetime.combine(self.saat.date(), time(0, 0))
        aday = gun + timedelta(days=(7 - gun.weekday()) % 7)   # weekday(): Pazartesi = 0
        return aday if aday > self.saat else aday + timedelta(days=7)

    def _sonraki_olay_ani(self):
        """Şu andan sonraki en erken olay anı (sıfırlama, bitiş veya gelmeme)."""
        adaylar = [self._sonraki_pazartesi()]
        for r in self.rezervasyonlar.values():
            if r.durum == "KULLANIMDA":
                adaylar.append(r.bitis)
            elif r.durum == "ONAYLI":
                adaylar.append(r.baslangic + GIRIS_SONRA)
        adaylar = [a for a in adaylar if a > self.saat] or [None]
        return min(adaylar, key=lambda a: a or datetime.max)

    def _an_isle(self, t: datetime) -> list:
        """K11: aynı andaki olay sırası:
        1) HAFTALIK_SIFIRLAMA  2) TAMAMLANDI (numaraya göre)
        3) GELMEDI (numaraya göre)  4) boşalan her kaynak için bekleme taraması."""
        zaman = zaman_yaz(t)
        olaylar = []
        # 1) K6: Pazartesi 00:00 geçildiğinde bakiye kotaya eşitlenir.
        if t.weekday() == 0 and t.time() == time(0, 0):
            for u in self.kullanicilar.values():
                u.bakiye = self._kota(u)
            olaylar.append({"zaman": zaman, "tur": "HAFTALIK_SIFIRLAMA"})
        # 2) Bitiş saati gelen KULLANIMDA rezervasyonlar TAMAMLANDI olur, +2.
        for r in self.rezervasyonlar.values():          # sözlük sırası = numara sırası
            if r.durum == "KULLANIMDA" and r.bitis <= t:
                r.durum = "TAMAMLANDI"
                u = self.kullanicilar[r.kullanici]
                self._guven_degistir(u, GUVEN_TAMAM)
                olaylar.append({"zaman": zaman, "tur": "TAMAMLANDI", "rezervasyon": r.id,
                                "kullanici": u.id, "guvenilirlik": u.guvenilirlik})
        # 3) Başlangıç + 15 dk'ya kadar giriş yapılmayanlar GELMEDI olur, -15.
        bosalanlar = []
        for r in self.rezervasyonlar.values():
            if r.durum == "ONAYLI" and r.baslangic + GIRIS_SONRA <= t:
                r.durum = "GELMEDI"
                u = self.kullanicilar[r.kullanici]
                self._guven_degistir(u, GUVEN_GELMEDI)
                olaylar.append({"zaman": zaman, "tur": "GELMEDI", "rezervasyon": r.id,
                                "kullanici": u.id, "guvenilirlik": u.guvenilirlik})
                if r.kaynak not in bosalanlar:
                    bosalanlar.append(r.kaynak)
        # 4) Gelmeme sırasıyla, boşalan her kaynak için bekleme taraması.
        for kaynak_id in bosalanlar:
            olaylar.extend(self._bekleme_tara(kaynak_id))
        return olaylar

    def kullanici_ekle(self, id, ad, rol, sertifikalar, bakiye, guvenilirlik) -> dict:
        # 1) ID_MEVCUT  2) TANIMSIZ_DEGER  3) GECERSIZ_DEGER
        if id in self.kullanicilar:
            return red("ID_MEVCUT")
        if rol not in self.roller:
            return red("TANIMSIZ_DEGER")
        kota = self.roller[rol]["haftalik_kota"]
        bakiye_gecerli = isinstance(bakiye, (int, float)) and not isinstance(bakiye, bool) and 0 <= bakiye <= kota
        guven_gecerli = isinstance(guvenilirlik, int) and not isinstance(guvenilirlik, bool) and 0 <= guvenilirlik <= 100
        if not (bakiye_gecerli and guven_gecerli):
            return red("GECERSIZ_DEGER")
        self.kullanicilar[id] = Kullanici(id, ad, rol, list(sertifikalar or []), bakiye, guvenilirlik)
        return tamam()

    def kaynak_ekle(self, id, ad, tur, izinli_roller) -> dict:
        # 1) ID_MEVCUT  2) TANIMSIZ_DEGER (GECERSIZ_DEGER kaynak için denetlenmez)
        if id in self.kaynaklar:
            return red("ID_MEVCUT")
        izinli_roller = list(izinli_roller or [])
        if tur not in self.turler or any(r not in self.roller for r in izinli_roller):
            return red("TANIMSIZ_DEGER")
        self.kaynaklar[id] = Kaynak(id, ad, tur, izinli_roller)
        return tamam()

    # ================================================================== ARAYÜZ İÇİN SALT OKUNUR
    # Bu fonksiyonlar durumu değiştirmez ve iş kuralı uygulamaz; yalnızca arayüzün
    # göstereceği veriyi hazırlar. Böylece arayüzde hiçbir kural bilgisi bulunmaz.
    def aciklama(self, kod: str) -> str:
        return HATA_ACIKLAMALARI.get(kod, kod)

    def simdi(self) -> str:
        return zaman_yaz(self.saat)

    def secenekler(self) -> dict:
        """Formlarda seçilecek değerler: başlangıç dosyasındaki roller, türler, sertifikalar."""
        sertifikalar = {t["sertifika"] for t in self.turler.values() if t["sertifika"]}
        for u in self.kullanicilar.values():
            sertifikalar.update(u.sertifikalar)
        return {"roller": list(self.roller), "turler": list(self.turler),
                "sertifikalar": sorted(sertifikalar),
                "kotalar": {r: v["haftalik_kota"] for r, v in self.roller.items()}}

    def kullanici_listesi(self) -> list:
        return [{"id": u.id, "ad": u.ad, "rol": u.rol, "kota": self._kota(u)}
                for u in self.kullanicilar.values()]

    def kaynak_listesi(self) -> list:
        """Kaynaklar, başlangıç dosyasındaki tür sırasına göre gruplanmış olarak."""
        tur_sirasi = {t: i for i, t in enumerate(self.turler)}
        kaynaklar = sorted(self.kaynaklar.values(), key=lambda k: tur_sirasi.get(k.tur, 99))
        return [{"id": k.id, "ad": k.ad, "tur": k.tur, "izinli_roller": list(k.izinli_roller),
                 "hazirlik_dk": self.turler[k.tur]["hazirlik_dk"]} for k in kaynaklar]

    def rezervasyon_bilgisi(self, rid: str):
        r = self.rezervasyonlar.get(rid)
        if r is None:
            return None
        u = self.kullanicilar[r.kullanici]
        h = timedelta(minutes=self.turler[self.kaynaklar[r.kaynak].tur]["hazirlik_dk"])
        # K3: hazırlık kontrolünde ONAYLI, KULLANIMDA ve TAMAMLANDI sayılır.
        hazirlik_bitis = zaman_yaz(r.bitis + h) if h and r.durum in HAZIRLIK_DURUMLARI else None
        return {"id": r.id, "kullanici": r.kullanici, "kullanici_ad": u.ad, "kaynak": r.kaynak,
                "baslangic": zaman_yaz(r.baslangic), "bitis": zaman_yaz(r.bitis), "ucret": r.ucret,
                "durum": r.durum, "paket": r.paket, "hazirlik_bitis": hazirlik_bitis}

    def gun_gorunumu(self, gun: str) -> list:
        """Takvim için: o gün her kaynağın tüm rezervasyonları (her durumda) ve bakımları."""
        gun_bas = zaman_oku(f"{gun}T00:00")
        gun_son = gun_bas + timedelta(days=1)
        satirlar = []
        for k in self.kaynak_listesi():
            rezler = [self.rezervasyon_bilgisi(r.id) for r in self.rezervasyonlar.values()
                      if r.kaynak == k["id"] and kesisir(r.baslangic, r.bitis, gun_bas, gun_son)]
            bakimlar = [{"baslangic": zaman_yaz(b.baslangic), "bitis": zaman_yaz(b.bitis)}
                        for b in self.bakimlar
                        if b.kaynak == k["id"] and kesisir(b.baslangic, b.bitis, gun_bas, gun_son)]
            satirlar.append({**k, "rezervasyonlar": rezler, "bakimlar": bakimlar})
        return satirlar

    # ------------------------------------------------------------------ dağıtıcı
    def isle(self, komut: dict) -> dict:
        """CLI için: komut sözlüğünü ilgili metoda yönlendirir."""
        k = komut.get
        ad = k("komut")
        if ad == "saat":
            return self.saat_ilerlet(k("zaman"))
        if ad in ("rezervasyon", "fiyat", "bekleme"):
            return getattr(self, ad)(k("kullanici"), k("kaynak"), k("baslangic"), k("bitis"))
        if ad == "paket":
            return self.paket(k("kullanici"), k("kalemler"))
        if ad in ("iptal", "giris", "cikis"):
            return getattr(self, ad)(k("rezervasyon"))
        if ad == "sorgu":
            return self.sorgu(k("tur"), k("id"), k("gun"))
        if ad == "kullanici_ekle":
            return self.kullanici_ekle(k("id"), k("ad"), k("rol"), k("sertifikalar"),
                                       k("bakiye"), k("guvenilirlik"))
        if ad == "kaynak_ekle":
            return self.kaynak_ekle(k("id"), k("ad"), k("tur"), k("izinli_roller"))
        return red("BILINMEYEN_KOMUT")
