import base64
import io
import os
import zipfile
import streamlit as st
from pypdf import PdfReader
from docx import Document
from PIL import Image
from fpdf import FPDF

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

st.set_page_config(
    page_title="رصين AI — التدقيق القانوني",
    page_icon="⚖️",
    layout="centered",
)

PREFERRED_TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

PREFERRED_VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.2-11b-vision-preview",
]

B2B_CATEGORIES = [
    "المقاولون والمؤسسات الاقتصادية (مقاولة، مناولة، شراكة)",
    "المؤسسات الناشئة وشركات المساهمة البسيطة",
    "عقود التوريد والتجهيز والخدمات بين المؤسسات",
    "التعاقد والمعاملات الإلكترونية وحماية المعطيات",
]

SPECIALTY_OPTIONS = [
    "الصفقات العمومية — البناء",
    "الصفقات العمومية — التجهيز",
    "الصفقات العمومية — التوريد",
    "الصفقات العمومية — الخدمات",
    "المؤسسات الاقتصادية والمقاولون",
    "المؤسسات الناشئة وشركات المساهمة البسيطة",
]

LAW_REFERENCE_OPTIONS = [
    "الصفقات العمومية — القانون 23-12",
    "الوقاية من الفساد ومكافحته — القانون 06-01",
    "شركة المساهمة البسيطة — القانون 22-09",
    "التوقيع والتصديق الإلكتروني — القانون 15-04",
    "المعاملات الإلكترونية — القانون 18-05 (والنصوص ذات الصلة مثل 26-02)",
    "حماية المعطيات ذات الطابع الشخصي — القانون 18-07",
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    .main .block-container {
        max-width: 760px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    .top-banner {
        background: #18222f;
        color: #f8fafc;
        padding: 1.2rem 1.35rem;
        border-radius: 14px;
        margin-bottom: 0.95rem;
    }
    .top-title {
        font-size: 1.38rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
    }
    .top-sub {
        font-size: 0.88rem;
        color: #cbd5e1;
        margin: 0;
        line-height: 1.5;
    }
    .legend-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.55rem;
        margin-bottom: 1rem;
    }
    .legend-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.55rem 0.65rem;
        text-align: center;
        font-size: 0.83rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stButton > button, .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif;
    }
    @media (max-width: 640px) {
        .legend-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_groq_api_key() -> str:
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    return st.session_state.get("manual_groq_key", "").strip()


def resolve_groq_models(api_key: str) -> tuple[list[str], list[str]]:
    text_list = []
    vision_list = []
    if api_key and HAS_GROQ:
        try:
            client = Groq(api_key=api_key)
            resp = client.models.list()
            for item in getattr(resp, "data", []) or []:
                mid = getattr(item, "id", "") or ""
                if not mid:
                    continue
                low = mid.lower()
                if any(k in low for k in ["whisper", "tts", "guard", "embed", "audio"]):
                    continue
                if any(v in low for v in ["vision", "scout", "maverick", "vl"]):
                    vision_list.append(mid)
                else:
                    text_list.append(mid)
        except Exception:
            pass

    for m in PREFERRED_TEXT_MODELS:
        if m not in text_list:
            text_list.append(m)
    for vm in PREFERRED_VISION_MODELS:
        if vm not in vision_list:
            vision_list.append(vm)
    return text_list, vision_list


def build_prompt_system(
    language: str,
    track: str,
    b2b_category: str,
    specialty: str,
    law_reference: str,
) -> str:
    b2b_part = f"\n- تصنيف B2B: {b2b_category}" if track == "B2B" and b2b_category else ""
    return (
        f"أنت مستشار قانوني متخصص في منصة 'رصين AI' للتدقيق والامتثال القانوني في الجزائر.\n"
        f"لغة التقرير: {language}.\n"
        f"- المسار: {track}{b2b_part}\n"
        f"- الاختصاص: {specialty}\n"
        f"- مرجع القانون المعتمد: {law_reference}\n\n"
        "اكتب التقرير بوضوح واختصار منظم:\n"
        "1. ملخص تنفيذي.\n"
        "2. نقاط التدقيق بالإشارات اللونية:\n"
        "   - 🔴 مخالفة أو إشكال قانوني (مع ذكر المرجع القانوني الجزائري بدقة).\n"
        "   - 🟠 تنبيه أو تحفظ يحتاج مراجعة.\n"
        "   - 🟢 بند متوافق وسليم.\n"
        "3. توصيات عملية للتصحيح.\n\n"
        "تنبيه إلزامي: لا تخترع أو تغيّر أرقام القوانين أو سنواتها؛ التزم حصراً بالأرقام والمرجعيات الصحيحة "
        "(مثل 23-12، 06-01، 22-09، 15-04، 18-05، 26-02، 18-07) ولا تكتب أرقام قوانين غير متأكد منها."
    )


def run_audit_engine(
    api_key: str,
    system_msg: str,
    user_msg: str,
    text_candidates: list[str],
) -> str:
    client = Groq(api_key=api_key)
    last_error = ""
    for model_id in text_candidates:
        try:
            res = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=2800,
            )
            content = (res.choices[0].message.content or "").strip()
            if content:
                return content
        except Exception as err:
            last_error = f"{model_id}: {err}"
            continue
    raise RuntimeError(last_error or "تعذر إتمام التدقيق عبر مزود الذكاء الاصطناعي.")


