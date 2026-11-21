import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="المستشار القانوني الذكي رصين AI",
    page_icon="⚖️",
    layout="wide",
)

MAX_TENDER_CHARS = 22000
MAX_CONTRACTOR_CHARS = 16000

CANDIDATE_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

B2B_TARGET_USERS = [
    "المقاولون والمؤسسات الاقتصادية المشاركة في الصفقات والمناقصات",
    "المؤسسات الناشئة وحاملو المشاريع المبتكرة في العقود والشراكات",
    "شركات المساهمة البسيطة والشركات التجارية",
    "مكاتب الدراسات والاستشارة الهندسية والقانونية",
    "المتعاملون من الباطن (Sous-traitants) والموردون",
    "المستشارون القانونيون ومديرو العقود والامتثال داخل المؤسسات",
]

B2B_KEY_DOCUMENTS = [
    "السجل التجاري (Extrait du registre de commerce)",
    "البطاقة الجبائية (NIF)، الرقم الإحصائي (NIS)، وشهادات الأداء والضرائب",
    "شهادات شبه الضمان الاجتماعي (CNAS / CASNOS / CACOBATPH)",
    "القانون الأساسي (Statuts) وتفويض التوقيع والتمثيل القانوني",
    "شهادات التأهيل والتصنيف المهني أو الاعتمادات",
    "المراجع المهنية والقدرات التقنية والمالية",
    "التواقيع والأختام والتصريحات الموقعة والمصادق عليها",
]

LEGAL_REFERENCES_CORPUS = """
المرجعية القانونية الجزائرية الشاملة المعتمدة في منصة رصين AI (لمساري B2G وB2B):

1. القانون رقم 23-12 المؤرخ في 05 أوت 2023 المحدد للقواعد العامة المتعلقة بالصفقات العمومية:
   - مبادئ حرية الوصول إلى الطلبات العمومية، المساواة في معاملة المتعهدين، وشفافية الإجراءات.
   - أحكام دفاتر الشروط، ملف الترشح والعرض التقني والمالي، الآجال، الكفالات والضمانات، والطعون.
   - أحكام وشروط الإلغاء (إلغاء الإجراء، عدم الجدوى، أو الإلغاء لأسباب تتعلق بالمصلحة العامة أو الإخلال بالشروط القانونية) والسند القانوني الصحيح الواجب تطبيقه.

2. القانون العضوي رقم 06-01 المؤرخ في 20 فيفري 2006 المتعلق بالوقاية من الفساد ومكافحته:
   - قواعد النزاهة والشفافية، منع تضارب المصالح، تجريم الامتيازات غير المبررة أو المحاباة أو استغلال النفوذ في إبرام وتنفيذ العقود والصفقات.

3. القانون رقم 18-07 المؤرخ في 10 جوان 2018 المتعلق بحماية الأشخاص الطبيعيين في مجال معالجة المعطيات ذات الطابع الشخصي، المعدل والمتمم بالقانون رقم 25-11:
   - مشروعية المعالجة، الغاية المحددة والمشروعة، تناسب المعطيات، مدة الاحتفاظ، تأمين وسرية المعطيات، وحقوق الأشخاص المعنيين.

4. القانون المدني الجزائري (الأمر رقم 75-58 المعدل والمتمم):
   - أركان وشروط صحة العقود والالتزامات (التراضي، المحل، السبب، الأهلية، وصلاحيات التوقيع والتمثيل القانوني).
   - أحكام البطلان، الإبطال، الفسخ، والإلغاء، والآثار القانونية المترتبة على الإخلال بالالتزامات التعاقدية.

5. القانون التجاري الجزائري (الأمر رقم 75-59 المعدل والمتمم):
   - قواعد الأعمال التجارية، السجل التجاري، أهلية وصفة التاجر والمؤسسة الاقتصادية، والعقود والالتزامات التجارية بين المتعاملين.

6. القانون رقم 15-04 المحدد للقواعد العامة المتعلقة بالتوقيع والتصديق الإلكترونيين، والقانون رقم 26-02 ذات الصلة بالنشاطات الرقمية:
   - حجية الوثائق والمحررات والتواقيع الإلكترونية، شروط التصديق الإلكتروني، والأحكام المنظمة للأنشطة والمعاملات الرقمية.

7. القانون رقم 22-09 المتعلق بشركة المساهمة البسيطة:
   - قواعد تأسيس وتسيير وصلاحيات التمثيل والتوقيع والالتزامات القانونية لشركات المساهمة البسيطة عند تدقيق ملفات المتعاملين الاقتصاديين في B2B.
""".strip()

