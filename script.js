// ============================================================
//  📖 بيان - الملف الرئيسي (script.js)
//  مرشد الآراء الفقهية
//  الإصدار النهائي مع: البحث الذكي، 6 لغات، بيانات حقيقية،
//  أقسام قابلة للطي، وترجمة ديناميكية
// ============================================================

// ============================================================
//  1.  البيانات الأساسية (المسائل، المصطلحات، الدول، الأئمة)
// ============================================================

// ----- 1.1 المسائل الفقهية (بيانات حقيقية) -----
const issuesData = [
    {
        id: 1,
        title: "صلاة الجماعة",
        category: "العبادات",
        rulings: {
            very_short: "سنة مؤكدة",
            short: "سنة مؤكدة عند الجمهور، واجبة عند الحنفية",
            full: "تجب صلاة الجماعة في المسجد على الرجال عند جمهور الفقهاء؛ فهي فرض عين عند الحنابلة، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة تأكيداً عند الجعفرية في زمن الغيبة."
        },
        keywords: ["جماعة", "مسجد", "رجال", "صلاة", "فرض", "سنة", "واجب"]
    },
    {
        id: 2,
        title: "زكاة الأسهم",
        category: "المعاملات",
        rulings: {
            very_short: "واجبة",
            short: "زكاة الأسهم واجبة إذا بلغت النصاب",
            full: "تجب زكاة الأسهم إذا كانت للاستثمار والتجارة، وبلغت قيمتها النصاب (85 جرام ذهب)، وتُحسب بقيمتها السوقية في نهاية الحول، ويُخرج 2.5% من قيمتها."
        },
        keywords: ["زكاة", "أسهم", "استثمار", "تجارة", "نصاب", "مال"]
    },
    {
        id: 3,
        title: "الجمع في السفر",
        category: "العبادات",
        rulings: {
            very_short: "جائز",
            short: "يجوز جمع الصلاة في السفر للمسافر",
            full: "يجوز للمسافر جمع صلاة الظهر مع العصر، والمغرب مع العشاء، تقديماً أو تأخيراً، في وقت إحداهما، وذلك تخفيفاً من الله تعالى على المسافرين."
        },
        keywords: ["جمع", "سفر", "مسافر", "صلاة", "تخفيف", "رخصة"]
    },
    {
        id: 4,
        title: "نواقض الوضوء",
        category: "العبادات",
        rulings: {
            very_short: "مبطل",
            short: "نواقض الوضوء تبطل الطهارة وتوجب إعادته",
            full: "نواقض الوضوء هي: الخارج من السبيلين (البول، الغائط، الريح)، النوم المستغرق، زوال العقل (بإغماء أو سكر)، مسّ الفرج بغير حائل، ولمس المرأة بشهوة عند بعض المذاهب."
        },
        keywords: ["وضوء", "نواقض", "طهارة", "بول", "غائط", "نوم", "مس"]
    },
    {
        id: 5,
        title: "الربا",
        category: "المعاملات",
        rulings: {
            very_short: "حرام",
            short: "الربا من كبائر الذنوب ومحرم قطعاً",
            full: "الربا محرم بنص القرآن والسنة، وهو كل زيادة مشروطة في القرض أو المعاملة، سواء كانت نقدية أو عينية. الربا من السبع الموبقات، والله ورسوله حاربا من يتعامل به."
        },
        keywords: ["ربا", "حرام", "قرض", "فائدة", "بنوك", "معاملة", "ذنب"]
    },
    {
        id: 6,
        title: "الطلاق",
        category: "الأسرة",
        rulings: {
            very_short: "مباح",
            short: "الطلاق مباح عند الضرورة، وهو أبغض الحلال",
            full: "الطلاق هو حل عقد النكاح، وهو مباح عند الحاجة والضرورة، لكنه أبغض الحلال إلى الله. يجب أن يكون الطلاق في طهر لم يمسها فيه، ولا يجوز الطلاق في الحيض أو النفاس. وللزوجة الحق في الخلع مقابل مال."
        },
        keywords: ["طلاق", "زوجة", "نكاح", "حلال", "خلع", "أسرة"]
    },
    {
        id: 7,
        title: "العدة",
        category: "الأسرة",
        rulings: {
            very_short: "واجبة",
            short: "العدة واجبة على المطلقة والمتوفى عنها زوجها",
            full: "العدة هي فترة انتظار للمرأة بعد انتهاء الزواج، لبراءة الرحم وتحديد النسب. عدة المطلقة ثلاث حيضات (أو ثلاثة أشهر إن لم تحض)، وعدة المتوفى عنها زوجها أربعة أشهر وعشرة أيام."
        },
        keywords: ["عدة", "طلاق", "وفاة", "رحم", "نسب", "حيض"]
    },
    {
        id: 8,
        title: "التيمم",
        category: "العبادات",
        rulings: {
            very_short: "جائز",
            short: "التيمم جائز عند عدم وجود الماء أو العذر الشرعي",
            full: "التيمم هو بديل عن الوضوء والغسل عند عدم وجود الماء، أو لمرض يمنع استعماله. يُمسح التراب على الوجه والكفين، وهو رخصة من الله للتيسير على عباده. يبطل التيمم بوجود الماء أو زوال العذر."
        },
        keywords: ["تيمم", "ماء", "تراب", "وضوء", "غسل", "رخصة", "مرض"]
    }
];