def read_image_content(api_key: str, pil_image: Image.Image, file_name: str, vision_candidates: list[str]) -> str:
    rgb = pil_image.convert("RGB")
    buffer = io.BytesIO()
    rgb.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    if api_key and HAS_GROQ:
        client = Groq(api_key=api_key)
        for v_model in vision_candidates:
            try:
                res = client.chat.completions.create(
                    model=v_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"استخرج بدقة النص الكامل من هذه الصورة ({file_name}) بنفس لغتها الأصلية.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                                },
                            ],
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1800,
                )
                extracted = (res.choices[0].message.content or "").strip()
                if extracted:
                    return extracted
            except Exception:
                continue

    if HAS_OCR:
        try:
            ocr_text = pytesseract.image_to_string(rgb, lang="ara+fra+eng").strip()
            if ocr_text:
                return ocr_text
        except Exception:
            pass

    return f"(صورة مرفقة: {file_name})"


def read_uploaded_files(files, api_key: str, vision_candidates: list[str]) -> str:
    if not files:
        return ""
    sections = []
    for item in files:
        fname = item.name
        lower_name = fname.lower()
        raw_bytes = item.getvalue()
        try:
            if lower_name.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(raw_bytes))
                extracted_pages = []
                for idx, page in enumerate(reader.pages, start=1):
                    txt = (page.extract_text() or "").strip()
                    if txt:
                        extracted_pages.append(f"[صفحة {idx}]\n{txt}")
                sections.append(
                    f"=== PDF: {fname} ===\n"
                    + ("\n\n".join(extracted_pages) if extracted_pages else "(ملف PDF بدون طبقة نصية مباشرة).")
                )
            elif lower_name.endswith(".docx"):
                doc = Document(io.BytesIO(raw_bytes))
                lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                for tbl in doc.tables:
                    for row in tbl.rows:
                        cells = [c.text.strip() for c in row.cells if c.text.strip()]
                        if cells:
                            lines.append(" | ".join(cells))
                sections.append(f"=== Word (.docx): {fname} ===\n" + "\n".join(lines))
            elif lower_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
                img = Image.open(io.BytesIO(raw_bytes))
                sections.append(f"=== صورة ({fname}) ===\n" + read_image_content(api_key, img, fname, vision_candidates))
            else:
                decoded = raw_bytes.decode("utf-8", errors="ignore").strip()
                sections.append(f"=== ملف ({fname}) ===\n" + (decoded if decoded else "ملف مرفق."))
        except Exception as err:
            sections.append(f"=== تعذر قراءة ({fname}) ===\n{err}")
    return "\n\n".join(sections)


