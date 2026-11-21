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

FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

B2B_TYPES = [
    "عقود المناولة والشراكة للمقاولين والمؤسسات الاقتصادية",
    "تأسيس وتسيير الشركات (المؤسسات الناشئة وشركة المساهمة البسيطة)",
    "عقود التوريد والتجهيز والخدمات بين المؤسسات",
    "التعاقد والمعاملات الإلكترونية وحماية المعطيات",
]

SPECIALTIES = [
    "الصفقات العمومية — البناء والأشغال",
    "الصفقات العمومية — التجهيز",
    "الصفقات العمومية — التوريد",
    "الصفقات العمومية — الخدمات",
    "المؤسسات الاقتصادية والمقاولون",
    "المؤسسات الناشئة وشركات المساهمة البسيطة",
]

LEGAL_REFERENCES = [
    "تنظيم الصفقات العمومية وتفويضات المرفق العام",
    "الوقاية من الفساد ومكافحته",
    "أحكام الشركات التجارية وشركة المساهمة البسيطة",
    "التوقيع والتصديق الإلكتروني والمعاملات الإلكترونية",
    "حماية الأشخاص الطبيعيين في مجال معالجة المعطيات ذات الطابع الشخصي",
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    .main .block-container {
        max-width: 780px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    .raseen-header {
        background: #18222f;
        color: #f8fafc;
        padding: 1.2rem 1.3rem;
        border-radius: 14px;
        margin-bottom: 1rem;
    }
    .raseen-title {
        font-size: 1.4rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
    }
    .raseen-sub {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin: 0;
    }
    .signal-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.55rem;
        margin-bottom: 1rem;
    }
    .signal-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.55rem 0.7rem;
        font-size: 0.84rem;
        font-weight: 700;
        text-align: center;
    }
    .stButton > button, .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif;
    }
    @media (max-width: 640px) {
        .signal-row {
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


def fetch_available_groq_models(api_key: str) -> tuple[list[str], list[str]]:
    text_models = []
    vision_models = []
    if api_key and HAS_GROQ:
        try:
            client = Groq(api_key=api_key)
            resp = client.models.list()
            for m in getattr(resp, "data", []) or []:
                mid = getattr(m, "id", "") or ""
                if not mid:
                    continue
                low = mid.lower()
                if any(k in low for k in ["whisper", "tts", "guard", "embed", "audio"]):
                    continue
                if any(v in low for v in ["vision", "scout", "maverick", "vl"]):
                    vision_models.append(mid)
                else:
                    text_models.append(mid)
        except Exception:
            pass
    for fb in FALLBACK_MODELS:
        if fb not in text_models:
            text_models.append(fb)
    for vfb in ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.2-11b-vision-preview"]:
        if vfb not in vision_models:
            vision_models.append(vfb)
    return text_models, vision_models


def build_system_prompt(
    lang: str,
    track: str,
    b2b_subtype: str,
    selected_specialties: list[str],
    selected_refs: list[str],
) -> str:
    specs_str = "، ".join(selected_specialties) if selected_specialties else "الصفقات العمومية والمؤسسات الاقتصادية"
    refs_str = "، ".join(selected_refs) if selected_refs else "المرجعية القانونية الجزائرية المعتمدة"
    subtype_line = f"\n- تصنيف B2B الفرعي: {b2b_subtype}" if track == "B2B" and b2b_subtype else ""
    return (
        f"أنت مستشار قانوني متخصص في منصة 'رصين AI' للتدقيق والامتثال القانوني في الجزائر.\n"
        f"لغة التقرير المطلوبة: {lang}.\n"
        f"- المسار: {track}{subtype_line}\n"
        f"- الاختصاصات المعتمدة: {specs_str}\n"
        f"- مراجع القوانين المعتمدة: {refs_str}\n\n"
        "قسّم التقرير بوضوح إلى:\n"
        "1. ملخص تنفيذي.\n"
        "2. نقاط التدقيق بالإشارات اللونية:\n"
        "   - 🔴 مخالفة أو إشكال قانوني (مع بيان المرجع القانوني الجزائري المناسب).\n"
        "   - 🟠 تنبيه أو تحفظ يستدعي مراجعة.\n"
        "   - 🟢 بند متوافق وسليم.\n"
        "3. توصيات عملية للتصحيح أو الصياغة."
    )


def run_groq_audit(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    preferred_model: str,
    candidate_models: list[str],
) -> tuple[str, str]:
    client = Groq(api_key=api_key)
    ordered = []
    if preferred_model:
        ordered.append(preferred_model)
    for m in candidate_models:
        if m not in ordered:
            ordered.append(m)

    last_err = ""
    for m in ordered:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=3000,
            )
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt, m
        except Exception as e:
            last_err = f"{m}: {e}"
            continue
    raise RuntimeError(last_err or "تعذر تنفيذ التدقيق عبر نماذج Groq.")


def extract_image_text(api_key: str, img: Image.Image, filename: str, vision_models: list[str]) -> str:
    rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    if api_key and HAS_GROQ:
        client = Groq(api_key=api_key)
        for vm in vision_models:
            try:
                resp = client.chat.completions.create(
                    model=vm,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"استخرج بدقة النص الكامل من الصورة ({filename}) بنفس لغتها الأصلية.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1800,
                )
                out = (resp.choices[0].message.content or "").strip()
                if out:
                    return out
            except Exception:
                continue

    if HAS_OCR:
        try:
            ocr_txt = pytesseract.image_to_string(rgb, lang="ara+fra+eng").strip()
            if ocr_txt:
                return ocr_txt
        except Exception:
            pass

    return f"(صورة مرفقة: {filename})"


def extract_from_files(uploaded_files, api_key: str, vision_models: list[str]) -> str:
    if not uploaded_files:
        return ""
    parts = []
    for f in uploaded_files:
        name = f.name
        low = name.lower()
        raw = f.getvalue()
        try:
            if low.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(raw))
                pages = []
                for idx, page in enumerate(reader.pages, start=1):
                    t = (page.extract_text() or "").strip()
                    if t:
                        pages.append(f"[صفحة {idx}]\n{t}")
                parts.append(
                    f"=== PDF: {name} ===\n"
                    + ("\n\n".join(pages) if pages else "(ملف PDF بدون طبقة نصية مباشرة).")
                )
            elif low.endswith(".docx"):
                doc = Document(io.BytesIO(raw))
                lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                for tbl in doc.tables:
                    for row in tbl.rows:
                        vals = [c.text.strip() for c in row.cells if c.text.strip()]
                        if vals:
                            lines.append(" | ".join(vals))
                parts.append(f"=== Word (.docx): {name} ===\n" + "\n".join(lines))
            elif low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                img = Image.open(io.BytesIO(raw))
                parts.append(f"=== صورة ({name}) ===\n" + extract_image_text(api_key, img, name, vision_models))
            else:
                txt = raw.decode("utf-8", errors="ignore").strip()
                parts.append(f"=== ملف ({name}) ===\n" + (txt if txt else "ملف مرفق."))
        except Exception as e:
            parts.append(f"=== خطأ في قراءة ({name}) ===\n{e}")
    return "\n\n".join(parts)


