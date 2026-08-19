import streamlit as st
import re
import sqlite3
import json
import os
import csv
import io

# =====================================================================
# 0) استيراد المكتبات الاختيارية بأمان
# =====================================================================
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

# =====================================================================
# 1) الحصول على مفتاح Gemini (من st.secrets أو متغير البيئة)
# =====================================================================
def get_gemini_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, AttributeError):
        pass
    if DOTENV_AVAILABLE:
        return os.getenv("GEMINI_API_KEY")
    return None

GEMINI_API_KEY = get_gemini_api_key()
USE_GEMINI = GEMINI_API_KEY is not None and GENAI_AVAILABLE
if USE_GEMINI:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        USE_GEMINI = False

# =====================================================================
# 2) قاعدة البيانات (SQLite)
# =====================================================================
DB_PATH = "fiqh.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            title_ar TEXT, title_en TEXT, title_fr TEXT, title_fa TEXT, title_ms TEXT, title_ur TEXT,
            keywords_ar TEXT, keywords_en TEXT, keywords_fr TEXT, keywords_fa TEXT, keywords_ms TEXT, keywords_ur TEXT,
            ruling_vs_ar TEXT, ruling_s_ar TEXT, ruling_f_ar TEXT,
            ruling_vs_en TEXT, ruling_s_en TEXT, ruling_f_en TEXT,
            ruling_vs_fr TEXT, ruling_s_fr TEXT, ruling_f_fr TEXT,
            ruling_vs_fa TEXT, ruling_s_fa TEXT, ruling_f_fa TEXT,
            ruling_vs_ms TEXT, ruling_s_ms TEXT, ruling_f_ms TEXT,
            ruling_vs_ur TEXT, ruling_s_ur TEXT, ruling_f_ur TEXT,
            rulings_by_madhab_ar JSON, rulings_by_madhab_en JSON, rulings_by_madhab_fr JSON,
            rulings_by_madhab_fa JSON, rulings_by_madhab_ms JSON, rulings_by_madhab_ur JSON
        )
    ''')
    # جدول المراجع المرفوعة (RAG) — نصوص مصدرية يرفعها المشرف، تُقسّم
    # إلى مقاطع (chunks) ويُخزَّن تمثيلها الرقمي (embedding) لكل مقطع
    # لاسترجاع الأقرب دلالياً لسؤال المستخدم بسرعة عند البحث.
    c.execute('''
        CREATE TABLE IF NOT EXISTS reference_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_title TEXT,
            madhab_tag TEXT,
            chunk_text TEXT,
            embedding JSON,
            added_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def seed_initial_issues():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    issues = [
        {
            "topic": "ibadat",
            "title_ar": "صلاة الجماعة", "title_en": "Congregational Prayer", "title_fr": "La prière en congrégation",
            "title_fa": "نماز جماعت", "title_ms": "Solat Berjemaah", "title_ur": "نماز باجماعت",
            "keywords_ar": "جماعة,مسجد,رجال,صلاة,فرض,سنة,واجب",
            "keywords_en": "congregation,mosque,men,prayer,obligatory,sunnah",
            "keywords_fr": "congrégation,mosquée,hommes,prière,obligatoire,sunna",
            "keywords_fa": "جماعت,مسجد,مردان,نماز,فرض,سنت,واجب",
            "keywords_ms": "jemaah,masjid,lelaki,solat,fardu,sunnah,wajib",
            "keywords_ur": "جماعت,مسجد,مرد,نماز,فرض,سنت,واجب",
            "ruling_vs_ar": "سنة مؤكدة", "ruling_s_ar": "سنة مؤكدة عند الجمهور، واجبة عند الحنفية",
            "ruling_f_ar": "تجب صلاة الجماعة في المسجد على الرجال عند جمهور الفقهاء؛ فهي فرض عين عند الحنابلة، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة تأكيداً عند الجعفرية في زمن الغيبة.",
            "ruling_vs_en": "Emphasized Sunnah", "ruling_s_en": "Emphasized sunnah for most jurists, obligatory for the Hanafis",
            "ruling_f_en": "Congregational prayer in the mosque is required of men according to the majority of jurists: an individual obligation for the Hanbalis, an emphasized obligation for the Hanafis, a communal obligation for the Malikis and Shafi'is, and a strongly recommended act for the Ja'faris during the Occultation.",
            "ruling_vs_fr": "Sunna fortement recommandée", "ruling_s_fr": "Sunna fortement recommandée pour la majorité, obligatoire pour les hanafites",
            "ruling_f_fr": "La prière en congrégation à la mosquée est requise des hommes selon la majorité des juristes : obligation individuelle chez les hanbalites, obligation appuyée chez les hanafites, obligation collective chez les malikites et les chaféites, et acte fortement recommandé chez les jaafarites durant l'Occultation.",
            "ruling_vs_fa": "سنت مؤکد", "ruling_s_fa": "سنت مؤکد نزد جمهور، واجب نزد حنفیان",
            "ruling_f_fa": "نماز جماعت در مسجد بر مردان واجب است به اتفاق جمهور فقها؛ فرض عین برای حنبلی‌ها، واجب مؤکد برای حنفی‌ها، فرض کفایه برای مالکی‌ها و شافعی‌ها، و مستحب مؤکد برای جعفری‌ها در زمان غیبت.",
            "ruling_vs_ms": "Sunnah muakkadah", "ruling_s_ms": "Sunnah muakkadah bagi majoriti, wajib bagi Hanafi",
            "ruling_f_ms": "Solat berjemaah di masjid diwajibkan ke atas lelaki menurut majoriti ulama; fardu ain bagi Hanbali, wajib muakkad bagi Hanafi, fardu kifayah bagi Maliki dan Syafii, dan mustahab muakkad bagi Jaafari semasa ghaib.",
            "ruling_vs_ur": "سنت مؤکدہ", "ruling_s_ur": "سنت مؤکدہ نزد جمہور، واجب نزد احناف",
            "ruling_f_ur": "مسجد میں نماز باجماعت مردوں پر جمہور فقہاء کے نزدیک واجب ہے؛ حنابلہ کے نزدیک فرض عین، احناف کے نزدیک واجب مؤکد، مالکیہ و شافعیہ کے نزدیک فرض کفایہ، اور جعفریہ کے نزدیک مستحب مؤکد ہے۔",
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
            "rulings_by_madhab_en": json.dumps({
                "maliki": {"very_short": "Communal obligation", "short": "Communal obligation on the locality, emphasized sunnah for the individual", "full": "A communal obligation (fard kifayah) upon the residents of a locality; for a single individual it is an emphasized sunnah, and abandoning it is disliked only for one who habitually neglects it."},
                "shafii": {"very_short": "Emphasized Sunnah", "short": "Communal obligation on society, emphasized sunnah for the individual", "full": "A communal obligation upon society as a whole, and an emphasized sunnah for the individual — this is the most authoritative view in the school."},
                "hanafi": {"very_short": "Wajib", "short": "Obligatory (wajib) on every free, sane, adult man", "full": "It is obligatory (wajib), one degree below fard, upon every free, sane, adult, capable man; abandoning it without excuse is strongly disliked according to later scholars."},
                "hanbali": {"very_short": "Fard Ayn", "short": "Individual obligation on every capable man", "full": "It is an individual obligation (fard ayn) upon every legally accountable, capable man; it may not be abandoned except for a recognized legal excuse."},
                "zahiri": {"very_short": "Fard Ayn", "short": "Individual obligation, based on the literal Prophetic command", "full": "It is an individual obligation, taken from the literal wording of the Prophet's command to maintain it, without interpretation that would divert it away from obligation."},
                "jafari": {"very_short": "Strongly recommended", "short": "Strongly recommended during the Occultation, not individually obligatory", "full": "It is strongly recommended rather than individually obligatory during the Major Occultation, and its reward is great."},
                "zaidi": {"very_short": "Fard Kifayah", "short": "Close to the Sunni emphasis on maintaining it", "full": "It is a communal obligation; the Zaidi view is close to the Sunni emphasis on maintaining it in congregation."},
                "ibadi": {"very_short": "Emphasized Sunnah", "short": "A visible marker of the religion; should not be habitually abandoned", "full": "It is one of the visible markers of the religion, an emphasized sunnah that should not be habitually abandoned, though it is not a condition for the validity of the prayer."}
            }),
            "rulings_by_madhab_fr": "{}",
            "rulings_by_madhab_fa": "{}",
            "rulings_by_madhab_ms": "{}",
            "rulings_by_madhab_ur": "{}"
        },
        {
            "topic": "ibadat",
            "title_ar": "صلاة الجنازة", "title_en": "The Funeral Prayer", "title_fr": "La prière funéraire",
            "title_fa": "نماز جنازه", "title_ms": "Solat Jenazah", "title_ur": "نماز جنازہ",
            "keywords_ar": "جنازة,ميت,دفن,صلاة,تكبيرات,فرض كفاية",
            "keywords_en": "funeral,death,burial,prayer,takbir,fard kifayah",
            "keywords_fr": "funérailles,mort,enterrement,prière,takbir,fard kifayah",
            "keywords_fa": "جنازه,مرگ,دفن,نماز,تکبیر,فرض کفایه",
            "keywords_ms": "jenazah,kematian,pengebumian,solat,takbir,fardu kifayah",
            "keywords_ur": "جنازہ,موت,تدفین,نماز,تکبیر,فرض کفایہ",
            "ruling_vs_ar": "فرض كفاية", "ruling_s_ar": "فرض كفاية على المسلمين، تسقط بفعل البعض",
            "ruling_f_ar": "صلاة الجنازة فرض كفاية عند جمهور الفقهاء؛ إذا قام بها من يكفي سقط الإثم عن الباقين، وإذا تركها الجميع أثم الجميع. وهي صلاة بلا ركوع ولا سجود، تُؤدى قياماً بعدد من التكبيرات يتفاوت بين المذاهب (أربع تكبيرات عند جمهور أهل السنة، وخمس عند الجعفرية).",
            "ruling_vs_en": "Fard Kifayah", "ruling_s_en": "A collective obligation on Muslims, waived if some perform it",
            "ruling_f_en": "The funeral prayer is a collective obligation (fard kifayah) according to the majority of jurists: if enough people perform it, the sin is lifted from the rest, but if everyone abandons it, all are sinful. It has no bowing or prostration — only standing with a number of takbirs that varies by school (four for most Sunni schools, five for the Ja'fari school).",
            "ruling_vs_fr": "Fard Kifayah", "ruling_s_fr": "Obligation collective, levée si certains l'accomplissent",
            "ruling_f_fr": "La prière funéraire est une obligation collective (fard kifayah) selon la majorité des juristes : si un nombre suffisant de personnes l'accomplit, le péché est levé pour les autres, mais si tous l'abandonnent, tous sont fautifs. Elle ne comporte ni inclinaison ni prosternation — seulement une position debout avec un nombre de takbirs qui varie selon l'école (quatre pour la plupart des écoles sunnites, cinq pour l'école jaafarite).",
            "ruling_vs_fa": "فرض کفایه", "ruling_s_fa": "واجب کفایی بر مسلمانان، با انجام برخی ساقط می‌شود",
            "ruling_f_fa": "نماز جنازه نزد اکثر فقها فرض کفایه است: اگر عده کافی آن را برگزار کنند، گناه از دیگران ساقط می‌شود، ولی اگر همه ترک کنند همه گناهکارند. این نماز بدون رکوع و سجده است و فقط ایستاده با تعدادی تکبیر برگزار می‌شود که بین مذاهب متفاوت است (چهار تکبیر نزد اکثر مذاهب اهل سنت، پنج تکبیر نزد مذهب جعفری).",
            "ruling_vs_ms": "Fardu Kifayah", "ruling_s_ms": "Kewajipan kolektif ke atas umat Islam, gugur jika sebahagian melaksanakannya",
            "ruling_f_ms": "Solat jenazah adalah fardu kifayah menurut majoriti fuqaha: jika sebilangan orang melaksanakannya, dosa gugur bagi yang lain, tetapi jika semua meninggalkannya, semua berdosa. Solat ini tiada rukuk atau sujud — hanya berdiri dengan beberapa takbir yang berbeza mengikut mazhab (empat takbir bagi kebanyakan mazhab Sunni, lima takbir bagi mazhab Jaafari).",
            "ruling_vs_ur": "فرض کفایہ", "ruling_s_ur": "مسلمانوں پر اجتماعی فرض، بعض کے ادا کرنے سے ساقط ہو جاتا ہے",
            "ruling_f_ur": "نماز جنازہ جمہور فقہاء کے نزدیک فرض کفایہ ہے: اگر کافی تعداد ادا کر لے تو باقیوں سے گناہ ساقط ہو جاتا ہے، اور اگر سب چھوڑ دیں تو سب گنہگار ہوں گے۔ اس نماز میں رکوع و سجدہ نہیں ہوتا — صرف قیام کی حالت میں چند تکبیریں ہوتی ہیں جن کی تعداد مذاہب کے درمیان مختلف ہے (جمہور اہل سنت کے نزدیک چار تکبیریں، جعفری مذہب کے نزدیک پانچ)۔",
            "rulings_by_madhab_ar": json.dumps({
                "maliki": {"very_short": "فرض كفاية", "short": "فرض كفاية، تُؤدى بأربع تكبيرات", "full": "فرض كفاية على المسلمين، تُؤدى بأربع تكبيرات دون ركوع أو سجود، ويُدعى فيها للميت بعد كل تكبيرة."},
                "shafii": {"very_short": "فرض كفاية", "short": "فرض كفاية بأربع تكبيرات، تُقرأ الفاتحة بعد الأولى", "full": "فرض كفاية بأربع تكبيرات؛ تُقرأ بعد التكبيرة الأولى الفاتحة، وبعد الثانية الصلاة على النبي ﷺ، وبعد الثالثة الدعاء للميت."},
                "hanafi": {"very_short": "فرض كفاية", "short": "فرض كفاية بأربع تكبيرات دون قراءة الفاتحة", "full": "فرض كفاية بأربع تكبيرات، ولا تُقرأ فيها الفاتحة عند الحنفية بل يُكتفى بالثناء والدعاء بعد كل تكبيرة."},
                "hanbali": {"very_short": "فرض كفاية", "short": "فرض كفاية بأربع تكبيرات، مع قراءة الفاتحة", "full": "فرض كفاية بأربع تكبيرات، تُقرأ بعد الأولى الفاتحة سراً، ثم الصلاة على النبي ﷺ، ثم الدعاء للميت."},
                "zahiri": {"very_short": "فرض كفاية", "short": "فرض كفاية أخذاً بظاهر الأحاديث الواردة", "full": "فرض كفاية أخذاً بظاهر الأحاديث الواردة عن النبي ﷺ في صفتها، دون زيادة عليها أو قياس."},
                "jafari": {"very_short": "واجب كفائي", "short": "واجب كفائي بخمس تكبيرات دون ركوع أو سجود", "full": "واجب كفائي على المسلمين؛ تُؤدى بخمس تكبيرات، يتخللها الشهادتان والصلاة على النبي وآله والدعاء للمؤمنين والميت، دون ركوع أو سجود."},
                "zaidi": {"very_short": "فرض كفاية", "short": "قريب من الرأي السني، غالباً بأربع تكبيرات", "full": "فرض كفاية، ويقترب الرأي الزيدي في صفتها من الرأي السني، وتُؤدى غالباً بأربع تكبيرات."},
                "ibadi": {"very_short": "فرض كفاية", "short": "فرض كفاية دون ركوع أو سجود", "full": "فرض كفاية على المسلمين، تُؤدى قياماً دون ركوع أو سجود، بعدد من التكبيرات يقارب المعروف عند جمهور المذاهب."}
            }),
            "rulings_by_madhab_en": "{}",
            "rulings_by_madhab_fr": "{}",
            "rulings_by_madhab_fa": "{}",
            "rulings_by_madhab_ms": "{}",
            "rulings_by_madhab_ur": "{}"
        },
        {
            "topic": "muamalat",
            "title_ar": "الربا", "title_en": "Riba (Usury/Interest)", "title_fr": "Riba (Usure/Intérêt)",
            "title_fa": "ربا", "title_ms": "Riba", "title_ur": "سود (ربا)",
            "keywords_ar": "ربا,حرام,قرض,فائدة,بنوك,معاملة",
            "keywords_en": "riba,usury,forbidden,loan,interest,banks,transaction",
            "keywords_fr": "riba,usure,interdit,prêt,intérêt,banques,transaction",
            "keywords_fa": "ربا,حرام,قرض,سود,بانک,معامله",
            "keywords_ms": "riba,haram,pinjaman,faedah,bank,muamalat",
            "keywords_ur": "سود,ربا,حرام,قرض,بینک,معاملہ",
            "ruling_vs_ar": "حرام", "ruling_s_ar": "الربا من كبائر الذنوب ومحرم قطعاً",
            "ruling_f_ar": "الربا محرم بنص القرآن والسنة، وهو كل زيادة مشروطة في القرض أو المعاملة، سواء كانت نقدية أو عينية. الربا من السبع الموبقات.",
            "ruling_vs_en": "Forbidden", "ruling_s_en": "Riba is a major sin and unequivocally forbidden",
            "ruling_f_en": "Riba is forbidden by explicit Qur'anic and Prophetic text; it is any conditional increase in a loan or transaction, whether monetary or in kind. Riba is one of the seven destructive major sins.",
            "ruling_vs_fr": "Interdit", "ruling_s_fr": "Le riba est un péché majeur et formellement interdit",
            "ruling_f_fr": "Le riba est interdit par un texte explicite du Coran et de la Sunna ; c'est tout surplus conditionnel dans un prêt ou une transaction, monétaire ou en nature. Le riba fait partie des sept péchés capitaux destructeurs.",
            "ruling_vs_fa": "حرام", "ruling_s_fa": "ربا از گناهان کبیره و قطعاً حرام است",
            "ruling_f_fa": "ربا به نص قرآن و سنت حرام است، و آن هر افزایش مشروط در قرض یا معامله است، خواه نقدی باشد یا جنسی. ربا از هفت گناه کبیره است.",
            "ruling_vs_ms": "Haram", "ruling_s_ms": "Riba tergolong dosa besar dan haram secara pasti",
            "ruling_f_ms": "Riba diharamkan berdasarkan nas al-Quran dan sunnah; ia adalah sebarang tambahan bersyarat dalam pinjaman atau muamalat, sama ada berbentuk wang atau barangan. Riba termasuk salah satu daripada tujuh dosa besar.",
            "ruling_vs_ur": "حرام", "ruling_s_ur": "سود کبیرہ گناہوں میں سے ہے اور قطعی طور پر حرام ہے",
            "ruling_f_ur": "سود قرآن و سنت کی صریح نصوص سے حرام ہے، اور یہ قرض یا معاملے میں کوئی بھی مشروط اضافہ ہے، خواہ نقدی ہو یا جنسی۔ سود سات ہلاک کرنے والے کبیرہ گناہوں میں سے ایک ہے۔",
            "rulings_by_madhab_ar": json.dumps({
                "maliki": {"very_short": "حرام", "short": "حرام قطعاً، مع تفصيل معروف في الأصناف الستة الربوية", "full": "الربا محرم إجماعاً؛ وللمالكية تفصيل معروف في علة ربا الفضل ضمن الأصناف الستة الواردة في الحديث (الذهب، الفضة، البر، الشعير، التمر، الملح)."},
                "shafii": {"very_short": "حرام", "short": "حرام قطعاً بنص القرآن والسنة", "full": "الربا محرم إجماعاً؛ ويُفرّق الشافعية بين ربا الفضل وربا النسيئة، مع ضوابط دقيقة في تحديد علة الربا في الأموال الربوية."},
                "hanafi": {"very_short": "حرام", "short": "حرام قطعاً، مع توسع معروف في تطبيق العلة", "full": "الربا محرم إجماعاً؛ وللحنفية توسع معروف في تطبيق علة الربا على كل موزون أو مكيل من جنس واحد، أوسع من غيرهم."},
                "hanbali": {"very_short": "حرام", "short": "حرام قطعاً، مع التزام صارم بظاهر النصوص", "full": "الربا محرم إجماعاً، ويتميز الحنابلة بالتزام صارم بظاهر الأحاديث الواردة في تحديد الأصناف الربوية."},
                "zahiri": {"very_short": "حرام", "short": "حرام قطعاً، اقتصاراً على الأصناف الستة المنصوصة فقط", "full": "الربا محرم إجماعاً؛ ويقتصر الظاهرية على الأصناف الستة الواردة نصاً في الحديث دون قياس عليها لأصناف أخرى."},
                "jafari": {"very_short": "حرام", "short": "حرام قطعاً، من كبائر الذنوب", "full": "الربا محرم إجماعاً ومن كبائر الذنوب عند الجعفرية؛ مع اجتهادات معاصرة حول بعض صور التعامل مع المصارف."},
                "zaidi": {"very_short": "حرام", "short": "حرام قطعاً، قريب من رأي جمهور أهل السنة", "full": "الربا محرم إجماعاً، ويقترب الرأي الزيدي في تفاصيله من رأي جمهور أهل السنة."},
                "ibadi": {"very_short": "حرام", "short": "حرام قطعاً بإجماع المذاهب", "full": "الربا محرم إجماعاً عند الإباضية كسائر المذاهب، بلا خلاف يُذكر في أصل التحريم."}
            }),
            "rulings_by_madhab_en": "{}",
            "rulings_by_madhab_fr": "{}",
            "rulings_by_madhab_fa": "{}",
            "rulings_by_madhab_ms": "{}",
            "rulings_by_madhab_ur": "{}"
        }
    ]
    for issue in issues:
        c.execute("SELECT COUNT(*) FROM issues WHERE title_ar = ?", (issue["title_ar"],))
        if c.fetchone()[0] > 0:
            continue  # موجودة مسبقاً — لا تُضاف مرة أخرى (يمنع التكرار عند إعادة التشغيل)
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
            issue["topic"], issue["title_ar"], issue["title_en"], issue["title_fr"], issue["title_fa"], issue["title_ms"], issue["title_ur"],
            issue["keywords_ar"], issue["keywords_en"], issue["keywords_fr"], issue["keywords_fa"], issue["keywords_ms"], issue["keywords_ur"],
            issue["ruling_vs_ar"], issue["ruling_s_ar"], issue["ruling_f_ar"],
            issue["ruling_vs_en"], issue["ruling_s_en"], issue["ruling_f_en"],
            issue["ruling_vs_fr"], issue["ruling_s_fr"], issue["ruling_f_fr"],
            issue["ruling_vs_fa"], issue["ruling_s_fa"], issue["ruling_f_fa"],
            issue["ruling_vs_ms"], issue["ruling_s_ms"], issue["ruling_f_ms"],
            issue["ruling_vs_ur"], issue["ruling_s_ur"], issue["ruling_f_ur"],
            issue["rulings_by_madhab_ar"], issue["rulings_by_madhab_en"], issue["rulings_by_madhab_fr"],
            issue["rulings_by_madhab_fa"], issue["rulings_by_madhab_ms"], issue["rulings_by_madhab_ur"]
        ))
    conn.commit()
    conn.close()

