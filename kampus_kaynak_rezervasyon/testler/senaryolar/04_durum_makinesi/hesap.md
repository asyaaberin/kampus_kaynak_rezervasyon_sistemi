# 04 – K8 durum makinesi, giriş penceresi, iade kademeleri, güvenilirlik

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00. ODA dilimi 1 KP, LAB dilimi 2 KP.

| No | Saat | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|---|
| 1 | 08:00 | o1 ODA-1 10–11 | r1, 4, 116 | 4 dilim × 1 |
| 2 | 08:00 | giris r1 | GIRIS_PENCERESI_DISI | pencere 09:50–10:15 |
| 3 | | giris r99 | BULUNAMADI | sıra: BULUNAMADI → DURUM_HATASI → GIRIS_PENCERESI_DISI |
| 4 | | cikis r1 | DURUM_HATASI | çıkış için KULLANIMDA gerekir |
| 5 | → 09:50 | saat | [] | |
| 6 | 09:50 | giris r1 | KULLANIMDA | pencerenin alt sınırı b−10 dahil |
| 7-8 | | giris / iptal r1 | DURUM_HATASI | iptal yalnız ONAYLI'dan yapılabilir |
| 9 | → 11:00 | saat | TAMAMLANDI r1, o1 82 | bitiş anı yeni saate eşit, olay dahil. +2 → 82 |
| 10 | | cikis r1 | DURUM_HATASI | zaten TAMAMLANDI |
| 11 | 11:00 | o2 ODA-2 03-09 12–14 | r2, 8, 112 | 8 dilim |
| 12 | 11:00 | iptal r2 | iade 8, 120, 80 | kalan 25 sa ≥ 24 → %100 |
| 13 | | o2 ODA-2 13–14 | r3, 4, 116 | |
| 14 | 11:00 | iptal r3 | iade 2, 118 | kalan **tam 2 sa** → %50 kademesi (2 sa dahil). 4/2 = 2 |
| 15 | | o2 ODA-2 15:00–16:15 | r4, 5, 113 | 5 dilim (14-16 bandında 4, 16-18 bandında 1), bantlar boş |
| 16 | → 12:00 | saat | [] | |
| 17 | 12:00 | iptal r4 | iade 2, 115 | kalan 3 sa → %50 × 5 = 2,5 → **aşağı yuvarlanır, 2** |
| 18 | | o2 ODA-2 13:00–13:30 | r5, 2, 113 | r3 ve r4 IPTAL olduğu için ardışık kontrolünde sayılmaz |
| 19 | 12:00 | iptal r5 | iade 0, 113, **75** | kalan 1 sa < 2 sa → %0, güven −5 |
| 20 | | o3 ODA-1 13–15 | r6, 8, 112 | 12-14 ve 14-16 bantlarında ONAYLI rezervasyon yok |
| 21-22 | → 12:55 | giris r6 | KULLANIMDA | |
| 23-24 | → 13:40 | cikis r6 | TAMAMLANDI, güven 80, [] | erken çıkış: güven değişmez, iade yok |
| 25 | | sorgu o3 | r6 bitiş **13:40** | bitiş, çıkış saatine çekildi; ücret 8 aynı kaldı |
| 26 | 13:40 | o3 LAB-1 14–15 | r7, 8, 104 | 4 dilim × 2 = 8 |
| 27-30 | 13:50 giriş, 14:25 çıkış | | TAMAMLANDI | r7'nin bitişi artık 14:25 |
| 31 | 14:25 | a1 LAB-1 14:30–15:00 | HAZIRLIK_IHLALI | TAMAMLANDI hazırlıkta sayılır: 14:30 < 14:25+10 = 14:35 |
| 32 | | a1 LAB-1 14:45–15:15 | r8, 4, 296 | 14:45 ≥ 14:35. r7 TAMAMLANDI olduğu için doluluğa sayılmaz → 2 dilim × 2 = 4 |
| 33 | | o2 ODA-2 16–17 | r9, 4, 109 | |
| 34 | → 16:15 | saat | 15:00 GELMEDI r8 a1 65; 16:15 GELMEDI r9 o2 60 | r8 14:45+15 = 15:00. r9 16:00+15 = 16:15 (yeni saate eşit, dahil). o2: 75−15 = 60 |
| 35 | | giris r9 | DURUM_HATASI | GELMEDI |
| 36 | | o1 ODA-1 17–18 | r10, 4, 112 | r9 GELMEDI olduğu için doluluğa sayılmaz |
| 37-38 | → 17:14 | giris r10 | KULLANIMDA | 17:14 ≤ 17:15 |
| 39 | → 18:00 | saat | TAMAMLANDI r10 o1 84 | 82+2 |
| 40 | | sorgu o2 | r3, r5, r4, r9, r2 | başlangıca göre sıralı. r3 ile r5 aynı anda (13:00) başlıyor → numara sırası. bakiye 109, güven 60 |
