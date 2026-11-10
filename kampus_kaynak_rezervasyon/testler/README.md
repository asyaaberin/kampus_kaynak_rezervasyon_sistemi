# Test senaryoları

Her senaryo klasörü şu dosyaları içerir:

- `komutlar.jsonl`: komut dosyası
- `beklenen.jsonl`: beklenen sonuçlar
- `hesap.md`: beklenen her değerin kurallardan elle yapılmış hesabı

Beklenen değerler programın çıktısından kopyalanmamıştır; kurallardan elle hesaplanmıştır.
Bir klasörde `baslangic.json` yoksa senaryo ortak `baslangic_test.json` dosyasını kullanır.

## Çalıştırma

Tüm senaryoları (resmi örnek dahil) çalıştırıp alan alan karşılaştırmak için:

```bash
python testler/hepsini_calistir.py
```

Beklenen çıktı: `TOPLAM: 213/213 satır, 10/10 senaryo geçti`.

Tek bir senaryo için:

```bash
./calistir.sh testler/baslangic_test.json testler/senaryolar/01_k10_dogrulama/komutlar.jsonl > sonuc.jsonl
python testler/karsilastir.py sonuc.jsonl testler/senaryolar/01_k10_dogrulama/beklenen.jsonl
```

Karşılaştırma gizli testlerle aynı kuralla yapılır: fazladan alan serbesttir; eksik veya
farklı alan hatadır.

## Senaryolar

| Klasör | Satır | Sınanan kurallar |
|---|---|---|
| `01_k10_dogrulama` | 29 | K10'un 13 kodunun hepsi; birden çok hata olduğunda sıranın etkisi; sınırlar (22:00, 180 dk, ileri tarih eşitliği, bakiye = ücret); bakımdan hemen sonra rezervasyon; simetrik hazırlık formülü |
| `02_ucret_doluluk` | 15 | K5: tam 0,25 doluluk → 1,25; 2,5 → 3 yuvarlama; 0,5 ve 0,75 bantları; `kaynak_ekle` sonrası payda; pik / pik dışı dilimler; IPTAL rezervasyonun ve başka günün doluluğa sayılmaması |
| `03_paket` | 18 | K7: paket denetim sırası, `kalemler` alanı, kalemlerin birbirinin doluluğuna katılmaması, paket kaleminin tek başına iptali |
| `04_durum_makinesi` | 40 | K8: giriş penceresinin iki ucu, iade kademeleri (%100 / tam 2 saatte %50 / %0), erken çıkış ve hazırlığa etkisi, sorgudaki sıralama |
| `05_bakiye_guvenilirlik` | 25 | K6: Pazartesi sıfırlaması, iade kota tavanı; güvenilirlik < 50'nin etkileri; güvenilirliğin 0 ve 100'e kırpılması |
| `06_bekleme` | 23 | K9: kayıt açma koşulları, sıralama, tarama, erken çıkışta otomatik atama, geçmişe düşen kaydın silinmesi |
| `07_olay_sirasi` | 12 | K11: aynı anda TAMAMLANDI ve GELMEDI, taramanın gelmeme sırasıyla yapılması, SAAT_GERI |
| `08_ekleme_sorgu` | 23 | Ekleme komutlarının hata sırası (ID_MEVCUT → TANIMSIZ_DEGER → GECERSIZ_DEGER), sorgular |
| `09_parametre_degisikligi` | 9 | Kendi `baslangic.json` dosyasıyla aynı kodun yeni parametrelere uyması |

Dokümandaki 24 hata kodunun tamamı bu senaryolarda en az bir kez beklenen sonuç olarak yer alır.