def build_docx(report_text: str, meta_info: str) -> bytes:
    doc = Document()
    doc.add_heading("تقرير التدقيق القانوني — رصين AI", level=1)
    doc.add_paragraph(meta_info)
    for line in report_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("### "):
            doc.add_heading(clean[4:], level=3)
        elif clean.startswith("## "):
            doc.add_heading(clean[3:], level=2)
        else:
            doc.add_paragraph(clean)
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.getvalue()


def locate_font() -> str | None:
    candidates = [
        "Amiri-Regular.ttf",
        "Cairo-Regular.ttf",
        "NotoNaskhArabic-Regular.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def build_pdf(report_text: str, meta_info: str) -> bytes | None:
    font_path = locate_font()
    if not font_path:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("RaseenDocFont", "", font_path, uni=True)
    pdf.set_font("RaseenDocFont", size=13)
    pdf.multi_cell(0, 9, "تقرير التدقيق القانوني — رصين AI")
    pdf.set_font("RaseenDocFont", size=9)
    pdf.multi_cell(0, 6, meta_info)
    pdf.ln(3)
    pdf.set_font("RaseenDocFont", size=10)
    pdf.multi_cell(0, 7, report_text)
    raw = pdf.output(dest="S")
    return bytes(raw) if isinstance(raw, (bytes, bytearray)) else str(raw).encode("utf-8", errors="ignore")


def build_zip(report_text: str, meta_info: str, files) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("rapport_raseen_ai.txt", (meta_info + "\n\n" + report_text).encode("utf-8"))
        zf.writestr("rapport_raseen_ai.docx", build_docx(report_text, meta_info))
        pdf_bytes = build_pdf(report_text, meta_info)
        if pdf_bytes:
            zf.writestr("rapport_raseen_ai.pdf", pdf_bytes)
        if files:
            for item in files:
                zf.writestr(f"sources/{item.name}", item.getvalue())
    buf.seek(0)
    return buf.getvalue()


# ==========================================
# جهة الإعدادات: المسار + تصنيف B2B + اللغة + الاختصاص + مرجع القانون
# ==========================================
api_key = get_groq_api_key()
text_models, vision_models = resolve_groq_models(api_key)

with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")

    track = st.radio(
        "المسار",
        options=["B2G", "B2B"],
        horizontal=True,
    )

    b2b_category = ""
    if track == "B2B":
        b2b_category = st.selectbox(
            "تقسيم B2B حسب النوع",
            options=B2B_CATEGORIES,
        )

    language = st.selectbox(
        "اللغة",
        options=["العربية", "الفرنسية"],
    )

    specialty = st.selectbox(
        "الاختصاص",
        options=SPECIALTY_OPTIONS,
    )

    law_reference = st.selectbox(
        "مرجع القانون",
        options=LAW_REFERENCE_OPTIONS,
    )

    if not api_key:
        st.markdown("---")
        st.text_input("مفتاح GROQ_API_KEY", type="password", key="manual_groq_key")
        api_key = get_groq_api_key()
        text_models, vision_models = resolve_groq_models(api_key)


# ==========================================
# الواجهة الرئيسية للتدقيق
# ==========================================
st.markdown(
    """
    <div class="top-banner">
        <div class="top-title">⚖️ رصين AI — التدقيق القانوني</div>
        <div class="top-sub">تدقيق النصوص والوثائق القانونية في الجزائر مع ضبط المسار، اللغة، الاختصاص، ومرجع القانون من الإعدادات.</div>
    </div>
    <div class="legend-grid">
        <div class="legend-card">🔴 مخالفة / إشكال</div>
        <div class="legend-card">🟠 تنبيه / مراجعة</div>
        <div class="legend-card">🟢 متوافق / سليم</div>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_summary = (
    f"المسار: {track}"
    + (f" ({b2b_category})" if track == "B2B" and b2b_category else "")
    + f" | اللغة: {language} | الاختصاص: {specialty} | المرجع: {law_reference}"
)
st.caption(meta_summary)

extra_context = st.text_input(
    "سياق إضافي (اختياري)",
    placeholder="مثال: دفتر شروط بناء أو تجهيز أو توريد، عقد مقاولة، شركة مساهمة بسيطة...",
)

input_text = st.text_area(
    "النص القانوني أو البند المراد تدقيقه",
    height=155,
    placeholder="اكتبي أو الصقي النص القانوني هنا...",
)

uploaded_docs = st.file_uploader(
    "إرفاق ملف أو وثيقة (اختياري — غير إجباري للمتعامل)",
    type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
    accept_multiple_files=True,
)

if "final_report" not in st.session_state:
    st.session_state.final_report = ""

if st.button("🚀 تشغيل التدقيق القانوني", type="primary"):
    if not api_key:
        st.error("يرجى ضبط GROQ_API_KEY في Streamlit Secrets أو إدخاله في الإعدادات.")
    elif not HAS_GROQ:
        st.error("مكتبة groq غير مثبّتة.")
    else:
        with st.spinner("جاري التدقيق القانوني..."):
            extracted_docs = read_uploaded_files(uploaded_docs, api_key, vision_models)
            parts = []
            if extra_context.strip():
                parts.append(f"السياق: {extra_context.strip()}")
            if input_text.strip():
                parts.append(f"النص المدخل:\n{input_text.strip()}")
            if extracted_docs.strip():
                parts.append(f"محتوى الملفات المرفوعة:\n{extracted_docs.strip()}")

            combined_input = "\n\n".join(parts).strip()
            if not combined_input:
                st.warning("أدخلي نصاً قانونياً أو أرفقي ملفاً اختيارياً واحداً على الأقل.")
            else:
                try:
                    sys_prompt = build_prompt_system(language, track, b2b_category, specialty, law_reference)
                    usr_prompt = f"المادة المطلوب تدقيقها:\n{combined_input[:28000]}"
                    st.session_state.final_report = run_audit_engine(
                        api_key, sys_prompt, usr_prompt, text_models
                    )
                except Exception as exc:
                    st.error(f"تعذر إتمام التدقيق: {exc}")

if st.session_state.final_report:
    st.markdown("---")
    st.markdown("### 📄 تقرير التدقيق")
    st.markdown(st.session_state.final_report)

    st.markdown("### ⬇️ تحميل التقرير")
    rep_content = st.session_state.final_report
    col_left, col_right = st.columns(2)
    with col_left:
        st.download_button(
            "تحميل Word (.docx)",
            data=build_docx(rep_content, meta_summary),
            file_name="rapport_raseen_ai.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        pdf_data = build_pdf(rep_content, meta_summary)
        if pdf_data:
            st.download_button(
                "تحميل PDF (.pdf)",
                data=pdf_data,
                file_name="rapport_raseen_ai.pdf",
                mime="application/pdf",
            )
        else:
            st.download_button(
                "تحميل نص التقرير (.txt)",
                data=rep_content.encode("utf-8"),
                file_name="rapport_raseen_ai.txt",
                mime="text/plain; charset=utf-8",
            )
    with col_right:
        st.download_button(
            "تحميل نص (.txt)",
            data=rep_content.encode("utf-8"),
            file_name="rapport_raseen_ai.txt",
            mime="text/plain; charset=utf-8",
        )
        st.download_button(
            "تحميل حزمة كاملة (.zip)",
            data=build_zip(rep_content, meta_summary, uploaded_docs),
            file_name="raseen_ai_package.zip",
            mime="application/zip",
        ) 