def load_issues(lang, topic_filter="all"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    lang_suffix = lang
    query = f'''
        SELECT id, topic, title_{lang_suffix}, keywords_{lang_suffix},
               ruling_vs_{lang_suffix}, ruling_s_{lang_suffix}, ruling_f_{lang_suffix},
               rulings_by_madhab_{lang_suffix}
        FROM issues
    '''
    params = ()
    if topic_filter != "all":
        query += " WHERE topic = ?"
        params = (topic_filter,)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    issues = []
    for row in rows:
        kw = row[3].split(',') if row[3] else []
        issues.append({
            "id": row[0],
            "topic": row[1],
            "title": row[2],
            "keywords": [k.strip() for k in kw if k.strip()],
            "rulings": {
                "very_short": row[4],
                "short": row[5],
                "full": row[6]
            },
            "rulings_by_madhab": json.loads(row[7]) if row[7] else {}
        })
    return issues

def import_from_csv(csv_content):
    conn = sqlite3.connect(DB_PATH)
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
            row.get("title_ar", ""), row.get("title_en", ""), row.get("title_fr", ""), row.get("title_fa", ""), row.get("title_ms", ""), row.get("title_ur", ""),
            row.get("keywords_ar", ""), row.get("keywords_en", ""), row.get("keywords_fr", ""), row.get("keywords_fa", ""), row.get("keywords_ms", ""), row.get("keywords_ur", ""),
            row.get("ruling_vs_ar", ""), row.get("ruling_s_ar", ""), row.get("ruling_f_ar", ""),
            row.get("ruling_vs_en", ""), row.get("ruling_s_en", ""), row.get("ruling_f_en", ""),
            row.get("ruling_vs_fr", ""), row.get("ruling_s_fr", ""), row.get("ruling_f_fr", ""),
            row.get("ruling_vs_fa", ""), row.get("ruling_s_fa", ""), row.get("ruling_f_fa", ""),
            row.get("ruling_vs_ms", ""), row.get("ruling_s_ms", ""), row.get("ruling_f_ms", ""),
            row.get("ruling_vs_ur", ""), row.get("ruling_s_ur", ""), row.get("ruling_f_ur", ""),
            row.get("rulings_by_madhab_ar", "{}"), row.get("rulings_by_madhab_en", "{}"), row.get("rulings_by_madhab_fr", "{}"),
            row.get("rulings_by_madhab_fa", "{}"), row.get("rulings_by_madhab_ms", "{}"), row.get("rulings_by_madhab_ur", "{}")
        ))
        count += 1
    conn.commit()
    conn.close()
    return count

