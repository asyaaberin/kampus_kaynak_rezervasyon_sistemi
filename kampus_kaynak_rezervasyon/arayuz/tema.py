"""Renk paleti ve ortak stil. Tüm renkler tek yerde durur (tutarlılık için)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


def uygulamayi_hazirla(uygulama):
    """Sistem koyu temada olsa bile uygulama açık renk paletiyle çizilir.
    (Aksi halde Fusion stili koyu paleti alır ve açık zeminde yazılar kaybolur.)"""
    try:
        uygulama.styleHints().setColorScheme(Qt.ColorScheme.Light)   # Qt 6.8+
    except AttributeError:
        pass
    uygulama.setStyle("Fusion")
    p = QPalette()
    renkler = {
        QPalette.Window: "#f8fafc", QPalette.WindowText: "#0f172a",
        QPalette.Base: "#ffffff", QPalette.AlternateBase: "#f8fafc",
        QPalette.Text: "#0f172a", QPalette.PlaceholderText: "#94a3b8",
        QPalette.Button: "#ffffff", QPalette.ButtonText: "#0f172a", QPalette.BrightText: "#ffffff",
        QPalette.Highlight: "#2563eb", QPalette.HighlightedText: "#ffffff",
        QPalette.ToolTipBase: "#ffffff", QPalette.ToolTipText: "#0f172a",
        QPalette.Light: "#ffffff", QPalette.Midlight: "#f1f5f9", QPalette.Mid: "#cbd5e1",
        QPalette.Dark: "#94a3b8", QPalette.Shadow: "#64748b", QPalette.Link: "#2563eb",
    }
    for rol, renk in renkler.items():
        p.setColor(rol, QColor(renk))
    for rol in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, rol, QColor("#94a3b8"))
    uygulama.setPalette(p)
    uygulama.setStyleSheet(STIL)

# Rezervasyon durum renkleri: (dolgu, kenar, yazı)
DURUM_RENK = {
    "ONAYLI":     ("#3b82f6", "#1d4ed8", "#ffffff"),
    "KULLANIMDA": ("#16a34a", "#15803d", "#ffffff"),
    "TAMAMLANDI": ("#94a3b8", "#64748b", "#ffffff"),
    "IPTAL":      ("#fee2e2", "#ef4444", "#b91c1c"),
    "GELMEDI":    ("#fef3c7", "#f59e0b", "#b45309"),
}
SOLUK_DURUMLAR = {"IPTAL", "GELMEDI"}   # taralı ve soluk çizilir

BAKIM_RENK = QColor("#475569")
SAAT_CIZGISI = QColor("#dc2626")
SECIM_KENAR = QColor("#0f172a")
IZGARA_SAAT = QColor("#cbd5e1")
IZGARA_CEYREK = QColor("#eef2f6")
GRUP_ZEMIN = QColor("#f1f5f9")
SURUKLE_ZEMIN = QColor(59, 130, 246, 50)

BASARI = "#15803d"
HATA = "#b91c1c"
SOLUK_YAZI = "#64748b"

STIL = """
QWidget { font-size: 10pt; }
QMainWindow, QWidget#kok { background: #f8fafc; }
QFrame#kart { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; }
QLabel#baslik { font-weight: 600; color: #0f172a; font-size: 10.5pt; }
QLabel#saat { font-size: 15pt; font-weight: 700; color: #0f172a; }
QLabel#soluk { color: #64748b; }
QPushButton { padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; }
QPushButton:hover { background: #f1f5f9; }
QPushButton:disabled { color: #94a3b8; }
QPushButton#birincil { background: #2563eb; color: white; border-color: #1d4ed8; font-weight: 600; }
QPushButton#birincil:hover { background: #1d4ed8; }
QTableWidget { border: none; gridline-color: #eef2f6; selection-background-color: #dbeafe; selection-color: #0f172a; }
QHeaderView::section { background: #f8fafc; border: none; border-bottom: 1px solid #e2e8f0; padding: 3px; color: #475569; }
QPlainTextEdit { font-family: Consolas, 'Courier New', monospace; font-size: 9pt; background: #f8fafc; border: 1px solid #e2e8f0; }
QProgressBar { border: 1px solid #e2e8f0; border-radius: 3px; background: #f1f5f9; text-align: center; height: 14px; }
QProgressBar::chunk { border-radius: 3px; }
"""
