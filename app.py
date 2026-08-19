import streamlit as st

st.set_page_config(
    page_title="بيان - مرشد الآراء الفقهية",
    page_icon="📖",
    layout="wide"
)

# ============================================================
# البيانات الأساسية (5 مسائل نموذجية)
# ============================================================
issues = [
    {
        "id": 1,
        "title": "صلاة الجماعة",
        "category": "العبادات",
        "keywords": ["جماعة", "مسجد", "صلاة", "فرض", "سنة"],
        "answers": {
            "مالكي": "فرض كفاية",
            "شافعي": "سنة مؤكدة",
            "حنفي": "واجب",
            "حنبلي": "فرض عين",
            "جعفري": "مستحب مؤكد",
            "ظاهري": "فرض عين",
            "زيدي": "فرض كفاية",
            "إباضي": "سنة مؤكدة"
        }
    },
    {
        "id": 2,
        "title": "زكاة الأسهم",
        "category": "المعاملات",
        "keywords": ["زكاة", "أسهم", "استثمار", "تجارة", "نصاب"],
        "answers": {
            "مالكي": "واجبة",
            "شافعي": "واجبة",
            "حنفي": "واجبة",
            "حنبلي": "واجبة",
            "جعفري": "واجبة",
            "ظاهري": "واجبة",
            "زيدي": "واجبة",
            "إباضي": "واجبة"
        }
    },
    {
        "id": 3,
        "title": "الجمع في السفر",
        "category": "العبادات",
        "keywords": ["جمع", "سفر", "مسافر", "صلاة", "تخفيف"],
        "answers": {
            "مالكي": "جائز",
            "شافعي": "جائز",
            "حنفي": "جائز",
            "حنبلي": "جائز",
            "جعفري": "جائز",
            "ظاهري": "جائز",
            "زيدي": "جائز",
            "إباضي": "جائز"
        }
    },
    {
        "id": 4,
        "title": "نواقض الوضوء",
        "category": "العبادات",
        "keywords": ["وضوء", "طهارة", "بول", "غائط", "نوم", "مس"],
        "answers": {
            "مالكي": "مبطل",
            "شافعي": "مبطل",
            "حنفي": "مبطل",
            "حنبلي": "مبطل",
            "جعفري": "مبطل",
            "ظاهري": "مبطل",
            "زيدي": "مبطل",
            "إباضي": "مبطل"
        }
    },
    {
        "id": 5,
        "title": "الربا",
        "category": "المعاملات",
        "keywords": ["ربا", "حرام", "قرض", "فائدة", "بنوك"],
        "answers": {
            "مالكي": "حرام",
            "شافعي": "حرام",
            "حنفي": "حرام",
            "حنبلي": "حرام",
            "جعفري": "حرام",
            "ظاهري": "حرام",
            "زيدي": "حرام",
            "إباضي": "حرام"
        }
    }
]

MADHHABS = ["مالكي", "شافعي", "حنفي", "حنبلي", "جعفري", "ظاهري", "زيدي", "إباضي"]

# ============================================================
# واجهة التطبيق
# ============================================================

# الهيدر
st.markdown("""
<div style="text-align: center; padding: 20px 0; background: linear-gradient(145deg, #0f231c, #2a5c4a); color: white; border-radius: 16px; margin-bottom: 25px;">
    <h1 style="font-size: 2.5rem; margin: 0;">📖 بيان - مرشد الآراء الفقهية</h1>
    <p style="font-size: 1rem; color: #d6e4de; margin: 6px 0 0;">للفهم والتبصر، لا لإصدار الفتاوى</p>
</div>
""", unsafe_allow_html=True)

# اختيار المذاهب (متعدد)
st.markdown("### 🏛️ اختر المذاهب (يمكنك اختيار أكثر من واحد)")
selected_madhabs = st.multiselect(
    "المذاهب",
    MADHHABS,
    default=["مالكي", "شافعي", "حنفي"],
    label_visibility="collapsed"
)

if not selected_madhabs:
    st.warning("⚠️ الرجاء اختيار مذهب واحد على الأقل.")

st.divider()

# اختيار الموضوع
st.markdown("### 📂 اختر الموضوع")
topic_filter = st.radio(
    "الموضوع",
    ["الكل", "العبادات", "المعاملات", "الأسرة", "مواضيع أخرى"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# مستوى الإجابة
st.markdown("### 📝 مستوى الإجابة")
level = st.radio(
    "المستوى",
    ["مختصرة (كلمة)", "مبسطة (سطر)", "مفصلة (فقرة)"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# كتابة السؤال
st.markdown("### ✍️ اكتب سؤالك")
question = st.text_input(
    "",
    placeholder="مثال: ما حكم صلاة الجماعة؟",
    label_visibility="collapsed"
)

search_clicked = st.button("🔍 ابحث عن الإجابة", use_container_width=True)

st.divider()

# ============================================================
# عرض النتائج
# ============================================================
st.markdown("### 📊 الإجابة")

if search_clicked and question and selected_madhabs:
    # تصفية حسب الموضوع
    filtered = []
    for issue in issues:
        if topic_filter == "الكل" or issue["category"] == topic_filter:
            filtered.append(issue)
    
    # البحث في العناوين والكلمات المفتاحية
    query = question.strip().lower()
    results = []
    for issue in filtered:
        if query in issue["title"].lower() or any(query in kw.lower() for kw in issue["keywords"]):
            results.append(issue)
    
    if results:
        for issue in results:
            st.markdown(f"**📌 {issue['title']}** &nbsp;·&nbsp; _{issue['category']}_")
            
            # عرض آراء المذاهب المختارة
            cols = st.columns(len(selected_madhabs))
            for col, madhab in zip(cols, selected_madhabs):
                with col:
                    answer = issue["answers"].get(madhab, "غير متوفر")
                    st.markdown(f"""
                    <div style="background: #f5f7f5; padding: 12px 16px; border-radius: 12px; border-right: 4px solid #d4a854; margin-bottom: 10px; height: 100%;">
                        <h4 style="margin: 0; color: #1e3a2f; font-size: 0.95rem;">{madhab}</h4>
                        <div style="font-size: 1.1rem; font-weight: 600; color: #16281f; margin: 4px 0;">{answer}</div>
                        <div style="font-size: 0.75rem; color: #6a7f78;">رأي المذهب</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("*هذا والله أعلم*")
            st.markdown("---")
    else:
        st.warning("🔍 لم نجد مسألة بهذا الوصف. جرّب صياغة أخرى.")
elif search_clicked and not selected_madhabs:
    st.warning("⚠️ الرجاء اختيار مذهب واحد على الأقل.")
elif search_clicked and not question:
    st.info("✍️ اكتب سؤالك أولاً.")
else:
    st.caption("ستظهر الإجابة هنا بعد كتابة السؤال والضغط على زر البحث.")

# التذييل
st.markdown("""
<div style="text-align:center; padding: 16px 0; color:#6a7f78;">
    <p>المعرفة أمانة. نراجع كل مادة من مصادرها الأصلية، ونوضح مواضع الاتفاق والاختلاف بإنصاف.</p>
    <p style="font-size:0.8rem;">© ٢٠٢٤ بيان - مرشد الآراء الفقهية</p>
</div>
""", unsafe_allow_html=True)