# =====================================================================
# 3a) محرك الاسترجاع الدلالي من المراجع المرفوعة (RAG)
#     الفكرة: يرفع المشرف نصوص مراجع فعلية يملك حقوق استخدامها. تُقسَّم
#     إلى مقاطع صغيرة، ويُحسب لكل مقطع تمثيل رقمي (embedding) مرة واحدة
#     عند الرفع ويُخزَّن. عند كل سؤال، يُحسب تمثيل السؤال فقط (سريع جداً)
#     وتُقارن به كل المقاطع المخزّنة رياضياً (تشابه جيب التمام) لإيجاد
#     الأقرب دلالياً في أجزاء من الثانية، ثم تُمرَّر تلك المقاطع فقط
#     للذكاء الاصطناعي ليبني إجابته عليها ويستشهد بمصدرها — بدل توليد
#     إجابة من الذاكرة العامة للنموذج.
# =====================================================================
import numpy as np

EMBED_MODEL = "models/text-embedding-004"

def chunk_text(text, max_chars=700, overlap=100):
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if len(c) > 30]

def embed_texts(texts, task_type="retrieval_document"):
    """يُرجع قائمة متجهات embedding لكل نص، أو None إن تعذّر (لا مفتاح/لا مكتبة)."""
    if not USE_GEMINI or not texts:
        return None
    try:
        vectors = []
        for t in texts:
            result = genai.embed_content(model=EMBED_MODEL, content=t, task_type=task_type)
            vectors.append(result["embedding"])
        return vectors
    except Exception:
        return None

def add_reference_document(title, madhab_tag, raw_text):
    """يقسّم نصاً مرجعياً إلى مقاطع، يحسب embedding لكل مقطع، ويخزّنها. يُرجع عدد المقاطع المضافة أو -1 عند الفشل."""
    chunks = chunk_text(raw_text)
    if not chunks:
        return 0
    vectors = embed_texts(chunks, task_type="retrieval_document")
    if vectors is None:
        return -1
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for chunk, vec in zip(chunks, vectors):
        c.execute(
            "INSERT INTO reference_chunks (source_title, madhab_tag, chunk_text, embedding, added_at) VALUES (?,?,?,?,?)",
            (title, madhab_tag or "", chunk, json.dumps(vec), now),
        )
    conn.commit()
    conn.close()
    return len(chunks)

def count_reference_chunks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM reference_chunks")
    n = c.fetchone()[0]
    conn.close()
    return n

def list_reference_sources():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT source_title, COUNT(*) FROM reference_chunks GROUP BY source_title")
    rows = c.fetchall()
    conn.close()
    return rows