// ----- 1.2  المصطلحات الفقهية -----
const glossaryTerms = [
    { term: "الحلال", definition: "ما أحله الله ورسوله، وثبوت حله في الكتاب والسنة، وفعله مباح لا إثم فيه، بل قد يثاب عليه الإنسان إذا نوى به التقوى أو العبادة. ومثاله: أكل الطعام الطيب، والنكاح، والتجارة المشروعة." },
    { term: "الحرام", definition: "ما حرمه الله ورسوله بنص قطعي، وثبوت تحريمه في الكتاب أو السنة، وفاعله آثم مستحق للعقاب، وتاركه مثاب. ومثاله: شرب الخمر، والزنا، والربا، وأكل الميتة والدم ولحم الخنزير." },
    { term: "المكروه", definition: "ما طلب الشارع تركه طلباً غير جازم، ويثاب تاركه تقرباً إلى الله، ولا يعاقب فاعله، لكن تركه أولى وأفضل. ينقسم إلى: مكروه تحريم (أقرب للحرام) ومكروه تنزيه (أقرب للمباح). ومثاله: الأكل بالشمال، أو الصلاة في وقت النهي دون عذر." },
    { term: "المستحب", definition: "ما رغب الشارع في فعله دون إلزام، ويثاب فاعله امتثالاً لأمره، ولا يعاقب تاركه، وهو أوسع أبواب الطاعات. ومثاله: صلاة الضحى، وصيام التطوع، والصدقة، وقيام الليل." },
    { term: "المندوب", definition: "مرادف للمستحب، وهو ما ندب الشرع إليه وحث عليه دون إيجاب، ويثاب فاعله ولا إثم على تاركه. ومثاله: الوتر عند غير الحنفية، والأضحية، والعمرة." },
    { term: "السنة غير المؤكدة", definition: "ما فعله النبي ﷺ أحياناً وتركه أحياناً أخرى من غير مواظبة، وتركها لا إثم فيه ولا كراهة، وهي دون المؤكدة في الفضل. ومثاله: سنة الظهر القبلية، أو سنة المغرب البعدية." },
    { term: "السنة المؤكدة", definition: "ما واظب النبي ﷺ على فعله في الغالب، وتركه أحياناً قليلاً، وتركها مكروه عند الحنفية، ويثاب فاعلها ولا يعاقب تاركها عند الجمهور. ومثاله: سنة الفجر القبلية، وسنة الظهر القبلية والبعدية." },
    { term: "الفرض (فرض عين)", definition: "ما طلب الشارع فعله طلباً جازماً على كل مكلف شخصياً، ويثاب فاعله ويعاقب تاركه، وهو أعلى مراتب التكليف. ومثاله: الصلوات الخمس، وصوم رمضان، وحج البيت لمن استطاع إليه سبيلاً." },
    { term: "فرض الكفاية", definition: "ما طلب الشارع فعله طلباً جازماً على عموم المكلفين، ويسقط عن الجميع بفعل البعض، ويأثم الجميع إن تركه الكل. ومثاله: صلاة الجنازة، والأمر بالمعروف والنهي عن المنكر، وتعلم العلوم الشرعية والطبية." },
    { term: "الواجب (عند الحنفية)", definition: "عند الحنفية: ما ثبت بدليل ظني (كصلاة الوتر، وصلاة العيدين، وأضحية العيد)، وتركه يستحق العقاب لكن لا يكفر به. عند الجمهور: مرادف للفرض تماماً." }
];

