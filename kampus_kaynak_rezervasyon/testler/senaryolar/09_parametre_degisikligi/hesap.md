# 09 – Değiştirilmiş başlangıç parametreleri (kod değişmeden yeni kural)

Bu senaryo **kendi `baslangic.json` dosyasını** kullanır. Değişiklikler:
- YAZICI: hazırlık **45** dk, temel **10**
- ODA: temel **6**, **enerji yoğun**
- OGRENCI: kota **50**, ileri **2** gün, azami **60** dk
- LAB türü tanımlı değil

Dilimler: YAZICI 10 × 0,25 = 2,5 (pikte 3,75); ODA 6 × 0,25 = 1,5 (pikte 2,25).

| No | İşlem | Beklenen | Elle hesap |
|---|---|---|---|
| 1 | o1 YAZ-1 10–11 | r1, 15, 35 | 4 pik dilim × 3,75 = 15. 50−15 = 35 |
| 2 | o2 YAZ-1 11:30–12:00 | HAZIRLIK_IHLALI | yeni h = 45: 11:30 < 11:00+45 = 11:45 (eski h = 20 ile geçerdi) |
| 3 | o2 YAZ-1 11:45–12:30 | r2, 12, 38 | 11:45 ≥ 11:45 → geçer. 45 dk ≤ 60. 11:45 dilimi 10-12 bandında: r1 60/(2×120) = 0,25 → 1,25 → 2,5 × 1,25 × 1,5 = 4,6875. 12:00 ve 12:15 dilimleri 12-14 bandında: boş → 2 × 3,75 = 7,5. Toplam 12,1875 → 12. 50−12 = 38 |
| 4 | o1 ODA-1 10:00–11:30 | SURE_SINIRI | 90 > 60 (yeni azami süre) |
| 5 | o1 ODA-1 03-10 08:00–08:30 | r3, 3, 32 | ileri 2 gün → sınır 03-10 08:00 (eşit geçerli). 08:00 pik değil: 2 × 1,5 = 3. 35−3 = 32 |
| 6 | o1 ODA-1 03-10 08:15 | ILERI_TARIH_SINIRI | 08:15 > 08:00 |
| 7 | o1 ODA-2 03-08 10–11 | r4, 9, 23 | ODA artık enerji yoğun → pik uygulanır: 4 × 1,5 × 1,5 = 9 (03-08'de ODA bandı boş). 32−9 = 23 |
| 8 | o3 bakiye 51 | GECERSIZ_DEGER | yeni kota 50 |
| 9 | LAB türü | TANIMSIZ_DEGER | bu dosyada LAB tanımlı değil |
