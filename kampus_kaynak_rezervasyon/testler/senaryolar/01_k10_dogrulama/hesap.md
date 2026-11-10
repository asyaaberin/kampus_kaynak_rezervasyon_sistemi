# 01 – K10 doğrulama sırası (rezervasyon hataları)

Başlangıç: `testler/baslangic_test.json`, saat **2027-03-08T08:00 (Pazartesi)**.
Dilim ücretleri: ODA 4×0,25 = **1**; YAZICI 12×0,25 = **3** (pikte 3×1,5 = **4,5**).

| No | Talep | Beklenen | Elle gerekçe |
|---|---|---|---|
| 1 | x1 yok | BULUNAMADI | K10-1: kullanıcı yok |
| 2 | ODA-9 yok | BULUNAMADI | K10-1: kaynak yok |
| 3 | 10:10 | ZAMAN_ADIMI_HATASI | :10 15 dakikalık adıma oturmaz |
| 4 | 11:00→10:00 | ZAMAN_ADIMI_HATASI | bitiş başlangıçtan önce |
| 5 | 10:00→10:00 | ZAMAN_ADIMI_HATASI | K1 "bitiş başlangıçtan sonra olmalı" (onaylı yorum 1) |
| 6 | 07:00–07:30 | GECMIS_ZAMAN | 07:00 < 08:00. Çalışma saati dışı da ama adım 3, adım 4'ten önce gelir |
| 7 | 21:30–22:15 | CALISMA_SAATI_DISI | bitiş 22:00'ı aşıyor |
| 8 | 21:00 → ertesi gün 09:00 | CALISMA_SAATI_DISI | gün aşımı. Süre de aşılıyor ama adım 4, adım 5'ten önce gelir |
| 9 | ODA-1 21:30–22:00 | TAMAM r1, 2, 118 | 22:00 sınırı dahil. 2 dilim × 1 × 1,0 (20-22 bandı boş) = 2. 120−2 = 118 |
| 10 | 15 dk | SURE_SINIRI | 15 < 30 |
| 11 | 195 dk | SURE_SINIRI | 195 > 180 (OGRENCI azami süresi) |
| 12 | ODA-2 10:00–13:00 | TAMAM r2, 12, 106 | 180 dk tam sınırda. ODA'nın 10-12 ve 12-14 bantları boş (r1 20-22'de). 12 dilim × 1 = 12. 118−12 = 106 |
| 13 | ODA-1 03-15 08:00 | TAMAM r3, 2, 104 | Sınır = 03-08 08:00 + 7×24 sa = 03-15 08:00. "Aşamaz" dendiği için eşit geçerli. 2 dilim → 2 |
| 14 | ODA-1 03-15 08:15 | ILERI_TARIH_SINIRI | 08:15 > 08:00 |
| 15 | o1 → CIH-1 | ROL_IZNI_YOK | OGRENCI izinli değil. Sertifika da yok ama adım 7, adım 8'den önce gelir |
| 16 | o1 → LAB-1 | SERTIFIKA_YOK | LAB_GUVENLIK yok |
| 17 | YAZ-2 09:30–10:30 | BAKIM | bakım 08:00–10:00 ile kesişir |
| 18 | YAZ-2 10:00–11:00 | TAMAM r4, 18, 86 | K2: bakım 10:00'da biter ve bakımdan sonra hazırlık uygulanmaz. 4 pik dilim × 4,5 × 1,0 = 18. 104−18 = 86 |
| 19 | o2 YAZ-2 10:30–11:30 | KESISME | r4 (10–11) ile kesişir |
| 20 | o2 YAZ-2 11:15–12:00 | HAZIRLIK_IHLALI | 11:15 < 11:00+20 = 11:20 |
| 21 | o2 YAZ-1 14:00–15:00 | TAMAM r5, 18, 102 | YAZICI'nın 14-16 bandı boş → 1,0. 4 × 4,5 = 18. 120−18 = 102 |
| 22 | o1 YAZ-1 13:00–13:45 | HAZIRLIK_IHLALI | **Simetrik formül, talep mevcut rezervasyondan önce:** e+h = 13:45+20 = 14:05 > 14:00 = b′ ve b = 13:00 < e′+h = 15:20 |
| 23 | o1 YAZ-1 12:45–13:30 | TAMAM r6, 14, 72 | e+h = 13:50 ≤ 14:00 → geçer. YAZICI'nın 12-14 bandı boş. 3 pik dilim × 4,5 = 13,5 → **yukarı yuvarlanır, 14**. 86−14 = 72 |
| 24 | o2 YAZ-1 15:30–16:00 | ARDISIK_KULLANIM | Hazırlık: 15:30 ≥ 15:20, geçer. K4: 15:30 < 15:00+60 = 16:00 |
| 25 | o2 YAZ-1 16:00–16:30 | TAMAM r7, 6, 96 | 16:00 < 16:00 olmadığı için geçer (sınır). 16:00 dilimi pik değil (10–16, 16 hariç). 2 × 3 = 6. 102−6 = 96 |
| 26 | o9 ekle (bakiye 5) | TAMAM | |
| 27 | o9 ODA-1 16:00–18:00 | BAKIYE_YETERSIZ | ODA'nın 16-18 bandı boş. 8 dilim × 1 = 8 > 5 |
| 28 | aynı talep için fiyat | TAMAM 8 | fiyat bakiyeye bakmaz |
| 29 | o9 ODA-1 16:00–17:15 | TAMAM r8, 5, 0 | 5 dilim = 5. Kural "ücret > bakiye" olduğu için 5 = 5 geçer. Bakiye 0 |