def retrieve_relevant_chunks(query, top_k=5, min_similarity=0.55):
    """يسترجع أقرب المقاطع دلالياً لسؤال المستخدم خلال أجزاء من الثانية
    (تشابه جيب التمام على متجهات محسوبة مسبقاً)، أو [] إن لم تتوفر مراجع
    أو تعذّر حساب تمثيل السؤال."""
    total = count_reference_chunks()
    if total == 0:
        return []
    q_vec = embed_texts([query], task_type="retrieval_query")
    if not q_vec:
        return []
    q_vec = np.array(q_vec[0])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, source_title, madhab_tag, chunk_text, embedding FROM reference_chunks")
    rows = c.fetchall()
    conn.close()

    scored = []
    for row_id, title, tag, chunk, emb_json in rows:
        vec = np.array(json.loads(emb_json))
        denom = (np.linalg.norm(q_vec) * np.linalg.norm(vec))
        sim = float(np.dot(q_vec, vec) / denom) if denom else 0.0
        if sim >= min_similarity:
            scored.append({"title": title, "tag": tag, "chunk": chunk, "score": sim})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def rag_generate_answer(question, lang, madhab_codes, level, T):
    """يبني إجابة بالاستناد الحصري إلى المقاطع المسترجعة من المراجع
    المرفوعة، مع الاستشهاد بعنوان المصدر لكل مذهب. يُرجع None إن لم
    توجد مقاطع ذات صلة كافية (فيتحول البحث تلقائياً لطبقة التوليد
    الحر التالية)."""
    if not USE_GEMINI:
        return None
    chunks = retrieve_relevant_chunks(question, top_k=6)
    if not chunks:
        return None

    context_block = "\n\n".join(f"[{i+1}] (المصدر: {c['title']}) {c['chunk']}" for i, c in enumerate(chunks))
    madhab_list_str = ", ".join(f"{code} ({MADHHAB_NAMES[code][lang]})" for code in madhab_codes)
    level_hint = {
        "very_short": "كلمة أو كلمتين فقط",
        "short": "سطر واحد مختصر",
        "full": "فقرة قصيرة من سطرين إلى أربعة أسطر",
    }.get(level, "سطر واحد مختصر")

    prompt = f"""
أنت مساعد بحثي. لديك مقاطع مسترجعة من مراجع فقهية فعلية رفعها المشرف (مذكورة أدناه مع أرقامها ومصادرها). اعتمد حصرياً على هذه المقاطع في إجابتك، ولا تضف معلومات من خارجها.

المقاطع المرجعية:
{context_block}

سؤال المستخدم: "{question}"

المطلوب: لكل مذهب من المذاهب التالية: {madhab_list_str}
- إن كانت المقاطع أعلاه تتضمن ما يخص هذا المذهب في هذه المسألة، لخّص رأيه المستفاد منها حصراً، بمستوى تفصيل: {level_hint}، مع الإشارة لرقم المقطع المصدر مثل [1].
- إن كانت المقاطع لا تتضمن شيئاً عن هذا المذهب في هذه المسألة تحديداً، اكتب حرفياً: "لا يوجد في المراجع المرفوعة ما يخص هذا المذهب في هذه المسألة."

اكتب النص بلغة رمزها ISO: "{lang}"

أخرج النتيجة بصيغة JSON فقط بلا أي شرح إضافي، بهذا الشكل بالضبط: {{"maliki": "نص الإجابة مع [رقم المصدر]", "shafii": "..."}}
"""
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        data = json.loads(raw[json_start:json_end])
        cards = []
        sources_used = sorted({c["title"] for c in chunks})
        for code in madhab_codes:
            answer = data.get(code)
            if answer and "لا يوجد في المراجع" not in answer:
                cards.append({
                    "label": MADHHAB_NAMES[code][lang],
                    "answer": answer,
                    "note": T["rag_badge"].format(", ".join(sources_used)),
                })
        return cards if cards else None
    except Exception:
        return None

# =====================================================================
# 3b) SEMANTIC SEARCH ضمن قاعدة البيانات (GEMINI)
# =====================================================================
def semantic_search(query, issues, lang):
    if not USE_GEMINI or not issues:
        return None
    titles_with_ids = [f"{issue['id']}: {issue['title']}" for issue in issues]
    prompt = f"""
    أنت مساعد فقهي. لديك قائمة بعناوين مسائل فقهية. سؤال المستخدم: "{query}".

    قائمة العناوين (مع أرقامها):
    {chr(10).join(titles_with_ids)}

    المطلوب: حدد ما يصل إلى 3 عناوين من القائمة هي الأقرب لسؤال المستخدم.
    أخرج النتيجة على شكل قائمة بأرقام المسائل مفصولة بفواصل (مثال: 3, 7, 12).
    إذا لم تجد أي تطابق، اكتب "لا يوجد".
    """
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        if result == "لا يوجد":
            return []
        ids = re.findall(r'\d+', result)
        return [int(id) for id in ids[:3]]
    except Exception:
        return None

# =====================================================================
# 3b) توليد إجابة حرة بالذكاء الاصطناعي عندما لا توجد مسألة مطابقة في
#     قاعدة البيانات الموثقة. هذه الإجابات تُعرض دائماً موسومة بوضوح
#     كمحتوى غير مُراجَع من عالم شرعي — وليست بديلاً عن قاعدة البيانات،
#     بل حل احتياطي فقط عند عدم وجود تطابق.
# =====================================================================
def ai_generate_answer(question, lang, madhab_codes, level, T):
    if not USE_GEMINI or not madhab_codes:
        return None

    madhab_list_str = ", ".join(f"{code} ({MADHHAB_NAMES[code][lang]})" for code in madhab_codes)
    level_hint = {
        "very_short": "كلمة أو كلمتين فقط",
        "short": "سطر واحد مختصر",
        "full": "فقرة قصيرة من سطرين إلى أربعة أسطر",
    }.get(level, "سطر واحد مختصر")

    prompt = f"""
أنت مساعد بحثي متخصص في عرض آراء المذاهب الفقهية الإسلامية المعروفة والموثقة تاريخياً في كتب كل مذهب المعتمدة. أنت لا تُصدر فتوى شخصية، ولا تخترع رأياً غير موثق لمذهب معين.

سؤال المستخدم: "{question}"

المطلوب: لكل مذهب من المذاهب التالية، اذكر رأيه الفقهي المعروف (إن وُجد رأي موثق) في هذه المسألة تحديداً:
{madhab_list_str}

مستوى التفصيل المطلوب لكل إجابة: {level_hint}
اكتب نص كل إجابة بلغة رمزها ISO: "{lang}"

قاعدة صارمة: إن لم يكن هناك رأي معروف وموثق لمذهب معين في هذه المسألة تحديداً (خصوصاً في المسائل المستحدثة/المعاصرة التي لم يتناولها فقهاء المذهب الكلاسيكيون)، اكتب صراحة في تلك الحقلة أنه لا يوجد رأي موثق متاح، بدل اختلاق رأي أو تخمينه.

أخرج النتيجة بصيغة JSON فقط، بلا أي نص أو شرح إضافي قبله أو بعده، وبهذا الشكل بالضبط (استخدم رموز المذاهب اللاتينية التالية حرفياً كمفاتيح): {{"maliki": "نص الإجابة", "shafii": "نص الإجابة"}}
"""
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        data = json.loads(raw[json_start:json_end])
        cards = []
        for code in madhab_codes:
            answer = data.get(code)
            if answer:
                cards.append({
                    "label": MADHHAB_NAMES[code][lang],
                    "answer": answer,
                    "note": T["ai_badge"],
                })
        return cards if cards else None
    except Exception:
        return None

# =====================================================================
# 4) SEARCH LOGIC (قاعدة البيانات الموثقة فقط)
# =====================================================================
def search_issues(query, topic_filter, madhabs, level, lang, T, MADHHAB_NAMES, TOPICS):
    if not query:
        return []
    all_issues = load_issues(lang, topic_filter)
    if not all_issues:
        return []
    q = query.strip().lower()

    semantic_ids = None
    if USE_GEMINI:
        semantic_ids = semantic_search(q, all_issues, lang)

    results = []
    if semantic_ids is not None:
        for id in semantic_ids:
            issue = next((i for i in all_issues if i["id"] == id), None)
            if issue and issue not in results:
                results.append(issue)

    if not results:
        for issue in all_issues:
            pool = (issue["title"].lower() + " " +
                    " ".join(issue["keywords"]).lower() + " " +
                    issue["rulings"]["full"].lower())
            if q in pool:
                results.append(issue)
        if not results:
            words = re.findall(r"\w+", q)
            for issue in all_issues:
                pool = issue["title"].lower() + " " + " ".join(issue["keywords"]).lower()
                if any(w in pool for w in words):
                    results.append(issue)

    final_results = []
    for issue in results:
        cards = []
        per_madhab = issue.get("rulings_by_madhab", {})
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
                "label": TOPICS[issue["topic"]][lang],
                "answer": issue["rulings"].get(level, issue["rulings"]["full"]),
                "note": T["note_general"],
            })
        final_results.append({
            "title": issue["title"],
            "topic": TOPICS[issue["topic"]][lang],
            "cards": cards,
        })
    return final_results

# =====================================================================
# 5) UI DATA (Translations, Madhhabs, etc.)
# =====================================================================
LANGS = {"العربية": "ar", "English": "en", "Français": "fr", "فارسی": "fa", "Bahasa Melayu": "ms", "اردو": "ur"}

