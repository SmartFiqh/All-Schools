import streamlit as st

st.set_page_config(page_title="بيان", page_icon="📖")

st.title("📖 بيان - مرشد الآراء الفقهية")
st.write("للفهم والتبصر، لا لإصدار الفتاوى")

# بيانات بسيطة
madhab = st.selectbox("اختر المذهب", ["المالكي", "الشافعي", "الحنفي"])
issue = st.selectbox("اختر المسألة", ["صلاة الجماعة", "زكاة الأسهم", "الربا"])

if st.button("🔍 ابحث"):
    st.success(f"تم البحث عن: {issue} - المذهب: {madhab}")
    st.caption("هذا والله أعلم")