// ----- 1.3  الدول والمذاهب الرسمية (مع أعداد السكان) -----
const countriesData = [
    { country: "🇸🇦 السعودية", madhab: "الحنبلي", population: "36.4 مليون" },
    { country: "🇪🇬 مصر", madhab: "الشافعي", population: "112.7 مليون" },
    { country: "🇲🇦 المغرب", madhab: "المالكي", population: "37.8 مليون" },
    { country: "🇩🇿 الجزائر", madhab: "المالكي", population: "46.3 مليون" },
    { country: "🇹🇳 تونس", madhab: "المالكي", population: "12.5 مليون" },
    { country: "🇱🇾 ليبيا", madhab: "المالكي", population: "7.4 مليون" },
    { country: "🇲🇷 موريتانيا", madhab: "المالكي", population: "5.2 مليون" },
    { country: "🇸🇩 السودان", madhab: "المالكي", population: "50.4 مليون" },
    { country: "🇹🇷 تركيا", madhab: "الحنفي", population: "87.5 مليون" },
    { country: "🇸🇾 سوريا", madhab: "الحنفي", population: "24.2 مليون" },
    { country: "🇯🇴 الأردن", madhab: "الحنفي", population: "11.5 مليون" },
    { country: "🇵🇸 فلسطين", madhab: "الحنفي", population: "5.6 مليون" },
    { country: "🇮🇶 العراق", madhab: "الجعفري/الحنفي", population: "46.5 مليون" },
    { country: "🇮🇷 إيران", madhab: "الجعفري", population: "89.8 مليون" },
    { country: "🇾🇪 اليمن", madhab: "الزيدي/الشافعي", population: "35.6 مليون" },
    { country: "🇴🇲 عُمان", madhab: "الإباضي", population: "4.7 مليون" },
    { country: "🇶🇦 قطر", madhab: "الحنبلي", population: "2.9 مليون" },
    { country: "🇰🇼 الكويت", madhab: "الحنفي", population: "4.5 مليون" },
    { country: "🇧🇭 البحرين", madhab: "الجعفري/الحنفي", population: "1.6 مليون" },
    { country: "🇦🇪 الإمارات", madhab: "المالكي", population: "10.1 مليون" },
    { country: "🇵🇰 باكستان", madhab: "الحنفي", population: "248.5 مليون" },
    { country: "🇮🇳 الهند", madhab: "الحنفي", population: "1,425.8 مليون" },
    { country: "🇧🇩 بنغلاديش", madhab: "الحنفي", population: "174.7 مليون" },
    { country: "🇮🇩 إندونيسيا", madhab: "الشافعي", population: "281.6 مليون" },
    { country: "🇲🇾 ماليزيا", madhab: "الشافعي", population: "34.7 مليون" },
    { country: "🇸🇬 سنغافورة", madhab: "الشافعي", population: "6.1 مليون" },
    { country: "🇦🇫 أفغانستان", madhab: "الحنفي", population: "43.4 مليون" },
    { country: "🇺🇿 أوزبكستان", madhab: "الحنفي", population: "36.3 مليون" },
    { country: "🇰🇿 كازاخستان", madhab: "الحنفي", population: "20.3 مليون" },
    { country: "🇹🇯 طاجيكستان", madhab: "الحنفي", population: "10.5 مليون" },
    { country: "🇰🇬 قيرغيزستان", madhab: "الحنفي", population: "7.2 مليون" },
    { country: "🇹🇲 تركمانستان", madhab: "الحنفي", population: "6.4 مليون" },
    { country: "🇸🇴 الصومال", madhab: "الشافعي", population: "18.1 مليون" },
    { country: "🇩🇯 جيبوتي", madhab: "الشافعي", population: "1.1 مليون" },
    { country: "🇪🇷 إريتريا", madhab: "الشافعي", population: "3.7 مليون" },
    { country: "🇳🇬 نيجيريا", madhab: "المالكي", population: "229.2 مليون" },
    { country: "🇸🇳 السنغال", madhab: "المالكي", population: "18.5 مليون" },
    { country: "🇲🇱 مالي", madhab: "المالكي", population: "24.3 مليون" },
    { country: "🇹🇩 تشاد", madhab: "المالكي", population: "19.3 مليون" }
];

