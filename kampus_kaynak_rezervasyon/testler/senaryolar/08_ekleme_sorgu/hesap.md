# 08 – kullanici_ekle / kaynak_ekle denetim sırası ve sorgular

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00.
Sıra: ID_MEVCUT → TANIMSIZ_DEGER → GECERSIZ_DEGER (GECERSIZ_DEGER yalnız kullanici_ekle'de denetlenir).

| No | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|
| 1 | o1 tekrar | ID_MEVCUT | başlangıç dosyasında var |
| 2 | o1, rol YOK, bakiye 999 | ID_MEVCUT | ID önce denetlenir |
| 3 | n1, rol YOK, bakiye 999 | TANIMSIZ_DEGER | TANIMSIZ, GECERSIZ'den önce gelir |
| 4 | bakiye −1 | GECERSIZ_DEGER | < 0 |
| 5 | bakiye 121 | GECERSIZ_DEGER | > OGRENCI kotası 120 |
| 6 | güven 101 | GECERSIZ_DEGER | > 100 |
| 7 | güven −1 | GECERSIZ_DEGER | < 0 |
| 8 | güven 50,5 | GECERSIZ_DEGER | tam sayı değil |
| 9 | n1 ARASTIRMACI, bakiye 300, güven 0 | TAMAM | sınır değerler geçerli (300 = kota, 0 dahil) |
| 10 | ODA-1 tekrar (tür HAVUZ) | ID_MEVCUT | ID önce |
| 11 | tür HAVUZ | TANIMSIZ_DEGER | |
| 12 | izinli rollerde MISAFIR var | TANIMSIZ_DEGER | |
| 13 | K1, boş izinli roller | TAMAM | kaynak için GECERSIZ_DEGER denetlenmez |
| 14 | K1 tekrar | ID_MEVCUT | 13. adımda eklendi |
| 15 | sorgu n1 | 300, 0, [] | |
| 16 | o1 → K1 | ROL_IZNI_YOK | izinli listesi boş |
| 17 | sorgu kullanıcı x | BULUNAMADI | |
| 18 | sorgu kaynak YAZ-2 03-08 | [BAKIM 08–10] | bakım pencereleri listelenir |
| 19 | YAZ-2 03-09 | [] | o güne ait bir şey yok |
| 20 | kaynak X | BULUNAMADI | |
| 21 | n1 CIH-1 08–09 | r1, 16, 284 | Güven 0 → ileri sınır 1 gün, ama talep aynı gün. Başlangıç = saat (08:00) → geçmiş değil. CIHAZ dilimi 16 × 0,25 = 4; 08–09 pik değil → 4 dilim × 4 = 16. 300−16 = 284 |
| 22 | t1 CIH-1 12–13 | r2, 24, 576 | 4 pik dilim × 4 × 1,5 = 24. 12-14 bandı boş (r1 08-10 bandında). 600−24 = 576 |
| 23 | sorgu kaynak CIH-1 | r1, r2 | başlangıca göre sıralı |