UI = {
    "ar": {
        "app_title": "الجامع المختصر لآراء المذاهب",
        "app_subtitle": "منصة لعرض ومقارنة آراء المذاهب الفقهية — للفهم والتبصر، وليست موقع إفتاء.",
        "lang_label": "اللغة",
        "s1_title": "١ — اختر المذهب",
        "group_q": "مذاهب السنة، أم مذاهب الشيعة، أم المذهب الإباضي؟",
        "multi_hint": "💡 يمكنك اختيار أكثر من مذهب لعرض إجاباتها جنباً إلى جنب للمقارنة.",
        "sub_select": "اختر مذهباً واحداً أو أكثر:",
        "s2_title": "٢ — اختر الموضوع",
        "topic_q": "اختر الموضوع الفقهي",
        "s3_title": "٣ — طريقة عرض الإجابة",
        "level_q": "اختر مستوى التفصيل",
        "s4_title": "٤ — اكتب سؤالك",
        "question_placeholder": "مثال: ما حكم صلاة الجماعة؟",
        "search_btn": "🔍 ابحث عن الإجابة",
        "s5_title": "٥ — الإجابة",
        "answer_placeholder": "ستظهر الإجابة هنا بعد كتابة السؤال والضغط على زر البحث.",
        "no_question_warning": "الرجاء كتابة سؤالك أولاً في الفقرة الرابعة.",
        "no_madhab_warning": "الرجاء اختيار مذهب واحد على الأقل.",
        "no_results_warning": "🔍 لم نجد مسألة بهذا الوصف ضمن الموضوع المختار، وتعذّر توليد إجابة بالذكاء الاصطناعي. جرّب صياغة أخرى.",
        "signature": "هذا والله أعلم",
        "note_general": "رأي عام موحّد — لم يُفصّل بعد لكل مذهب",
        "note_madhab": "رأي المذهب {}",
        "ai_badge": "🤖 إجابة الذكاء الاصطناعي",
        "ai_disclaimer": "⚠️ هذه إجابة ولّدها الذكاء الاصطناعي تلقائياً لعدم وجود هذه المسألة في قاعدة البيانات الموثقة. إنها ليست فتوى ولم تُراجع من عالم شرعي؛ يُرجى التحقق من مصدر موثوق أو استشارة أهل العلم قبل العمل بها.",
        "ai_generating": "🤖 جاري توليد إجابة بالذكاء الاصطناعي...",
        "ai_unavailable": "ميزة الإجابة التلقائية بالذكاء الاصطناعي غير مفعّلة حالياً (لم يُضبط مفتاح Gemini API).",
        "rag_badge": "📖 مبني على المراجع المرفوعة ({})",
        "rag_expander": "📁 إدارة المراجع (RAG) — للمشرفين",
        "rag_intro": "ارفع نصوص مراجع فقهية تملك حقوق استخدامها؛ سيُقسّمها النظام إلى مقاطع ويبحث فيها دلالياً قبل أي توليد حر بالذكاء الاصطناعي.",
        "rag_title_label": "عنوان المصدر",
        "rag_madhab_label": "المذهب (اختياري)",
        "rag_text_label": "الصق النص هنا، أو ارفع ملف .txt",
        "rag_file_label": "أو ارفع ملف نصي (.txt)",
        "rag_submit": "إضافة المرجع وفهرسته",
        "rag_processing": "جاري تقسيم النص وحساب التمثيل الرقمي للمقاطع...",
        "rag_success": "✅ أُضيف {} مقطعاً من «{}» إلى فهرس المراجع.",
        "rag_empty_warning": "⚠️ الرجاء لصق نص أو رفع ملف قبل الإضافة.",
        "rag_failed": "❌ تعذّر فهرسة المرجع (تحقق من مفتاح Gemini API).",
        "rag_current_sources": "المصادر المفهرسة حالياً:",
        "rag_no_sources": "لا توجد مراجع مفهرسة بعد.",
        "expander_imams": "📜 الأئمة المؤسسون للمذاهب",
        "expander_countries": "🗺️ الدول الإسلامية والمذهب الرسمي السائد",
        "expander_glossary": "📚 مصطلحات فقهية رئيسية",
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
    },
    "en": {
        "app_title": "The Concise Compendium of Madhhab Opinions",
        "app_subtitle": "A platform for presenting and comparing juristic (fiqh) opinions — for understanding, not for issuing formal rulings (fatwas).",
        "lang_label": "Language",
        "s1_title": "1 — Choose the Madhhab",
        "group_q": "Sunni schools, Shia schools, or the Ibadi school?",
        "multi_hint": "💡 You can select more than one school to compare their answers side by side.",
        "sub_select": "Choose one or more schools:",
        "s2_title": "2 — Choose the Topic",
        "topic_q": "Choose a fiqh topic",
        "s3_title": "3 — Answer Detail Level",
        "level_q": "Choose the level of detail",
        "s4_title": "4 — Type Your Question",
        "question_placeholder": "Example: What is the ruling on congregational prayer?",
        "search_btn": "🔍 Search for the Ruling",
        "s5_title": "5 — The Answer",
        "answer_placeholder": "The answer will appear here after you type a question and press search.",
        "no_question_warning": "Please type your question first in section 4.",
        "no_madhab_warning": "Please select at least one school.",
        "no_results_warning": "🔍 No matching issue was found, and an AI answer could not be generated. Try rephrasing.",
        "signature": "And God knows best",
        "note_general": "A general, unified opinion — not yet detailed per school",
        "note_madhab": "Opinion of the {} school",
        "ai_badge": "🤖 AI-generated answer",
        "ai_disclaimer": "⚠️ This answer was generated automatically by AI because this issue isn't in the verified database yet. It is not a fatwa and has not been reviewed by a scholar; please verify with a trusted source or a qualified scholar before acting on it.",
        "ai_generating": "🤖 Generating an AI answer...",
        "ai_unavailable": "Automatic AI answering is currently disabled (no Gemini API key configured).",
        "rag_badge": "📖 Based on uploaded references ({})",
        "rag_expander": "📁 Manage References (RAG) — Admins",
        "rag_intro": "Upload fiqh reference texts you have rights to use; the system will chunk them and search semantically before falling back to free AI generation.",
        "rag_title_label": "Source title",
        "rag_madhab_label": "Madhhab (optional)",
        "rag_text_label": "Paste the text here, or upload a .txt file",
        "rag_file_label": "Or upload a text file (.txt)",
        "rag_submit": "Add and Index Reference",
        "rag_processing": "Chunking text and computing embeddings...",
        "rag_success": "✅ Added {} chunks from \"{}\" to the reference index.",
        "rag_empty_warning": "⚠️ Please paste text or upload a file before adding.",
        "rag_failed": "❌ Failed to index the reference (check your Gemini API key).",
        "rag_current_sources": "Currently indexed sources:",
        "rag_no_sources": "No references indexed yet.",
        "expander_imams": "📜 The Founding Imams of the Schools",
        "expander_countries": "🗺️ Muslim-Majority Countries & Their Prevailing Official School",
        "expander_glossary": "📚 Key Juristic Terms",
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
    },
    "fr": {
        "app_title": "Le Recueil Concis des Avis des Écoles Juridiques",
        "app_subtitle": "Une plateforme pour présenter et comparer les avis juridiques (fiqh) — pour la compréhension, non pour émettre des fatwas.",
        "lang_label": "Langue",
        "s1_title": "1 — Choisir l'école juridique",
        "group_q": "Écoles sunnites, écoles chiites, ou école ibadite ?",
        "multi_hint": "💡 Vous pouvez sélectionner plusieurs écoles pour comparer leurs réponses côte à côte.",
        "sub_select": "Choisissez une ou plusieurs écoles :",
        "s2_title": "2 — Choisir le sujet",
        "topic_q": "Choisissez un sujet de fiqh",
        "s3_title": "3 — Niveau de détail de la réponse",
        "level_q": "Choisissez le niveau de détail",
        "s4_title": "4 — Écrivez votre question",
        "question_placeholder": "Exemple : Quel est le statut de la prière en congrégation ?",
        "search_btn": "🔍 Rechercher la réponse",
        "s5_title": "5 — La réponse",
        "answer_placeholder": "La réponse apparaîtra ici après avoir écrit une question et appuyé sur rechercher.",
        "no_question_warning": "Veuillez d'abord écrire votre question à la section 4.",
        "no_madhab_warning": "Veuillez sélectionner au moins une école.",
        "no_results_warning": "🔍 Aucune question correspondante trouvée, et impossible de générer une réponse par IA. Essayez une autre formulation.",
        "signature": "Et Dieu est plus savant",
        "note_general": "Avis général unifié — pas encore détaillé par école",
        "note_madhab": "Avis de l'école {}",
        "ai_badge": "🤖 Réponse générée par l'IA",
        "ai_disclaimer": "⚠️ Cette réponse a été générée automatiquement par l'IA car cette question ne figure pas encore dans la base de données vérifiée. Ce n'est pas une fatwa et elle n'a pas été révisée par un érudit ; veuillez vérifier auprès d'une source fiable ou d'un savant qualifié avant d'agir en conséquence.",
        "ai_generating": "🤖 Génération d'une réponse par IA...",
        "ai_unavailable": "La réponse automatique par IA est actuellement désactivée (aucune clé API Gemini configurée).",
        "rag_badge": "📖 Basé sur les références téléversées ({})",
        "rag_expander": "📁 Gérer les références (RAG) — Administrateurs",
        "rag_intro": "Téléversez des textes de référence en fiqh dont vous avez les droits d'utilisation ; le système les découpera et les recherchera sémantiquement avant de recourir à la génération IA libre.",
        "rag_title_label": "Titre de la source",
        "rag_madhab_label": "Madhhab (optionnel)",
        "rag_text_label": "Collez le texte ici, ou téléversez un fichier .txt",
        "rag_file_label": "Ou téléversez un fichier texte (.txt)",
        "rag_submit": "Ajouter et indexer la référence",
        "rag_processing": "Découpage du texte et calcul des vecteurs...",
        "rag_success": "✅ {} extraits de « {} » ajoutés à l'index des références.",
        "rag_empty_warning": "⚠️ Veuillez coller du texte ou téléverser un fichier avant d'ajouter.",
        "rag_failed": "❌ Échec de l'indexation de la référence (vérifiez votre clé API Gemini).",
        "rag_current_sources": "Sources actuellement indexées :",
        "rag_no_sources": "Aucune référence indexée pour le moment.",
        "expander_imams": "📜 Les Imams Fondateurs des Écoles",
        "expander_countries": "🗺️ Pays à Majorité Musulmane et Leur École Officielle Dominante",
        "expander_glossary": "📚 Termes Juridiques Clés",
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
    },
    "fa": {
        "app_title": "جامع مختصر آراء مذاهب",
        "app_subtitle": "پلتفرمی برای نمایش و مقایسه آراء فقهی مذاهب — برای فهم و بصیرت، نه صدور فتوا.",
        "lang_label": "زبان",
        "s1_title": "۱ — انتخاب مذهب",
        "group_q": "مذاهب اهل سنت، مذاهب شیعه، یا مذهب اباضی؟",
        "multi_hint": "💡 می‌توانید بیش از یک مذهب را برای مقایسه پاسخ‌ها انتخاب کنید.",
        "sub_select": "یک یا چند مذهب را انتخاب کنید:",
        "s2_title": "۲ — انتخاب موضوع",
        "topic_q": "موضوع فقهی را انتخاب کنید",
        "s3_title": "۳ — سطح نمایش پاسخ",
        "level_q": "سطح جزئیات را انتخاب کنید",
        "s4_title": "۴ — سوال خود را بنویسید",
        "question_placeholder": "مثال: حکم نماز جماعت چیست؟",
        "search_btn": "🔍 جستجوی پاسخ",
        "s5_title": "۵ — پاسخ",
        "answer_placeholder": "پاسخ پس از نوشتن سوال و کلیک روی جستجو نمایش داده می‌شود.",
        "no_question_warning": "لطفاً ابتدا سوال خود را در بخش ۴ بنویسید.",
        "no_madhab_warning": "لطفاً حداقل یک مذهب را انتخاب کنید.",
        "no_results_warning": "🔍 هیچ مسئله‌ای یافت نشد و تولید پاسخ با هوش مصنوعی ممکن نشد. عبارت دیگری را امتحان کنید.",
        "signature": "والله اعلم",
        "note_general": "نظر عمومی واحد — هنوز به‌تفکیک مذهب نیست",
        "note_madhab": "نظر مذهب {}",
        "ai_badge": "🤖 پاسخ تولیدشده توسط هوش مصنوعی",
        "ai_disclaimer": "⚠️ این پاسخ به‌طور خودکار توسط هوش مصنوعی تولید شده زیرا این مسئله هنوز در پایگاه داده تأییدشده موجود نیست. این فتوا نیست و توسط یک عالم دینی بررسی نشده است؛ لطفاً پیش از عمل به آن، از منبع معتبر یا عالم مختص استعلام کنید.",
        "ai_generating": "🤖 در حال تولید پاسخ با هوش مصنوعی...",
        "ai_unavailable": "پاسخ خودکار با هوش مصنوعی در حال حاضر غیرفعال است (کلید Gemini API تنظیم نشده است).",
        "rag_badge": "📖 بر اساس مراجع بارگذاری‌شده ({})",
        "rag_expander": "📁 مدیریت مراجع (RAG) — مدیران",
        "rag_intro": "متون مرجع فقهی که حق استفاده از آن‌ها را دارید بارگذاری کنید؛ سیستم آن‌ها را به بخش‌هایی تقسیم کرده و پیش از تولید آزاد هوش مصنوعی، در آن‌ها جستجوی معنایی می‌کند.",
        "rag_title_label": "عنوان منبع",
        "rag_madhab_label": "مذهب (اختیاری)",
        "rag_text_label": "متن را اینجا جای‌گذاری کنید، یا فایل .txt بارگذاری کنید",
        "rag_file_label": "یا یک فایل متنی (.txt) بارگذاری کنید",
        "rag_submit": "افزودن و فهرست‌بندی منبع",
        "rag_processing": "در حال تقسیم متن و محاسبه بردارها...",
        "rag_success": "✅ {} بخش از «{}» به فهرست مراجع افزوده شد.",
        "rag_empty_warning": "⚠️ لطفاً پیش از افزودن، متنی جای‌گذاری یا فایلی بارگذاری کنید.",
        "rag_failed": "❌ فهرست‌بندی منبع ناموفق بود (کلید Gemini API را بررسی کنید).",
        "rag_current_sources": "منابع فهرست‌شده فعلی:",
        "rag_no_sources": "هنوز هیچ منبعی فهرست نشده است.",
        "expander_imams": "📜 ائمه مؤسس مذاهب",
        "expander_countries": "🗺️ کشورهای اسلامی و مذهب رسمی",
        "expander_glossary": "📚 اصطلاحات کلیدی فقهی",
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
    },
    "ms": {
        "app_title": "Himpunan Ringkas Pendapat Mazhab",
        "app_subtitle": "Platform untuk memaparkan dan membandingkan pendapat fiqh mazhab — untuk kefahaman dan wawasan, bukan laman fatwa.",
        "lang_label": "Bahasa",
        "s1_title": "1 — Pilih Mazhab",
        "group_q": "Mazhab Sunni, Syiah, atau Ibadi?",
        "multi_hint": "💡 Anda boleh memilih lebih daripada satu mazhab untuk membandingkan jawapan mereka.",
        "sub_select": "Pilih satu atau lebih mazhab:",
        "s2_title": "2 — Pilih Topik",
        "topic_q": "Pilih topik fiqh",
        "s3_title": "3 — Tahap Perincian Jawapan",
        "level_q": "Pilih tahap perincian",
        "s4_title": "4 — Taip Soalan Anda",
        "question_placeholder": "Contoh: Apakah hukum solat berjemaah?",
        "search_btn": "🔍 Cari Jawapan",
        "s5_title": "5 — Jawapan",
        "answer_placeholder": "Jawapan akan muncul di sini selepas anda menaip soalan dan menekan cari.",
        "no_question_warning": "Sila taip soalan anda terlebih dahulu di bahagian 4.",
        "no_madhab_warning": "Sila pilih sekurang-kurangnya satu mazhab.",
        "no_results_warning": "🔍 Tiada isu sepadan ditemui, dan jawapan AI tidak dapat dijana. Cuba kata kunci lain.",
        "signature": "Dan Allah lebih mengetahui",
        "note_general": "Pendapat umum yang disatukan — belum diperincikan mengikut mazhab",
        "note_madhab": "Pendapat mazhab {}",
        "ai_badge": "🤖 Jawapan dijana oleh AI",
        "ai_disclaimer": "⚠️ Jawapan ini dijana secara automatik oleh AI kerana isu ini belum terdapat dalam pangkalan data yang disahkan. Ia bukan fatwa dan belum disemak oleh ulama; sila sahkan dengan sumber yang dipercayai atau ulama yang berkelayakan sebelum bertindak berdasarkannya.",
        "ai_generating": "🤖 Menjana jawapan AI...",
        "ai_unavailable": "Jawapan automatik AI kini dinyahaktifkan (kunci API Gemini tidak ditetapkan).",
        "rag_badge": "📖 Berdasarkan rujukan yang dimuat naik ({})",
        "rag_expander": "📁 Urus Rujukan (RAG) — Pentadbir",
        "rag_intro": "Muat naik teks rujukan fiqh yang anda mempunyai hak untuk digunakan; sistem akan memecahkannya kepada bahagian dan mencari secara semantik sebelum beralih kepada penjanaan AI bebas.",
        "rag_title_label": "Tajuk sumber",
        "rag_madhab_label": "Mazhab (pilihan)",
        "rag_text_label": "Tampal teks di sini, atau muat naik fail .txt",
        "rag_file_label": "Atau muat naik fail teks (.txt)",
        "rag_submit": "Tambah dan Indeks Rujukan",
        "rag_processing": "Memecahkan teks dan mengira vektor...",
        "rag_success": "✅ {} bahagian daripada \"{}\" ditambah ke indeks rujukan.",
        "rag_empty_warning": "⚠️ Sila tampal teks atau muat naik fail sebelum menambah.",
        "rag_failed": "❌ Gagal mengindeks rujukan (semak kunci API Gemini anda).",
        "rag_current_sources": "Sumber yang diindeks sekarang:",
        "rag_no_sources": "Tiada rujukan diindeks lagi.",
        "expander_imams": "📜 Imam Pengasas Mazhab",
        "expander_countries": "🗺️ Negara Islam & Mazhab Rasmi",
        "expander_glossary": "📚 Istilah Fiqh Utama",
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
    },
    "ur": {
        "app_title": "مذاہب کی آراء کا مختصر مجموعہ",
        "app_subtitle": "مذاہب فقہیہ کی آراء دکھانے اور موازنہ کرنے کا پلیٹ فارم — فہم و بصیرت کے لیے، فتویٰ جاری کرنے کے لیے نہیں۔",
        "lang_label": "زبان",
        "s1_title": "۱ — مذہب منتخب کریں",
        "group_q": "اہل سنت کے مذاہب، اہل تشیع کے مذاہب، یا اباضی مذہب؟",
        "multi_hint": "💡 آپ موازنہ کے لیے ایک سے زیادہ مذاہب منتخب کر سکتے ہیں۔",
        "sub_select": "ایک یا زیادہ مذاہب منتخب کریں:",
        "s2_title": "۲ — موضوع منتخب کریں",
        "topic_q": "فقہی موضوع منتخب کریں",
        "s3_title": "۳ — جواب کی تفصیل کی سطح",
        "level_q": "تفصیل کی سطح منتخب کریں",
        "s4_title": "۴ — اپنا سوال لکھیں",
        "question_placeholder": "مثال: نماز باجماعت کا کیا حکم ہے؟",
        "search_btn": "🔍 جواب تلاش کریں",
        "s5_title": "۵ — جواب",
        "answer_placeholder": "جواب یہاں ظاہر ہوگا جب آپ سوال لکھیں گے اور تلاش پر کلک کریں گے۔",
        "no_question_warning": "براہ کرم پہلے حصہ ۴ میں اپنا سوال لکھیں۔",
        "no_madhab_warning": "براہ کرم کم از کم ایک مذہب منتخب کریں۔",
        "no_results_warning": "🔍 کوئی مسئلہ نہیں ملا، اور AI جواب بھی تیار نہیں ہو سکا۔ دوسرے الفاظ آزمائیں۔",
        "signature": "واللہ اعلم",
        "note_general": "متفقہ عمومی رائے — ابھی تک مذہب کے لحاظ سے تفصیل نہیں دی گئی",
        "note_madhab": "مذہب {} کی رائے",
        "ai_badge": "🤖 مصنوعی ذہانت سے تیار کردہ جواب",
        "ai_disclaimer": "⚠️ یہ جواب خودکار طور پر AI نے تیار کیا ہے کیونکہ یہ مسئلہ ابھی تصدیق شدہ ڈیٹا بیس میں موجود نہیں۔ یہ فتویٰ نہیں ہے اور کسی عالم دین نے اس کا جائزہ نہیں لیا؛ براہ کرم عمل کرنے سے پہلے کسی معتبر ذریعہ یا اہل علم سے تصدیق کریں۔",
        "ai_generating": "🤖 AI کے ذریعے جواب تیار کیا جا رہا ہے...",
        "ai_unavailable": "خودکار AI جواب فی الحال غیر فعال ہے (Gemini API کلید مقرر نہیں کی گئی)۔",
        "rag_badge": "📖 اپ لوڈ کردہ حوالہ جات پر مبنی ({})",
        "rag_expander": "📁 حوالہ جات کا انتظام (RAG) — منتظمین",
        "rag_intro": "فقہی حوالہ جات کے متن اپ لوڈ کریں جن کے استعمال کا حق آپ کے پاس ہے؛ نظام انہیں حصوں میں تقسیم کر کے آزاد AI جوابات سے پہلے ان میں معنوی تلاش کرے گا۔",
        "rag_title_label": "ماخذ کا عنوان",
        "rag_madhab_label": "مذہب (اختیاری)",
        "rag_text_label": "متن یہاں پیسٹ کریں، یا .txt فائل اپ لوڈ کریں",
        "rag_file_label": "یا ایک متنی فائل (.txt) اپ لوڈ کریں",
        "rag_submit": "حوالہ شامل اور انڈیکس کریں",
        "rag_processing": "متن تقسیم اور ویکٹر شمار کیے جا رہے ہیں...",
        "rag_success": "✅ «{}» سے {} حصے حوالہ انڈیکس میں شامل کیے گئے۔",
        "rag_empty_warning": "⚠️ شامل کرنے سے پہلے براہ کرم متن پیسٹ کریں یا فائل اپ لوڈ کریں۔",
        "rag_failed": "❌ حوالہ انڈیکس نہیں ہو سکا (اپنی Gemini API کلید چیک کریں)۔",
        "rag_current_sources": "فی الحال انڈیکس شدہ ماخذ:",
        "rag_no_sources": "ابھی تک کوئی حوالہ انڈیکس نہیں ہوا۔",
        "expander_imams": "📜 مذاہب کے بانی ائمہ",
        "expander_countries": "🗺️ اسلامی ممالک اور سرکاری مذہب",
        "expander_glossary": "📚 اہم فقہی اصطلاحات",
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
    },
}

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
    "sunni": {"ar": "مذاهب السنة", "en": "Sunni Schools", "fr": "Écoles sunnites", "fa": "مذاهب اهل سنت", "ms": "Mazhab Sunni", "ur": "اہل سنت کے مذاہب",
              "members": ["maliki", "shafii", "hanafi", "hanbali", "zahiri"]},
    "shia": {"ar": "مذاهب الشيعة", "en": "Shia Schools", "fr": "Écoles chiites", "fa": "مذاهب شیعه", "ms": "Mazhab Syiah", "ur": "شیعہ مذاہب",
             "members": ["jafari", "zaidi"]},
    "ibadi": {"ar": "المذهب الإباضي", "en": "Ibadi School", "fr": "École ibadite", "fa": "مذهب اباضی", "ms": "Mazhab Ibadi", "ur": "اباضی مذہب",
              "members": ["ibadi"]},
}