def to_docx_bytes(report_text: str, header_info: str) -> bytes:
    doc = Document()
    doc.add_heading("تقرير التدقيق القانوني — رصين AI", level=1)
    doc.add_paragraph(header_info)
    for line in report_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            doc.add_heading(s[4:], level=3)
        elif s.startswith("## "):
            doc.add_heading(s[3:], level=2)
        else:
            doc.add_paragraph(s)
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.getvalue()


def find_font_file() -> str | None:
    for p in [
        "Amiri-Regular.ttf",
        "Cairo-Regular.ttf",
        "NotoNaskhArabic-Regular.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None


def to_pdf_bytes(report_text: str, header_info: str) -> bytes | None:
    font_path = find_font_file()
    if not font_path:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("RaseenFont", "", font_path, uni=True)
    pdf.set_font("RaseenFont", size=13)
    pdf.multi_cell(0, 9, "تقرير التدقيق القانوني — رصين AI")
    pdf.set_font("RaseenFont", size=9)
    pdf.multi_cell(0, 6, header_info)
    pdf.ln(3)
    pdf.set_font("RaseenFont", size=10)
    pdf.multi_cell(0, 7, report_text)
    res = pdf.output(dest="S")
    return bytes(res) if isinstance(res, (bytes, bytearray)) else str(res).encode("utf-8", errors="ignore")


def to_zip_bytes(report_text: str, header_info: str, uploaded_files) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("rapport_raseen_ai.txt", (header_info + "\n\n" + report_text).encode("utf-8"))
        zf.writestr("rapport_raseen_ai.docx", to_docx_bytes(report_text, header_info))
        pdf_data = to_pdf_bytes(report_text, header_info)
        if pdf_data:
            zf.writestr("rapport_raseen_ai.pdf", pdf_data)
        if uploaded_files:
            for f in uploaded_files:
                zf.writestr(f"sources/{f.name}", f.getvalue())
    buf.seek(0)
    return buf.getvalue()


# ==========================================
# جهة الإعدادات: المسار + اللغة + الاختصاصات + مراجع القوانين
# ==========================================
api_key = get_groq_api_key()
text_models, vision_models = fetch_available_groq_models(api_key)

with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")

    track = st.radio(
        "المسار",
        options=["B2G", "B2B"],
        horizontal=True,
    )

    b2b_subtype = ""
    if track == "B2B":
        b2b_subtype = st.selectbox(
            "تصنيف B2B حسب النوع",
            options=B2B_TYPES,
        )

    lang = st.selectbox(
        "اللغة",
        options=["العربية", "الفرنسية"],
    )

    selected_specialties = st.multiselect(
        "الاختصاصات",
        options=SPECIALTIES,
        default=SPECIALTIES[:4],
    )

    selected_refs = st.multiselect(
        "مراجع القوانين",
        options=LEGAL_REFERENCES,
        default=LEGAL_REFERENCES[:4],
    )

    st.markdown("---")
    if not api_key:
        st.text_input("مفتاح GROQ_API_KEY", type="password", key="manual_groq_key")
        api_key = get_groq_api_key()
        text_models, vision_models = fetch_available_groq_models(api_key)
    chosen_model = st.selectbox("النموذج", options=text_models, index=0)


# ==========================================
# الواجهة الرئيسية
# ==========================================
st.markdown(
    """
    <div class="raseen-header">
        <div class="raseen-title">⚖️ رصين AI — التدقيق القانوني</div>
        <div class="raseen-sub">الصفقات العمومية (البناء • التجهيز • التوريد • الخدمات) والمؤسسات الاقتصادية والمقاولون والمؤسسات الناشئة وشركات المساهمة البسيطة.</div>
    </div>
    <div class="signal-row">
        <div class="signal-item">🔴 مخالفة / إشكال</div>
        <div class="signal-item">🟠 تنبيه / مراجعة</div>
        <div class="signal-item">🟢 متوافق / سليم</div>
    </div>
    """,
    unsafe_allow_html=True,
)

active_summary = f"المسار: {track}" + (f" ({b2b_subtype})" if track == "B2B" and b2b_subtype else "") + f" | اللغة: {lang}"
st.caption(active_summary)

context_note = st.text_input(
    "سياق إضافي (اختياري)",
    placeholder="مثال: دفتر شروط بناء أو تجهيز أو توريد، عقد مقاولة، شركة مساهمة بسيطة...",
)

legal_text = st.text_area(
    "النص القانوني أو البند المراد تدقيقه",
    height=150,
    placeholder="اكتبي أو الصقي النص هنا...",
)

uploaded_files = st.file_uploader(
    "رفع وثيقة أو ملف مرفق (اختياري — غير إجباري)",
    type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
    accept_multiple_files=True,
)

if "report_text" not in st.session_state:
    st.session_state.report_text = ""
if "used_model" not in st.session_state:
    st.session_state.used_model = ""

if st.button("🚀 بدء التدقيق القانوني", type="primary"):
    if not api_key:
        st.error("يرجى ضبط GROQ_API_KEY في Streamlit Secrets أو إدخاله في الإعدادات.")
    elif not HAS_GROQ:
        st.error("مكتبة groq غير مثبّتة.")
    else:
        with st.spinner("جاري التدقيق القانوني..."):
            extracted = extract_from_files(uploaded_files, api_key, vision_models)
            parts = []
            if context_note.strip():
                parts.append(f"السياق: {context_note.strip()}")
            if legal_text.strip():
                parts.append(f"النص المدخل:\n{legal_text.strip()}")
            if extracted.strip():
                parts.append(f"محتوى الملفات المرفوعة:\n{extracted.strip()}")

            combined = "\n\n".join(parts).strip()
            if not combined:
                st.warning("أدخلي نصاً أو ارفعي ملفاً اختيارياً واحداً على الأقل.")
            else:
                try:
                    sys_p = build_system_prompt(lang, track, b2b_subtype, selected_specialties, selected_refs)
                    usr_p = f"المادة المطلوب تدقيقها:\n{combined[:28000]}"
                    rep_txt, act_m = run_groq_audit(api_key, sys_p, usr_p, chosen_model, text_models)
                    st.session_state.report_text = rep_txt
                    st.session_state.used_model = act_m
                except Exception as exc:
                    st.error(f"تعذر إتمام التدقيق: {exc}")

if st.session_state.report_text:
    st.markdown("---")
    st.markdown("### 📄 تقرير التدقيق")
    if st.session_state.used_model:
        st.caption(f"النموذج المنفّذ: `{st.session_state.used_model}` | {active_summary}")
    st.markdown(st.session_state.report_text)

    st.markdown("### ⬇️ تحميل التقرير")
    rep = st.session_state.report_text
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "تحميل Word (.docx)",
            data=to_docx_bytes(rep, active_summary),
            file_name="rapport_raseen_ai.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        pdf_bytes = to_pdf_bytes(rep, active_summary)
        if pdf_bytes:
            st.download_button(
                "تحميل PDF (.pdf)",
                data=pdf_bytes,
                file_name="rapport_raseen_ai.pdf",
                mime="application/pdf",
            )
        else:
            st.download_button(
                "تحميل نص التقرير (.txt)",
                data=rep.encode("utf-8"),
                file_name="rapport_raseen_ai.txt",
                mime="text/plain; charset=utf-8",
            )
    with c2:
        st.download_button(
            "تحميل نص (.txt)",
            data=rep.encode("utf-8"),
            file_name="rapport_raseen_ai.txt",
            mime="text/plain; charset=utf-8",
        )
        st.download_button(
            "تحميل حزمة كاملة (.zip)",
            data=to_zip_bytes(rep, active_summary, uploaded_files),
            file_name="raseen_ai_package.zip",
            mime="application/zip",
        ) 
