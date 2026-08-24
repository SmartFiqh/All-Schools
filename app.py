# -*- coding: utf-8 -*-
# app.py
#
# A simple, dependency-light Streamlit app. Only the "streamlit" package
# (and the Python standard library) is required, which makes it easy to
# fork on GitHub and deploy directly on Streamlit Community Cloud with
# no API keys or extra configuration.
import streamlit as st
import re
import sqlite3
import json
import csv
import io
from typing import List, Dict
from dataclasses import dataclass

DB_PATH = "fiqh.db"

# ============================================
# Arabic Text Normalization (for better local matching)
# ============================================

_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED\u0640]')
_AR_PUNCT = re.compile(r'[\u060C\u061B\u061F\u066A-\u066D،؛؟!.,:;"\'()\[\]{}؟]')

def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for more forgiving search matching:
    strips diacritics/tatweel, unifies alef/yeh/teh-marbuta forms,
    collapses punctuation and extra whitespace."""
    if not text:
        return ""
    t = text.strip()
    t = _AR_DIACRITICS.sub('', t)
    t = re.sub(r'[إأآٱ]', 'ا', t)
    t = t.replace('ى', 'ي')
    t = t.replace('ة', 'ه')
    t = t.replace('ؤ', 'و')
    t = t.replace('ئ', 'ي')
    t = _AR_PUNCT.sub(' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()

# ============================================

# Data Classes for Type Safety
# ============================================

@dataclass
class Issue:
    """Represents a fiqh issue with multilingual content."""
    id: int
    topic: str
    title: str
    keywords: List[str]
    rulings: Dict[str, str]
    rulings_by_madhab: Dict[str, Dict[str, str]]
    
    def get_ruling(self, level: str = "full") -> str:
        return self.rulings.get(level, self.rulings.get("full", ""))


@dataclass
class SearchResult:
    """Represents a search result with madhab cards."""
    title: str
    topic: str
    cards: List[Dict[str, str]]

# ============================================
# Database Layer
# ============================================

class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._seed_initial_issues()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        with self._get_connection() as conn:
            c = conn.cursor()
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    title_ar TEXT, title_en TEXT, title_fr TEXT, 
                    title_fa TEXT, title_ms TEXT, title_ur TEXT,
                    keywords_ar TEXT, keywords_en TEXT, keywords_fr TEXT, 
                    keywords_fa TEXT, keywords_ms TEXT, keywords_ur TEXT,
                    ruling_vs_ar TEXT, ruling_s_ar TEXT, ruling_f_ar TEXT,
                    ruling_vs_en TEXT, ruling_s_en TEXT, ruling_f_en TEXT,
                    ruling_vs_fr TEXT, ruling_s_fr TEXT, ruling_f_fr TEXT,
                    ruling_vs_fa TEXT, ruling_s_fa TEXT, ruling_f_fa TEXT,
                    ruling_vs_ms TEXT, ruling_s_ms TEXT, ruling_f_ms TEXT,
                    ruling_vs_ur TEXT, ruling_s_ur TEXT, ruling_f_ur TEXT,
                    rulings_by_madhab_ar JSON, rulings_by_madhab_en JSON, 
                    rulings_by_madhab_fr JSON, rulings_by_madhab_fa JSON, 
                    rulings_by_madhab_ms JSON, rulings_by_madhab_ur JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_topic ON issues(topic)')
            
            conn.commit()
    
    def _seed_initial_issues(self) -> None:
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM issues")
            if c.fetchone()[0] > 0:
                return
            
            issues = self._get_seed_data()
            for issue in issues:
                placeholders = ','.join(['?' for _ in issue])
                columns = ','.join(issue.keys())
                c.execute(f"INSERT INTO issues ({columns}) VALUES ({placeholders})", list(issue.values()))
            
            conn.commit()
    
    def _get_seed_data(self) -> List[Dict]:
        return [{
            "topic": "ibadat",
            "title_ar": "صلاة الجماعة",
            "title_en": "Congregational Prayer",
            "title_fr": "La prière en congrégation",
            "title_fa": "نماز جماعت",
            "title_ms": "Solat Berjemaah",
            "title_ur": "نماز باجماعت",
            "keywords_ar": "جماعة,مسجد,رجال,صلاة,فرض,سنة,واجب",
            "keywords_en": "congregation,mosque,men,prayer,obligatory,sunnah",
            "keywords_fr": "congrégation,mosquée,hommes,prière,obligatoire,sunna",
            "keywords_fa": "جماعت,مسجد,مردان,نماز,فرض,سنت,واجب",
            "keywords_ms": "jemaah,masjid,lelaki,solat,fardu,sunnah,wajib",
            "keywords_ur": "جماعت,مسجد,مرد,نماز,فرض,سنت,واجب",
            "ruling_vs_ar": "سنة مؤكدة",
            "ruling_s_ar": "سنة مؤكدة عند الجمهور، واجبة عند الحنفية",
            "ruling_f_ar": "تجب صلاة الجماعة في المسجد على الرجال عند جمهور الفقهاء؛ فهي فرض عين عند الحنابلة، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة تأكيداً عند الجعفرية في زمن الغيبة.",
            "ruling_vs_en": "Emphasized Sunnah",
            "ruling_s_en": "Emphasized sunnah for most jurists, obligatory for the Hanafis",
            "ruling_f_en": "Congregational prayer in the mosque is required of men according to the majority of jurists.",
            "ruling_vs_fr": "Sunna fortement recommandée",
            "ruling_s_fr": "Sunna fortement recommandée pour la majorité, obligatoire pour les hanafites",
            "ruling_f_fr": "La prière en congrégation à la mosquée est requise des hommes selon la majorité des juristes.",
            "ruling_vs_fa": "سنت مؤکد",
            "ruling_s_fa": "سنت مؤکد نزد جمهور، واجب نزد حنفیان",
            "ruling_f_fa": "نماز جماعت در مسجد بر مردان واجب است به اتفاق جمهور فقها.",
            "ruling_vs_ms": "Sunnah muakkadah",
            "ruling_s_ms": "Sunnah muakkadah bagi majoriti, wajib bagi Hanafi",
            "ruling_f_ms": "Solat berjemaah di masjid diwajibkan ke atas lelaki menurut majoriti ulama.",
            "ruling_vs_ur": "سنت مؤکدہ",
            "ruling_s_ur": "سنت مؤکدہ نزد جمہور، واجب نزد احناف",
            "ruling_f_ur": "مسجد میں نماز باجماعت مردوں پر جمہور فقہاء کے نزدیک واجب ہے.",
            "rulings_by_madhab_ar": json.dumps({
                "maliki": {"very_short": "فرض كفاية", "short": "فرض كفاية على أهل الحي، سنة مؤكدة للفرد", "full": "فرض كفاية على أهل الحي؛ وفي حق الفرد الواحد سنة مؤكدة لا يُكره تركها إلا لمن واظب عليه."},
                "shafii": {"very_short": "سنة مؤكدة", "short": "فرض كفاية على المجتمع، سنة مؤكدة للفرد", "full": "فرض كفاية على المجتمع ككل، وسنة مؤكدة في حق الفرد؛ وهو الأصح في المذهب."},
                "hanafi": {"very_short": "واجب", "short": "واجبة على كل رجل حر بالغ عاقل", "full": "واجبة وجوباً غير ملزم على كل رجل حر بالغ عاقل قادر؛ وتركها بلا عذر مكروه تحريماً عند المتأخرين."},
                "hanbali": {"very_short": "فرض عين", "short": "فرض عين على كل رجل قادر", "full": "فرض عين على كل رجل مكلف قادر؛ لا يجوز تركها إلا لعذر شرعي معتبر."},
                "zahiri": {"very_short": "فرض عين", "short": "فرض عين؛ ظاهر الأمر النبوي يقتضي الوجوب", "full": "فرض عين أخذاً بظاهر الأمر النبوي بالمحافظة عليها، دون تأويل يصرفه عن الوجوب."},
                "jafari": {"very_short": "مستحب مؤكد", "short": "مستحبة استحباباً مؤكداً في زمن الغيبة", "full": "مستحبة استحباباً مؤكداً وليست واجبة عيناً في زمن الغيبة الكبرى، وثوابها عظيم."},
                "zaidi": {"very_short": "فرض كفاية", "short": "قريب من رأي أهل السنة في تأكيدها", "full": "فرض كفاية، ويقترب الرأي الزيدي من الرأي السني في التأكيد على المحافظة عليها جماعة."},
                "ibadi": {"very_short": "سنة مؤكدة", "short": "من أعلام الدين ولا تُترك باستمرار", "full": "من أعلام الدين الظاهرة، سنة مؤكدة لا ينبغي تركها باستمرار وإن لم تكن شرطاً لصحة الصلاة."}
            }),
            "rulings_by_madhab_en": "{}",
            "rulings_by_madhab_fr": "{}",
            "rulings_by_madhab_fa": "{}",
            "rulings_by_madhab_ms": "{}",
            "rulings_by_madhab_ur": "{}"
        }]
    
    def load_issues(self, lang: str, topic_filter: str = "all") -> List[Issue]:
        with self._get_connection() as conn:
            c = conn.cursor()
            
            query = f'''
                SELECT id, topic, title_{lang}, keywords_{lang},
                       ruling_vs_{lang}, ruling_s_{lang}, ruling_f_{lang},
                       rulings_by_madhab_{lang}
                FROM issues
            '''
            params = ()
            if topic_filter != "all":
                query += " WHERE topic = ?"
                params = (topic_filter,)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            issues = []
            for row in rows:
                kw = row[f'keywords_{lang}'].split(',') if row[f'keywords_{lang}'] else []
                issues.append(Issue(
                    id=row['id'],
                    topic=row['topic'],
                    title=row[f'title_{lang}'],
                    keywords=[k.strip() for k in kw if k.strip()],
                    rulings={
                        "very_short": row[f'ruling_vs_{lang}'],
                        "short": row[f'ruling_s_{lang}'],
                        "full": row[f'ruling_f_{lang}']
                    },
                    rulings_by_madhab=json.loads(row[f'rulings_by_madhab_{lang}']) if row[f'rulings_by_madhab_{lang}'] else {}
                ))
            return issues
    
    def import_from_csv(self, csv_content: bytes) -> int:
        with self._get_connection() as conn:
            c = conn.cursor()
            reader = csv.DictReader(io.StringIO(csv_content.decode('utf-8')))
            count = 0
            
            for row in reader:
                c.execute('''
                    INSERT INTO issues (
                        topic, title_ar, title_en, title_fr, title_fa, title_ms, title_ur,
                        keywords_ar, keywords_en, keywords_fr, keywords_fa, keywords_ms, keywords_ur,
                        ruling_vs_ar, ruling_s_ar, ruling_f_ar,
                        ruling_vs_en, ruling_s_en, ruling_f_en,
                        ruling_vs_fr, ruling_s_fr, ruling_f_fr,
                        ruling_vs_fa, ruling_s_fa, ruling_f_fa,
                        ruling_vs_ms, ruling_s_ms, ruling_f_ms,
                        ruling_vs_ur, ruling_s_ur, ruling_f_ur,
                        rulings_by_madhab_ar, rulings_by_madhab_en, rulings_by_madhab_fr,
                        rulings_by_madhab_fa, rulings_by_madhab_ms, rulings_by_madhab_ur
                    ) VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?)
                ''', (
                    row.get("topic", "other"),
                    row.get("title_ar", ""), row.get("title_en", ""), row.get("title_fr", ""),
                    row.get("title_fa", ""), row.get("title_ms", ""), row.get("title_ur", ""),
                    row.get("keywords_ar", ""), row.get("keywords_en", ""), row.get("keywords_fr", ""),
                    row.get("keywords_fa", ""), row.get("keywords_ms", ""), row.get("keywords_ur", ""),
                    row.get("ruling_vs_ar", ""), row.get("ruling_s_ar", ""), row.get("ruling_f_ar", ""),
                    row.get("ruling_vs_en", ""), row.get("ruling_s_en", ""), row.get("ruling_f_en", ""),
                    row.get("ruling_vs_fr", ""), row.get("ruling_s_fr", ""), row.get("ruling_f_fr", ""),
                    row.get("ruling_vs_fa", ""), row.get("ruling_s_fa", ""), row.get("ruling_f_fa", ""),
                    row.get("ruling_vs_ms", ""), row.get("ruling_s_ms", ""), row.get("ruling_f_ms", ""),
                    row.get("ruling_vs_ur", ""), row.get("ruling_s_ur", ""), row.get("ruling_f_ur", ""),
                    row.get("rulings_by_madhab_ar", "{}"), row.get("rulings_by_madhab_en", "{}"),
                    row.get("rulings_by_madhab_fr", "{}"), row.get("rulings_by_madhab_fa", "{}"),
                    row.get("rulings_by_madhab_ms", "{}"), row.get("rulings_by_madhab_ur", "{}")
                ))
                count += 1
            
            conn.commit()
            return count

# ============================================
# Search Service
# ============================================

class SearchService:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._cache = {}
    
    def search(self, query: str, topic_filter: str, madhabs: List[str], 
               level: str, lang: str, T: Dict) -> List[SearchResult]:
        if not query:
            return []
        
        cache_key = f"{query}|{topic_filter}|{','.join(madhabs)}|{level}|{lang}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        all_issues = self.db.load_issues(lang, topic_filter)
        if not all_issues:
            return []
        
        q = query.strip().lower()
        
        # Normalized, scored local search: tolerant of diacritics and
        # alef/teh-marbuta spelling variants, and gives full-phrase matches
        # a higher score than partial keyword overlap.
        norm_q_terms = {t for t in normalize_arabic(q).split() if len(t) > 1}
        norm_query_full = normalize_arabic(q)
        
        scored = []
        for issue in all_issues:
            pool_raw = (issue.title + " " + " ".join(issue.keywords) + " " + issue.rulings["full"])
            pool_norm = normalize_arabic(pool_raw)
            
            score = 0
            if norm_query_full and norm_query_full in pool_norm:
                score += 5
            for term in norm_q_terms:
                if term in pool_norm:
                    score += 1
            
            if score > 0:
                scored.append((score, issue))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [issue for _, issue in scored]
        
        final_results = []
        for issue in results:
            cards = []
            per_madhab = issue.rulings_by_madhab
            if per_madhab:
                for m in madhabs:
                    data = per_madhab.get(m)
                    if data:
                        cards.append({
                            "label": MADHHAB_NAMES[m][lang],
                            "answer": data.get(level, data.get("full", "")),
                            "note": T["note_madhab"].format(MADHHAB_NAMES[m][lang]),
                        })
            
            if not cards:
                cards.append({
                    "label": TOPICS[issue.topic][lang],
                    "answer": issue.rulings.get(level, issue.rulings.get("full", "")),
                    "note": T["note_general"],
                })
            
            final_results.append(SearchResult(
                title=issue.title,
                topic=TOPICS[issue.topic][lang],
                cards=cards
            ))
        
        self._cache[cache_key] = final_results
        return final_results

# ============================================
# Constants & Data
# ============================================

LANGS = {"العربية": "ar", "English": "en", "Français": "fr", 
         "فارسی": "fa", "Bahasa Melayu": "ms", "اردو": "ur"}

LANG_FLAGS = {"ar": "🇸🇦", "en": "🇬🇧", "fr": "🇫🇷", "fa": "🇮🇷", "ms": "🇲🇾", "ur": "🇵🇰"}

MADHHAB_NAMES = {
    "maliki": {"ar": "مالكي", "en": "Maliki", "fr": "Malikite", "fa": "مالکی", "ms": "Maliki", "ur": "مالکی"},
    "shafii": {"ar": "شافعي", "en": "Shafi'i", "fr": "Chaféite", "fa": "شافعی", "ms": "Syafie", "ur": "شافعی"},
    "hanafi": {"ar": "حنفي", "en": "Hanafi", "fr": "Hanafite", "fa": "حنفی", "ms": "Hanafi", "ur": "حنفی"},
    "hanbali": {"ar": "حنبلي", "en": "Hanbali", "fr": "Hanbalite", "fa": "حنبلی", "ms": "Hanbali", "ur": "حنبلی"},
    "zahiri": {"ar": "ظاهري", "en": "Zahiri", "fr": "Zahirite", "fa": "ظاهری", "ms": "Zahiri", "ur": "ظاہری"},
    "jafari": {"ar": "جعفري", "en": "Ja'fari", "fr": "Jaafarite", "fa": "جعفری", "ms": "Jaafari", "ur": "جعفری"},
    "zaidi": {"ar": "زيدي", "en": "Zaidi", "fr": "Zaydite", "fa": "زیدی", "ms": "Zaidi", "ur": "زیدی"},
    "ibadi": {"ar": "إباضي", "en": "Ibadi", "fr": "Ibadite", "fa": "اباضی", "ms": "Ibadi", "ur": "اباضی"},
}

GROUPS = {
    "sunni": {"ar": "مذاهب السنة", "en": "Sunni Schools", "fr": "Écoles sunnites", "fa": "مذاهب اهل سنت", 
              "ms": "Mazhab Sunni", "ur": "اہل سنت کے مذاہب", "members": ["maliki", "shafii", "hanafi", "hanbali", "zahiri"]},
    "shia": {"ar": "مذاهب الشيعة", "en": "Shia Schools", "fr": "Écoles chiites", "fa": "مذاهب شیعه", 
             "ms": "Mazhab Syiah", "ur": "شیعہ مذاہب", "members": ["jafari", "zaidi"]},
    "ibadi": {"ar": "المذهب الإباضي", "en": "Ibadi School", "fr": "École ibadite", "fa": "مذهب اباضی", 
              "ms": "Mazhab Ibadi", "ur": "اباضی مذہب", "members": ["ibadi"]},
}

TOPICS = {
    "ibadat": {"ar": "العبادات", "en": "Acts of Worship", "fr": "Actes d'adoration", 
               "fa": "عبادات", "ms": "Ibadat", "ur": "عبادات"},
    "muamalat": {"ar": "المعاملات", "en": "Transactions", "fr": "Transactions", 
                 "fa": "معاملات", "ms": "Muamalat", "ur": "معاملات"},
    "family": {"ar": "الأسرة", "en": "Family", "fr": "Famille", 
               "fa": "خانواده", "ms": "Keluarga", "ur": "خاندان"},
    "other": {"ar": "مواضيع أخرى", "en": "Other Topics", "fr": "Autres sujets", 
              "fa": "موضوعات دیگر", "ms": "Topik Lain", "ur": "دیگر موضوعات"},
}

LEVELS = {
    "very_short": {"ar": "مختصرة (كلمة)", "en": "Very short (one word)", "fr": "Très bref (un mot)", 
                   "fa": "بسیار مختصر (یک واژه)", "ms": "Sangat ringkas (satu perkataan)", "ur": "بہت مختصر (ایک لفظ)"},
    "short": {"ar": "مبسطة (سطر)", "en": "Short (one line)", "fr": "Bref (une ligne)", 
              "fa": "ساده (یک خط)", "ms": "Ringkas (satu baris)", "ur": "آسان (ایک سطر)"},
    "full": {"ar": "مفصل (أكثر من سطر)", "en": "Detailed (full)", "fr": "Détaillé (complet)", 
             "fa": "مفصل (چند خط)", "ms": "Terperinci (penuh)", "ur": "تفصیلی (مکمل)"},
}

# ============================================
# UI Translations
# ============================================

UI = {
    "ar": {
        "app_title": "الجامع المختصر لآراء المذاهب",
        "app_subtitle": "منصة لعرض ومقارنة آراء المذاهب الفقهية - للفهم والتبصر، وليست موقع إفتاء.",
        "lang_label": "اللغة",
        "s1_title": "١ - اختر المذهب",
        "group_q": "مذاهب السنة، أم مذاهب الشيعة، أم المذهب الإباضي؟",
        "multi_hint": "💡 يمكنك اختيار أكثر من مذهب لعرض إجاباتها جنباً إلى جنب للمقارنة.",
        "sub_select": "اختر مذهباً واحداً أو أكثر:",
        "s2_title": "٢ - اختر الموضوع",
        "topic_q": "اختر الموضوع الفقهي",
        "s3_title": "٣ - طريقة عرض الإجابة",
        "level_q": "اختر مستوى التفصيل",
        "s4_title": "٤ - اكتب سؤالك",
        "question_placeholder": "مثال: ما حكم صلاة الجماعة؟",
        "search_btn": "🔍 ابحث عن الإجابة",
        "s5_title": "٥ - الإجابة",
        "answer_placeholder": "ستظهر الإجابة هنا بعد كتابة السؤال والضغط على زر البحث.",
        "no_question_warning": "الرجاء كتابة سؤالك أولاً في الفقرة الرابعة.",
        "no_madhab_warning": "الرجاء اختيار مذهب واحد على الأقل.",
        "no_results_warning": "🔍 لم نجد مسألة بهذا الوصف ضمن الموضوع المختار. جرّب كلمات أو صياغة أخرى.",
        "signature": "هذا والله أعلم",
        "note_general": "رأي عام موحّد - لم يُفصّل بعد لكل مذهب",
        "note_madhab": "رأي المذهب {}",
        "expander_imams": "📜 الأئمة المؤسسون للمذاهب",
        "expander_countries": "🗺️ الدول الإسلامية والمذهب الرسمي السائد",
        "expander_glossary": "📚 مصطلحات فقهية رئيسية",
        "rules_title": "📘 القواعد والأصول الفقهية الرئيسية",
        "rules_definition": "التعريف",
        "rules_example": "مثال",
        "expander_comments": "💬 أضف تعليقك أو ملاحظتك",
        "rating_label": "قيّم فائدة الإجابة:",
        "comment_placeholder": "اكتب ملاحظتك هنا...",
        "comment_submit": "إرسال التعليق",
        "comment_success": "✅ تم إرسال تعليقك، شكراً لك.",
        "comment_warning": "⚠️ الرجاء كتابة تعليق قبل الإرسال.",
        "comments_title": "تعليقات هذه الجلسة:",
        "comments_note": "ملاحظة: هذه التعليقات محفوظة لجلستك الحالية فقط.",
        "birthplace": "مكان الميلاد",
        "founding_place": "مكان تأسيس المذهب",
        "scholars": "أشهر فقهاء المذهب",
        "official_madhab": "المذهب الرسمي",
        "population": "عدد السكان (تقريبي)",
        "badge_madhabs": "مذاهب",
        "badge_langs": "لغات",
        "badge_countries": "دولة",
    },
    "en": {
        "app_title": "The Concise Compendium of Madhhab Opinions",
        "app_subtitle": "A platform for presenting and comparing juristic (fiqh) opinions - for understanding, not for issuing formal rulings (fatwas).",
        "lang_label": "Language",
        "s1_title": "1 - Choose the Madhhab",
        "group_q": "Sunni schools, Shia schools, or the Ibadi school?",
        "multi_hint": "💡 You can select more than one school to compare their answers side by side.",
        "sub_select": "Choose one or more schools:",
        "s2_title": "2 - Choose the Topic",
        "topic_q": "Choose a fiqh topic",
        "s3_title": "3 - Answer Detail Level",
        "level_q": "Choose the level of detail",
        "s4_title": "4 - Type Your Question",
        "question_placeholder": "Example: What is the ruling on congregational prayer?",
        "search_btn": "🔍 Search for the Ruling",
        "s5_title": "5 - The Answer",
        "answer_placeholder": "The answer will appear here after you type a question and press search.",
        "no_question_warning": "Please type your question first in section 4.",
        "no_madhab_warning": "Please select at least one school.",
        "no_results_warning": "🔍 No matching issue was found. Try different keywords or wording.",
        "signature": "And God knows best",
        "note_general": "A general, unified opinion - not yet detailed per school",
        "note_madhab": "Opinion of the {} school",
        "expander_imams": "📜 The Founding Imams of the Schools",
        "expander_countries": "🗺️ Muslim-Majority Countries & Their Prevailing Official School",
        "expander_glossary": "📚 Key Juristic Terms",
        "rules_title": "📘 Key Jurisprudential Rules and Principles",
        "rules_definition": "Definition",
        "rules_example": "Example",
        "expander_comments": "💬 Add Your Comment or Note",
        "rating_label": "Rate how helpful this answer was:",
        "comment_placeholder": "Write your note here...",
        "comment_submit": "Submit Comment",
        "comment_success": "✅ Your comment has been submitted, thank you.",
        "comment_warning": "⚠️ Please write a comment before submitting.",
        "comments_title": "Comments in this session:",
        "comments_note": "Note: these comments are saved for your current session only.",
        "birthplace": "Birthplace",
        "founding_place": "Where the school was founded",
        "scholars": "Prominent scholars of the school",
        "official_madhab": "Official school",
        "population": "Population (approx.)",
        "badge_madhabs": "Schools",
        "badge_langs": "Languages",
        "badge_countries": "Countries",
    },
    "fr": {
        "app_title": "Le Recueil Concis des Avis des Écoles Juridiques",
        "app_subtitle": "Une plateforme pour présenter et comparer les avis juridiques (fiqh) - pour la compréhension, non pour émettre des fatwas.",
        "lang_label": "Langue",
        "s1_title": "1 - Choisir l'école juridique",
        "group_q": "Écoles sunnites, écoles chiites, ou école ibadite ?",
        "multi_hint": "💡 Vous pouvez sélectionner plusieurs écoles pour comparer leurs réponses côte à côte.",
        "sub_select": "Choisissez une ou plusieurs écoles :",
        "s2_title": "2 - Choisir le sujet",
        "topic_q": "Choisissez un sujet de fiqh",
        "s3_title": "3 - Niveau de détail de la réponse",
        "level_q": "Choisissez le niveau de détail",
        "s4_title": "4 - Écrivez votre question",
        "question_placeholder": "Exemple : Quel est le statut de la prière en congrégation ?",
        "search_btn": "🔍 Rechercher la réponse",
        "s5_title": "5 - La réponse",
        "answer_placeholder": "La réponse apparaîtra ici après avoir écrit une question et appuyé sur rechercher.",
        "no_question_warning": "Veuillez d'abord écrire votre question à la section 4.",
        "no_madhab_warning": "Veuillez sélectionner au moins une école.",
        "no_results_warning": "🔍 Aucune question correspondante trouvée. Essayez d'autres mots-clés ou une autre formulation.",
        "signature": "Et Dieu est plus savant",
        "note_general": "Avis général unifié - pas encore détaillé par école",
        "note_madhab": "Avis de l'école {}",
        "expander_imams": "📜 Les Imams Fondateurs des Écoles",
        "expander_countries": "🗺️ Pays à Majorité Musulmane et Leur École Officielle Dominante",
        "expander_glossary": "📚 Termes Juridiques Clés",
        "rules_title": "📘 Règles et principes juridiques clés",
        "rules_definition": "Définition",
        "rules_example": "Exemple",
        "expander_comments": "💬 Ajoutez Votre Commentaire ou Remarque",
        "rating_label": "Évaluez l'utilité de cette réponse :",
        "comment_placeholder": "Écrivez votre remarque ici...",
        "comment_submit": "Envoyer le commentaire",
        "comment_success": "✅ Votre commentaire a été envoyé, merci.",
        "comment_warning": "⚠️ Veuillez écrire un commentaire avant d'envoyer.",
        "comments_title": "Commentaires de cette session :",
        "comments_note": "Remarque : ces commentaires ne sont conservés que pour votre session actuelle.",
        "birthplace": "Lieu de naissance",
        "founding_place": "Lieu de fondation de l'école",
        "scholars": "Savants marquants de l'école",
        "official_madhab": "École officielle",
        "population": "Population (approx.)",
        "badge_madhabs": "Écoles",
        "badge_langs": "Langues",
        "badge_countries": "Pays",
    },
    "fa": {
        "app_title": "جامع مختصر آراء مذاهب",
        "app_subtitle": "پلتفرمی برای نمایش و مقایسه آراء فقهی مذاهب - برای فهم و بصیرت، نه صدور فتوا.",
        "lang_label": "زبان",
        "s1_title": "۱ - انتخاب مذهب",
        "group_q": "مذاهب اهل سنت، مذاهب شیعه، یا مذهب اباضی؟",
        "multi_hint": "💡 می‌توانید بیش از یک مذهب را برای مقایسه پاسخ‌ها انتخاب کنید.",
        "sub_select": "یک یا چند مذهب را انتخاب کنید:",
        "s2_title": "۲ - انتخاب موضوع",
        "topic_q": "موضوع فقهی را انتخاب کنید",
        "s3_title": "۳ - سطح نمایش پاسخ",
        "level_q": "سطح جزئیات را انتخاب کنید",
        "s4_title": "۴ - سوال خود را بنویسید",
        "question_placeholder": "مثال: حکم نماز جماعت چیست؟",
        "search_btn": "🔍 جستجوی پاسخ",
        "s5_title": "۵ - پاسخ",
        "answer_placeholder": "پاسخ پس از نوشتن سوال و کلیک روی جستجو نمایش داده می‌شود.",
        "no_question_warning": "لطفاً ابتدا سوال خود را در بخش ۴ بنویسید.",
        "no_madhab_warning": "لطفاً حداقل یک مذهب را انتخاب کنید.",
        "no_results_warning": "🔍 هیچ مسئله‌ای یافت نشد. کلمات یا عبارت دیگری را امتحان کنید.",
        "signature": "والله اعلم",
        "note_general": "نظر عمومی واحد - هنوز به‌تفکیک مذهب نیست",
        "note_madhab": "نظر مذهب {}",
        "expander_imams": "📜 ائمه مؤسس مذاهب",
        "expander_countries": "🗺️ کشورهای اسلامی و مذهب رسمی",
        "expander_glossary": "📚 اصطلاحات کلیدی فقهی",
        "rules_title": "📘 قواعد و اصول فقهی اصلی",
        "rules_definition": "تعریف",
        "rules_example": "مثال",
        "expander_comments": "💬 نظر یا پیشنهاد خود را اضافه کنید",
        "rating_label": "میزان مفید بودن پاسخ را ارزیابی کنید:",
        "comment_placeholder": "نظر خود را اینجا بنویسید...",
        "comment_submit": "ارسال نظر",
        "comment_success": "✅ نظر شما با موفقیت ارسال شد، سپاسگزاریم.",
        "comment_warning": "⚠️ لطفاً قبل از ارسال، نظر خود را بنویسید.",
        "comments_title": "نظرات این جلسه:",
        "comments_note": "توجه: این نظرات فقط برای جلسه فعلی ذخیره می‌شوند.",
        "birthplace": "محل تولد",
        "founding_place": "محل تأسیس مذهب",
        "scholars": "مشهورترین فقهای مذهب",
        "official_madhab": "مذهب رسمی",
        "population": "جمعیت (تقریبی)",
        "badge_madhabs": "مذهب",
        "badge_langs": "زبان",
        "badge_countries": "کشور",
    },
    "ms": {
        "app_title": "Himpunan Ringkas Pendapat Mazhab",
        "app_subtitle": "Platform untuk memaparkan dan membandingkan pendapat fiqh mazhab - untuk kefahaman dan wawasan, bukan laman fatwa.",
        "lang_label": "Bahasa",
        "s1_title": "1 - Pilih Mazhab",
        "group_q": "Mazhab Sunni, Syiah, atau Ibadi?",
        "multi_hint": "💡 Anda boleh memilih lebih daripada satu mazhab untuk membandingkan jawapan mereka.",
        "sub_select": "Pilih satu atau lebih mazhab:",
        "s2_title": "2 - Pilih Topik",
        "topic_q": "Pilih topik fiqh",
        "s3_title": "3 - Tahap Perincian Jawapan",
        "level_q": "Pilih tahap perincian",
        "s4_title": "4 - Taip Soalan Anda",
        "question_placeholder": "Contoh: Apakah hukum solat berjemaah?",
        "search_btn": "🔍 Cari Jawapan",
        "s5_title": "5 - Jawapan",
        "answer_placeholder": "Jawapan akan muncul di sini selepas anda menaip soalan dan menekan cari.",
        "no_question_warning": "Sila taip soalan anda terlebih dahulu di bahagian 4.",
        "no_madhab_warning": "Sila pilih sekurang-kurangnya satu mazhab.",
        "no_results_warning": "🔍 Tiada isu sepadan ditemui. Cuba kata kunci atau ungkapan lain.",
        "signature": "Dan Allah lebih mengetahui",
        "note_general": "Pendapat umum yang disatukan - belum diperincikan mengikut mazhab",
        "note_madhab": "Pendapat mazhab {}",
        "expander_imams": "📜 Imam Pengasas Mazhab",
        "expander_countries": "🗺️ Negara Islam & Mazhab Rasmi",
        "expander_glossary": "📚 Istilah Fiqh Utama",
        "rules_title": "📘 Peraturan dan Prinsip Fiqh Utama",
        "rules_definition": "Definisi",
        "rules_example": "Contoh",
        "expander_comments": "💬 Tambah Ulasan atau Nota Anda",
        "rating_label": "Nilaikan kemanfaatan jawapan ini:",
        "comment_placeholder": "Tulis ulasan anda di sini...",
        "comment_submit": "Hantar Ulasan",
        "comment_success": "✅ Ulasan anda telah dihantar, terima kasih.",
        "comment_warning": "⚠️ Sila tulis ulasan sebelum menghantar.",
        "comments_title": "Ulasan sesi ini:",
        "comments_note": "Nota: ulasan ini hanya disimpan untuk sesi semasa anda.",
        "birthplace": "Tempat lahir",
        "founding_place": "Tempat penubuhan mazhab",
        "scholars": "Ulama terkemuka mazhab",
        "official_madhab": "Mazhab rasmi",
        "population": "Penduduk (anggaran)",
        "badge_madhabs": "Mazhab",
        "badge_langs": "Bahasa",
        "badge_countries": "Negara",
    },
    "ur": {
        "app_title": "مذاہب کی آراء کا مختصر مجموعہ",
        "app_subtitle": "مذاہب فقہیہ کی آراء دکھانے اور موازنہ کرنے کا پلیٹ فارم - فہم و بصیرت کے لیے، فتویٰ جاری کرنے کے لیے نہیں۔",
        "lang_label": "زبان",
        "s1_title": "۱ - مذہب منتخب کریں",
        "group_q": "اہل سنت کے مذاہب، اہل تشیع کے مذاہب، یا اباضی مذہب؟",
        "multi_hint": "💡 آپ موازنہ کے لیے ایک سے زیادہ مذاہب منتخب کر سکتے ہیں۔",
        "sub_select": "ایک یا زیادہ مذاہب منتخب کریں:",
        "s2_title": "۲ - موضوع منتخب کریں",
        "topic_q": "فقہی موضوع منتخب کریں",
        "s3_title": "۳ - جواب کی تفصیل کی سطح",
        "level_q": "تفصیل کی سطح منتخب کریں",
        "s4_title": "۴ - اپنا سوال لکھیں",
        "question_placeholder": "مثال: نماز باجماعت کا کیا حکم ہے؟",
        "search_btn": "🔍 جواب تلاش کریں",
        "s5_title": "۵ - جواب",
        "answer_placeholder": "جواب یہاں ظاہر ہوگا جب آپ سوال لکھیں گے اور تلاش پر کلک کریں گے۔",
        "no_question_warning": "براہ کرم پہلے حصہ ۴ میں اپنا سوال لکھیں۔",
        "no_madhab_warning": "براہ کرم کم از کم ایک مذہب منتخب کریں۔",
        "no_results_warning": "🔍 کوئی مسئلہ نہیں ملا۔ دوسرے الفاظ یا انداز میں لکھ کر آزمائیں۔",
        "signature": "واللہ اعلم",
        "note_general": "متفقہ عمومی رائے - ابھی تک مذہب کے لحاظ سے تفصیل نہیں دی گئی",
        "note_madhab": "مذہب {} کی رائے",
        "expander_imams": "📜 مذاہب کے بانی ائمہ",
        "expander_countries": "🗺️ اسلامی ممالک اور سرکاری مذہب",
        "expander_glossary": "📚 اہم فقہی اصطلاحات",
        "rules_title": "📘 اہم فقہی اصول و قواعد",
        "rules_definition": "تعریف",
        "rules_example": "مثال",
        "expander_comments": "💬 اپنا تبصرہ یا نوٹ شامل کریں",
        "rating_label": "اس جواب کی افادیت کی درجہ بندی کریں:",
        "comment_placeholder": "اپنا تبصرہ یہاں لکھیں...",
        "comment_submit": "تبصرہ جمع کریں",
        "comment_success": "✅ آپ کا تبصرہ موصول ہوگیا، شکریہ۔",
        "comment_warning": "⚠️ براہ کرم جمع کرنے سے پہلے تبصرہ لکھیں۔",
        "comments_title": "اس سیشن کے تبصرے:",
        "comments_note": "نوٹ: یہ تبصرے صرف آپ کے موجودہ سیشن کے لیے محفوظ ہیں۔",
        "birthplace": "جائے پیدائش",
        "founding_place": "مذہب کے قیام کی جگہ",
        "scholars": "مشہور فقہاء",
        "official_madhab": "سرکاری مذہب",
        "population": "آبادی (تقریباً)",
        "badge_madhabs": "مذاہب",
        "badge_langs": "زبانیں",
        "badge_countries": "ممالک",
    },
}

# ============================================
# Additional Data
# ============================================

GLOSSARY = [
    {"term": {"ar": "الحلال", "en": "Halal (Lawful)", "fr": "Halal (Licite)", "fa": "حلال", "ms": "Halal", "ur": "حلال"},
     "definition": {"ar": "ما أذن الشارع بفعله أو استعماله، سواء كان مندوباً أو واجباً أو مباحاً؛ وهو ضد الحرام.",
                    "en": "What the Lawgiver has permitted to be done or used, whether recommended, obligatory, or simply neutral; the opposite of haram.",
                    "fr": "Ce que le Législateur a autorisé, qu'il s'agisse d'un acte recommandé, obligatoire ou simplement neutre ; le contraire du haram.",
                    "fa": "آنچه شارع انجام یا استفاده آن را مجاز دانسته، خواه مستحب، واجب یا صرفاً مباح باشد؛ در برابر حرام.",
                    "ms": "Apa yang dibenarkan oleh Pembuat Syariat, sama ada digalakkan, wajib, atau sekadar harus; lawan bagi haram.",
                    "ur": "وہ چیز جسے شارع نے جائز قرار دیا، خواہ مستحب ہو، واجب ہو یا محض مباح؛ حرام کی ضد۔"},
     "example": {"ar": "البيع المباح، الطعام الحلال.",
                 "en": "A permissible sale; lawful food.",
                 "fr": "Une vente licite ; une nourriture halal.",
                 "fa": "خرید و فروش مباح، غذای حلال.",
                 "ms": "Jualan yang harus, makanan halal.",
                 "ur": "جائز بیع، حلال کھانا۔"}},
    {"term": {"ar": "المباح", "en": "Mubah (Neutral / Permissible)", "fr": "Mubah (Indifférent)", "fa": "مباح", "ms": "Mubah", "ur": "مباح"},
     "definition": {"ar": "فعل أو ترك استوى فيه الفعل والترك شرعاً، فلا ثواب في فعله ولا إثم في تركه.",
                    "en": "An act that is neither commanded nor forbidden - doing it and leaving it are equal, with no reward or sin attached.",
                    "fr": "Un acte ni commandé ni interdit - l'accomplir ou le délaisser sont équivalents, sans récompense ni péché.",
                    "fa": "کاری که نه امر شده و نه نهی شده؛ انجام و ترک آن یکسان است و نه پاداشی دارد نه گناهی.",
                    "ms": "Perbuatan yang tidak diperintah dan tidak dilarang - melakukan dan meninggalkannya adalah sama, tiada pahala atau dosa.",
                    "ur": "وہ کام جس کا نہ حکم دیا گیا نہ منع کیا گیا؛ کرنا اور چھوڑنا برابر ہے، نہ ثواب نہ گناہ۔"},
     "example": {"ar": "الأكل من الطيبات، اختيار لون الثوب.",
                 "en": "Eating wholesome food; choosing the color of one's clothing.",
                 "fr": "Manger des aliments licites ; choisir la couleur de son vêtement.",
                 "fa": "خوردن غذاهای پاکیزه، انتخاب رنگ لباس.",
                 "ms": "Makan makanan yang baik, memilih warna pakaian.",
                 "ur": "پاکیزہ کھانا کھانا، لباس کا رنگ چننا۔"}},
    {"term": {"ar": "الحرام", "en": "Haram (Forbidden)", "fr": "Haram (Interdit)", "fa": "حرام", "ms": "Haram", "ur": "حرام"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً جازماً؛ يُثاب تاركه امتثالاً ويُعاقب فاعله.",
                    "en": "What the Lawgiver has decisively commanded to be avoided; leaving it is rewarded and committing it is sinful.",
                    "fr": "Ce que le Législateur a interdit de façon décisive ; l'éviter est récompensé et le commettre est un péché.",
                    "fa": "آنچه شارع قطعاً از ترک آن خواسته؛ ترک آن پاداش دارد و انجام آن گناه است.",
                    "ms": "Apa yang dilarang secara tegas; meninggalkannya berpahala dan melakukannya berdosa.",
                    "ur": "جسے شارع نے قطعی طور پر چھوڑنے کا حکم دیا؛ چھوڑنے پر ثواب اور کرنے پر گناہ ہے۔"},
     "example": {"ar": "الربا، أكل لحم الخنزير.",
                 "en": "Usury (riba); eating pork.",
                 "fr": "L'usure (riba) ; consommer du porc.",
                 "fa": "ربا، خوردن گوشت خوک.",
                 "ms": "Riba, memakan daging babi.",
                 "ur": "سود، خنزیر کا گوشت کھانا۔"}},
    {"term": {"ar": "المكروه", "en": "Makruh (Disliked)", "fr": "Makruh (Réprouvé)", "fa": "مکروه", "ms": "Makruh", "ur": "مکروہ"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً غير جازم؛ يُثاب تاركه ولا يأثم فاعله.",
                    "en": "What the Lawgiver has asked to be avoided, but not decisively; leaving it is rewarded, yet committing it is not sinful.",
                    "fr": "Ce que le Législateur a demandé d'éviter, mais de façon non décisive ; l'éviter est récompensé, le commettre n'est pas un péché.",
                    "fa": "آنچه شارع ترک آن را خواسته اما نه به‌طور قطعی؛ ترک آن پاداش دارد و انجام آن گناه ندارد.",
                    "ms": "Apa yang diminta ditinggalkan tetapi tidak secara tegas; meninggalkannya berpahala, melakukannya tidak berdosa.",
                    "ur": "جسے شارع نے چھوڑنے کو کہا مگر قطعی طور پر نہیں؛ چھوڑنے پر ثواب اور کرنے پر گناہ نہیں۔"},
     "example": {"ar": "الأكل من ثوم نيء قبل الذهاب إلى المسجد، الإسراف في الماء عند الوضوء.",
                 "en": "Eating raw garlic before going to the mosque; excessive use of water in ablution.",
                 "fr": "Manger de l'ail cru avant d'aller à la mosquée ; le gaspillage d'eau lors des ablutions.",
                 "fa": "خوردن سیر خام پیش از رفتن به مسجد، اسراف در آب وضو.",
                 "ms": "Makan bawang putih mentah sebelum ke masjid, membazir air ketika wuduk.",
                 "ur": "مسجد جانے سے پہلے کچا لہسن کھانا، وضو میں پانی کا اسراف۔"}},
    {"term": {"ar": "الواجب", "en": "Wajib (Obligatory)", "fr": "Wajib (Obligatoire)", "fa": "واجب", "ms": "Wajib", "ur": "واجب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً؛ يأثم تاركه ويثاب فاعله، ويرادف الفرض عند جمهور الفقهاء.",
                    "en": "What the Lawgiver has decisively commanded to be done; leaving it is sinful and performing it is rewarded. Most jurists treat it as synonymous with Fard.",
                    "fr": "Ce que le Législateur a ordonné de façon décisive ; l'omettre est un péché, l'accomplir est récompensé. Assimilé au Fard par la majorité des juristes.",
                    "fa": "آنچه شارع قطعاً انجام آن را خواسته؛ ترک آن گناه و انجام آن پاداش دارد. نزد جمهور مرادف فرض است.",
                    "ms": "Apa yang diperintah secara tegas untuk dilakukan; meninggalkannya berdosa, melakukannya berpahala. Disamakan dengan Fardu oleh majoriti ulama.",
                    "ur": "جسے شارع نے قطعی طور پر کرنے کا حکم دیا؛ چھوڑنے پر گناہ اور کرنے پر ثواب ہے۔ جمہور کے نزدیک فرض کے مترادف۔"},
     "example": {"ar": "الصلوات الخمس، الزكاة.",
                 "en": "The five daily prayers; zakat.",
                 "fr": "Les cinq prières quotidiennes ; la zakat.",
                 "fa": "نمازهای پنج‌گانه، زکات.",
                 "ms": "Solat lima waktu, zakat.",
                 "ur": "پانچ وقت کی نمازیں، زکوٰۃ۔"}},
    {"term": {"ar": "الفرض", "en": "Fard (Compulsory)", "fr": "Fard (Obligation certaine)", "fa": "فرض", "ms": "Fardu", "ur": "فرض"},
     "definition": {"ar": "مرادف للواجب عند جمهور الفقهاء. أما عند الحنفية فهو ما ثبت بدليل قطعي الثبوت والدلالة كالقرآن والسنة المتواترة، وينكره كافر بخلاف الواجب الثابت بدليل ظني.",
                    "en": "Synonymous with Wajib for most jurists. The Hanafis distinguish it as what is established by a definitive text (Qur'an or mass-transmitted Sunnah), so denying it amounts to disbelief, unlike Wajib which rests on a probable proof.",
                    "fr": "Synonyme de Wajib pour la majorité des juristes. Les hanafites le distinguent comme ce qui repose sur une preuve définitive (Coran, Sunna mutawatir), dont le déni équivaut à la mécréance.",
                    "fa": "نزد جمهور مرادف واجب است. نزد حنفیان: آنچه با دلیل قطعی (قرآن یا سنت متواتر) ثابت شده و انکار آن کفر است.",
                    "ms": "Sinonim Wajib bagi majoriti ulama. Bagi Hanafi, ia dibezakan sebagai apa yang sabit dengan dalil qat'i (al-Quran atau Sunnah mutawatir).",
                    "ur": "جمہور کے نزدیک واجب کے مترادف۔ احناف کے نزدیک وہ جو دلیل قطعی سے ثابت ہو (قرآن یا سنت متواترہ)، اس کا انکار کفر ہے۔"},
     "example": {"ar": "فرضية الصلوات الخمس بالقرآن، فرضية الزكاة.",
                 "en": "The obligation of the five prayers, established by the Qur'an.",
                 "fr": "L'obligation des cinq prières, établie par le Coran.",
                 "fa": "وجوب نمازهای پنج‌گانه با قرآن.",
                 "ms": "Kewajipan solat lima waktu yang disabitkan al-Quran.",
                 "ur": "قرآن سے ثابت پانچ نمازوں کی فرضیت۔"}},
    {"term": {"ar": "فرض الكفاية", "en": "Fard Kifayah (Collective Obligation)", "fr": "Fard Kifaya (Obligation collective)", "fa": "فرض کفایه", "ms": "Fardu Kifayah", "ur": "فرض کفایہ"},
     "definition": {"ar": "تكليف يسقط الإثم عن جميع المكلفين إذا قام به من يكفي منهم، ويأثم الجميع إذا تركه الكل.",
                    "en": "A collective obligation - if enough people perform it, the sin is lifted from the rest; if all neglect it, all are sinful.",
                    "fr": "Obligation collective - si un nombre suffisant l'accomplit, les autres en sont dispensés ; si tous la délaissent, tous sont en faute.",
                    "fa": "تکلیفی که با انجام آن توسط برخی، از دیگران ساقط می‌شود؛ اگر همه ترک کنند همه گناهکارند.",
                    "ms": "Kewajipan kolektif - jika sebahagian melaksanakannya, yang lain terlepas; jika semua meninggalkannya, semua berdosa.",
                    "ur": "ایسا فرض جو بعض کے کرنے سے باقی سب سے ساقط ہو جائے؛ اگر سب چھوڑ دیں تو سب گنہگار ہوں۔"},
     "example": {"ar": "صلاة الجنازة، تعلم الطب والصناعات الضرورية للأمة.",
                 "en": "The funeral prayer; training enough doctors to meet the community's needs.",
                 "fr": "La prière funéraire ; former suffisamment de médecins pour les besoins de la communauté.",
                 "fa": "نماز جنازه، آموختن پزشکی به اندازه نیاز جامعه.",
                 "ms": "Solat jenazah, mempelajari perubatan untuk memenuhi keperluan masyarakat.",
                 "ur": "نماز جنازہ، معاشرے کی ضرورت پوری کرنے کے لیے طب کی تعلیم۔"}},
    {"term": {"ar": "المستحب", "en": "Mustahabb (Recommended)", "fr": "Moustahabb (Recommandé)", "fa": "مستحب", "ms": "Mustahab", "ur": "مستحب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً غير جازم؛ يثاب فاعله امتثالاً ولا يأثم تاركه، ويشمل عند كثير من الأصوليين السنة والمندوب والتطوع.",
                    "en": "What the Lawgiver has encouraged, though not decisively; performing it is rewarded and leaving it carries no sin. It broadly covers Sunnah, Mandub, and voluntary acts.",
                    "fr": "Ce que le Législateur a encouragé sans décision ferme ; l'accomplir est récompensé, le délaisser n'est pas un péché. Il englobe la Sunna, le Mandoub et les actes volontaires.",
                    "fa": "آنچه شارع بدون الزام قطعی تشویق کرده؛ انجام آن پاداش دارد و ترک آن گناه ندارد. شامل سنت، مندوب و تطوع می‌شود.",
                    "ms": "Apa yang digalakkan tanpa tuntutan tegas; melakukannya berpahala, meninggalkannya tidak berdosa. Merangkumi Sunnah, Mandub dan amalan sukarela.",
                    "ur": "جسے شارع نے بغیر قطعی تاکید کے پسند فرمایا؛ کرنے پر ثواب، چھوڑنے پر گناہ نہیں۔ اس میں سنت، مندوب اور نفل شامل ہیں۔"},
     "example": {"ar": "صلاة الوتر عند الجمهور، السواك.",
                 "en": "The witr prayer for most jurists; using the miswak.",
                 "fr": "La prière du witr pour la majorité ; l'usage du siwak.",
                 "fa": "نماز وتر نزد جمهور، مسواک زدن.",
                 "ms": "Solat witir menurut majoriti, bersiwak.",
                 "ur": "جمہور کے نزدیک وتر، مسواک کرنا۔"}},
    {"term": {"ar": "المندوب", "en": "Mandub (Encouraged)", "fr": "Mandoub (Encouragé)", "fa": "مندوب", "ms": "Mandub", "ur": "مندوب"},
     "definition": {"ar": "عند بعض الأصوليين مرادف للمستحب، وعند آخرين هو ما لم يواظب عليه النبي ﷺ مواظبة السنن الراتبة، فهو دون السنة في التأكيد.",
                    "en": "For some jurists synonymous with Mustahabb; for others, an act the Prophet ﷺ did not perform as consistently as the confirmed Sunnahs, so it ranks slightly below Sunnah.",
                    "fr": "Pour certains juristes, synonyme de Moustahabb ; pour d'autres, un acte que le Prophète ﷺ n'a pas accompli aussi régulièrement que les Sunnas confirmées.",
                    "fa": "نزد برخی مرادف مستحب؛ نزد برخی دیگر عملی که پیامبر ﷺ به اندازه سنت‌های مؤکد بر آن مداومت نکرده است.",
                    "ms": "Bagi sesetengah ulama sinonim Mustahab; bagi yang lain, amalan yang tidak dilakukan Nabi ﷺ seistiqamah Sunnah muakkad.",
                    "ur": "بعض کے نزدیک مستحب کا مترادف؛ بعض کے نزدیک وہ عمل جس پر نبی ﷺ نے سنن مؤکدہ جیسی مداومت نہیں فرمائی۔"},
     "example": {"ar": "صلاة الضحى، صيام الاثنين والخميس.",
                 "en": "The mid-morning (Duha) prayer; fasting on Mondays and Thursdays.",
                 "fr": "La prière de Doha ; le jeûne du lundi et jeudi.",
                 "fa": "نماز ضحی، روزه دوشنبه و پنجشنبه.",
                 "ms": "Solat Dhuha, puasa Isnin dan Khamis.",
                 "ur": "نماز چاشت، پیر اور جمعرات کا روزہ۔"}},
    {"term": {"ar": "السنة", "en": "Sunnah", "fr": "Sunna", "fa": "سنت", "ms": "Sunat", "ur": "سنت"},
     "definition": {"ar": "ما واظب النبي ﷺ على فعله دون إيجاب؛ يثاب فاعلها ولا يأثم تاركها، وتنقسم إلى سنة مؤكدة وسنة غير مؤكدة (زائدة).",
                    "en": "What the Prophet ﷺ regularly did without making it obligatory; performing it is rewarded and leaving it is not sinful. It divides into emphasized and non-emphasized Sunnah.",
                    "fr": "Ce que le Prophète ﷺ accomplissait régulièrement sans en faire une obligation ; récompensée si accomplie, non fautive si délaissée.",
                    "fa": "آنچه پیامبر ﷺ بدون الزام بر آن مداومت داشته؛ انجام آن پاداش دارد و ترک آن گناه ندارد.",
                    "ms": "Apa yang dilakukan Nabi ﷺ secara berterusan tanpa mewajibkannya; berpahala jika dilakukan, tidak berdosa jika ditinggalkan.",
                    "ur": "جس پر نبی ﷺ نے بغیر وجوب کے مداومت فرمائی؛ کرنے پر ثواب، چھوڑنے پر گناہ نہیں۔"},
     "example": {"ar": "السواك عند الوضوء، الأذكار بعد الصلاة.",
                 "en": "Using the miswak during ablution; remembrance (adhkar) after prayer.",
                 "fr": "Le siwak lors des ablutions ; les invocations après la prière.",
                 "fa": "مسواک هنگام وضو، اذکار پس از نماز.",
                 "ms": "Bersiwak ketika berwuduk, zikir selepas solat.",
                 "ur": "وضو کے وقت مسواک، نماز کے بعد اذکار۔"}},
    {"term": {"ar": "السنة المؤكدة", "en": "Emphasized Sunnah (Sunnah Mu'akkadah)", "fr": "Sunna confirmée (Mu'akkada)", "fa": "سنت مؤکد", "ms": "Sunat Muakkad", "ur": "سنت مؤکدہ"},
     "definition": {"ar": "ما واظب عليه النبي ﷺ مواظبة تامة ولم يتركه إلا نادراً لبيان الجواز؛ تركها بلا عذر إساءة وتفريط، وإن لم يأثم صاحبها إثم تارك الواجب.",
                    "en": "What the Prophet ﷺ maintained continuously, rarely leaving it and only to show it was not obligatory; abandoning it without excuse is blameworthy, though it does not carry the sin of abandoning a Wajib.",
                    "fr": "Ce que le Prophète ﷺ a maintenu de façon quasi continue ; la délaisser sans excuse est blâmable, bien que ce ne soit pas le péché d'un Wajib délaissé.",
                    "fa": "آنچه پیامبر ﷺ به‌طور کامل بر آن مداومت داشته و به‌ندرت ترک کرده؛ ترک بی‌عذر آن نکوهیده است، هرچند گناه ترک واجب را ندارد.",
                    "ms": "Apa yang dilakukan Nabi ﷺ secara konsisten dan jarang ditinggalkan; meninggalkannya tanpa keuzuran adalah tercela, walaupun bukan berdosa seperti Wajib.",
                    "ur": "جس پر نبی ﷺ نے مکمل مداومت فرمائی اور شاذ ہی چھوڑی؛ بلا عذر چھوڑنا ناپسندیدہ ہے، اگرچہ واجب چھوڑنے جیسا گناہ نہیں۔"},
     "example": {"ar": "ركعتا الفجر، الوتر عند الجمهور (واجب عند الحنفية).",
                 "en": "The two rak'ahs before Fajr; witr prayer (obligatory according to the Hanafis).",
                 "fr": "Les deux rak'ahs avant Fajr ; le witr (obligatoire chez les hanafites).",
                 "fa": "دو رکعت سنت فجر، وتر (نزد حنفیان واجب است).",
                 "ms": "Dua rakaat sebelum Subuh, witir (wajib bagi Hanafi).",
                 "ur": "فجر کی دو سنتیں، وتر (احناف کے نزدیک واجب)۔"}},
]

IMAMS = [
    {"name": {"ar": "الإمام مالك بن أنس الأصبحي", "en": "Imam Malik ibn Anas al-Asbahi", 
              "fr": "L'imam Malik ibn Anas al-Asbahi", "fa": "امام مالک بن انس اصبحی", 
              "ms": "Imam Malik bin Anas al-Asbahi", "ur": "امام مالک بن انس اصبحی"},
     "school": MADHHAB_NAMES["maliki"], "lifespan": "93 - 179 AH",
     "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
     "founding_place": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
     "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق",
                  "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq",
                  "fr": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq",
                  "fa": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق",
                  "ms": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil bin Ishaq",
                  "ur": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق"}},
    {"name": {"ar": "الإمام محمد بن إدريس الشافعي", "en": "Imam Muhammad ibn Idris al-Shafi'i", 
              "fr": "L'imam Muhammad ibn Idris al-Chafi'i", "fa": "امام محمد بن ادریس شافعی", 
              "ms": "Imam Muhammad bin Idris al-Syafie", "ur": "امام محمد بن ادریس شافعی"},
     "school": MADHHAB_NAMES["shafii"], "lifespan": "150 - 204 AH",
     "birthplace": {"ar": "غزة", "en": "Gaza", "fr": "Gaza", "fa": "غزه", "ms": "Gaza", "ur": "غزہ"},
     "founding_place": {"ar": "بغداد ثم مصر (المذهب الجديد)", "en": "Baghdad, then Egypt (the new doctrine)", 
                        "fr": "Bagdad, puis l'Égypte (la nouvelle doctrine)", "fa": "بغداد سپس مصر (مذهب جدید)", 
                        "ms": "Baghdad, kemudian Mesir (mazhab baru)", "ur": "بغداد پھر مصر (نیا مذہب)"},
     "scholars": {"ar": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي",
                  "en": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i",
                  "fr": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i",
                  "fa": "مزنی، بویطی، نووی، ابن حجر هیتمی، رافعی",
                  "ms": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i",
                  "ur": "مزنی، بویطی، نووی، ابن حجر ہیتمی، رافعی"}},
]

COUNTRIES = [
    {"flag": "🇸🇦", "name": {"ar": "السعودية", "en": "Saudi Arabia", "fr": "Arabie saoudite", "fa": "عربستان سعودی", "ms": "Arab Saudi", "ur": "سعودی عرب"}, "madhab": "hanbali", "population": "36.4M"},
    {"flag": "🇪🇬", "name": {"ar": "مصر", "en": "Egypt", "fr": "Égypte", "fa": "مصر", "ms": "Mesir", "ur": "مصر"}, "madhab": "shafii", "population": "112.7M"},
    {"flag": "🇲🇦", "name": {"ar": "المغرب", "en": "Morocco", "fr": "Maroc", "fa": "مراکش", "ms": "Maghribi", "ur": "مراکش"}, "madhab": "maliki", "population": "37.8M"},
    {"flag": "🇹🇷", "name": {"ar": "تركيا", "en": "Turkey", "fr": "Turquie", "fa": "ترکیه", "ms": "Turki", "ur": "ترکی"}, "madhab": "hanafi", "population": "87.5M"},
    {"flag": "🇮🇷", "name": {"ar": "إيران", "en": "Iran", "fr": "Iran", "fa": "ایران", "ms": "Iran", "ur": "ایران"}, "madhab": "jafari", "population": "89.8M"},
    {"flag": "🇴🇲", "name": {"ar": "عُمان", "en": "Oman", "fr": "Oman", "fa": "عمان", "ms": "Oman", "ur": "عمان"}, "madhab": "ibadi", "population": "4.7M"},
    {"flag": "🇸🇩", "name": {"ar": "السودان", "en": "Sudan", "fr": "Soudan", "fa": "سودان", "ms": "Sudan", "ur": "سوڈان"}, "madhab": "maliki", "population": "48.1M"},
    {"flag": "🇸🇾", "name": {"ar": "سوريا", "en": "Syria", "fr": "Syrie", "fa": "سوریه", "ms": "Syria", "ur": "شام"}, "madhab": "hanafi", "population": "23.2M"},
    {"flag": "🇮🇶", "name": {"ar": "العراق", "en": "Iraq", "fr": "Irak", "fa": "عراق", "ms": "Iraq", "ur": "عراق"}, "madhab": "jafari", "population": "44.5M"},
    {"flag": "🇦🇪", "name": {"ar": "الإمارات", "en": "United Arab Emirates", "fr": "Émirats arabes unis", "fa": "امارات متحده عربی", "ms": "Emiriah Arab Bersatu", "ur": "متحدہ عرب امارات"}, "madhab": "maliki", "population": "10.0M"},
    {"flag": "🇯🇴", "name": {"ar": "الأردن", "en": "Jordan", "fr": "Jordanie", "fa": "اردن", "ms": "Jordan", "ur": "اردن"}, "madhab": "shafii", "population": "11.3M"},
    {"flag": "🇧🇭", "name": {"ar": "البحرين", "en": "Bahrain", "fr": "Bahreïn", "fa": "بحرین", "ms": "Bahrain", "ur": "بحرین"}, "madhab": "jafari", "population": "1.5M"},
    {"flag": "🇰🇼", "name": {"ar": "الكويت", "en": "Kuwait", "fr": "Koweït", "fa": "کویت", "ms": "Kuwait", "ur": "کویت"}, "madhab": "maliki", "population": "4.3M"},
    {"flag": "🇹🇳", "name": {"ar": "تونس", "en": "Tunisia", "fr": "Tunisie", "fa": "تونس", "ms": "Tunisia", "ur": "تیونس"}, "madhab": "maliki", "population": "12.4M"},
    {"flag": "🇱🇾", "name": {"ar": "ليبيا", "en": "Libya", "fr": "Libye", "fa": "لیبی", "ms": "Libya", "ur": "لیبیا"}, "madhab": "maliki", "population": "7.0M"},
    {"flag": "🇩🇿", "name": {"ar": "الجزائر", "en": "Algeria", "fr": "Algérie", "fa": "الجزایر", "ms": "Algeria", "ur": "الجزائر"}, "madhab": "maliki", "population": "45.4M"},
    {"flag": "🇮🇩", "name": {"ar": "إندونيسيا", "en": "Indonesia", "fr": "Indonésie", "fa": "اندونزی", "ms": "Indonesia", "ur": "انڈونیشیا"}, "madhab": "shafii", "population": "277.5M"},
    {"flag": "🇲🇾", "name": {"ar": "ماليزيا", "en": "Malaysia", "fr": "Malaisie", "fa": "مالزی", "ms": "Malaysia", "ur": "ملائیشیا"}, "madhab": "shafii", "population": "33.9M"},
    {"flag": "🇵🇰", "name": {"ar": "باكستان", "en": "Pakistan", "fr": "Pakistan", "fa": "پاکستان", "ms": "Pakistan", "ur": "پاکستان"}, "madhab": "hanafi", "population": "240.5M"},
    {"flag": "🇦🇫", "name": {"ar": "أفغانستان", "en": "Afghanistan", "fr": "Afghanistan", "fa": "افغانستان", "ms": "Afghanistan", "ur": "افغانستان"}, "madhab": "hanafi", "population": "41.1M"},
    {"flag": "🇱🇧", "name": {"ar": "لبنان", "en": "Lebanon", "fr": "Liban", "fa": "لبنان", "ms": "Lubnan", "ur": "لبنان"}, "madhab": "shafii", "population": "5.5M"},
    {"flag": "🇵🇸", "name": {"ar": "فلسطين", "en": "Palestine", "fr": "Palestine", "fa": "فلسطین", "ms": "Palestin", "ur": "فلسطین"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇹🇩", "name": {"ar": "تشاد", "en": "Chad", "fr": "Tchad", "fa": "چاد", "ms": "Chad", "ur": "چاڈ"}, "madhab": "maliki", "population": "18.3M"},
    {"flag": "🇳🇬", "name": {"ar": "نيجيريا", "en": "Nigeria", "fr": "Nigeria", "fa": "نیجریه", "ms": "Nigeria", "ur": "نائیجیریا"}, "madhab": "maliki", "population": "223.8M"},
    {"flag": "🇸🇴", "name": {"ar": "الصومال", "en": "Somalia", "fr": "Somalie", "fa": "سومالی", "ms": "Somalia", "ur": "صومالیہ"}, "madhab": "shafii", "population": "18.1M"},
    {"flag": "🇩🇯", "name": {"ar": "جيبوتي", "en": "Djibouti", "fr": "Djibouti", "fa": "جیبوتی", "ms": "Djibouti", "ur": "جبوتی"}, "madhab": "shafii", "population": "1.1M"},
]

COUNTRIES_NOTE = {
    "ar": "ملاحظة: يُقصد بـ«المذهب الرسمي» المذهب الفقهي السائد تاريخياً بين غالبية المسلمين في البلد أو المعتمد في محاكمه الشرعية؛ وقد تتعايش فيه مذاهب أخرى.",
    "en": "Note: the \"official school\" refers to the madhhab historically prevailing among the country's Muslim majority or followed in its Sharia courts; other schools may coexist there.",
    "fr": "Remarque : l'« école officielle » désigne le madhhab historiquement prédominant chez la majorité musulmane du pays ou suivi dans ses tribunaux islamiques ; d'autres écoles peuvent y coexister.",
    "fa": "توجه: «مذهب رسمی» به مذهبی گفته می‌شود که تاریخاً در میان اکثریت مسلمانان آن کشور رایج بوده یا در دادگاه‌های شرعی آن پیروی می‌شود؛ مذاهب دیگر نیز ممکن است در آن حضور داشته باشند.",
    "ms": "Nota: \"mazhab rasmi\" merujuk kepada mazhab yang secara sejarah dominan dalam kalangan majoriti Muslim negara tersebut atau diikuti di mahkamah syariahnya; mazhab lain mungkin turut wujud.",
    "ur": "نوٹ: \"سرکاری مذہب\" سے مراد وہ مذہب ہے جو تاریخی طور پر ملک کی مسلم اکثریت میں غالب رہا یا اس کی شرعی عدالتوں میں اپنایا جاتا ہے؛ دیگر مذاہب بھی وہاں موجود ہو سکتے ہیں۔",
}

# ============================================
# UI Components
# ============================================

def display_fiqh_rules(lang: str, T: Dict) -> None:
    """Display fiqh rules and principles section with multilingual support."""
    
    # تعريف القواعد مع ترجمات لكل اللغات
    rules_data = {
        "اليقين لا يزول بالشك": {
            "ar": {"definition": "إذا ثبت أمر بيقين فلا يزول إلا بيقين مثله، ولا يؤثر فيه مجرد الشك.",
                   "example": "من تيقن الطهارة وشك في الحدث، يبقى على الطهارة."},
            "en": {"definition": "Certainty cannot be overridden by doubt.",
                   "example": "If someone is certain of purity and doubts impurity, they remain in a state of purity."},
            "fr": {"definition": "La certitude ne peut être remplacée par le doute.",
                   "example": "Si quelqu'un est certain de la pureté et doute de l'impureté, il reste en état de pureté."},
            "fa": {"definition": "یقین به شک زایل نمی‌شود.",
                   "example": "کسی که یقین به طهارت دارد و به حدث شک می‌کند، بر طهارت باقی می‌ماند."},
            "ms": {"definition": "Keyakinan tidak boleh digantikan dengan keraguan.",
                   "example": "Jika seseorang yakin suci dan ragu najis, dia kekal dalam keadaan suci."},
            "ur": {"definition": "یقین شک سے زائل نہیں ہوتا۔",
                   "example": "جو شخص طہارت پر یقین رکھتا ہے اور حدث پر شک کرتا ہے، وہ طہارت پر باقی رہتا ہے۔"}
        },
        "المشقة تجلب التيسير": {
            "ar": {"definition": "عند وجود مشقة معتبرة في تطبيق الحكم الشرعي، يُفتح باب الرخصة والتخفيف.",
                   "example": "قصر الصلاة في السفر أو الإفطار في المرض."},
            "en": {"definition": "Hardship brings ease in Islamic jurisprudence.",
                   "example": "Shortening prayers during travel or breaking fast during illness."},
            "fr": {"definition": "La difficulté apporte la facilité dans la jurisprudence islamique.",
                   "example": "Raccourcir les prières pendant le voyage ou rompre le jeûne en cas de maladie."},
            "fa": {"definition": "مشقت باعث آسانی می‌شود.",
                   "example": "قصر نماز در سفر یا افطار در بیماری."},
            "ms": {"definition": "Kesukaran membawa kemudahan dalam fiqh.",
                   "example": "Memendekkan solat semasa musafir atau berbuka puasa ketika sakit."},
            "ur": {"definition": "مشقت آسانی لاتی ہے۔",
                   "example": "سفر میں نماز قصر کرنا یا بیماری میں روزہ افطار کرنا۔"}
        },
        "الضرر يزال": {
            "ar": {"definition": "كل ما فيه ضرر على الفرد أو الجماعة يجب رفعه أو منعه.",
                   "example": "منع الغش في البيع أو إزالة الأذى عن الطريق."},
            "en": {"definition": "Harm must be removed or prevented.",
                   "example": "Preventing fraud in sales or removing harm from the road."},
            "fr": {"definition": "Le préjudice doit être écarté ou empêché.",
                   "example": "Prévenir la fraude dans les ventes ou éliminer les nuisances de la route."},
            "fa": {"definition": "ضرر باید برطرف شود.",
                   "example": "منع تقلب در خرید و فروش یا برداشتن مزاحمت از راه."},
            "ms": {"definition": "Kemudaratan mesti dihilangkan atau dicegah.",
                   "example": "Mencegah penipuan dalam jualan atau membuang bahaya dari jalan."},
            "ur": {"definition": "نقصان کو دور کیا جانا چاہیے۔",
                   "example": "بیع میں دھوکہ دہی کو روکنا یا راستے سے نقصان کو ہٹانا۔"}
        },
        "العادة محكمة": {
            "ar": {"definition": "العرف والعادة المعتبرة شرعًا تُعتبر في الأحكام ما لم تخالف نصًا شرعيًا.",
                   "example": "أعراف الزواج أو البيع."},
            "en": {"definition": "Custom is a valid consideration in Islamic law.",
                   "example": "Customs regarding marriage or sales."},
            "fr": {"definition": "La coutume est considérée en droit islamique.",
                   "example": "Les coutumes relatives au mariage ou aux ventes."},
            "fa": {"definition": "عرف و عادت معتبر شرعی در احکام لحاظ می‌شود.",
                   "example": "عرف‌های ازدواج یا خرید و فروش."},
            "ms": {"definition": "Adat dipertimbangkan dalam hukum Islam.",
                   "example": "Adat mengenai perkahwinan atau jualan."},
            "ur": {"definition": "عادت کو اسلامی قانون میں معتبر سمجھا جاتا ہے۔",
                   "example": "شادی یا بیع کے متعلق رسوم۔"}
        },
        "الأمور بمقاصدها": {
            "ar": {"definition": "الحكم على الأفعال يكون بحسب نية صاحبها ومقصده.",
                   "example": "التفريق بين الصدقة والهدية."},
            "en": {"definition": "Actions are judged by their intentions.",
                   "example": "The distinction between charity and gift."},
            "fr": {"definition": "Les actions sont jugées selon leurs intentions.",
                   "example": "La distinction entre l'aumône et le cadeau."},
            "fa": {"definition": "کارها بر اساس نیت‌ها ارزیابی می‌شوند.",
                   "example": "تفاوت بین صدقه و هدیه."},
            "ms": {"definition": "Tindakan dinilai berdasarkan niat.",
                   "example": "Perbezaan antara sedekah dan hadiah."},
            "ur": {"definition": "اعمال کا دارومدار نیتوں پر ہے۔",
                   "example": "صدقہ اور ہدیہ میں فرق۔"}
        },
        "الضرورات تبيح المحظورات": {
            "ar": {"definition": "عند الضرورة يجوز ارتكاب المحظور بقدر الحاجة فقط.",
                   "example": "أكل الميتة عند الخوف من الهلاك."},
            "en": {"definition": "Necessities permit the forbidden to the extent of need.",
                   "example": "Eating carrion when fearing death."},
            "fr": {"definition": "Les nécessités permettent le prohibé dans la mesure du besoin.",
                   "example": "Manger de la charogne par crainte de mourir."},
            "fa": {"definition": "ضرورت‌ها حرام را به اندازه نیاز مجاز می‌کنند.",
                   "example": "خوردن مردار در صورت ترس از مرگ."},
            "ms": {"definition": "Keperluan membenarkan yang haram mengikut keperluan.",
                   "example": "Memakan bangkai apabila takut mati."},
            "ur": {"definition": "ضرورتیں ممنوعات کو ضرورت کے مطابق جائز کرتی ہیں۔",
                   "example": "موت کے خوف سے مردار کھانا۔"}
        },
        "الوسائل لها أحكام المقاصد": {
            "ar": {"definition": "ما كان وسيلة لشيء يأخذ حكم ذلك الشيء.",
                   "example": "الكتابة في العقود لحفظ الحقوق."},
            "en": {"definition": "The means take the ruling of their objectives.",
                   "example": "Writing contracts to preserve rights."},
            "fr": {"definition": "Les moyens prennent le jugement de leurs objectifs.",
                   "example": "Écrire des contrats pour préserver les droits."},
            "fa": {"definition": "وسایل حکم اهداف خود را دارند.",
                   "example": "نوشتن قراردادها برای حفظ حقوق."},
            "ms": {"definition": "Cara-cara mengambil hukum matlamatnya.",
                   "example": "Menulis kontrak untuk memelihara hak."},
            "ur": {"definition": "ذرائع اپنے مقاصد کا حکم رکھتے ہیں۔",
                   "example": "حقوق کے تحفظ کے لیے معاہدے تحریر کرنا۔"}
        },
        "القياس": {
            "ar": {"definition": "إلحاق فرع بأصل في الحكم لعلة جامعة بينهما.",
                   "example": "قياس المخدرات على الخمر في التحريم لعلة الإسكار."},
            "en": {"definition": "Extending a ruling from an original case to a new case due to shared reasoning.",
                   "example": "Analogizing drugs to alcohol in prohibition due to the reasoning of intoxication."},
            "fr": {"definition": "Extension d'une règle d'un cas original à un nouveau cas en raison d'un raisonnement partagé.",
                   "example": "Analogie des drogues à l'alcool dans l'interdiction en raison de l'intoxication."},
            "fa": {"definition": "الحاق فرع به اصل در حکم به دلیل علت مشترک.",
                   "example": "قیاس مواد مخدر بر خمر در تحریم به دلیل اسکار."},
            "ms": {"definition": "Memperluas hukum dari kes asal ke kes baru kerana persamaan sebab.",
                   "example": "Menganalogikan dadah kepada arak dalam pengharaman kerana sebab memabukkan."},
            "ur": {"definition": "حکم میں فرع کو اصل سے ملانا بوجہ مشترک علت۔",
                   "example": "نشہ کی علت کی وجہ سے منشیات کو شراب پر قیاس کرنا۔"}
        },
        "المصالح المرسلة": {
            "ar": {"definition": "اعتبار المصلحة التي لم يرد نص خاص بها ولم تُلغَ، إذا كانت تحقق منفعة عامة.",
                   "example": "توثيق العقود بالكتابة."},
            "en": {"definition": "Considering public interests not explicitly addressed in primary sources.",
                   "example": "Documenting contracts in writing."},
            "fr": {"definition": "Considération des intérêts publics non explicitement abordés dans les sources primaires.",
                   "example": "Documenter les contrats par écrit."},
            "fa": {"definition": "اعتبار مصلحتی که نص خاصی برای آن نیامده و لغو نشده است.",
                   "example": "مستند کردن قراردادها به نوشته."},
            "ms": {"definition": "Mempertimbangkan kepentingan awam yang tidak disebut secara khusus.",
                   "example": "Mendokumentasikan kontrak secara bertulis."},
            "ur": {"definition": "ان مفادات کا اعتبار جن کا کوئی خاص نص نہیں ہے۔",
                   "example": "معاہدات کو تحریر میں دستاویز کرنا۔"}
        },
        "الخاص يحكم العام": {
            "ar": {"definition": "إذا ورد نص عام ونص خاص، يُقدَّم الخاص في التطبيق.",
                   "example": "قوله تعالى: (وأحل الله البيع) عام، وقوله: (حرمت عليكم الميتة) خاص."},
            "en": {"definition": "When general and specific texts conflict, the specific takes precedence.",
                   "example": "The general verse: 'Allah has permitted trade' vs. 'Forbidden to you is carrion'."},
            "fr": {"definition": "Lorsque les textes généraux et spécifiques sont en conflit, le spécifique prévaut.",
                   "example": "Le verset général 'Allah a permis le commerce' vs 'Il vous est interdit la charogne'."},
            "fa": {"definition": "نص خاص بر عام مقدم می‌شود.",
                   "example": "آیه عام 'خداوند خرید و فروش را حلال کرده' vs 'مردار بر شما حرام شده'."},
            "ms": {"definition": "Teks khusus didahulukan daripada teks umum.",
                   "example": "Ayat umum 'Allah menghalalkan jual beli' vs 'Diharamkan kepada kamu bangkai'."},
            "ur": {"definition": "خاص کو عام پر ترجیح دی جاتی ہے۔",
                   "example": "عام آیت 'اللہ نے بیع کو حلال کیا' vs 'تم پر مردار حرام ہے'۔"}
        },
        "لا ضرر ولا ضرار": {
            "ar": {"definition": "قاعدة مأخوذة من حديث النبي ﷺ: (لا ضرر ولا ضرار)، وتعني أنه لا يجوز إيقاع الضرر بالنفس أو بالغير، ولا يجوز رد الضرر بضرر مثله.",
                   "example": "منع البناء الذي يضر بالجار."},
            "en": {"definition": "Based on the Prophetic hadith: 'No harm and no reciprocating harm.'",
                   "example": "Preventing construction that harms a neighbor."},
            "fr": {"definition": "Basé sur le hadith prophétique: 'Pas de mal et pas de réciprocité de mal.'",
                   "example": "Prévenir la construction qui nuit à un voisin."},
            "fa": {"definition": "بر اساس حدیث نبوی: 'نه ضرر و نه ضرر متقابل'.",
                   "example": "جلوگیری از ساخت و سازی که به همسایه ضرر می‌زند."},
            "ms": {"definition": "Berdasarkan hadis Nabi: 'Tidak boleh membahayakan dan tidak boleh membalas bahaya.'",
                   "example": "Mencegah pembinaan yang merugikan jiran."},
            "ur": {"definition": "نبوی حدیث پر مبنی: 'نہ نقصان اور نہ نقصان کا بدلہ'۔",
                   "example": "ایسی تعمیر کو روکنا جو پڑوسی کو نقصان پہنچائے۔"}
        },
        "الأصل في الأشياء الإباحة": {
            "ar": {"definition": "كل شيء لم يرد نص بتحريمه فحكمه الأصلي الإباحة، حتى يقوم دليل شرعي على المنع.",
                   "example": "إباحة الأطعمة والمشروبات والمعاملات المستحدثة ما لم يثبت فيها محذور شرعي."},
            "en": {"definition": "Anything not explicitly prohibited by a text is presumed permissible until evidence establishes otherwise.",
                   "example": "New foods, drinks, or transactions remain permissible unless a specific prohibition is shown."},
            "fr": {"definition": "Tout ce qui n'est pas explicitement interdit par un texte est présumé permis, jusqu'à preuve du contraire.",
                   "example": "Les nouveaux aliments ou transactions restent licites tant qu'aucune interdiction précise n'est établie."},
            "fa": {"definition": "هر چیزی که نص صریحی بر تحریم آن نیامده، اصل در آن اباحه است تا دلیلی بر منع بیاید.",
                   "example": "اباحه خوراکی‌ها و معاملات جدید تا زمانی که محذور شرعی در آن‌ها ثابت نشود."},
            "ms": {"definition": "Sesuatu yang tiada nas jelas mengharamkannya, hukum asalnya harus sehingga ada dalil yang melarangnya.",
                   "example": "Makanan, minuman, dan urus niaga baharu kekal harus selagi tiada larangan syarak yang jelas."},
            "ur": {"definition": "جس چیز کی حرمت پر واضح نص نہ ہو، اس کا اصل حکم اباحت ہے جب تک ممانعت کی دلیل نہ آئے۔",
                   "example": "نئے کھانوں، مشروبات اور معاملات کا جواز جب تک ان میں شرعی ممانعت ثابت نہ ہو۔"}
        },
        "الأصل براءة الذمة": {
            "ar": {"definition": "الأصل أن يبقى الإنسان غير مطالَب بحق أو التزام تجاه غيره حتى يثبت خلاف ذلك بدليل معتبر.",
                   "example": "من ادّعى ديناً على آخر فالبيّنة عليه؛ لأن الأصل براءة ذمة المدَّعى عليه."},
            "en": {"definition": "A person is presumed free of any claim or liability until proven otherwise by valid evidence.",
                   "example": "Whoever claims a debt against another must provide proof, since the defendant is presumed free of liability."},
            "fr": {"definition": "Une personne est présumée libre de toute obligation jusqu'à preuve valable du contraire.",
                   "example": "Celui qui prétend qu'une dette lui est due doit en apporter la preuve, l'accusé étant présumé sans dette."},
            "fa": {"definition": "اصل این است که انسان تا اثبات خلاف آن با دلیل معتبر، از هیچ حق یا تعهدی نسبت به دیگری مسئول نیست.",
                   "example": "هر کس ادعای دِینی بر دیگری کند، اثبات آن بر عهده اوست؛ زیرا اصل برائت ذمه مدعی‌علیه است."},
            "ms": {"definition": "Pada asalnya seseorang bebas daripada sebarang tuntutan atau tanggungan sehingga terbukti sebaliknya dengan bukti sah.",
                   "example": "Sesiapa mendakwa hutang ke atas orang lain wajib membawa bukti, kerana asalnya tertuduh bebas tanggungan."},
            "ur": {"definition": "اصل یہ ہے کہ انسان کسی حق یا ذمہ داری سے بری رہتا ہے جب تک معتبر دلیل سے اس کے خلاف ثابت نہ ہو۔",
                   "example": "جو کسی پر قرض کا دعویٰ کرے، ثبوت اسی کے ذمہ ہے؛ کیونکہ اصل مدعا علیہ کی برأت ہے۔"}
        },
        "الاستحسان": {
            "ar": {"definition": "العدول عن مقتضى قياس ظاهر إلى حكم آخر يقتضيه دليل أقوى، كنص خاص أو عرف أو ضرورة، تحقيقاً لمصلحة راجحة.",
                   "example": "جواز عقد الاستصناع استحساناً، وإن كان القياس الظاهر يقتضي منعه لكون المصنوع معدوماً وقت العقد."},
            "en": {"definition": "Departing from an apparent analogy toward a ruling supported by stronger evidence - a specific text, custom, or necessity - to serve a preponderant benefit.",
                   "example": "Permitting the manufacturing contract (istisna') by juristic preference, though strict analogy would forbid selling a non-existent item."},
            "fr": {"definition": "S'écarter d'une analogie apparente vers un jugement fondé sur une preuve plus forte - texte spécifique, coutume ou nécessité - pour un intérêt supérieur.",
                   "example": "Autoriser le contrat de fabrication (istisna') par préférence juridique, bien que l'analogie stricte l'interdirait."},
            "fa": {"definition": "عدول از قیاس ظاهر به حکمی دیگر که دلیل قوی‌تری چون نص خاص، عرف یا ضرورت اقتضا می‌کند، برای تحقق مصلحتی برتر.",
                   "example": "جواز عقد استصناع به استحسان، هرچند قیاس ظاهر آن را به دلیل معدوم بودن کالا هنگام عقد منع می‌کند."},
            "ms": {"definition": "Beralih daripada qiyas zahir kepada hukum lain yang disokong dalil lebih kuat - nas khusus, uruf, atau darurat - demi maslahat yang lebih besar.",
                   "example": "Membenarkan akad istisna' secara istihsan, walaupun qiyas zahir melarangnya kerana barang belum wujud semasa akad."},
            "ur": {"definition": "ظاہری قیاس سے ہٹ کر ایسے حکم کی طرف رجوع جسے خاص نص، عرف یا ضرورت جیسی مضبوط دلیل چاہتی ہو، بہتر مصلحت کے لیے۔",
                   "example": "استصناع کے معاہدے کا استحساناً جواز، اگرچہ ظاہری قیاس اسے معاہدے کے وقت چیز کے معدوم ہونے کی وجہ سے منع کرتا ہے۔"}
        },
        "الاستصحاب": {
            "ar": {"definition": "إبقاء الحكم الثابت في الماضي قائماً في الحال والمستقبل، ما لم يقم دليل شرعي على تغييره أو زواله.",
                   "example": "من ثبتت له ملكية شيء بيقين، بقي مالكاً له حتى يثبت زوال ملكه بدليل."},
            "en": {"definition": "Presuming that a previously established ruling remains in effect unless proven otherwise.",
                   "example": "Whoever is established as the owner of something remains so until evidence proves otherwise."},
            "fr": {"definition": "Présumer qu'un jugement précédemment établi reste valable, sauf preuve contraire.",
                   "example": "Celui dont la propriété d'un bien est établie en reste propriétaire jusqu'à preuve du contraire."},
            "fa": {"definition": "باقی نگه‌داشتن حکمی که در گذشته ثابت شده تا زمانی که دلیلی بر تغییر یا زوال آن اقامه نشود.",
                   "example": "کسی که مالکیت چیزی برایش به یقین ثابت شده، تا اثبات زوال آن با دلیل، مالک باقی می‌ماند."},
            "ms": {"definition": "Mengekalkan hukum yang telah sabit pada masa lalu sehingga ada dalil yang mengubah atau membatalkannya.",
                   "example": "Sesiapa yang sabit memiliki sesuatu kekal sebagai pemiliknya sehingga terbukti sebaliknya."},
            "ur": {"definition": "ماضی میں ثابت شدہ حکم کو حال و مستقبل میں برقرار رکھنا جب تک اس کے تبدیل یا زوال کی دلیل نہ ملے۔",
                   "example": "جس کی ملکیت یقینی طور پر ثابت ہو، وہ اس کا مالک رہتا ہے جب تک زوالِ ملکیت کی دلیل نہ آئے۔"}
        },
        "سد الذرائع": {
            "ar": {"definition": "منع فعل جائز في أصله متى كان وسيلة غالبة إلى مفسدة محققة، درءاً لتلك المفسدة قبل وقوعها.",
                   "example": "منع بيع السلاح في زمن الفتنة لمن يُخشى استعماله في قتال ظالم."},
            "en": {"definition": "Blocking an act permissible in itself when it is a likely means to a real harm, to prevent that harm before it occurs.",
                   "example": "Prohibiting the sale of weapons in times of unrest to those likely to use them for unjust bloodshed."},
            "fr": {"definition": "Interdire un acte permis en soi lorsqu'il est un moyen probable vers un préjudice réel, afin de le prévenir.",
                   "example": "Interdire la vente d'armes en temps de troubles à ceux susceptibles de les utiliser injustement."},
            "fa": {"definition": "منع کاری که در اصل جایز است هرگاه وسیله غالب به مفسده‌ای قطعی باشد، برای جلوگیری از آن مفسده پیش از وقوع.",
                   "example": "منع فروش سلاح در زمان آشوب به کسی که بیم استفاده ظالمانه از آن می‌رود."},
            "ms": {"definition": "Menghalang perbuatan yang asalnya harus apabila ia menjadi jalan yang kuat kepada kemudaratan nyata, bagi mencegahnya sebelum berlaku.",
                   "example": "Melarang jualan senjata semasa fitnah kepada golongan yang dikhuatiri menyalahgunakannya."},
            "ur": {"definition": "اصلاً جائز کام کو روکنا جب وہ کسی یقینی خرابی کا غالب ذریعہ بن جائے، تاکہ وہ خرابی وقوع سے پہلے رک جائے۔",
                   "example": "فتنے کے دور میں اسلحہ بیچنا اس شخص کو روکنا جس سے ظالمانہ استعمال کا خدشہ ہو۔"}
        },
        "درء المفاسد أولى من جلب المصالح": {
            "ar": {"definition": "عند تعارض مصلحة ومفسدة وتعذّر الجمع بينهما، يُقدَّم دفع المفسدة على تحصيل المصلحة.",
                   "example": "منع فتح باب معاملة مالية فيها ربا وإن حقق نفعاً اقتصادياً، درءاً لمفسدة الربا."},
            "en": {"definition": "When a benefit and a harm conflict and cannot both be achieved, preventing the harm takes priority over securing the benefit.",
                   "example": "Blocking a financial dealing involving usury even if it offers economic gain, to prevent the greater harm."},
            "fr": {"definition": "Lorsqu'un bienfait et un préjudice s'opposent sans conciliation possible, prévenir le préjudice prime sur l'obtention du bienfait.",
                   "example": "Interdire une opération financière usuraire malgré un gain économique, pour prévenir le préjudice."},
            "fa": {"definition": "هنگام تعارض مصلحت و مفسده و ناممکن بودن جمع میان آن‌ها، دفع مفسده بر جلب مصلحت مقدم است.",
                   "example": "منع معامله مالی ربوی هرچند سود اقتصادی داشته باشد، برای دفع مفسده ربا."},
            "ms": {"definition": "Apabila maslahat dan mafsadah bertembung dan tidak boleh digabungkan, mencegah mafsadah didahulukan daripada mengejar maslahat.",
                   "example": "Menghalang urus niaga kewangan yang mengandungi riba walaupun membawa keuntungan ekonomi."},
            "ur": {"definition": "جب مصلحت اور مفسدہ ٹکرائیں اور دونوں کو جمع کرنا ممکن نہ ہو تو مفسدہ دور کرنا مصلحت حاصل کرنے پر مقدم ہے۔",
                   "example": "سودی مالی معاملہ روکنا اگرچہ اس میں اقتصادی فائدہ ہو، سود کے نقصان کو روکنے کے لیے۔"}
        },
        "ما لا يتم الواجب إلا به فهو واجب": {
            "ar": {"definition": "كل وسيلة لا يتحقق أداء الواجب إلا بها، تأخذ حكم الوجوب تبعاً للواجب نفسه.",
                   "example": "تعلّم أحكام الطهارة والصلاة واجب؛ لأن صحة الصلاة الواجبة تتوقف عليه."},
            "en": {"definition": "Whatever a duty depends on for its fulfillment is itself obligatory, as a means to that duty.",
                   "example": "Learning the rulings of purification and prayer is obligatory, since the validity of the obligatory prayer depends on it."},
            "fr": {"definition": "Tout moyen indispensable à l'accomplissement d'une obligation devient lui-même obligatoire.",
                   "example": "Apprendre les règles de la purification et de la prière est obligatoire, car la validité de la prière en dépend."},
            "fa": {"definition": "هر وسیله‌ای که انجام واجب جز با آن ممکن نباشد، خود آن وسیله نیز واجب می‌شود.",
                   "example": "آموختن احکام طهارت و نماز واجب است؛ زیرا صحت نماز واجب بر آن متوقف است."},
            "ms": {"definition": "Setiap wasilah yang tanpanya sesuatu kewajipan tidak dapat disempurnakan, turut menjadi wajib.",
                   "example": "Mempelajari hukum bersuci dan solat adalah wajib, kerana sahnya solat wajib bergantung kepadanya."},
            "ur": {"definition": "وہ ذریعہ جس کے بغیر کوئی واجب مکمل نہ ہو سکے، وہ خود بھی واجب کے تابع واجب بن جاتا ہے۔",
                   "example": "طہارت اور نماز کے احکام سیکھنا واجب ہے؛ کیونکہ واجب نماز کی صحت اسی پر موقوف ہے۔"}
        },
        "إذا ضاق الأمر اتسع": {
            "ar": {"definition": "إذا ضاقت الأحوال على المكلف في تطبيق الحكم الأصلي، اتسع له مجال الرخصة والتخفيف رفعاً للحرج.",
                   "example": "التيمم عند تعذّر الماء أو الخوف من ضرر استعماله، توسعة على المكلف عند ضيق الحال."},
            "en": {"definition": "When circumstances become constrained for the individual applying the default ruling, the scope of concession and ease widens to lift hardship.",
                   "example": "Performing tayammum (dry ablution) when water is unavailable or its use would cause harm, as an easing in constrained circumstances."},
            "fr": {"definition": "Lorsque les circonstances deviennent contraignantes dans l'application du jugement initial, la marge de concession s'élargit pour lever la difficulté.",
                   "example": "Le tayammum (ablution sèche) lorsque l'eau manque ou que son usage serait nuisible."},
            "fa": {"definition": "هرگاه احوال مکلف در اجرای حکم اصلی تنگ شود، دامنه رخصت و تخفیف برای رفع حرج گسترده می‌شود.",
                   "example": "تیمم هنگام نبود آب یا بیم ضرر از استعمال آن، توسعه‌ای بر مکلف در تنگنا."},
            "ms": {"definition": "Apabila keadaan menyempit bagi mukallaf dalam melaksanakan hukum asal, ruang keringanan diperluaskan untuk mengangkat kesukaran.",
                   "example": "Bertayamum ketika air tiada atau membahayakan, sebagai kelonggaran ketika keadaan sempit."},
            "ur": {"definition": "جب مکلف کے لیے اصل حکم پر عمل تنگ ہو جائے تو رخصت و تخفیف کی گنجائش وسیع ہو جاتی ہے تاکہ حرج دور ہو۔",
                   "example": "پانی نہ ملنے یا اس کے استعمال سے نقصان کے خوف میں تیمم، تنگی کے وقت آسانی۔"}
        }
    }
    
    # عرض القواعد بنفس نمط الفقرات السابقة - كل شيء مخفي تحت العنوان الرئيسي
    # ملاحظة: تم استبدال الـ expander الداخلي بعناصر Markdown لتفادي خطأ
    # "Expanders may not be nested inside other expanders" في Streamlit.
    with st.expander(T["rules_title"]):
        for i, (rule_name, rule_translations) in enumerate(rules_data.items()):
            # الحصول على الترجمة حسب اللغة المختارة
            rule_content = rule_translations.get(lang, rule_translations.get("ar", {}))
            
            if i > 0:
                st.markdown("---")
            
            st.markdown(f"**📌 {rule_name}**")
            st.markdown(f"""
            <div class="info-box">
                <p><strong>{T['rules_definition']}:</strong> {rule_content.get('definition', '')}</p>
                <p><strong>{T['rules_example']}:</strong> {rule_content.get('example', '')}</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# Main Application
