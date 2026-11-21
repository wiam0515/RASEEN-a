import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="المستشار القانوني الذكي رصين AI",
    page_icon="⚖️",
    layout="wide",
)

MAX_TENDER_CHARS = 24000
MAX_CONTRACTOR_CHARS = 18000

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


def get_groq_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("يرجى إضافة GROQ_API_KEY في إعدادات Secrets على Streamlit Cloud.")
        st.stop()
    return Groq(api_key=api_key)


def _trim_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].strip() + "\n\n[... تم الاقتطاع حفاظاً على حد طول النص المرسل للنموذج ...]", True


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

    joined = "\n\n".join(parts)
    trimmed, _ = _trim_text(joined, MAX_CONTRACTOR_CHARS)
    return trimmed


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
قارن بدقة بين متطلبات دفتر الشروط أو العقد وبين ما يملكه المقاول أو المؤسسة الاقتصادية من وثائق وإثباتات وتواقيع، مع تطبيق الإشارات الضوئية (🔴 أحمر: خطأ / 🟠 برتقالي: تنبيه / 🟢 أخضر: صحيح) على عناصر المقارنة (الوثائق المتوفرة والناقصة، التواقيع والمصادقات والأختام المتوفرة والناقصة، وحالات الإلغاء أو الفسخ)، وذكر القانون الصحيح الواجب تطبيقه فوراً عند أي خطأ أو تنبيه أو إلغاء.
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
    tender_name: str,
    tender_text: str,
    contractor_summary: str,
) -> str:
    safe_tender_text, _ = _trim_text(tender_text, MAX_TENDER_CHARS)

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

ملف المقاول / المؤسسة الاقتصادية المشاركة في الصفقة أو المناقصة (الوثائق والتواقيع المرفقة):
\"\"\"
{contractor_summary if contractor_summary else "لم يتم رفع أو استخراج نصوص من ملفات المتعهد بعد؛ قارن متطلبات دفتر الشروط بالوثائق والتواقيع والصلاحيات القانونية المطلوبة من المقاول أو المؤسسة الاقتصادية ونبّه إلى النواقص المحتملة مع تطبيق الإشارات الضوئية والقانون الصحيح الواجب تطبيقه."}
\"\"\"
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_system_prompt(language, circuit)},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return (completion.choices[0].message.content or "").strip()


st.title("منصة التدقيق القانوني الذكي — المستشار القانوني الذكي رصين AI")
st.caption("خاص بتدقيق العقود والصفقات العمومية والمناقصات")

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

contractor_files = []
if circuit.startswith("B2B"):
    st.divider()
    st.subheader("تحميل ملف المقاول أو المؤسسة الاقتصادية المشاركة في الصفقة أو المناقصة")
    contractor_files = st.file_uploader(
        "ارفع وثائق وتواقيع المقاول أو المؤسسة الاقتصادية (PDF أو صور)",
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
            report = run_audit(
                client=groq_client,
                language=selected_language,
                circuit=circuit,
                sector=sector,
                tender_name=f"{tender_pdf.name} ({tender_pages} صفحات - {tender_method})",
                tender_text=tender_text,
                contractor_summary=contractor_text,
            )
            st.markdown("### تقرير المستشار القانوني الذكي — رصين AI")
            st.markdown(report)
        except Exception as exc:
            st.error(f"حدث خطأ أثناء تنفيذ التدقيق: {exc}") 