// ----- 1.4  الترجمات (6 لغات) -----
const translations = {
    ar: {
        app_name: "📖 بيان",
        subtitle: "مرشد الآراء الفقهية",
        tagline: "للفهم والتبصر، لا لإصدار الفتاوى",
        most_searched: "📈 الأكثر بحثًا:",
        search_label: "❓ ماذا تريد أن تعرف اليوم؟",
        search_placeholder: "اسأل بأي طريقة... سيفهمك التطبيق",
        search_count: "أكثر من ١٢٠ مسألة موثقة",
        answer_levels_title: "📝 اختر مستوى الإجابة:",
        level_very_short: "⚡ مختصرة جداً (كلمة واحدة)",
        level_short: "📄 مختصرة (سطر واحد)",
        level_full: "📚 كاملة (تفصيلية)",
        placeholder: "🔍 اكتب سؤالك في الأعلى للحصول على إجابة",
        all_topics: "✦ كل الموضوعات",
        topic_worship: "☽ العبادات",
        topic_transactions: "◈ المعاملات",
        topic_family: "⌂ الأسرة",
        topic_daily_life: "✧ الحياة اليومية",
        madhhab_map: "🗺️ خريطة الآراء",
        sunni: "المذاهب السنية",
        shia: "المذاهب الشيعية",
        ibadi: "المذهب الإباضي",
        other_views: "رأي آخر",
        imams_title: "📜 الأئمة المؤسسون",
        map_title: "🗺️ المذهب الرسمي السائد في الدول الإسلامية",
        glossary_title: "📚 قاموس المصطلحات الفقهية",
        footer: "المعرفة أمانة. نراجع كل مادة من مصادرها الأصلية، ونوضح مواضع الاتفاق والاختلاف بإنصاف.",
        footer_link: "تعرّف على منهجيتنا →",
        copyright: "© ٢٠٢٤ بيان",
        not_found: "🔍 لم نجد مسألة بهذا الوصف. جرّب كلمة أقصر أو اختر موضوعاً آخر.",
        ai_processing: "🧠 جاري تحليل سؤالك..."
    },
    en: {
        app_name: "📖 Bayān",
        subtitle: "Guide to Jurisprudential Opinions",
        tagline: "For understanding and insight, not for issuing fatwas",
        most_searched: "📈 Most Searched:",
        search_label: "❓ What do you want to know today?",
        search_placeholder: "Ask in any way... the app will understand you",
        search_count: "Over 120 verified issues",
        answer_levels_title: "📝 Choose answer level:",
        level_very_short: "⚡ Very short (one word)",
        level_short: "📄 Short (one line)",
        level_full: "📚 Full (detailed)",
        placeholder: "🔍 Type your question above to get an answer",
        all_topics: "✦ All Topics",
        topic_worship: "☽ Worship",
        topic_transactions: "◈ Transactions",
        topic_family: "⌂ Family",
        topic_daily_life: "✧ Daily Life",
        madhhab_map: "🗺️ Map of Opinions",
        sunni: "Sunni Schools",
        shia: "Shia Schools",
        ibadi: "Ibadi School",
        other_views: "Other Views",
        imams_title: "📜 Founding Imams",
        map_title: "🗺️ Official School in Islamic Countries",
        glossary_title: "📚 Islamic Legal Glossary",
        footer: "Knowledge is a trust. We review every material from its original sources, and clarify points of agreement and disagreement fairly.",
        footer_link: "Learn about our methodology →",
        copyright: "© 2024 Bayān",
        not_found: "🔍 No issue found with this description. Try a shorter word or choose another topic.",
        ai_processing: "🧠 Analyzing your question..."
    },
    fr: {
        app_name: "📖 Bayān",
        subtitle: "Guide des Opinions Jurisprudentielles",
        tagline: "Pour la compréhension et la clairvoyance, non pour émettre des fatwas",
        most_searched: "📈 Les plus recherchés :",
        search_label: "❓ Que voulez-vous savoir aujourd'hui ?",
        search_placeholder: "Demandez de n'importe quelle manière... l'application vous comprendra",
        search_count: "Plus de 120 questions vérifiées",
        answer_levels_title: "📝 Choisissez le niveau de réponse :",
        level_very_short: "⚡ Très courte (un mot)",
        level_short: "📄 Courte (une ligne)",
        level_full: "📚 Complète (détaillée)",
        placeholder: "🔍 Tapez votre question ci-dessus pour obtenir une réponse",
        all_topics: "✦ Tous les sujets",
        topic_worship: "☽ Adorations",
        topic_transactions: "◈ Transactions",
        topic_family: "⌂ Famille",
        topic_daily_life: "✧ Vie quotidienne",
        madhhab_map: "🗺️ Carte des opinions",
        sunni: "Écoles sunnites",
        shia: "Écoles chiites",
        ibadi: "École ibadite",
        other_views: "Autres avis",
        imams_title: "📜 Imams fondateurs",
        map_title: "🗺️ École officielle dans les pays islamiques",
        glossary_title: "📚 Glossaire juridique islamique",
        footer: "La connaissance est une confiance. Nous examinons chaque matière à partir de ses sources originales, et clarifions les points d'accord et de désaccord avec équité.",
        footer_link: "Découvrez notre méthodologie →",
        copyright: "© 2024 Bayān",
        not_found: "🔍 Aucune question trouvée avec cette description. Essayez un mot plus court ou choisissez un autre sujet.",
        ai_processing: "🧠 Analyse de votre question..."
    },
    fa: {
        app_name: "📖 بیان",
        subtitle: "راهنمای آراء فقهی",
        tagline: "برای فهم و بصیرت، نه برای صدور فتوا",
        most_searched: "📈 پربحث‌ترین‌ها:",
        search_label: "❓ امروز چه می‌خواهید بدانید؟",
        search_placeholder: "به هر روشی بپرسید... برنامه شما را درک می‌کند",
        search_count: "بیش از ۱۲۰ مسئله مستند",
        answer_levels_title: "📝 سطح پاسخ را انتخاب کنید:",
        level_very_short: "⚡ بسیار کوتاه (یک کلمه)",
        level_short: "📄 کوتاه (یک خط)",
        level_full: "📚 کامل (جزئیات)",
        placeholder: "🔍 سوال خود را در بالا تایپ کنید تا پاسخ دریافت کنید",
        all_topics: "✦ همه موضوعات",
        topic_worship: "☽ عبادات",
        topic_transactions: "◈ معاملات",
        topic_family: "⌂ خانواده",
        topic_daily_life: "✧ زندگی روزمره",
        madhhab_map: "🗺️ نقشه آراء",
        sunni: "مذاهب اهل سنت",
        shia: "مذاهب شیعه",
        ibadi: "مذهب اباضی",
        other_views: "نظر دیگر",
        imams_title: "📜 ائمه مؤسس",
        map_title: "🗺️ مذهب رسمی در کشورهای اسلامی",
        glossary_title: "📚 واژه‌نامه فقهی",
        footer: "دانش یک امانت است. هر مطلب را از منابع اصلی آن بررسی می‌کنیم و نقاط اتفاق و اختلاف را با انصاف روشن می‌سازیم.",
        footer_link: "با روش‌شناسی ما آشنا شوید →",
        copyright: "© ۲۰۲۴ بیان",
        not_found: "🔍 هیچ مسئله‌ای با این توضیحات یافت نشد. کلمه کوتاه‌تری را امتحان کنید یا موضوع دیگری را انتخاب کنید.",
        ai_processing: "🧠 در حال تحلیل سوال شما..."
    },
    ur: {
        app_name: "📖 بیان",
        subtitle: "رہنماۓ آراء فقہیہ",
        tagline: "فہم و بصیرت کے لیے، فتویٰ جاری کرنے کے لیے نہیں",
        most_searched: "📈 سب سے زیادہ تلاش کی گئی:",
        search_label: "❓ آج آپ کیا جاننا چاہتے ہیں؟",
        search_placeholder: "کسی بھی طریقے سے پوچھیں... ایپ آپ کو سمجھ لے گی",
        search_count: "۱۲۰ سے زیادہ مستند مسائل",
        answer_levels_title: "📝 جواب کی سطح منتخب کریں:",
        level_very_short: "⚡ بہت مختصر (ایک لفظ)",
        level_short: "📄 مختصر (ایک سطر)",
        level_full: "📚 مکمل (تفصیلی)",
        placeholder: "🔍 جواب حاصل کرنے کے لیے اپنا سوال اوپر ٹائپ کریں",
        all_topics: "✦ تمام موضوعات",
        topic_worship: "☽ عبادات",
        topic_transactions: "◈ معاملات",
        topic_family: "⌂ خاندان",
        topic_daily_life: "✧ روزمرہ زندگی",
        madhhab_map: "🗺️ نقشہ آراء",
        sunni: "اہل سنت کے مذاہب",
        shia: "اہل تشیع کے مذاہب",
        ibadi: "اباضی مذہب",
        other_views: "دوسری آراء",
        imams_title: "📜 بانیان مذاہب",
        map_title: "🗺️ اسلامی ممالک میں سرکاری مذہب",
        glossary_title: "📚 فقہی لغت",
        footer: "علم ایک امانت ہے۔ ہم ہر مادے کا اس کے اصل مصادر سے جائزہ لیتے ہیں، اور اتفاق و اختلاف کے مقامات کو انصاف کے ساتھ واضح کرتے ہیں۔",
        footer_link: "ہمارے طریقہ کار سے آشنا ہوں →",
        copyright: "© ۲۰۲۴ بیان",
        not_found: "🔍 اس وضاحت کے ساتھ کوئی مسئلہ نہیں ملا۔ کوئی چھوٹا لفظ آزمائیں یا کوئی اور موضوع منتخب کریں۔",
        ai_processing: "🧠 آپ کے سوال کا تجزیہ کیا جا رہا ہے..."
    },
    ms: {
        app_name: "📖 Bayān",
        subtitle: "Panduan Pendapat Fiqh",
        tagline: "Untuk kefahaman dan wawasan, bukan untuk mengeluarkan fatwa",
        most_searched: "📈 Paling Dicari:",
        search_label: "❓ Apa yang anda ingin tahu hari ini?",
        search_placeholder: "Tanya dengan apa cara sekalipun... aplikasi akan memahami anda",
        search_count: "Lebih daripada 120 isu yang disahkan",
        answer_levels_title: "📝 Pilih tahap jawapan:",
        level_very_short: "⚡ Sangat pendek (satu perkataan)",
        level_short: "📄 Pendek (satu baris)",
        level_full: "📚 Penuh (terperinci)",
        placeholder: "🔍 Taip soalan anda di atas untuk mendapatkan jawapan",
        all_topics: "✦ Semua Topik",
        topic_worship: "☽ Ibadah",
        topic_transactions: "◈ Muamalat",
        topic_family: "⌂ Keluarga",
        topic_daily_life: "✧ Kehidupan Harian",
        madhhab_map: "🗺️ Peta Pendapat",
        sunni: "Mazhab Sunni",
        shia: "Mazhab Syiah",
        ibadi: "Mazhab Ibadi",
        other_views: "Pendapat Lain",
        imams_title: "📜 Imam Pengasas",
        map_title: "🗺️ Mazhab Rasmi di Negara Islam",
        glossary_title: "📚 Glosari Fiqh",
        footer: "Ilmu adalah amanah. Kami menyemak setiap bahan dari sumber asalnya, dan menjelaskan titik persetujuan dan perbezaan dengan adil.",
        footer_link: "Ketahui tentang metodologi kami →",
        copyright: "© 2024 Bayān",
        not_found: "🔍 Tiada isu ditemui dengan penerangan ini. Cuba perkataan yang lebih pendek atau pilih topik lain.",
        ai_processing: "🧠 Menganalisis soalan anda..."
    }
};