CUSTOM_STYLES = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f4f7fb 0%, #eef3f9 100%);
    }
    .raseen-hero {
        background: linear-gradient(135deg, #0f2942 0%, #1b4368 100%);
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 14px;
        border-bottom: 4px solid #d4a32b;
        box-shadow: 0 6px 18px rgba(15, 41, 66, 0.12);
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .raseen-hero-title {
        margin: 0;
        font-size: 1.55rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.35;
    }
    .raseen-hero-sub {
        margin: 6px 0 0 0;
        font-size: 0.98rem;
        color: #f3d57b;
        font-weight: 500;
    }
    .raseen-card {
        background-color: #ffffff;
        border: 1px solid #d9e2ec;
        border-right: 4px solid #1b4368;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(15, 41, 66, 0.05);
    }
    .raseen-card-gold {
        border-right-color: #d4a32b;
    }
    .raseen-card h4 {
        margin-top: 0;
        color: #0f2942;
        font-size: 1.05rem;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f2942 0%, #1d4e7a 100%);
        color: #ffffff;
        border: 1px solid #d4a32b;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.65rem 1.2rem;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #163a5c 0%, #245f94 100%);
        border-color: #f3d57b;
    }
</style>
""".strip()

RASEEN_LOGO_SVG = """
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="شعار رصين AI">
  <rect x="2" y="2" width="60" height="60" rx="14" fill="#173857" stroke="#D4A32B" stroke-width="2.5"/>
  <path d="M32 13L46 19V30.5C46 39.8 39.9 47.9 32 51C24.1 47.9 18 39.8 18 30.5V19L32 13Z" fill="#0E2438" stroke="#F3D57B" stroke-width="2"/>
  <path d="M32 20V39" stroke="#F3D57B" stroke-width="2.4" stroke-linecap="round"/>
  <path d="M23 25H41" stroke="#F3D57B" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M23 25L19.5 32H26.5L23 25Z" fill="#D4A32B"/>
  <path d="M41 25L37.5 32H44.5L41 25Z" fill="#D4A32B"/>
  <circle cx="46" cy="46" r="8" fill="#D4A32B" stroke="#0E2438" stroke-width="2"/>
  <path d="M42.8 46.2L45 48.4L49.4 43.8" stroke="#0F2942" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""".strip()


def get_groq_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("يرجى إضافة GROQ_API_KEY في إعدادات Secrets على Streamlit Cloud.")
        st.stop()
    return Groq(api_key=api_key)


def get_available_models_order(client: Groq) -> list[str]:
    ordered = []
    try:
        models_resp = client.models.list()
        available_ids = [m.id for m in getattr(models_resp, "data", []) if getattr(m, "id", None)]
        for preferred in CANDIDATE_GROQ_MODELS:
            if preferred in available_ids and preferred not in ordered:
                ordered.append(preferred)
        for mid in available_ids:
            if mid not in ordered and ("llama" in mid or "gemma" in mid or "mixtral" in mid or "qwen" in mid or "deepseek" in mid):
                ordered.append(mid)
    except Exception:
        pass

    for fallback in CANDIDATE_GROQ_MODELS:
        if fallback not in ordered:
            ordered.append(fallback)
    return ordered


def _trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].strip() + "\n\n[... تم الاقتطاع حفاظاً على حد طول النص المرسل للنموذج ...]"


def extract_pdf_text_with_ocr_fallback(uploaded_file) -> tuple[str, int, str]:
    raw_bytes = uploaded_file.getvalue()
    reader = PdfReader(io.BytesIO(raw_bytes))
    total_pages = len(reader.pages)
    extracted_pages = []
    missing_pages = []

    for idx, page in enumerate(reader.pages, start=1):
        txt = (page.extract_text() or "").strip()
        if txt:
            extracted_pages.append(f"[صفحة {idx}]\n{txt}")
        else:
            missing_pages.append(idx)

    if extracted_pages and not missing_pages:
        return "\n\n".join(extracted_pages), total_pages, "نص مباشر من PDF"

    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(raw_bytes)
        combined_pages = []
        for idx, page in enumerate(reader.pages, start=1):
            direct_txt = (page.extract_text() or "").strip()
            if direct_txt:
                combined_pages.append(f"[صفحة {idx}]\n{direct_txt}")
            elif idx - 1 < len(images):
                ocr_txt = (pytesseract.image_to_string(images[idx - 1], lang="ara+fra") or "").strip()
                if ocr_txt:
                    combined_pages.append(f"[صفحة {idx} - OCR]\n{ocr_txt}")
        if combined_pages:
            return "\n\n".join(combined_pages), total_pages, "نص مباشر + استخراج بصري (OCR)"
    except Exception:
        pass

    if extracted_pages:
        return "\n\n".join(extracted_pages), total_pages, "نص جزئي من PDF"

    return "", total_pages, "غير مستخرج"


def extract_contractor_files_text(contractor_files) -> str:
    if not contractor_files:
        return ""

    parts = []
    for f in contractor_files:
        name_lower = f.name.lower()
        if name_lower.endswith(".pdf"):
            txt, pages, method = extract_pdf_text_with_ocr_fallback(f)
            if txt:
                parts.append(f"=== وثيقة ملف المتعهد: {f.name} ({pages} صفحات - {method}) ===\n{txt}")
            else:
                parts.append(
                    f"=== وثيقة ملف المتعهد: {f.name} ({pages} صفحات) ===\n[ملف مرفق بدون نص رقمي مباشر؛ يجب التحقق من الوثائق والتواقيع والأختام المرفقة فيه]"
                )
        else:
            try:
                from PIL import Image
                import pytesseract

                img = Image.open(io.BytesIO(f.getvalue()))
                ocr_txt = (pytesseract.image_to_string(img, lang="ara+fra") or "").strip()
                if ocr_txt:
                    parts.append(f"=== صورة وثيقة المتعهد: {f.name} ===\n{ocr_txt}")
                else:
                    parts.append(f"=== صورة وثيقة المتعهد: {f.name} ===\n[صورة وثيقة/توقيع/ختم مرفقة]")
            except Exception:
                parts.append(f"=== مرفق المتعهد: {f.name} ===\n[مرفق وثائق/تواقيع]")

    return _trim_text("\n\n".join(parts), MAX_CONTRACTOR_CHARS)


def build_system_prompt(language: str, circuit: str) -> str:
    if language == "العربية":
        lang_rule = "اكتب كامل التقرير باللغة العربية القانونية الواضحة والدقيقة."
    elif language == "Français":
        lang_rule = "Rédige l'intégralité du rapport en français juridique précis, clair et structuré."
    else:
        lang_rule = "اكتب التقرير باللغة العربية مع إدراج المصطلحات والتحليلات المقابلة بالفرنسية (عربي / فرنسي) بوضوح."

    mandatory_rules = """
قواعد إلزامية في جميع الحالات وفي كلا المسارين (B2G وB2B):
1. الإشارات الضوئية في كل بند أو عنصر أو مقارنة:
   - 🔴 أحمر: خطأ (مخالفة قانونية أو خلل جوهري أو نقص مؤثر في الوثائق أو التواقيع أو الشروط).
   - 🟠 برتقالي: تنبيه (نقطة تحتاج إلى مراجعة أو توضيح أو استكمال أو تحقق إضافي).
   - 🟢 أخضر: صحيح (بند أو وثيقة أو توقيع أو إجراء مطابق ومستوفٍ).
2. عند ظهور أي (🔴 أحمر: خطأ) أو (🟠 برتقالي: تنبيه): يجب فوراً ذكر القانون أو النص القانوني الصحيح الواجب تطبيقه من المدونة القانونية المعتمدة مع بيان الحكم القانوني الصحيح.
3. في كل حالة تتعلق بالإلغاء (إلغاء الإجراء، إلغاء الصفقة أو المناقصة، إلغاء العقد أو الفسخ أو الإبطال، أو إلغاء بند أو شرط أو عرض أو وثيقة أو توقيع): يجب تحديد القانون الصحيح الواجب تطبيقه بوضوح، وبيان الشروط والأحكام القانونية الصحيحة للإلغاء وآثاره.
""".strip()

    if circuit.startswith("B2G"):
        circuit_rule = """
المسار المختار هو B2G (الصفقات العمومية والمناقصات العمومية):
ابدأ بجدول أو ملخص يبرز الإشارات الضوئية (🔴 أحمر: خطأ / 🟠 برتقالي: تنبيه / 🟢 أخضر: صحيح) مع ذكر القانون الصحيح الواجب تطبيقه لكل خطأ أو تنبيه أو حالة إلغاء، ثم فصّل التحليل القانوني وخصص قسماً واضحاً لحالات الإلغاء والقانون الصحيح الواجب تطبيقه فيها.
""".strip()
    else:
        circuit_rule = """
المسار المختار هو B2B (مقارنة دفتر الشروط / العقد بملف المقاول أو المؤسسة الاقتصادية المشاركة):
يستفيد من هذا المسار: المقاولون والمؤسسات الاقتصادية، المؤسسات الناشئة وحاملو المشاريع المبتكرة، شركات المساهمة البسيطة والشركات التجارية، مكاتب الدراسات والاستشارة، المتعاملون من الباطن، والمستشارون القانونيون ومديرو العقود.
قارن بدقة بين متطلبات دفتر الشروط أو العقد وبين ما يملكه المقاول أو المؤسسة الاقتصادية من وثائق وتواقيع، مع التركيز على:
- السجل التجاري، البطاقة الجبائية والرقم الإحصائي وشهادات الأداء والضرائب، شهادات شبه الضمان الاجتماعي، القانون الأساسي وتفويض التوقيع، شهادات التأهيل والتصنيف أو الاعتماد، المراجع المهنية والقدرات، والتواقيع والأختام والتصريحات.
وطبّق الإشارات الضوئية (🔴 أحمر: خطأ / 🟠 برتقالي: تنبيه / 🟢 أخضر: صحيح) على كل وثيقة أو توقيع أو بند، مع ذكر القانون الصحيح الواجب تطبيقه فوراً عند أي خطأ أو تنبيه أو حالة إلغاء.
""".strip()

    return f"""
أنت المستشار القانوني الذكي لمنصة رصين AI المتخصصة في تدقيق العقود والصفقات العمومية والمناقصات وفق القانون الجزائري.
{lang_rule}

{mandatory_rules}

{circuit_rule}

المرجعية القانونية المعتمدة:
{LEGAL_REFERENCES_CORPUS}
""".strip()


def run_audit(
    client: Groq,
    language: str,
    circuit: str,
    sector: str,
    b2b_profile: str,
    tender_name: str,
    tender_text: str,
    contractor_summary: str,
) -> tuple[str, str]:
    safe_tender_text = _trim_text(tender_text, MAX_TENDER_CHARS)

    user_content = f"""
اللغة المطلوبة: {language}
المسار: {circuit}
القطاع: {sector}
ملف دفتر الشروط / العقد / المناقصة: {tender_name}

محتوى دفتر الشروط / العقد / المناقصة:
\"\"\"
{safe_tender_text}
\"\"\"
""".strip()

    if circuit.startswith("B2B"):
        user_content += f"""

الفئة المستفيدة في مسار B2B: {b2b_profile}
الوثائق الأساسية الواجب مطابقتها مع دفتر الشروط: {", ".join(B2B_KEY_DOCUMENTS)}

ملف المقاول / المؤسسة الاقتصادية المشاركة في الصفقة أو المناقصة (الوثائق والتواقيع المرفقة):
\"\"\"
{contractor_summary if contractor_summary else "لم يتم رفع أو استخراج نصوص من ملفات المتعهد بعد؛ قارن متطلبات دفتر الشروط بالوثائق الأساسية (السجل التجاري، الضرائب، شبه الضمان الاجتماعي، القانون الأساسي، التأهيل، المراجع، والتواقيع والأختام) ونبّه إلى النواقص المحتملة مع تطبيق الإشارات الضوئية والقانون الصحيح الواجب تطبيقه."}
\"\"\"
"""

    models_to_try = get_available_models_order(client)
    last_error = None

    for model_name in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": build_system_prompt(language, circuit)},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
            )
            content = (completion.choices[0].message.content or "").strip()
            if content:
                return content, model_name
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"تعذر تشغيل التدقيق على أي نموذج متاح في Groq. آخر خطأ: {last_error}")


st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="raseen-hero">
        <div>{RASEEN_LOGO_SVG}</div>
        <div>
            <h1 class="raseen-hero-title">منصة التدقيق القانوني الذكي — المستشار القانوني الذكي رصين AI</h1>
            <p class="raseen-hero-sub">خاص بتدقيق العقود والصفقات العمومية والمناقصات</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("اختيار اللغة")
    selected_language = st.selectbox(
        "اللغة",
        options=["العربية", "Français", "ثنائي اللغة (عربي / فرنسي)"],
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("إعدادات المسار والقطاع")
    circuit = st.selectbox(
        "المسار",
        options=["B2G (الصفقات العمومية والمناقصات)", "B2B (ملف المقاول / المؤسسة الاقتصادية)"],
    )
    sector = st.selectbox(
        "القطاع",
        options=[
            "البناء والأشغال العمومية (Travaux)",
            "الخدمات العامة (Services Publics)",
            "التوريدات والمعدات (Fournitures)",
            "الرقمنة والخدمات التقنية",
        ],
    )

st.subheader("تحميل دفتر الشروط / العقد / المناقصة (PDF)")
tender_pdf = st.file_uploader("اختر ملف دفتر الشروط أو العقد أو المناقصة (PDF)", type=["pdf"], key="tender_pdf")

b2b_profile = B2B_TARGET_USERS[0]
contractor_files = []

if circuit.startswith("B2B"):
    st.divider()
    st.markdown("### الفئات المستفيدة والوثائق المطلوب مطابقتها مع دفتر الشروط (B2B)")
    b2b_profile = st.selectbox("اختر الفئة المستفيدة في مسار B2B", options=B2B_TARGET_USERS)

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        users_html = "".join(f"<li>{item}</li>" for item in B2B_TARGET_USERS)
        st.markdown(
            f"""
            <div class="raseen-card">
                <h4>من يحتاج هذا التطبيق في مسار B2B؟</h4>
                <ul>{users_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with info_col2:
        docs_html = "".join(f"<li>{doc}</li>" for doc in B2B_KEY_DOCUMENTS)
        st.markdown(
            f"""
            <div class="raseen-card raseen-card-gold">
                <h4>الوثائق المهمة لمطابقتها مع دفتر الشروط</h4>
                <ul>{docs_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("تحميل ملف المقاول أو المؤسسة الاقتصادية المشاركة في الصفقة أو المناقصة")
    contractor_files = st.file_uploader(
        "ارفع وثائق وتواقيع المقاول أو المؤسسة الاقتصادية (السجل التجاري، الشهادات، القانون الأساسي، التواقيع — PDF أو صور)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="contractor_files",
    )

if st.button("تشغيل التدقيق القانوني", type="primary", use_container_width=True):
    if tender_pdf is None:
        st.warning("يرجى تحميل ملف دفتر الشروط أو العقد أو المناقصة (PDF) أولاً.")
        st.stop()

    try:
        tender_text, tender_pages, tender_method = extract_pdf_text_with_ocr_fallback(tender_pdf)
    except Exception as exc:
        st.error(f"تعذر قراءة ملف PDF: {exc}")
        st.stop()

    if not tender_text:
        st.error(
            f"تم رفع الملف ({tender_pdf.name} - {tender_pages} صفحات)، لكن لم يتم استخراج نص منه. تأكد من أن الملف يحتوي على نص قابل للنسخ أو أضف مكتبتي pdf2image وpytesseract لقراءة الصفحات المصورة."
        )
        st.stop()

    contractor_text = ""
    if circuit.startswith("B2B"):
        contractor_text = extract_contractor_files_text(contractor_files)
        if not contractor_files:
            st.info("ملاحظة: لم يتم رفع ملف للمقاول أو المؤسسة الاقتصادية؛ سيتم تدقيق دفتر الشروط وتحديد الأوراق والتواقيع المطلوبة من المتعهد.")

    st.markdown("### الإشارات الضوئية للتدقيق القانوني")
    col_red, col_amber, col_green = st.columns(3)
    with col_red:
        st.error("🔴 أحمر: خطأ + القانون الصحيح الواجب تطبيقه")
    with col_amber:
        st.warning("🟠 برتقالي: تنبيه + القانون الصحيح الواجب تطبيقه")
    with col_green:
        st.success("🟢 أخضر: صحيح")

    with st.spinner("جاري إجراء التدقيق القانوني عبر الذكاء الاصطناعي..."):
        try:
            groq_client = get_groq_client()
            report, used_model = run_audit(
                client=groq_client,
                language=selected_language,
                circuit=circuit,
                sector=sector,
                b2b_profile=b2b_profile,
                tender_name=f"{tender_pdf.name} ({tender_pages} صفحات - {tender_method})",
                tender_text=tender_text,
                contractor_summary=contractor_text,
            )
            st.caption(f"النموذج المنفّذ: {used_model}")
            st.markdown("### تقرير المستشار القانوني الذكي — رصين AI")
            st.markdown(report)
            with st.expander("المرجعية القانونية المعتمدة في التدقيق"):
                st.text(LEGAL_REFERENCES_CORPUS)
        except Exception as exc:
            st.error(f"حدث خطأ أثناء تنفيذ التدقيق: {exc}") 
