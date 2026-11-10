# 03 – K7 paket rezervasyon ve denetim sırası

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00.
Paket sırası: BULUNAMADI → PAKET_BOYUTU → GUVENILIRLIK_DUSUK → PAKET_RED → PAKET_ICI_KESISME → BAKIYE_YETERSIZ.

| No | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|
| 1-3 | d1 (güven 40), d2 (güven 50), k1 (bakiye 50) eklenir | TAMAM | |
| 4 | x9 paketi | BULUNAMADI | kullanıcı yok (`kalemler` alanını beklemiyoruz; PDF yalnız BOYUTU ve GUVENILIRLIK için boş liste diyor) |
| 5 | 1 kalem | PAKET_BOYUTU, [] | 1 < 2 |
| 6 | 5 kalem | PAKET_BOYUTU, [] | 5 > 4; boyut, kalem doğrulamasından önce gelir |
| 7 | d1, 1 kalem | PAKET_BOYUTU | güven 40 < 50 ama boyut önce denetlenir |
| 8 | d1, 2 geçerli kalem | GUVENILIRLIK_DUSUK, [] | 40 < 50 |
| 9 | 3 kalem: geçerli / 10:10 / 07:00 | PAKET_RED | Tüm kalemler doğrulanır: 0 TAMAM, 1 ZAMAN_ADIMI_HATASI, 2 GECMIS_ZAMAN. `sira` 0'dan başlar |
| 10 | 0 ve 1 aynı kaynakta kesişiyor, 2 YAZ-9 yok | PAKET_RED | Her kalem tek başına ve paket öncesi duruma göre doğrulanır. 0 ve 1 tek başına geçer, kendi aralarındaki kesişme 5. adımda bakılır. PAKET_RED 5. adımdan önce gelir |
| 11 | ODA-1 10–11 ve 10:30–11:30 | PAKET_ICI_KESISME | iki kalem de TAMAM listelenir |
| 12 | ODA-1 10–11 ve 11:30–12:00 | PAKET_ICI_KESISME | ODA'da h = 0 ama aynı kullanıcı: 30 dk < 60 → ardışık ihlali |
| 13 | ODA-1 10–11 ve 12–13 | p1 [r1,r2] [4,4] 8, 292 | Boşluk tam 60 dk → geçer. İkisi de boş bantta: 4 dilim × 1 = 4. 300−8 = 292 |
| 14 | t1: ODA-2 14–15 ve ODA-1 14–15 | p2 [r3,r4] [4,4] 8, 592 | **Kalemler birbirinin doluluğuna katılmaz:** 14-16 bandı paket öncesi boş → ikisi de 4. Sırayla alınsaydı ikincisi 60/240 = 0,25 → 5 olurdu. 600−8 = 592 |
| 15 | k1: YAZ-1 ve YAZ-2 14–17 | BAKIYE_YETERSIZ | Her biri: 8 pik dilim × 4,5 = 36 + 4 dilim × 3 = 12 → 48. Toplam 96 > 50. Kalemler TAMAM listelenir |
| 16 | d2 (güven tam 50) | p3 [r5,r6] [2,2] 4, 296 | 50 < 50 değil → paket yapılabilir. ODA'nın 16-18 bandı boş: 2 dilim → 2. 300−4 = 296 |
| 17 | iptal r3 (paketin tek kalemi) | iade 2, 594, 80 | Paket kalemi tek başına iptal edilebilir. 14:00'e 6 sa kaldı → %50 × 4 = 2. 592+2 = 594 ≤ 600 |
| 18 | sorgu kaynak ODA-1 | r1, r2, r4, r6 | yalnız ONAYLI olanlar, başlangıca göre sıralı |
