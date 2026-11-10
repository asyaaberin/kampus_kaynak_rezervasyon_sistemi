# 06 – K9 bekleme listesi: açma koşulları, sıralama, tarama, erken çıkış, silme

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00. YAZICI: h = 20, dilim 3, pikte 4,5.
Sıralama: güvenilirlik ↓, kayıt saati ↑, numara ↑.

| No | Saat | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|---|
| 1 | 08:00 | a1 YAZ-1 10–12 | r1, 36, 264 | 8 pik dilim × 4,5 |
| 2 | | o1 YAZ-1 11:00–11:30 bekleme | b1, sıra 1 | r1 ile KESISME |
| 3 | | o2 YAZ-1 12:00–13:00 bekleme | b2, sıra 2 | KESISME yok (12:00 < 12:00 değil), HAZIRLIK var (12:00 < 12:20) → kayıt açılır. Güven eşit (80), kayıt saati eşit → numara: b1, b2 |
| 4-5 | | h1 (güven 95) 10:30–11:30 | b3, **sıra 1** | daha yüksek güvenilirlik öne geçer |
| 6 | | o3 10:00–10:15 | SURE_SINIRI | başka hata varsa o hatanın kodu döner (SURE, KESISME'den önce gelir) |
| 7 | | o1 YAZ-1 14–15 | BEKLEME_GEREKSIZ | talep zaten geçerli |
| 8 | | o1 CIH-1 | ROL_IZNI_YOK | |
| 9-10 | | p1 (bakiye 0) YAZ-1 14–15 | BEKLEME_GEREKSIZ | bekleme açılırken bakiye denetlenmez. Ücret 18 > 0 olsa da talep "geçerli" sayılır |
| 11 | | p1 11:00–12:00 | b4, sıra 4 | bakiye 0 ama kayıt açılır. Sıra: b3(95), b1, b2, b4 |
| 12 | | x9 | BULUNAMADI | |
| 13 | 08:00 | iptal r1 | iade 18, 282, 80; 2 atama | Kalan tam 2 sa → %50 × 36 = 18. 264+18 = 282. **Tarama (b3, b1, b2, b4):** b3 h1 10:30–11:30 geçerli. 10-12 bandında YAZICI boş (r1 IPTAL) → 4 × 4,5 = 18, h1 120 → 102, r2. b1 10:30–11:30'daki r2 ile kesişiyor → listede kalır. b2 12:00 ≥ 11:30+20 → geçerli. 12-14 bandı boş → 18, o2 102, r3. b4 r2 ile kesişiyor → kalır. **Tarama sonuna kadar sürer** |
| 14-15 | → 10:25 | giris r2 | KULLANIMDA | pencere 10:20–10:45 |
| 16-17 | → 10:40 | cikis r2 | TAMAMLANDI, güven 95; atama b1 → r4 | Erken çıkış yer boşaltır, r2'nin bitişi 10:40 olur. Tarama: b1 o1 11:00–11:30. Hazırlık: 11:00 < 10:40+20 = 11:00 değil → geçer. r3'e göre: 11:30+20 = 11:50 ≤ 12:00 → geçer. 10-12 bandında ONAYLI/KULLANIMDA YAZICI yok → 2 × 4,5 = 9. o1 120 → 111. b4 r4 ile kesişiyor → kalır |
| 18 | → 11:05 | saat | [] | r4'ün gelmeme anı 11:15, henüz gelmedi |
| 19 | 11:05 | o3 11:15–12:00 bekleme | b5, sıra **1** | r4 ile KESISME. b4'ün başlangıcı 11:00 < 11:05 → **silindi**, bu yüzden listede yalnız b5 var |
| 20 | | h1 12:30–13:00 bekleme | b6, sıra 1 | r3 ile KESISME. h1 95 > o3 80 → b6 öne geçer |
| 21 | → 12:20 | saat | 11:15 GELMEDI r4 o1 65; 12:15 GELMEDI r3 o2 65; 12:15 ATAMA b6 → r5, 9, 93 | 11:15'teki taramada: b5 hâlâ r3 ile HAZIRLIK ihlali yapıyor (12:00+20 > 12:00), b6 r3 ile kesişiyor → ikisi de kalır. 12:15'te: b5'in başlangıcı 11:15 < 12:15 → silinir. b6 geçerli (r3 GELMEDI; h1'in r2'siyle ardışık boşluk 12:30 − 10:40 ≥ 60). 12-14 bandı boş → 2 × 4,5 = 9. 102−9 = 93 |
| 22 | | sorgu kaynak YAZ-1 | yalnız r5 | r1 IPTAL, r2 TAMAMLANDI, r3/r4 GELMEDI listelenmez |
| 23 | | sorgu h1 | r2 (bitiş 10:40, TAMAMLANDI, 18), r5 (ONAYLI, 9) | |
