# 02 – K5 ücret, doluluk, bant ve pik çarpanları

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00.
Formül: ücret = yuvarla( Σ dilim temel × 0,25 × bant × pik ), bant = 1 + 0,25 × ⌊4 × doluluk⌋,
doluluk = banttaki dolu dk / (türdeki kaynak sayısı × 120).

| No | İşlem | Beklenen | Elle hesap |
|---|---|---|---|
| 1 | o1 ODA-1 10:00–11:00 | r1, 4, 116 | ODA 10-12 bandı boş → 1,0. 4 dilim × 1 = 4 |
| 2 | o2 ODA-2 10:00–10:30 | r2, **3**, 117 | 10-12 bandında r1'in 60 dk'sı var: 60 / (2×120) = **tam 0,25 → 1,25** (alt sınır dahil). 2 dilim × 1 × 1,25 = **2,5 → 3** (yarım yukarı; Python `round(2.5)` 2 verirdi) |
| 3 | o3 ODA-2 11:00–11:30 | r3, 3, 117 | Dolu: 60+30 = 90 → 90/240 = 0,375 → 1,25. 2 × 1,25 = 2,5 → 3 |
| 4 | fiyat a1 ODA-1 11:00–12:00 | 6 | Dolu: 60+30+30 = 120 → 120/240 = 0,5 → 1,5. 4 × 1,5 = 6 |
| 5 | ODA-3 eklenir | TAMAM | ODA kaynak sayısı 3 olur |
| 6 | aynı fiyat | **5** | Payda değişti: 120/(3×120) = 1/3 → ⌊1,33⌋ = 1 → 1,25. 4 × 1,25 = 5 |
| 7 | a1 YAZ-1 15:00–17:00 | r4, 30, 270 | 14-16 bandı boş: 15:00–15:45 arası 4 pik dilim × 3 × 1,5 = 18. 16-18 bandı boş: 4 dilim × 3 (pik yok) = 12. Toplam 30. 300−30 = 270 |
| 8 | o1 YAZ-2 14:00–16:00 | r5, 45, 71 | 14-16 bandında r4'ün 15–16 arası 60 dk'sı var: 60/240 = 0,25 → 1,25. 8 pik dilim × 3 × 1,25 × 1,5 = 45. 116−45 = 71 |
| 9 | fiyat o3 YAZ-1 14:00–14:30 | 16 | 14-16 bandı: r4 60 + r5 120 = 180/240 = 0,75 → 1,75. 2 × 3 × 1,75 × 1,5 = 15,75 → 16. (Hazırlık: 14:30+20 = 14:50 ≤ 15:00, geçer) |
| 10 | a1 LAB-1 09:00–10:30 | r6, 12, 258 | LAB enerji yoğun değil. 08-10 bandında 4 dilim × 2 = 8, 10-12 bandında 2 dilim × 2 = 4. Toplam 12. 270−12 = 258 |
| 11 | t1 CIH-1 09:30–10:30 | r7, 20, 580 | CIHAZ dilimi 16×0,25 = 4. 09:30 ve 09:45 dilimleri pik değil: 2×4 = 8. 10:00 ve 10:15 pik: 2×6 = 12. Toplam 20 |
| 12 | fiyat a1 CIH-1 11:00–12:00 | 30 | CIHAZ'da 1 kaynak var. 10-12 bandında r7'nin 10:00–10:30 arası 30 dk'sı var: 30/120 = 0,25 → 1,25. 4 × 4 × 1,25 × 1,5 = 30. (Hazırlık: 11:00 ≥ 10:30+15) |
| 13 | iptal r7 (saat 08:00) | iade 0, 580, 75 | Başlangıca 1,5 sa kaldı (< 2 sa) → %0, güvenilirlik 80−5 = 75 |
| 14 | aynı fiyat | 24 | r7 IPTAL olduğu için doluluğa sayılmaz → 1,0. 4 × 6 = 24 |
| 15 | fiyat a1 ODA-1 **03-09** 10:00–11:00 | 4 | Doluluk aynı günle sınırlıdır; 03-09 boş. 4 × 1 = 4 |

Not: Doluluk 1 (çarpan 2,00) geçerli bir talep için pratikte oluşamaz. Banttaki tüm kaynaklar
120 dk dolu olsaydı, talep edilen kaynak da o bantta dolu olur ve talep KESISME alırdı.
