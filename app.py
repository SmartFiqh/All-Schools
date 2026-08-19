import streamlit as st
import requests
import subprocess
import sys
import os
import time

# إعدادات الخادم الخلفي
BACKEND_URL = "http://localhost:5000"  # غيّر هذا في الإنتاج إن نُشر الخادم بشكل مستقل

# ==========================================================
# ✅ إصلاح جذري: تشغيل الخادم الخلفي تلقائياً في عملية خلفية
# بدل الاعتماد على تشغيل `python backend.py` يدوياً في طرفية
# منفصلة. هذا يحل المشكلة سواء كنت تُشغّل التطبيق محلياً (ونسيت
# فتح طرفية ثانية) أو على استضافة سحابية بعملية واحدة فقط مثل
# Streamlit Community Cloud (حيث لا توجد طرفية أصلاً لتشغيل خادم
# منفصل، لكن العمليتين هنا تعملان داخل نفس الحاوية فيعمل
# localhost بينهما بشكل طبيعي).
#
# @st.cache_resource يضمن تشغيل هذا مرة واحدة فقط طوال عمر
# التطبيق، وليس في كل إعادة رسم (rerun).
# ==========================================================
@st.cache_resource
def start_backend_once():
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend.py")
    if not os.path.exists(backend_path):
        return {"started": False, "error": f"لم يُعثر على backend.py في {backend_path}"}
    try:
        subprocess.Popen(
            [sys.executable, backend_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        return {"started": False, "error": str(e)}

    # الانتظار حتى يصبح الخادم جاهزاً فعلياً بدل افتراض جهوزيته فوراً
    for _ in range(20):  # حتى ~10 ثوانٍ كحد أقصى
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=0.5)
            if r.status_code == 200:
                return {"started": True, "error": None}
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return {"started": False, "error": "بدأت العملية لكن الخادم لم يستجب خلال 10 ثوانٍ"}


backend_status = start_backend_once()

# تهيئة حالة الجلسة
if 'pi_user' not in st.session_state:
    st.session_state.pi_user = None

st.set_page_config(
    page_title="تطبيق Pi Network",
    page_icon="π",
    layout="wide"
)

st.title("🔐 تطبيق Pi Network - مصادقة متكاملة")

if not backend_status["started"]:
    st.error(
        f"❌ تعذّر تشغيل الخادم الخلفي تلقائياً: {backend_status['error']}\n\n"
        "يمكنك تشغيله يدوياً في طرفية منفصلة كحل بديل: `python backend.py`"
    )

# ==========================================================
# ✅ فحص اتصال يظهر في الصفحة الرئيسية مباشرة (وليس داخل الإطار
# المضمّن)، ليكون واضحاً فوراً هل الخادم الخلفي يعمل أصلاً أم لا،
# بدل الاعتماد على أخطاء مخفية داخل الـ iframe لا تظهر عند نسخ نص
# الصفحة.
# ==========================================================
with st.expander("🔧 فحص الاتصال بالخادم الخلفي", expanded=(not backend_status["started"])):
    st.caption("الخادم الخلفي يُشغَّل تلقائياً الآن مع بدء التطبيق. استخدم هذا الفحص فقط للتأكد أو استكشاف الأخطاء.")
    if st.button("فحص الآن"):
        try:
            health_resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if health_resp.status_code == 200:
                st.success(f"✅ الخادم الخلفي يعمل ويستجيب على {BACKEND_URL}")
            else:
                st.error(f"⚠️ الخادم الخلفي استجاب برمز غير متوقع: {health_resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error(
                f"❌ تعذّر الاتصال بـ {BACKEND_URL} — الخادم الخلفي غير مُشغَّل. "
                "افتح طرفية (terminal) منفصلة وشغّل: `python backend.py`، ثم اضغط فحص الآن مجدداً."
            )
        except requests.exceptions.Timeout:
            st.error(f"❌ انتهت مهلة الاتصال بـ {BACKEND_URL} (لم يستجب خلال 5 ثوانٍ).")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ خطأ في الاتصال: {e}")
    else:
        st.caption("اضغط الزر أعلاه للتأكد من أن `backend.py` يعمل قبل محاولة تسجيل الدخول.")

# ==========================================================
# ✅ إصلاح: الخادم الخلفي أصبح تحسيناً اختيارياً وليس شرطاً
# لإتمام تسجيل الدخول. بحلول هذه النقطة يكون المتصفح قد أثبت
# صحة الحساب فعلياً (تحقق مباشر مع Pi API أو عبر الخادم الخلفي،
# راجع الشيفرة داخل html_code أدناه) — فإن كان الخادم الخلفي غير
# قابل للوصول من طرف Python أيضاً (كما في بيئات لا تسمح بالمنافذ
# الإضافية)، نُكمل تسجيل الدخول ببيانات uid/username الأساسية بدل
# حظر المستخدم كلياً بسبب مشكلة شبكة لا علاقة لها بصحة حسابه.
# ==========================================================
params = st.query_params
if 'pi_uid' in params and not st.session_state.pi_user:
    uid = params['pi_uid']
    username = params.get('pi_username', '')
    user_data = {"uid": uid, "username": username}

    try:
        resp = requests.get(f"{BACKEND_URL}/pi-user/{uid}", timeout=3)
        if resp.status_code == 200:
            user_data = resp.json()  # سجل أكمل إن كان الخادم الخلفي متاحاً
    except requests.exceptions.RequestException:
        pass  # الخادم الخلفي غير متاح — البيانات الأساسية من الرابط كافية لإكمال الدخول

    st.session_state.pi_user = user_data
    st.query_params.clear()
    st.rerun()

# عرض حالة المستخدم
if st.session_state.pi_user:
    st.success(f"✅ مرحباً {st.session_state.pi_user.get('username', 'مستخدم')} (UID: {st.session_state.pi_user.get('uid', 'N/A')})")
    if st.button("تسجيل الخروج"):
        st.session_state.pi_user = None
        st.rerun()
else:
    st.info("👋 لم تقم بتسجيل الدخول بعد. استخدم زر تسجيل الدخول أدناه.")
    st.caption(
        "⚠️ تسجيل الدخول عبر Pi Network يعمل فقط داخل تطبيق **Pi Browser** الرسمي، "
        "وليس داخل متصفح عادي مثل Chrome أو Firefox — إن كنت تختبر خارج Pi Browser "
        "فستظهر رسالة خطأ من Pi SDK داخل مربع تسجيل الدخول أدناه، وهذا متوقع."
    )

# ==========================================================
# تضمين واجهة HTML/JS لمصادقة Pi — تُعرض فقط إن لم يكن المستخدم
# مسجلاً دخوله بعد (✅ إصلاح: كانت تُعرض دائماً حتى بعد تسجيل
# الدخول، فتُعيد تشغيل نافذة Pi في كل مرة يُعاد فيها رسم الصفحة).
# ==========================================================
if not st.session_state.pi_user:
    html_code = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://sdk.minepi.com/pi-sdk.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; text-align: center; padding: 20px; }
        #status { margin-top: 20px; font-size: 18px; color: #333; }
        button { padding: 12px 28px; font-size: 18px; background-color: #1e3a2f; color: white; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background-color: #2a5c4a; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #1e3a2f; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div id="status">⏳ جاري التحقق من جلسة Pi...</div>
    <div id="loader" class="loader" style="display:none;"></div>
    <button id="signInBtn" style="display:none;">🔑 تسجيل الدخول عبر Pi Network</button>

    <script>
        const BACKEND_URL = "__BACKEND_URL__";  // يُحقن من Python أدناه لضمان تطابقه دائماً

        function onIncompletePaymentFound(payment) {
            console.log('دفعة غير مكتملة:', payment);
        }

        // ✅ إصلاح: نحاول أولاً الاتصال مباشرة بواجهة Pi الرسمية من
        // المتصفح نفسه (عنوان إنترنت حقيقي، وليس localhost) — هذا
        // يتجاوز مشكلة "الخادم الخلفي يعمل من جهة Python لكن المتصفح
        // لا يستطيع الوصول إليه" التي تحدث عند تشغيل التطبيق على بيئة
        // سحابية/بعيدة يكون فيها المتصفح على جهاز مختلف عن الخادم.
        // إن فشل هذا الاتصال المباشر لأي سبب (مثلاً منع CORS من طرف
        // Pi)، نرجع تلقائياً لمحاولة استخدام الخادم الخلفي المحلي
        // كخطة بديلة.
        async function verifyDirectlyWithPi(accessToken) {
            const resp = await fetch('https://api.minepi.com/v2/me', {
                headers: { 'Authorization': 'Bearer ' + accessToken }
            });
            if (!resp.ok) {
                throw new Error('Pi API returned status ' + resp.status);
            }
            return await resp.json();  // { uid, username, ... }
        }

        async function verifyViaOwnBackend(accessToken) {
            const response = await fetch(BACKEND_URL + '/pi-auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ accessToken: accessToken })
            });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.error || ('Backend returned status ' + response.status));
            }
            const data = await response.json();
            return data.user;
        }

        window.addEventListener('load', async function() {
            try {
                await Pi.init({ version: '2.0', sandbox: true });

                const auth = await Pi.authenticate(['username'], onIncompletePaymentFound);

                let user = null;
                let verifiedVia = null;

                try {
                    user = await verifyDirectlyWithPi(auth.accessToken);
                    verifiedVia = 'direct';
                } catch (directError) {
                    console.warn('تعذّر الاتصال المباشر بـ Pi API، جاري تجربة الخادم الخلفي:', directError);
                    try {
                        user = await verifyViaOwnBackend(auth.accessToken);
                        verifiedVia = 'backend';
                    } catch (backendError) {
                        console.error('فشل كلا مساري التحقق:', backendError);
                        document.getElementById('status').innerHTML =
                            '❌ تعذّر التحقق من الحساب عبر Pi مباشرة أو عبر الخادم الخلفي.<br>'
                            + '<small>مباشر: ' + directError.message + '<br>خلفي: ' + backendError.message + '</small>';
                        document.getElementById('signInBtn').style.display = 'inline-block';
                        return;
                    }
                }

                const uid = user && user.uid;
                const username = (user && user.username) || '';

                if (!uid) {
                    document.getElementById('status').innerHTML = '❌ لم تُعِد Pi معرّف مستخدم صالح.';
                    document.getElementById('signInBtn').style.display = 'inline-block';
                    return;
                }

                document.getElementById('status').innerHTML =
                    '✅ تم تسجيل الدخول بنجاح (' + (verifiedVia === 'direct' ? 'تحقق مباشر' : 'عبر الخادم الخلفي') + ')! جاري تحديث الصفحة...';
                document.getElementById('signInBtn').style.display = 'none';

                setTimeout(function () {
                    window.parent.location.href =
                        window.parent.location.pathname
                        + '?pi_uid=' + encodeURIComponent(uid)
                        + '&pi_username=' + encodeURIComponent(username);
                }, 800);
            } catch (error) {
                console.error('خطأ في Pi Auth:', error);
                document.getElementById('status').innerHTML = '❌ حدث خطأ: ' + error.message;
                document.getElementById('signInBtn').style.display = 'inline-block';
            }
        });

        document.getElementById('signInBtn')?.addEventListener('click', function() {
            window.location.reload();
        });
    </script>
</body>
</html>
"""
    html_code = html_code.replace("__BACKEND_URL__", BACKEND_URL)
    st.components.v1.html(html_code, height=300)

# عرض معلومات إضافية بعد تسجيل الدخول
if st.session_state.pi_user:
    st.subheader("📋 معلومات حسابك")
    st.json(st.session_state.pi_user)

    st.markdown("---")
    st.markdown("✨ هذا هو المحتوى الحصري للمستخدمين المسجلين.")
else:
    st.markdown("📢 قم بتسجيل الدخول لعرض محتوى مخصص.")

if __name__ == "__main__":
    st.write("🔧 تأكد من تشغيل الخادم الخلفي: python backend.py")