# ============================================

def main():
    """Main application entry point."""
    
    # Initialize services
    db = DatabaseManager()
    search_service = SearchService(db)
    
    # Initialize session state
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "session_comments" not in st.session_state:
        st.session_state.session_comments = []
    
    lang = st.session_state.lang
    T = UI[lang]
    
    # RTL support
    is_rtl = lang in ["ar", "fa", "ur"]
    direction = "rtl" if is_rtl else "ltr"
    align = "right" if is_rtl else "left"
    
    # ---- Language bar: a compact bordered pill-selector, shown before any
    # other CSS/content so a language switch is reflected immediately.
    with st.container(border=True):
        lb1, lb2 = st.columns([1, 3])
        with lb1:
            st.markdown(f"**🌐 {T['lang_label']}**")
        with lb2:
            lang_choice = st.radio(
                T["lang_label"],
                list(LANGS.keys()),
                index=list(LANGS.values()).index(st.session_state.lang),
                horizontal=True,
                label_visibility="collapsed",
                format_func=lambda name: f"{LANG_FLAGS.get(LANGS[name], '')} {name}",
                key="lang_radio",
            )
    if LANGS[lang_choice] != st.session_state.lang:
        st.session_state.lang = LANGS[lang_choice]
        st.rerun()
    
    # Custom CSS
    st.markdown(f"""
    <style>
    .stApp {{ direction: {direction}; }}
    .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
        text-align: {align};
        line-height: 1.9;
    }}
    .stButton button {{ width: 100%; border-radius: 10px; }}

    /* Pill-styled radio groups app-wide (language bar, madhab/topic/level
       selectors) for a cohesive, modern look instead of the default
       bullet-point radio list. */
    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        gap: 6px; flex-wrap: wrap;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label {{
        background: #f0f3f1;
        border: 1px solid #e1e7e3;
        padding: 6px 16px;
        border-radius: 999px;
        transition: all 0.15s ease;
        margin: 0 !important;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {{
        background: #e3ece7;
        border-color: #2a5c4a;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"],
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {{
        background: #2a5c4a;
        border-color: #2a5c4a;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) p {{
        color: #ffffff !important;
        font-weight: 600;
    }}

    /* Header */
    .app-header {{
        position: relative;
        text-align: center;
        padding: 30px 20px 26px;
        background: radial-gradient(circle at 25% 15%, #1c3f31 0%, #0f231c 55%, #0a1a14 100%);
        color: white; border-radius: 20px; margin-bottom: 25px;
        overflow: hidden;
        box-shadow: 0 10px 28px rgba(15, 35, 28, 0.28);
    }}
    .app-header-accent {{
        position: absolute; top: 0; left: 0; right: 0; height: 5px;
        background: linear-gradient(90deg, #8a6a2e, #f2e6c9, #d4a854, #f2e6c9, #8a6a2e);
    }}
    .app-logo {{ margin-bottom: 4px; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.35)); }}
    .app-header h1 {{
        text-align: center !important;
        margin: 8px 0 6px;
        font-size: 1.85rem;
        letter-spacing: 0.2px;
    }}
    .app-subtitle {{
        text-align: center !important;
        color: #e7ddc4;
        font-size: 0.95rem;
        max-width: 640px;
        margin: 0 auto 16px;
        opacity: 0.92;
    }}
    .app-badges {{ display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }}
    .app-badge {{
        background: rgba(212, 168, 84, 0.14);
        border: 1px solid rgba(212, 168, 84, 0.5);
        color: #f2e6c9;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        white-space: nowrap;
    }}

    .answer-card {{
        background: #f5f7f5; border: 1px solid #e1e7e3;
        border-radius: 14px; padding: 16px 18px;
        margin-bottom: 12px;
    }}
    .answer-card .answer-text {{ font-size: 1.15rem; font-weight: 600; color: #16281f; margin: 4px 0; }}
    .answer-card .answer-note {{ font-size: 0.85rem; color: #6a7f78; }}
    .signature {{
        font-family: 'Brush Script MT', cursive;
        font-style: italic; font-size: 1rem; color: #b08d3f;
        text-align: center; margin: 6px 0 18px 0;
    }}
    .info-box {{
        background: #f8f9fa; border-radius: 10px; padding: 12px 16px;
        margin-bottom: 12px; border-left: 4px solid #2a5c4a;
    }}
    .country-box {{
        background: #f8f9fa; border-radius: 10px; padding: 12px;
        margin-bottom: 10px; text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # App header: logo, title, subtitle and quick-stat badges combined into
    # a single cohesive card with a gold accent border.
    st.markdown(f"""
    <div class="app-header">
        <div class="app-header-accent"></div>
        <div class="app-logo">
            <svg width="84" height="84" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
                <circle cx="60" cy="60" r="56" fill="#0f231c" stroke="#d4a854" stroke-width="3"/>
                <circle cx="60" cy="60" r="49" fill="none" stroke="#d4a854" stroke-width="0.75" opacity="0.5"/>
                <path d="M78 20 A15 15 0 1 0 81 47 A11.5 11.5 0 1 1 78 20 Z" fill="#d4a854"/>
                <path d="M60 50 C46 43 32 45 25 52 V90 C32 83 46 81 60 88 C74 81 88 83 95 90 V52 C88 45 74 43 60 50 Z" fill="none" stroke="#f2e6c9" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
                <line x1="60" y1="50" x2="60" y2="88" stroke="#f2e6c9" stroke-width="3"/>
                <path d="M32 59 Q46 55 58 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 67 Q46 63 58 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 75 Q46 71 58 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 59 Q74 55 88 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 67 Q74 63 88 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 75 Q74 71 88 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            </svg>
        </div>
        <h1>📖 {T['app_title']}</h1>
        <p class="app-subtitle">{T['app_subtitle']}</p>
        <div class="app-badges">
            <span class="app-badge">📖 8 {T['badge_madhabs']}</span>
            <span class="app-badge">🌐 6 {T['badge_langs']}</span>
            <span class="app-badge">🗺️ {len(COUNTRIES)} {T['badge_countries']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin: CSV Import
    with st.expander("📥 استيراد مسائل من CSV (للمشرفين)", expanded=False):
        st.info("**تنسيق CSV المطلوب:** يجب أن يحتوي على جميع الأعمدة المطابقة لقاعدة البيانات.")
        uploaded = st.file_uploader("اختر ملف CSV", type=["csv"])
        if uploaded:
            try:
                count = db.import_from_csv(uploaded.read())
                st.success(f"✅ تم استيراد {count} مسألة بنجاح!")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")
    
    # Main search interface
    st.markdown(f"### {T['s1_title']}")
    group_code = st.radio(
        T["group_q"],
        list(GROUPS.keys()),
        format_func=lambda g: GROUPS[g][lang],
        horizontal=True,
        label_visibility="collapsed",
    )
    sub_codes = GROUPS[group_code]["members"]
    st.caption(T["multi_hint"])
    
    if len(sub_codes) > 1:
        selected_madhabs = st.multiselect(
            T["sub_select"],
            options=sub_codes,
            default=[sub_codes[0]],
            format_func=lambda c: MADHHAB_NAMES[c][lang],
        )
    else:
        selected_madhabs = sub_codes
        st.caption(f"**{MADHHAB_NAMES[sub_codes[0]][lang]}**")
    
    st.divider()
    st.markdown(f"### {T['s2_title']}")
    topic = st.radio(
        T["topic_q"],
        list(TOPICS.keys()),
        format_func=lambda t: TOPICS[t][lang],
        horizontal=True,
        label_visibility="collapsed",
    )
    
    st.divider()
    st.markdown(f"### {T['s3_title']}")
    level = st.radio(
        T["level_q"],
        list(LEVELS.keys()),
        format_func=lambda lv: LEVELS[lv][lang],
        horizontal=True,
        label_visibility="collapsed",
    )
    
    st.divider()
    st.markdown(f"### {T['s4_title']}")
    question = st.text_input(
        T["s4_title"], placeholder=T["question_placeholder"], label_visibility="collapsed"
    )
    search_clicked = st.button(T["search_btn"], use_container_width=True)
    
    st.divider()
    st.markdown(f"### {T['s5_title']}")
    
    # Process search
    if search_clicked and not selected_madhabs:
        st.warning(T["no_madhab_warning"])
    elif search_clicked and question:
        results = search_service.search(question, topic, selected_madhabs, level, lang, T)
        
        # Display results
        if results:
            for r in results:
                st.markdown(f"**📌 {r.title}** &nbsp;·&nbsp; _{r.topic}_")
                cols = st.columns(len(r.cards)) if len(r.cards) > 1 else [st.container()]
                for col, card in zip(cols, r.cards):
                    with col:
                        st.markdown(f"""
                        <div class="answer-card">
                            <h4>{card['label']}</h4>
                            <div class="answer-text">{card['answer']}</div>
                            <div class="answer-note">{card['note']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown(f"<div class='signature'>{T['signature']}</div>", unsafe_allow_html=True)
        else:
            st.warning(T["no_results_warning"])
    elif search_clicked:
        st.info(T["no_question_warning"])
    else:
        st.caption(T["answer_placeholder"])
    
    st.markdown("---")
    
    # Information expanders
    with st.expander(T["expander_imams"]):
        for imam in IMAMS:
            st.markdown(f"""
            <div class="info-box">
                <h4>{imam['name'][lang]}</h4>
                <p style="color:#d4a854; font-weight:600;">{imam['school'][lang]} &nbsp;|&nbsp; {imam['lifespan']}</p>
                <p>📍 {T['birthplace']}: {imam['birthplace'][lang]} &nbsp;·&nbsp; 🏛️ {T['founding_place']}: {imam['founding_place'][lang]}</p>
                <p>🎓 {T['scholars']}: {imam['scholars'][lang]}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander(T["expander_countries"]):
        cols = st.columns(3)
        for i, c in enumerate(COUNTRIES):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="country-box">
                    <strong>{c['flag']} {c['name'][lang]}</strong><br>
                    <span style="color:#d4a854;">{T['official_madhab']}: {MADHHAB_NAMES[c['madhab']][lang]}</span><br>
                    <span style="font-size:0.8rem; color:#6a7f78;">👥 {T['population']}: {c['population']}</span>
                </div>
                """, unsafe_allow_html=True)
        st.caption(COUNTRIES_NOTE.get(lang, COUNTRIES_NOTE["ar"]))
    
    with st.expander(T["expander_glossary"]):
        glossary_cols = st.columns(2)
        for i, term in enumerate(GLOSSARY):
            example_html = ""
            if term.get("example"):
                example_html = f"<p>🔹 <strong>{T['rules_example']}:</strong> {term['example'][lang]}</p>"
            with glossary_cols[i % 2]:
                st.markdown(f"""
                <div class="info-box">
                    <h4>{term['term'][lang]}</h4>
                    <p>{term['definition'][lang]}</p>
                    {example_html}
                </div>
                """, unsafe_allow_html=True)
    
    # Display Fiqh Rules with translation support
    display_fiqh_rules(lang, T)
    
    # Comments section
    with st.expander(T["expander_comments"]):
        st.markdown(f"**{T['rating_label']}**")
        try:
            rating = st.feedback("stars")
            if rating is not None:
                rating = rating + 1
        except:
            rating = st.radio(T["rating_label"], [1, 2, 3, 4, 5], format_func=lambda n: "⭐" * n, horizontal=True, label_visibility="collapsed")
        
        comment_text = st.text_area(T["comment_placeholder"], placeholder=T["comment_placeholder"], label_visibility="collapsed")
        
        if st.button(T["comment_submit"]):
            if comment_text.strip():
                st.session_state.session_comments.append({"text": comment_text.strip(), "rating": rating or 5})
                st.success(T["comment_success"])
            else:
                st.warning(T["comment_warning"])
        
        if st.session_state.session_comments:
            st.markdown(f"**{T['comments_title']}**")
            for c in st.session_state.session_comments:
                st.markdown(f"- {'⭐' * int(c['rating'])} - {c['text']}")
        st.caption(T["comments_note"])


if __name__ == "__main__":
    main()