TOPICS = {
    "ibadat": {"ar": "العبادات", "en": "Acts of Worship", "fr": "Actes d'adoration", "fa": "عبادات", "ms": "Ibadat", "ur": "عبادات"},
    "muamalat": {"ar": "المعاملات", "en": "Transactions", "fr": "Transactions", "fa": "معاملات", "ms": "Muamalat", "ur": "معاملات"},
    "family": {"ar": "الأسرة", "en": "Family", "fr": "Famille", "fa": "خانواده", "ms": "Keluarga", "ur": "خاندان"},
    "other": {"ar": "مواضيع أخرى", "en": "Other Topics", "fr": "Autres sujets", "fa": "موضوعات دیگر", "ms": "Topik Lain", "ur": "دیگر موضوعات"},
}

LEVELS = {
    "very_short": {"ar": "مختصرة (كلمة)", "en": "Very short (one word)", "fr": "Très bref (un mot)", "fa": "بسیار مختصر (یک واژه)", "ms": "Sangat ringkas (satu perkataan)", "ur": "بہت مختصر (ایک لفظ)"},
    "short": {"ar": "مبسطة (سطر)", "en": "Short (one line)", "fr": "Bref (une ligne)", "fa": "ساده (یک خط)", "ms": "Ringkas (satu baris)", "ur": "آسان (ایک سطر)"},
    "full": {"ar": "مفصل (أكثر من سطر)", "en": "Detailed (full)", "fr": "Détaillé (complet)", "fa": "مفصل (چند خط)", "ms": "Terperinci (penuh)", "ur": "تفصیلی (مکمل)"},
}