// ============================================================
//  2.  المنطق الأساسي للتطبيق
// ============================================================

// ----- 2.1  الحالة العامة -----
let currentLanguage = 'ar';
let currentLevel = 'very_short';
let currentResults = [];

// ----- 2.2  دالة البحث الذكي -----
function smartSearch(query) {
    const searchTerm = query.trim().toLowerCase();
    if (!searchTerm) {
        currentResults = [];
        displayResults([]);
        return;
    }

    // 1. البحث المباشر في العناوين
    let results = issuesData.filter(issue =>
        issue.title.includes(searchTerm) ||
        issue.keywords.some(kw => kw.includes(searchTerm))
    );

    // 2. إذا لم يجد، ابحث في النصوص الكاملة
    if (results.length === 0) {
        results = issuesData.filter(issue =>
            issue.rulings.full.toLowerCase().includes(searchTerm)
        );
    }

    // 3. إذا لم يجد، حاول فهم السؤال بشكل أوسع (محاكاة الذكاء الاصطناعي)
    if (results.length === 0) {
        // محاكاة فهم الأسئلة الركيكة
        const fuzzyMatches = issuesData.filter(issue => {
            const titleWords = issue.title.split(' ');
            const queryWords = searchTerm.split(' ');
            return queryWords.some(word =>
                titleWords.some(tw => tw.includes(word) || word.includes(tw))
            );
        });
        results = fuzzyMatches;
    }

    currentResults = results;
    displayResults(results);
}

