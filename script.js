// بيانات وهمية للمسائل (محاكاة)
const issues = [
    { title: 'صلاة الجماعة', category: 'العبادات' },
    { title: 'زكاة الأسهم', category: 'المعاملات' },
    { title: 'الجمع في السفر', category: 'العبادات' },
    { title: 'نواقض الوضوء', category: 'العبادات' },
];

// عناصر الصفحة
const searchInput = document.getElementById('search');
const searchBtn = document.getElementById('searchBtn');

// وظيفة البحث
function searchIssues(query) {
    const results = issues.filter(issue =>
        issue.title.includes(query) || issue.category.includes(query)
    );
    displayResults(results);
}

// عرض النتائج (يمكنك توجيه المستخدم لصفحة نتائج)
function displayResults(results) {
    if (results.length === 0) {
        alert('لم نجد مسألة بهذا الوصف. جرّب كلمة أقصر.');
    } else {
        alert('تم العثور على ' + results.length + ' مسألة.');
        console.log(results);
    }
}

// أحداث البحث
searchBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (query) searchIssues(query);
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const query = searchInput.value.trim();
        if (query) searchIssues(query);
    }
});

// أزرار المذاهب
document.querySelectorAll('.m-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const madhhab = btn.textContent.trim();
        alert('تم اختيار المذهب: ' + madhhab);
        // هنا يمكنك تحديث الفلتر وعرض المسائل حسب المذهب
    });
});

// بطاقات التصنيفات
document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
        const category = card.textContent.trim();
        alert('تم اختيار التصنيف: ' + category);
        // هنا يمكنك تصفية المسائل حسب التصنيف
    });
});
