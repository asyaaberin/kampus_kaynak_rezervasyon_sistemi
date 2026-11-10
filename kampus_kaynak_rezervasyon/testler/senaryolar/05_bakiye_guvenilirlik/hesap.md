# 05 – K6 haftalık kota, iade tavanı ve güvenilirlik < 50 etkileri

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00 (Pazartesi). ODA dilimi 1 KP. OGRENCI kotası 120.

| No | Saat | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|---|
| 1 | → 03-14 09:00 (Pazar) | saat | [] | (03-08 08:00, 03-14 09:00] aralığında Pazartesi 00:00 yok. Başlangıç anı 03-08 00:00'ı "geçmek" sayılmaz |
| 2 | | o1 ODA-1 03-16 10–12 | r1, 8, 112 | 8 dilim |
| 3 | | o1 ODA-1 03-17 10–11 | r2, 4, 108 | |
| 4 | → 03-15 00:00 | saat | HAFTALIK_SIFIRLAMA | tam yeni saatteki olay dahil. Olay {zaman, tur} olarak raporlanır (onaylı yorum 2) |
| 5 | | sorgu o1 | bakiye **120** | 108 → kotaya eşitlendi |
| 6 | | o1 ODA-2 03-15 10–11 | r3, 4, 116 | |
| 7 | 03-15 00:00 | iptal r1 | **iade 4**, 120 | kalan 34 sa → %100 = 8. Ama tavan: 120 − 116 = 4. İade alanı gerçekte eklenen miktardır → 4 |
| 8 | | iptal r2 | **iade 0**, 120 | %100 = 4 ama bakiye zaten kotada |
| 9 | → 03-29 00:00 | saat | GELMEDI r3 (03-15 10:15, güven 65), SIFIRLAMA 03-22, SIFIRLAMA 03-29 | olaylar kronolojik sırada. İki Pazartesi geçildi |
| 10 | | d1 ekle (güven 49) | TAMAM | |
| 11 | 03-29 00:00 | d1 ODA-1 03-30 08:00 | ILERI_TARIH_SINIRI | 49 < 50 → sınır 1 gün = 03-30 00:00. 08:00 bunu aşar |
| 12 | | d1 ODA-1 03-29 10:00–10:30 | r4, 2, 118 | 1 gün içinde |
| 13 | | d1 paket | GUVENILIRLIK_DUSUK, [] | |
| 14 | | o1 ODA-2 09:00–09:30 | r5, 2, 118 | o1'in bakiyesi 03-29'da 120'ye sıfırlandı |
| 15 | | o1 ODA-2 11:00–11:30 | r6, 2, 116 | Ardışık: 11:00 ≥ 09:30+60 = 10:30. 10-12 bandında r4'ün 30 dk'sı var: 30/240 = 0,125 → 1,0 |
| 16 | → 11:15 | saat | GELMEDI r5 o1 **50**; r4 d1 34; r6 o1 **35** | 65−15 = 50; 49−15 = 34; 50−15 = 35. r6'nın olayı 11:00+15 = 11:15, yeni saate eşit |
| 17 | 11:15 | o1 ODA-1 03-31 10:00 | ILERI_TARIH_SINIRI | o1 artık 35 < 50 → sınır 03-30 11:15 |
| 18 | | o1 ODA-1 03-30 10:00 | r7, 2, 114 | sınır içinde. 116−2 = 114 |
| 19-20 | | z1 (güven 10) ODA-2 12:00–12:30 | r8, 2, 118 | 10 < 50 ama aynı gün, sınır içinde |
| 21-22 | | y1 (güven 99) ODA-2 13:00–13:30 | r9, 2, 118 | 12-14 bandında r8'in 30 dk'sı var: 0,125 → 1,0 |
| 23 | → 12:50 | saat | GELMEDI r8 z1 **0** | 10−15 = −5 → alt sınır 0'a kırpılır |
| 24 | | giris r9 | KULLANIMDA | pencere 12:50–13:15 |
| 25 | → 13:30 | saat | TAMAMLANDI r9 y1 **100** | 99+2 = 101 → üst sınır 100'e kırpılır |