GLOSSARY = [
    {"term": {"ar": "الفرض / فرض العين", "en": "Fard / Fard Ayn (Individual Obligation)", "fr": "Le fard / fard ayn (Obligation individuelle)", "fa": "فرض / فرض عین", "ms": "Fardu / Fardu Ain (Kewajipan Individu)", "ur": "فرض / فرض عین"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من كل مكلف بعينه، يُثاب فاعله ويُعاقب تاركه.",
                    "en": "What the Lawgiver has decisively commanded every legally accountable individual to perform; one who does it is rewarded, and one who abandons it is sinful.",
                    "fr": "Ce que le Législateur a ordonné de façon décisive à tout individu responsable d'accomplir ; celui qui l'accomplit est récompensé, et celui qui l'abandonne est fautif.",
                    "fa": "آنچه شارع به‌طور قطعی بر هر مکلفی واجب کرده است؛ انجام‌دهنده پاداش می‌گیرد و ترک‌کننده گناهکار است.",
                    "ms": "Apa yang Pembuat Syariat telah perintahkan secara tegas kepada setiap individu yang bertanggungjawab untuk melaksanakannya; yang melaksanakannya diberi pahala, dan yang meninggalkannya berdosa.",
                    "ur": "وہ چیز جسے شارع نے ہر مکلف پر قطعی طور پر واجب کیا ہے؛ اسے کرنے والا ثواب پاتا ہے اور چھوڑنے والا گنہگار ہے۔"}},
]

