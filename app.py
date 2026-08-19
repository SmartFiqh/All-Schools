import streamlit as st

st.set_page_config(page_title="الجامع المختصر لآراء المذاهب", page_icon="📖", layout="wide")

st.markdown("""
<div style="text-align:center; padding: 30px 0; background: linear-gradient(145deg, #0f231c, #2a5c4a); color: white; border-radius: 16px; margin-bottom: 25px;">
    <h1 style="font-size: 2.5rem;">📖 الجامع المختصر لآراء المذاهب</h1>
    <p style="font-size: 1.1rem; color: #d6e4de;">منصة لعرض ومقارنة آراء المذاهب الفقهية — للفهم والتبصر، وليست موقع إفتاء.</p>
</div>
""", unsafe_allow_html=True)

# بيانات وهمية (Mock) - 3 مسائل فقط للتجربة
issues = [
    {
        "title": "صلاة الجماعة",
        "topic": "العبادات",
        "maliki": "فرض كفاية",
        "shafii": "سنة مؤكدة",
        "hanafi": "واجب",
        "hanbali": "فرض عين",
        "jafari": "مستحب مؤكد"
    },
    {
        "title": "زكاة الأسهم",
        "topic": "المعاملات",
        "maliki": "واجبة",
        "shafii": "واجبة",
        "hanafi": "واجبة",
        "hanbali": "واجبة",
        "jafari": "واجبة"
    },
    {
        "title": "الجمع في السفر",
        "topic": "العبادات",
        "maliki": "جائز",
        "shafii": "جائز",
        "hanafi": "جائز",
        "hanbali": "جائز",
        "jafari": "جائز"
    }
]

# اختيار المذهب
st.markdown("### اختر المذهب")
madhab = st.radio(
    "المذهب",
    ["المالكي", "الشافعي", "الحنفي", "الحنبلي", "الجعفري"],
    horizontal=True,
    label_visibility="collapsed"
)

# اختيار الموضوع
st.markdown("### اختر الموضوع")
topic_filter = st.radio(
    "الموضوع",
    ["جميع الموضوعات", "العبادات", "المعاملات", "الأسرة", "مواضيع أخرى"],
    horizontal=True,
    label_visibility="collapsed"
)

# البحث
st.markdown("### اكتب سؤالك")
question = st.text_input("", placeholder="مثال: ما حكم صلاة الجماعة؟", label_visibility="collapsed")
search_clicked = st.button("🔍 ابحث", use_container_width=True)

# عرض النتائج
st.markdown("---")
st.markdown("### الإجابة")

if search_clicked and question:
    # تصفية النتائج حسب الموضوع
    filtered = []
    for issue in issues:
        if topic_filter == "جميع الموضوعات" or issue["topic"] == topic_filter:
            filtered.append(issue)
    
    # بحث بسيط في العناوين
    results = [i for i in filtered if question.strip().lower() in i["title"].lower()]
    
    if results:
        for r in results:
            st.markdown(f"**📌 {r['title']}**")
            
            # عرض رأي المذهب المختار
            madhab_key = {
                "المالكي": "maliki",
                "الشافعي": "shafii",
                "الحنفي": "hanafi",
                "الحنبلي": "hanbali",
                "الجعفري": "jafari"
            }[madhab]
            
            st.markdown(f"""
            <div style="background: #f5f7f5; padding: 16px; border-radius: 12px; border-right: 4px solid #d4a854; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #1e3a2f;">{madhab}</h4>
                <div style="font-size: 1.15rem; font-weight: 600; color: #16281f; margin: 4px 0;">{r[madhab_key]}</div>
                <div style="font-size: 0.85rem; color: #6a7f78;">رأي المذهب {madhab}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("*هذا والله أعلم*")
    else:
        st.warning("🔍 لم نجد مسألة بهذا الوصف. جرّب صياغة أخرى.")
elif search_clicked:
    st.info("✍️ اكتب سؤالك في الأعلى للحصول على إجابة.")
else:
    st.caption("ستظهر الإجابة هنا بعد كتابة السؤال والضغط على زر البحث.")

# معلومات إضافية
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6a7f78;">
    <p>المعرفة أمانة. نراجع كل مادة من مصادرها الأصلية، ونوضح مواضع الاتفاق والاختلاف بإنصاف.</p>
    <p style="font-size:0.8rem;">© ٢٠٢٤ الجامع المختصر لآراء المذاهب</p>
</div>
""", unsafe_allow_html=True)
