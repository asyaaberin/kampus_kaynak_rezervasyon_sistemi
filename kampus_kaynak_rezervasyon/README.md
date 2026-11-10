# Kampüs Kaynak Rezervasyon Sistemi

Yazılım Laboratuvarı I – Proje I (2026–2027 Güz). Kurallar (K1–K11) arayüzden bağımsız
bir Python modülünde (`rezervasyon/`) uygulanır. Bu modül iki yoldan kullanılır:
komut satırından (`calistir.sh` / `calistir.bat`) ve PySide6 masaüstü uygulamasından (`arayuz/`).

## Gereksinimler

- Python **3.11 veya üzeri**
- Rezervasyon modülü ve komut satırı için yalnızca standart kütüphane yeterlidir.
- Masaüstü uygulaması için **PySide6** gerekir (`requirements.txt`).

## Kurulum

### Windows

```bat
py -m pip install -r requirements.txt
```

`python` komutu çalışıyorsa `py` yerine `python` da kullanılabilir.

### Linux

```bash
python3 -m pip install -r requirements.txt
chmod +x calistir.sh
```

Komut satırı için bu adıma gerek yoktur; PySide6 yalnızca arayüz için gerekir.

## Komut satırından çalıştırma (gizli testler bu yolu kullanır)

```bash
# Linux
./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
```

```bat
:: Windows
calistir.bat baslangic.json komutlar.jsonl > sonuclar.jsonl
```

Her komut satırı için bir sonuç satırı yazılır. Çıktı UTF-8'dir, satır sonu `\n`'dir.
`calistir.bat` kod sayfasını UTF-8 yapar (`chcp 65001`) ve önce `python`, o çalışmazsa
`py -3` dener. `calistir.sh` sırayla `python3`, `python` ve `py`'yi dener.

Örnek senaryo:

```bash
./calistir.sh ornek/baslangic.json ornek/komutlar.jsonl > sonuc.jsonl
python3 testler/karsilastir.py sonuc.jsonl ornek/sonuclar.jsonl     # 19/19 satır geçti
```

## Masaüstü uygulaması

```bash
python -m arayuz                          # açılışta başlangıç dosyası seçilir
python -m arayuz ornek/baslangic.json     # doğrudan bu dosyayla açılır
```