IMAMS = [
    {"name": {"ar": "الإمام مالك بن أنس الأصبحي", "en": "Imam Malik ibn Anas al-Asbahi", "fr": "L'imam Malik ibn Anas al-Asbahi", "fa": "امام مالک بن انس اصبحی", "ms": "Imam Malik bin Anas al-Asbahi", "ur": "امام مالک بن انس اصبحی"},
     "school": MADHHAB_NAMES["maliki"], "lifespan": "93 - 179 AH",
     "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
     "founding_place": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
     "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق",
                  "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq",
                  "fr": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq",
                  "fa": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق",
                  "ms": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil bin Ishaq",
                  "ur": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق"}},
    {"name": {"ar": "الإمام محمد بن إدريس الشافعي", "en": "Imam Muhammad ibn Idris al-Shafi'i", "fr": "L'imam Muhammad ibn Idris al-Chafi'i", "fa": "امام محمد بن ادریس شافعی", "ms": "Imam Muhammad bin Idris al-Syafie", "ur": "امام محمد بن ادریس شافعی"},
     "school": MADHHAB_NAMES["shafii"], "lifespan": "150 - 204 AH",
     "birthplace": {"ar": "غزة", "en": "Gaza", "fr": "Gaza", "fa": "غزه", "ms": "Gaza", "ur": "غزہ"},
     "founding_place": {"ar": "بغداد ثم مصر (المذهب الجديد)", "en": "Baghdad, then Egypt (the new doctrine)", "fr": "Bagdad, puis l'Égypte (la nouvelle doctrine)", "fa": "بغداد سپس مصر (مذهب جدید)", "ms": "Baghdad, kemudian Mesir (mazhab baru)", "ur": "بغداد پھر مصر (نیا مذہب)"},
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
]

# =====================================================================
# 6) STREAMLIT UI
# =====================================================================
def main():
    init_db()
    seed_initial_issues()

    if "lang" not in st.session_state:
        st.session_state.lang = "ar"

    top_l, top_r = st.columns([5, 2])
    with top_r:
        lang_choice = st.radio(
            UI[st.session_state.lang]["lang_label"],
            list(LANGS.keys()),
            index=list(LANGS.values()).index(st.session_state.lang),
            horizontal=True,
        )
        st.session_state.lang = LANGS[lang_choice]

    lang = st.session_state.lang
    T = UI[lang]
    is_rtl = lang in ["ar", "fa", "ur"]
    direction = "rtl" if is_rtl else "ltr"
    align = "right" if is_rtl else "left"

    st.markdown(f"""
    <style>
    .stApp {{ direction: {direction}; }}
    .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
        text-align: {align};
        line-height: 1.9;
    }}
    div[role="radiogroup"], div[data-baseweb="select"], div[data-testid="stMultiSelect"] {{ direction: {direction}; }}
    .stButton button {{ width: 100%; }}
    .app-header {{
        text-align: center; padding: 26px 16px;
        background: linear-gradient(145deg, #0f231c, #2a5c4a);
        color: white; border-radius: 16px; margin-bottom: 25px;
    }}
    .app-header h1, .app-header p {{ text-align: center !important; }}
    .answer-card {{
        background: #f5f7f5; border: 1px solid #e1e7e3;
        border-radius: 14px; padding: 16px 18px;
        margin-bottom: 12px; direction: {direction}; text-align: {align};
    }}
    .answer-card h4 {{ margin: 0 0 6px 0; color: #1e3a2f; text-align: {align}; }}
    .answer-card .answer-text {{ font-size: 1.15rem; font-weight: 600; color: #16281f; margin: 4px 0; }}
    .answer-card .answer-note {{ font-size: 0.85rem; color: #6a7f78; }}
    .answer-card.ai-card {{ border: 1px dashed #b08d3f; background: #fbf6ea; }}
    .answer-card.ai-card .answer-note {{ color: #9c7a2e; font-weight: 600; }}
    .answer-card.rag-card {{ border: 1px solid #2f6f8f; background: #eaf3f7; }}
    .answer-card.rag-card .answer-note {{ color: #1f5670; font-weight: 600; }}
    .signature {{
        font-family: 'Brush Script MT', 'Segoe Script', cursive;
        font-style: italic; font-size: 1rem; color: #b08d3f;
        text-align: center; margin: 6px 0 18px 0; opacity: 0.9;
    }}
    .info-box {{
        background:#f5f7f5; padding:12px 16px; border-radius:12px; margin-bottom:10px;
        border-{"right" if is_rtl else "left"}:4px solid #d4a854;
        direction: {direction}; text-align: {align};
    }}
    .info-box h4 {{ margin:0; color:#1e3a2f; text-align: {align}; }}
    .info-box p {{ margin:2px 0; color:#3d4f5f; text-align: {align}; }}
    .glossary-box {{
        background:#f5f7f5; padding:12px 16px; border-radius:12px; margin-bottom:10px;
        border-{"right" if is_rtl else "left"}:4px solid #1e3a2f;
        direction: {direction}; text-align: {align};
    }}
    .country-box {{
        background:#f5f7f5; padding:8px 12px; border-radius:8px; margin-bottom:6px;
        border-{"right" if is_rtl else "left"}:3px solid #d4a854;
        direction: {direction}; text-align: {align};
    }}
    </style>
    """, unsafe_allow_html=True)

    # الشعار
    st.markdown("""
    <div style="text-align:center; margin-bottom:-6px;">
        <svg width="88" height="88" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="56" fill="#0f231c" stroke="#d4a854" stroke-width="3"/>
            <circle cx="60" cy="60" r="49" fill="none" stroke="#d4a854" stroke-width="0.75" opacity="0.5"/>

            <!-- هلال -->
            <path d="M78 20 A15 15 0 1 0 81 47 A11.5 11.5 0 1 1 78 20 Z" fill="#d4a854"/>

            <!-- كتاب مفتوح -->
            <path d="M60 50 C46 43 32 45 25 52 V90 C32 83 46 81 60 88 C74 81 88 83 95 90 V52 C88 45 74 43 60 50 Z"
                  fill="none" stroke="#f2e6c9" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
            <line x1="60" y1="50" x2="60" y2="88" stroke="#f2e6c9" stroke-width="3"/>

            <!-- سطور الصفحة اليسرى -->
            <path d="M32 59 Q46 55 58 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            <path d="M32 67 Q46 63 58 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            <path d="M32 75 Q46 71 58 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>

            <!-- سطور الصفحة اليمنى -->
            <path d="M62 59 Q74 55 88 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            <path d="M62 67 Q74 63 88 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            <path d="M62 75 Q74 71 88 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
        </svg>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="app-header">
        <h1>📖 {T['app_title']}</h1>
        <p>{T['app_subtitle']}</p>
    </div>
    """, unsafe_allow_html=True)

    if not USE_GEMINI:
        st.caption(f"ℹ️ {T['ai_unavailable']}")

    # استيراد CSV
    with st.expander("📥 استيراد مسائل من CSV (للمشرفين)", expanded=False):
        st.info("""
        **تنسيق CSV المطلوب:** يجب أن يحتوي على أعمدة: `topic, title_ar, title_en, title_fr, title_fa, title_ms, title_ur, keywords_ar, keywords_en, keywords_fr, keywords_fa, keywords_ms, keywords_ur, ruling_vs_ar, ruling_s_ar, ruling_f_ar, ...` (جميع الأعمدة التي في قاعدة البيانات).
        """)
        uploaded = st.file_uploader("اختر ملف CSV", type=["csv"])
        if uploaded:
            try:
                count = import_from_csv(uploaded.read())
                st.success(f"✅ تم استيراد {count} مسألة بنجاح!")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")

    # -------------------------------------------------------------
    # لوحة إدارة المراجع (RAG) — يرفع المشرف نصوصاً مرجعية فعلية،
    # يفهرسها النظام دلالياً لتُستخدم كأساس للإجابات المبنية على
    # مراجع بدل التوليد الحر بالذكاء الاصطناعي.
    # -------------------------------------------------------------
    with st.expander(T["rag_expander"]):
        if not USE_GEMINI:
            st.warning(T["ai_unavailable"])
        st.caption(T["rag_intro"])

        ref_title = st.text_input(T["rag_title_label"], key="rag_title_input")
        ref_madhab = st.selectbox(
            T["rag_madhab_label"],
            [""] + list(MADHHAB_NAMES.keys()),
            format_func=lambda c: "—" if c == "" else MADHHAB_NAMES[c][lang],
            key="rag_madhab_input",
        )
        ref_text = st.text_area(T["rag_text_label"], height=150, key="rag_text_input")
        ref_file = st.file_uploader(T["rag_file_label"], type=["txt"], key="rag_file_input")

        if st.button(T["rag_submit"], disabled=not USE_GEMINI):
            content = ref_text.strip()
            if not content and ref_file:
                content = ref_file.read().decode("utf-8", errors="ignore").strip()
            if not content or not ref_title.strip():
                st.warning(T["rag_empty_warning"])
            else:
                with st.spinner(T["rag_processing"]):
                    n_chunks = add_reference_document(ref_title.strip(), ref_madhab, content)
                if n_chunks > 0:
                    st.success(T["rag_success"].format(n_chunks, ref_title.strip()))
                else:
                    st.error(T["rag_failed"])

        st.markdown(f"**{T['rag_current_sources']}**")
        sources = list_reference_sources()
        if sources:
            for title, n in sources:
                st.markdown(f"- {title} ({n})")
        else:
            st.caption(T["rag_no_sources"])

    # أقسام البحث
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
    if search_clicked and not selected_madhabs:
        st.warning(T["no_madhab_warning"])
    elif search_clicked and question:
        results = search_issues(question, topic, selected_madhabs, level, lang, T, MADHHAB_NAMES, TOPICS)
        ai_used = False
        rag_used = False

        # -------------------------------------------------------------
        # طبقات الإجابة بالترتيب:
        # 1) قاعدة البيانات الموثقة (search_issues أعلاه)
        # 2) استرجاع دلالي من المراجع المرفوعة (RAG) — إن وُجدت مراجع
        #    مفهرسة ذات صلة كافية بالسؤال
        # 3) توليد حر بالذكاء الاصطناعي كحل أخير — موسوم بوضوح كغير مُراجَع
        # -------------------------------------------------------------
        if not results and USE_GEMINI:
            with st.spinner(T["ai_generating"]):
                rag_cards = rag_generate_answer(question, lang, selected_madhabs, level, T)
            if rag_cards:
                results = [{"title": question, "topic": TOPICS[topic][lang], "cards": rag_cards}]
                rag_used = True

        if not results and USE_GEMINI:
            with st.spinner(T["ai_generating"]):
                ai_cards = ai_generate_answer(question, lang, selected_madhabs, level, T)
            if ai_cards:
                results = [{"title": question, "topic": TOPICS[topic][lang], "cards": ai_cards}]
                ai_used = True

        if results:
            if ai_used:
                st.warning(T["ai_disclaimer"])
            for r in results:
                st.markdown(f"**📌 {r['title']}** &nbsp;·&nbsp; _{r['topic']}_")
                cols = st.columns(len(r["cards"])) if len(r["cards"]) > 1 else [st.container()]
                for col, card in zip(cols, r["cards"]):
                    with col:
                        if ai_used:
                            card_class = "answer-card ai-card"
                        elif rag_used:
                            card_class = "answer-card rag-card"
                        else:
                            card_class = "answer-card"
                        st.markdown(f"""
                        <div class="{card_class}">
                            <h4>{card['label']}</h4>
                            <div class="answer-text">{card['answer']}</div>
                            <div class="answer-note">{card['note']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown(f"<div class='signature'>{T['signature']}</div>", unsafe_allow_html=True)
        else:
            st.warning(T["no_results_warning"])
            if not USE_GEMINI:
                st.caption(T["ai_unavailable"])
    elif search_clicked:
        st.info(T["no_question_warning"])
    else:
        st.caption(T["answer_placeholder"])

    st.markdown("---")

    # أقسام مرجعية
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

    with st.expander(T["expander_glossary"]):
        for term in GLOSSARY:
            st.markdown(f"""
            <div class="glossary-box">
                <h4>{term['term'][lang]}</h4>
                <p>{term['definition'][lang]}</p>
            </div>
            """, unsafe_allow_html=True)

    with st.expander(T["expander_comments"]):
        if "session_comments" not in st.session_state:
            st.session_state.session_comments = []
        st.markdown(f"**{T['rating_label']}**")
        try:
            rating = st.feedback("stars")
            if rating is not None:
                rating = rating + 1
        except Exception:
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
                st.markdown(f"- {'⭐' * int(c['rating'])} — {c['text']}")
        st.caption(T["comments_note"])

if __name__ == "__main__":
    main()
