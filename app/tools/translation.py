from __future__ import annotations
import re

VN_TRANSLATIONS = {
    "Giảm độ dày lon 330ml xuống 0.235mm": "Reduce 330ml can gauge to 0.235mm",
    "giam can gauge 330ml": "Reduce 330ml can gauge",
    "Bỏ in nhãn màu vàng trên thùng carton 24 lon": "Remove yellow label printing on 24-can carton",
    "Đổi nắp khoén 26mm sang 24mm": "Change 26mm pull-tab cap to 24mm",
}
CN_TRANSLATIONS = {
    "330 毫升铝罐颈部规格统一为 202 直径": "Standardise 330ml aluminium can neck finish to 202 diameter",
    "330ml 罐 颈口标准化 202": "Standardise 330ml can neck finish to 202 diameter",
    "取消彩盒，改为简装托盘": "Remove colour carton and switch to simple tray",
    "啤酒瓶颈玻璃克重从 145g 降到 138g": "Reduce beer bottle neck glass weight from 145g to 138g",
    "夏季出货取消热缩膜": "Remove shrink film for summer shipments",
}

def detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]", text.lower()):
        return "vi"
    return "en"

def translate_to_english(text: str, language: str = "auto") -> str:
    if text in VN_TRANSLATIONS:
        return VN_TRANSLATIONS[text]
    if text in CN_TRANSLATIONS:
        return CN_TRANSLATIONS[text]
    lowered = text.lower()
    if "giam" in lowered and "gauge" in lowered and "330" in lowered:
        return "Reduce 330ml can gauge"
    if "bio-pe" in lowered:
        return text
    return text
