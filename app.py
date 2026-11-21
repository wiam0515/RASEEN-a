import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="رصين AI | Raseen AI - التدقيق القانوني",
    page_icon="⚖️",
    layout="wide",
)

SYSTEM_PROMPT = """
أنت خبير قانوني متخصص في القانون الجزائري، الصفقات العمومية، العقود التجارية، وحماية المعطيات ذات الطابع الشخصي.
حلل الوثيقة أو النص القانوني المقدم باللغتين العربية والفرنسية حسب المسار والقطاع المحددين، مع التركيز على:
1. القانون رقم 23-12 المتعلق بالصفقات العمومية وتفويضات المرفق العام.
2. القانون رقم 06-01 المتعلق بالوقاية من الفساد ومكافحته.
3. القانون رقم 18-07 المتعلق بحماية الأشخاص الطبيعيين في مجال معالجة المعطيات ذات الطابع الشخصي، المعدل والمتمم بالقانون رقم 25-11.
4. خصوصيات ملف وسم المشروع المبتكر (Projet Innovant) في مساري B2B وB2G.

قدم التقرير بوضوح ومنهجية دقيقة مع إرفاق التحليل باللغتين العربية والفرنسية وتحديد المخاطر القانونية والتوصيات العملية.
""".strip()


def get_groq_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("يرجى إضافة GROQ_API_KEY في إعدادات Secrets على Streamlit Cloud.")
        st.stop()
    return Groq(api_key=api_key)


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    pages_text = []
    for idx, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        if extracted.strip():
            pages_text.append(f"--- صفحة {idx} ---\n{extracted.strip()}")
    return "\n\n".join(pages_text)


def run_legal_audit(
    client: Groq,
    circuit: str,
    sector: str,
    innovant_label: bool,
    document_text: str,
) -> str:
    label_status = "نعم (ملف وسم المشروع المبتكر - Projet Innovant)" if innovant_label else "لا"
    user_prompt_text = f"""
المسار (Circuit): {circuit}
القطاع (Secteur): {sector}
وسم المشروع المبتكر (Projet Innovant): {label_status}
الإطار المرجعي: القانون 23-12، القانون 06-01، والقانون 18-07 المعدل بالقانون 25-11.

محتوى الوثيقة / المعطيات للتدقيق القانوني:
{document_text}

المطلوب:
- إعداد تقرير تدقيق قانوني مفصل باللغتين العربية والفرنسية.
- تقييم مدى المطابقة القانونية والتنظيمية حسب المسار ({circuit}) والقطاع ({sector}) ووضع وسم المشروع المبتكر ({label_status}).
- إبراز الثغرات أو المخاطر القانونية والتوصيات التصحيحية الفورية.
""".strip()

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_text},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content or ""


st.title("⚖️ رصين AI — منصة التدقيق القانوني الذكي")
st.caption("تدقيق قانوني ثنائي اللغة (العربية / الفرنسية) لملفات الصفقات والعقود والمناقصات وملف وسم المشروع المبتكر (Projet Innovant)")

with st.sidebar:
    st.header("إعدادات التدقيق")
    circuit = st.selectbox("اختر المسار", options=["B2G (الصفقات العمومية)", "B2B (العقود والقطاع الخاص)"])
    sector = st.selectbox(
        "اختر القطاع",
        options=[
            "البناء والأشغال العمومية (Travaux)",
            "الخدمات العامة (Services Publics)",
            "الرقمنة والابتكار (Numérique & Innovation)",
            "التوريدات والمعدات (Fournitures)",
        ],
    )
    innovant_label = st.checkbox("ملف وسم المشروع المبتكر (Projet Innovant)", value=True)

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_pdf = st.file_uploader("رفع ملف PDF (دفتر شروط / عقد / وثيقة)", type=["pdf"])

with col2:
    manual_text = st.text_area(
        "أو أدخل نص الوثيقة / البنود مباشرة هنا",
        height=180,
        placeholder="اكتب أو الصق بنود دفتر الشروط أو العقد أو المعطيات المراد تدقيقها...",
    )

if st.button("تشغيل التدقيق القانوني", type="primary", use_container_width=True):
    extracted_text = ""
    if uploaded_pdf is not None:
        try:
            extracted_text = extract_pdf_text(uploaded_pdf)
        except Exception as exc:
            st.error(f"تعذر قراءة ملف PDF: {exc}")
            st.stop()

    final_text = "\n\n".join(part for part in [extracted_text.strip(), manual_text.strip()] if part)

    if not final_text:
        st.warning("يرجى رفع ملف PDF يحتوي على نص قابل للقراءة أو إدخال نص في خانة النص قبل تشغيل التدقيق.")
        st.stop()

    summary_rows = [
        {"العنصر": "المنصة", "القيمة": "رصين AI"},
        {"العنصر": "النموذج الذكي", "القيمة": "llama-3.3-70b-versatile (Groq)"},
        {"العنصر": "المسار", "القيمة": circuit},
        {"العنصر": "القطاع", "القيمة": sector},
        {"العنصر": "وسم المشروع المبتكر (Projet Innovant)", "القيمة": "مفعّل" if innovant_label else "غير مفعّل"},
        {"العنصر": "المرجعية القانونية", "القيمة": "القانون 23-12 | القانون 06-01 | القانون 18-07 المعدل بالقانون 25-11"},
    ]
    st.table(summary_rows)

    with st.spinner("جاري إجراء التدقيق القانوني عبر Groq..."):
        try:
            groq_client = get_groq_client()
            ai_report_text = run_legal_audit(
                client=groq_client,
                circuit=circuit,
                sector=sector,
                innovant_label=innovant_label,
                document_text=final_text,
            )
            st.markdown("### 📄 تقرير التدقيق القانوني")
            st.markdown(ai_report_text)
        except Exception as exc:
            st.error(f"حدث خطأ أثناء الاتصال بخدمة التدقيق: {exc}") 