(Windows'ta `py -m arayuz`.) Komutlar proje kök klasöründen çalıştırılmalıdır.

**Tek ekran düzeni:**

- **Üst çubuk:** başlangıç dosyası (📂 ile değiştirilir, tüm durum sıfırlanır), simüle saat,
  hızlı ilerletme (+15 dk / +1 sa / +1 gün) ve tarih-saat seçimi. Son ilerletmede oluşan
  olaylar hemen altında listelenir.
- **Takvim:** Kaynaklar satır, eksen 08:00–22:00'dir ve 15 dakikalık ızgara görünür.
  - Kutu renkleri durumu gösterir. IPTAL ve GELMEDI taralı çizilir; bunlar yeni bir
    rezervasyonla çakışırsa alt şeride iner.
  - Bakım koyu taralı, hazırlık süresi kutunun ardında açık taralı bir kuyruk olarak görünür.
    Simüle saat kırmızı çizgiyle gösterilir.
  - Boş alana **sürüklemek** aralığı seçip talep formunu doldurur. Kutuya **tıklamak**
    rezervasyonu seçer.
- **Ayrıntı şeridi:** Seçili rezervasyonun bilgileri ve Giriş / Çıkış / İptal düğmeleri.
  Sonuç (iade, bakiye, güvenilirlik, otomatik atamalar) hemen altında görünür.
- **Kullanıcı paneli:** Kullanıcı listeden seçilir. Bakiye, güvenilirlik, rezervasyonlar ve
  bekleme kayıtları gösterilir. **+** düğmesi kullanıcı ekler, **Sorgula** düğmesi `sorgu`
  komutunu günlüğe yazar.
- **Talep formu:** Tek talep veya paket. Fiyat canlı gösterilir. Paket reddedilirse her
  kalemin sonucu kendi satırında görünür. Talep KESISME veya HAZIRLIK_IHLALI ile
  reddedilirse **Bekleme aç** düğmesi aynı talep için bekleme kaydı açar.
- **Olay günlüğü:** Oturumdaki tüm sonuçlar listelenir. Seçilen satırın komut ve sonuç
  JSON'u yanda gösterilir.

Arayüzde iş kuralı yoktur: hiçbir talebi kendisi engellemez, her şeyi modüle sorar ve
modülün cevabını gösterir. Hata kodlarının Türkçe açıklamaları modüldeki
`HATA_ACIKLAMALARI` sözlüğündedir.

## Testler

```bash
python testler/hepsini_calistir.py
```

Bu komut örnek senaryoyu ve `testler/senaryolar/` altındaki 9 senaryoyu gerçek komut satırı
üzerinden çalıştırır, sonuçları alan alan karşılaştırır (toplam 213 satır). Her senaryo
klasöründe şu dosyalar bulunur:

- `komutlar.jsonl`
- `beklenen.jsonl`
- `hesap.md`: beklenen her değerin kurallardan elle yapılmış hesabı

Karşılaştırma gizli testlerdeki kuralla yapılır: fazladan alan serbesttir; eksik veya
farklı alan hatadır.

| Senaryo | Konu |
|---|---|
| 01_k10_dogrulama | 13 doğrulama kodu, sıra ve sınır değerleri |
| 02_ucret_doluluk | tam 0,25 doluluk, 0,5 yuvarlama, `kaynak_ekle` sonrası payda |
| 03_paket | paket denetim sırası, `kalemler` alanı |
| 04_durum_makinesi | giriş penceresi, iade kademeleri, erken çıkış |
| 05_bakiye_guvenilirlik | Pazartesi sıfırlaması, iade kota tavanı, güvenilirlik < 50 |
| 06_bekleme | bekleme sıralaması, tarama, erken çıkış ile atama |
| 07_olay_sirasi | aynı anda TAMAMLANDI / GELMEDI, SAAT_GERI |
| 08_ekleme_sorgu | ekleme hataları, sorgular |
| 09_parametre_degisikligi | değiştirilmiş başlangıç dosyasıyla aynı kod |

## Klasör yapısı

```
rezervasyon/motor.py     RezervasyonSistemi: tüm kurallar (K1–K11), komut metotları, isle()
calistir.py              komut satırı: başlangıç + komutlar → stdout JSONL
calistir.sh / .bat       teslim betikleri
arayuz/                  PySide6 uygulaması (takvim, paneller, pencereler, oturum)
ornek/                   resmi örnek: baslangic.json, komutlar.jsonl, sonuclar.jsonl
testler/                 senaryolar, karşılaştırma ve toplu çalıştırma betikleri
```

## Belirsiz noktalarda seçilen yorumlar

1. Bitiş = başlangıç durumunda ZAMAN_ADIMI_HATASI döner (K1 "bitiş başlangıçtan sonra
   olmalı" esas alınmıştır).
2. HAFTALIK_SIFIRLAMA, `saat` sonucundaki olaylarda `{zaman, tur}` alanlarıyla raporlanır.
3. İptal sonucundaki `bakiye`, iade eklendikten sonraki ve bekleme taramasından önceki değerdir.
4. Giriş penceresi iki ucu dahil `[b−10, b+15]` aralığıdır. b+15 anında GELMEDI olayı
   işlendiği için pratikte üst uç kullanılamaz.
5. Bekleme sonucundaki `sira`, kaydın öncelik sırasına göre dizilmiş listedeki yeridir.
   Öncelik sırası: güvenilirlik, sonra kayıt saati, sonra numara.
6. Yalnızca bakiyesi yetmeyen bir talep için bekleme istenirse BEKLEME_GEREKSIZ döner,
   çünkü bekleme açılırken bakiye denetlenmez.
7. Başlangıçtan önce çıkış yapılırsa bitiş başlangıca eşitlenir.
8. Bekleme taraması yalnızca iptal, gelmeme ve çıkışta yapılır; bitiş saatinde
   tamamlanmada yapılmaz.
9. Başlangıcı geçmişe düşen bekleme kayıtları saatin her değiştiği anda sessizce silinir.
10. `sorgu kullanici` sonucunda arayüz için ek bir `beklemeler` alanı vardır.