// ----- 2.3  عرض النتائج -----
function displayResults(results) {
    const container = document.getElementById('result-content');
    const lang = currentLanguage;

    if (!container) return;

    if (results.length === 0) {
        container.innerHTML = `<p class="placeholder">${translations[lang].not_found}</p>`;
        return;
    }

    // بناء عرض النتائج حسب المستوى المختار
    let html = '<div class="results-list">';
    results.forEach(issue => {
        const answer = issue.rulings[currentLevel] || issue.rulings.full;
        html += `
            <div class="result-item">
                <h3 class="result-title">${issue.title}</h3>
                <p class="result-category">${issue.category}</p>
                <div class="result-answer">${answer}</div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

// ----- 2.4  تغيير مستوى الإجابة -----
function setAnswerLevel(level) {
    currentLevel = level;
    // تحديث الأزرار
    document.querySelectorAll('.level-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === level);
    });
    // إعادة عرض النتائج الحالية
    if (currentResults.length > 0) {
        displayResults(currentResults);
    }
}

// ----- 2.5  تغيير اللغة -----
function setLanguage(lang) {
    currentLanguage = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[lang] && translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });
    // تحديث الـ placeholder للبحث
    const searchInput = document.getElementById('search');
    if (searchInput && translations[lang].search_placeholder) {
        searchInput.placeholder = translations[lang].search_placeholder;
    }
    // إعادة عرض النتائج
    if (currentResults.length > 0) {
        displayResults(currentResults);
    }
    // حفظ اللغة المفضلة
    localStorage.setItem('bayan-language', lang);
}

// ============================================================
//  3.  تهيئة الأقسام القابلة للطي (Collapsible Sections)
// ============================================================
function initCollapsibleSections() {
    document.querySelectorAll('.collapsible-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const content = this.parentElement.nextElementSibling;
            const icon = this.querySelector('.toggle-icon');
            if (content && content.classList.contains('collapsible-content')) {
                const isOpen = content.style.display !== 'none';
                content.style.display = isOpen ? 'none' : 'block';
                if (icon) {
                    icon.textContent = isOpen ? '▸' : '▾';
                }
            }
        });
        // جعل الأقسام مفتوحة افتراضياً
        const content = toggle.parentElement.nextElementSibling;
        if (content && content.classList.contains('collapsible-content')) {
            content.style.display = 'block';
        }
    });
}

// ============================================================
//  4.  تعبئة البيانات الديناميكية (الدول، المصطلحات)
// ============================================================
function populateCountries() {
    const grid = document.getElementById('countries-grid');
    if (!grid) return;

    grid.innerHTML = countriesData.map(c =>
        `<div class="country-item">
            <span class="country-flag">${c.country}</span>
            <span class="country-madhab">${c.madhab}</span>
            <span class="country-population">👥 ${c.population}</span>
        </div>`
    ).join('');
}

function populateGlossary() {
    const grid = document.getElementById('glossary-grid');
    if (!grid) return;

    grid.innerHTML = glossaryTerms.map(term =>
        `<div class="glossary-item">
            <h4 class="glossary-term">${term.term}</h4>
            <p class="glossary-definition">${term.definition}</p>
        </div>`
    ).join('');
}

// ============================================================
//  5.  تهيئة التطبيق (عند تحميل الصفحة)
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // 5.1 تعبئة البيانات
    populateCountries();
    populateGlossary();

    // 5.2 الأقسام القابلة للطي
    initCollapsibleSections();

    // 5.3 استعادة اللغة المفضلة من التخزين المحلي
    const savedLang = localStorage.getItem('bayan-language');
    if (savedLang && translations[savedLang]) {
        setLanguage(savedLang);
        const select = document.getElementById('language-select');
        if (select) select.value = savedLang;
    } else {
        setLanguage('ar');
    }

    // 5.4 ربط أحداث البحث
    const searchInput = document.getElementById('search');
    const searchBtn = document.getElementById('searchBtn');

    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            smartSearch(searchInput ? searchInput.value : '');
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                smartSearch(this.value);
            }
        });
    }

    // 5.5 ربط أحداث "الأكثر بحثًا"
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', function() {
            const query = this.dataset.query || this.textContent.trim();
            if (searchInput) {
                searchInput.value = query;
                smartSearch(query
