"""
Russian Vocab Studio – translations
Türkçe / Русский / English
"""

TRANSLATIONS = {
    "tr": {
        "app_title": "Rusça Kelime Stüdyosu",
        "app_subtitle": "PDF'den Rusça kelimeleri çıkar, temiz bir CSV olarak dışa aktar.",
        "language": "Dil",

        "status_ready": "Hazır",
        "status_working": "İşleniyor…",
        "status_ocr_init": "OCR modeli yükleniyor (ilk seferde ~200 MB iniyor)…",
        "status_ocr_running": "OCR çalışıyor…",
        "status_ocr_page": "OCR — sayfa {pos}",
        "status_searchable_pdf": "Aranabilir PDF oluşturuluyor…",
        "msg_searchable_pdf_done": "Aranabilir PDF: {path}",
        "status_done": "Tamamlandı",
        "status_error": "Hata",

        "pdf_card_title": "PDF",
        "pdf_drop_hint": "PDF'i buraya sürükle veya seçmek için tıkla",
        "pdf_change": "Değiştir",
        "pdf_browse": "PDF Seç",
        "pdf_no_file": "Henüz PDF seçilmedi",
        "pdf_pages_label": "{n} sayfa",

        "pages_card_title": "Sayfa Aralığı",
        "pages_start": "Başlangıç",
        "pages_end": "Bitiş",
        "pages_all": "Tüm sayfalar",

        "pos_card_title": "Kelime Türleri",
        "pos_noun": "İsim",
        "pos_verb": "Fiil",
        "pos_adj": "Sıfat",
        "pos_adv": "Zarf",
        "pos_other": "Diğer",

        "filters_card_title": "Filtreler",
        "filter_remove_proper": "Özel isimleri çıkar",
        "filter_remove_basic": "Temel kelimeleri çıkar",
        "filter_min_length": "Min. harf sayısı",
        "filter_min_freq": "Min. tekrar",
        "filters_hint": "Sadece N harften uzun ve PDF'de en az N kez geçen kelimeleri al. Örn. “min. tekrar = 5” → 5 ve daha fazla kez geçenler.",

        "output_card_title": "Çıktı",
        "output_path": "Kayıt yolu",
        "output_choose": "Seç",
        "output_open_folder": "Klasörü Aç",
        "output_include_freq": "Frekansı dahil et",
        "output_include_pos": "Kelime türünü dahil et",
        "output_sort": "Sıralama",
        "sort_freq": "Sıklığa göre (azalan)",
        "sort_alpha": "Alfabetik",

        "reading_card_title": "Okuma Modu",
        "reading_auto": "Otomatik",
        "reading_text": "Sadece metin",
        "reading_ocr": "OCR (taranmış PDF)",

        "action_extract": "Kelimeleri Çıkar",
        "action_extracting": "Çıkarılıyor…",
        "action_cancel": "İptal",

        "msg_select_pdf": "Önce bir PDF seç.",
        "msg_done": "{n} kelime çıkarıldı → {path}",
        "msg_error": "Bir hata oluştu: {err}",
        "msg_no_words": "Bu PDF'den çıkarılacak kelime bulunamadı.",
        "msg_no_cyrillic": "PDF'de Kiril metni bulunamadı — büyük olasılıkla taranmış görüntü PDF'i (metin katmanı yok).\n\nÇözüm: PDF'i önceden OCR'lat (ör. ilovepdf.com/ocr-pdf veya Adobe Acrobat) ve OCR'lı versiyonu tekrar yükle. Ya da “Okuma Modu → OCR”u dene (EasyOCR / Tesseract kurulu olmalı).",
        "msg_no_tokens": "PDF'de Kiril karakterleri var ama tanınabilir kelime çıkarılamadı (alışılmadık karakter kodlaması olabilir).",
        "msg_all_filtered": "Kelimeler bulundu ama hepsi filtreler tarafından elendi. “Min. tekrar”ı 1'e indirmeyi veya “Temel kelimeleri çıkar” seçeneğini kapatmayı dene.",
        "msg_pymorphy_missing": "Rusça analiz için 'pymorphy3' kurulu değil. Kurmak için: pip install pymorphy3",
        "msg_pymupdf_missing": "PDF okuma için 'pymupdf' kurulu değil. Kurmak için: pip install pymupdf",
        "msg_custom_exclude_missing": "Özel exclude dosyası bulunamadı: {path}",
        "msg_cancelled": "İşlem iptal edildi.",
        "msg_csv_locked": "CSV dosyası başka bir programda açık görünüyor (büyük ihtimalle Excel). Lütfen dosyayı kapat veya farklı bir kayıt yolu seç, sonra tekrar dene.\n\nDosya: {path}",
        "msg_csv_perm_denied": "Bu konuma yazma izni yok. Lütfen farklı bir kayıt yolu seç.\n\nDosya: {path}",
        "msg_csv_write_failed": "CSV yazılamadı: {err}\n\nDosya: {path}",

        "dlg_pdf_title": "PDF Seç",
        "dlg_csv_title": "CSV'yi nereye kaydedeyim?",
        "dlg_pdf_filter": "PDF dosyaları (*.pdf)",
        "dlg_csv_filter": "CSV dosyaları (*.csv)",
        "dlg_exclude_title": "Hariç tutulacak kelimeler (.txt)",
        "dlg_txt_filter": "Metin dosyaları (*.txt)",

        "export_mode": "Dışa aktarma",
        "export_single": "Tek CSV",
        "export_separate": "Türlere ayır (her POS ayrı dosya)",
        "export_both": "Her ikisi",
        "export_hint": "Yukarıdaki “Kelime Türleri” pillerinden sadece istediklerini seçebilirsin (ör. yalnız fiil). “Türlere ayır” seçilirse seçtiğin her tür ayrı bir CSV olur.",

        "exclude_card_title": "Özel hariç listesi (opsiyonel)",
        "exclude_hint": "Her satırda bir lemma içeren .txt dosyası",
        "exclude_pick": "Dosya seç",
        "exclude_clear": "Temizle",
        "exclude_none": "Seçili değil",

        "advanced_show": "Gelişmiş ayarları göster",
        "advanced_hide": "Gelişmiş ayarları gizle",
    },

    "ru": {
        "app_title": "Русский Словарь Студия",
        "app_subtitle": "Извлеките русские слова из PDF и экспортируйте в CSV.",
        "language": "Язык",

        "status_ready": "Готово",
        "status_working": "Обработка…",
        "status_ocr_init": "Загрузка OCR‑моделей (первый раз ~200 МБ)…",
        "status_ocr_running": "OCR обрабатывает…",
        "status_ocr_page": "OCR — стр. {pos}",
        "status_searchable_pdf": "Создаём PDF с текстовым слоем…",
        "msg_searchable_pdf_done": "PDF с поиском: {path}",
        "status_done": "Завершено",
        "status_error": "Ошибка",

        "pdf_card_title": "PDF",
        "pdf_drop_hint": "Перетащите PDF сюда или нажмите для выбора",
        "pdf_change": "Изменить",
        "pdf_browse": "Выбрать PDF",
        "pdf_no_file": "PDF ещё не выбран",
        "pdf_pages_label": "{n} страниц",

        "pages_card_title": "Диапазон страниц",
        "pages_start": "С",
        "pages_end": "По",
        "pages_all": "Все страницы",

        "pos_card_title": "Части речи",
        "pos_noun": "Существительное",
        "pos_verb": "Глагол",
        "pos_adj": "Прилагательное",
        "pos_adv": "Наречие",
        "pos_other": "Другое",

        "filters_card_title": "Фильтры",
        "filter_remove_proper": "Убрать имена собственные",
        "filter_remove_basic": "Убрать базовые слова",
        "filter_min_length": "Мин. длина",
        "filter_min_freq": "Мин. частота",
        "filters_hint": "Включай только слова длиной от N букв и встречающиеся в PDF не реже N раз. Напр. «мин. частота = 5» → возьмёт от 5 и более.",

        "output_card_title": "Экспорт",
        "output_path": "Путь сохранения",
        "output_choose": "Выбрать",
        "output_open_folder": "Открыть папку",
        "output_include_freq": "Включить частоту",
        "output_include_pos": "Включить часть речи",
        "output_sort": "Сортировка",
        "sort_freq": "По частоте (убыв.)",
        "sort_alpha": "По алфавиту",

        "reading_card_title": "Режим чтения",
        "reading_auto": "Авто",
        "reading_text": "Только текст",
        "reading_ocr": "OCR (сканы)",

        "action_extract": "Извлечь слова",
        "action_extracting": "Извлечение…",
        "action_cancel": "Отмена",

        "msg_select_pdf": "Сначала выберите PDF.",
        "msg_done": "Извлечено {n} слов → {path}",
        "msg_error": "Произошла ошибка: {err}",
        "msg_no_words": "Из этого PDF не удалось извлечь слова.",
        "msg_pymorphy_missing": "Нужен 'pymorphy3'. Установите: pip install pymorphy3",
        "msg_pymupdf_missing": "Нужен 'pymupdf'. Установите: pip install pymupdf",
        "msg_custom_exclude_missing": "Файл исключений не найден: {path}",
        "msg_cancelled": "Отменено.",
        "msg_csv_locked": "Похоже, CSV‑файл открыт в другой программе (скорее всего, в Excel). Закройте файл или выберите другой путь сохранения и попробуйте снова.\n\nФайл: {path}",
        "msg_csv_perm_denied": "Нет прав на запись в это место. Выберите другой путь сохранения.\n\nФайл: {path}",
        "msg_csv_write_failed": "Не удалось записать CSV: {err}\n\nФайл: {path}",

        "dlg_pdf_title": "Выбрать PDF",
        "dlg_csv_title": "Куда сохранить CSV?",
        "dlg_pdf_filter": "PDF файлы (*.pdf)",
        "dlg_csv_filter": "CSV файлы (*.csv)",
        "dlg_exclude_title": "Файл исключений (.txt)",
        "dlg_txt_filter": "Текстовые файлы (*.txt)",

        "export_mode": "Режим экспорта",
        "export_single": "Один CSV",
        "export_separate": "По частям речи (каждая в своём файле)",
        "export_both": "Оба",
        "export_hint": "Над этой картой включи только нужные «Части речи» (например, только глаголы). При выборе «По частям речи» каждая включённая часть сохранится в отдельный CSV.",

        "exclude_card_title": "Свой список исключений (необязательно)",
        "exclude_hint": "Файл .txt — по одной лемме на строку",
        "exclude_pick": "Выбрать файл",
        "exclude_clear": "Очистить",
        "exclude_none": "Не выбрано",

        "advanced_show": "Показать расширенные настройки",
        "advanced_hide": "Скрыть расширенные настройки",
    },

    "en": {
        "app_title": "Russian Vocab Studio",
        "app_subtitle": "Extract Russian words from a PDF and export a clean CSV.",
        "language": "Language",

        "status_ready": "Ready",
        "status_working": "Working…",
        "status_ocr_init": "Loading OCR models (~200 MB on first run)…",
        "status_ocr_running": "Running OCR…",
        "status_ocr_page": "OCR — page {pos}",
        "status_searchable_pdf": "Building searchable PDF…",
        "msg_searchable_pdf_done": "Searchable PDF: {path}",
        "status_done": "Done",
        "status_error": "Error",

        "pdf_card_title": "PDF",
        "pdf_drop_hint": "Drop a PDF here or click to browse",
        "pdf_change": "Change",
        "pdf_browse": "Browse PDF",
        "pdf_no_file": "No PDF selected yet",
        "pdf_pages_label": "{n} pages",

        "pages_card_title": "Page Range",
        "pages_start": "From",
        "pages_end": "To",
        "pages_all": "All pages",

        "pos_card_title": "Parts of Speech",
        "pos_noun": "Nouns",
        "pos_verb": "Verbs",
        "pos_adj": "Adjectives",
        "pos_adv": "Adverbs",
        "pos_other": "Other",

        "filters_card_title": "Filters",
        "filter_remove_proper": "Remove proper nouns",
        "filter_remove_basic": "Remove basic words",
        "filter_min_length": "Min. length",
        "filter_min_freq": "Min. frequency",
        "filters_hint": "Keep only words at least N letters long and appearing at least N times in the PDF. E.g. “min. frequency = 5” → 5 or more occurrences.",

        "output_card_title": "Export",
        "output_path": "Save to",
        "output_choose": "Choose",
        "output_open_folder": "Open folder",
        "output_include_freq": "Include frequency",
        "output_include_pos": "Include part of speech",
        "output_sort": "Sort",
        "sort_freq": "Frequency (desc)",
        "sort_alpha": "Alphabetical",

        "reading_card_title": "Reading mode",
        "reading_auto": "Auto",
        "reading_text": "Text only",
        "reading_ocr": "OCR (scanned)",

        "action_extract": "Extract Vocabulary",
        "action_extracting": "Extracting…",
        "action_cancel": "Cancel",

        "msg_select_pdf": "Please pick a PDF first.",
        "msg_done": "Extracted {n} words → {path}",
        "msg_error": "Something went wrong: {err}",
        "msg_no_words": "No words could be extracted from this PDF.",
        "msg_pymorphy_missing": "'pymorphy3' is required. Install it with: pip install pymorphy3",
        "msg_pymupdf_missing": "'pymupdf' is required. Install it with: pip install pymupdf",
        "msg_custom_exclude_missing": "Custom exclude file not found: {path}",
        "msg_cancelled": "Extraction cancelled.",
        "msg_csv_locked": "The CSV file appears to be open in another program (most likely Excel). Please close it or pick a different save path and try again.\n\nFile: {path}",
        "msg_csv_perm_denied": "No permission to write to that location. Please pick a different save path.\n\nFile: {path}",
        "msg_csv_write_failed": "Could not write CSV: {err}\n\nFile: {path}",

        "dlg_pdf_title": "Select a PDF",
        "dlg_csv_title": "Save CSV as…",
        "dlg_pdf_filter": "PDF files (*.pdf)",
        "dlg_csv_filter": "CSV files (*.csv)",
        "dlg_exclude_title": "Words to exclude (.txt)",
        "dlg_txt_filter": "Text files (*.txt)",

        "export_mode": "Export mode",
        "export_single": "Single CSV",
        "export_separate": "Split by POS (one file each)",
        "export_both": "Both",
        "export_hint": "Use the “Parts of Speech” pills above to keep only what you want (e.g. verbs only). With “Split by POS”, each enabled part of speech is written to its own CSV.",

        "exclude_card_title": "Custom exclude list (optional)",
        "exclude_hint": "A .txt file with one lemma per line",
        "exclude_pick": "Pick file",
        "exclude_clear": "Clear",
        "exclude_none": "None selected",

        "advanced_show": "Show advanced settings",
        "advanced_hide": "Hide advanced settings",
    },
}

LANGUAGES = [
    ("tr", "Türkçe"),
    ("ru", "Русский"),
    ("en", "English"),
]


class I18n:
    """Tiny helper. Falls back to English, then to the key itself."""

    def __init__(self, lang: str = "tr"):
        self.lang = lang if lang in TRANSLATIONS else "tr"

    def set(self, lang: str) -> None:
        if lang in TRANSLATIONS:
            self.lang = lang

    def t(self, key: str, **kwargs) -> str:
        bundle = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])
        text = bundle.get(key) or TRANSLATIONS["en"].get(key) or key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text
