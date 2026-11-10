# 07 – K11 aynı andaki olayların sırası, SAAT_GERI

Başlangıç: `testler/baslangic_test.json`, saat 2027-03-08T08:00.
Aynı anda: HAFTALIK_SIFIRLAMA → TAMAMLANDI (numara ↑) → GELMEDI (numara ↑) → boşalan kaynaklar için tarama (gelmeme sırasıyla).

| No | İşlem | Beklenen | Elle gerekçe |
|---|---|---|---|
| 1 | o1 ODA-1 11–12 | r1, 4, 116 | ODA 10-12 bandı boş, 4 dilim |
| 2 | o2 ODA-2 11–12 | r2, 5, 115 | r1'in 60 dk'sı: 60/240 = 0,25 → 1,25. 4 × 1,25 = 5 |
| 3 | a1 LAB-1 10:00–11:15 | r3, 10, 290 | 5 dilim × 2 |
| 4 | t1 CIH-1 10:00–11:15 | r4, 30, 570 | 5 pik dilim × 4 × 1,5 = 30 |
| 5 | o3 ODA-2 11:30–12:00 bekleme | b1, 1 | r2 ile KESISME |
| 6 | a1 ODA-1 11:30–12:00 bekleme | b2, 1 | r1 ile KESISME. ODA-1 listesinde tek kayıt |
| 7-9 | → 09:55, r3 ve r4'e giriş | KULLANIMDA | pencere 09:50–10:15 |
| 10 | saat 09:00 | SAAT_GERI | 09:00 < 09:55 |
| 11 | saat 09:55 (aynı saat) | TAMAM, [] | geri değil; (09:55, 09:55] aralığı boş |
| 12 | → 11:15 | 6 olay | **11:15'te dört olay aynı anda:** r3 ve r4'ün bitişi (TAMAMLANDI), r1 ve r2'nin başlangıç+15'i (GELMEDI). r1 ve r2'nin numarası daha küçük olsa da TAMAMLANDI'lar önce gelir: r3 82, r4 82. Sonra GELMEDI r1 o1 65, r2 o2 65. **Tarama gelmeme sırasıyla yapılır:** önce ODA-1 (r1) → b2 (numarası b1'den büyük olsa da önce atanır). ODA 10-12 bandında ONAYLI/KULLANIMDA yok → 2 dilim × 1 = 2, a1 290 → 288, r5. Sonra ODA-2 (r2) → b1: bant 10-12'de artık r5'in 30 dk'sı var: 30/240 = 0,125 → 1,0 → 2, o3 120 → 118, r6 |
