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

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية لرصين AI
# ==========================================
st.set_page_config(
    page_title="رصين AI — التدقيق القانوني",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

SYSTEM_PROMPT = """أنت المستشار القانوني الذكي لمنصة "رصين AI" للامتثال والتدقيق القانوني في الجزائر (B2G / B2B).
حلّل النص أو الملف المرفق بدقة قانونية عالية، واكتب التقرير منظماً ومباشراً:
1. نظرة عامة موجزة على الوثيقة أو البند.
2. بنود التدقيق بالإشارات اللونية:
   - 🔴 خطأ / مخالفة قانونية: مع ذكر النص القانوني الجزائري المناسب.
   - 🟠 تنبيه / تحفظ يحتاج مراجعة: مع توضيح الإجراء أو المرجع القانوني.
   - 🟢 متوافق / سليم: البنود المطابقة للأحكام القانونية.
3. ملخص رقمي سريع لعدد النقاط (أحمر / برتقالي / أخضر).
4. توصيات عملية مختصرة للتصحيح.

التزم بالمرجعية القانونية الجزائرية ذات الصلة (الصفقات العمومية 23-12، مكافحة الفساد 06-01، حماية المعطيات ذات الطابع الشخصي 18-07، التوقيع والتصديق الإلكتروني 15-04، القانون التجاري / شركة المساهمة البسيطة 22-09، وغيرها)، واكتب بنفس لغة المادة المدققة (العربية أو الفرنسية)."""

# ==========================================
# 2. تصميم أنيق وعصري متجاوب مع الهاتف
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    .main .block-container {
        max-width: 780px;
        padding-top: 1.3rem;
        padding-bottom: 3rem;
    }
    .hero-card {
        background: #111827;
        color: #f9fafb;
        padding: 1.35rem 1.4rem;
        border-radius: 18px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 25px rgba(17, 24, 39, 0.08);
        margin-bottom: 1.1rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(245, 158, 11, 0.16);
        color: #fbbf24;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.22rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.55rem;
    }
    .hero-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
        line-height: 1.35;
    }
    .hero-sub {
        font-size: 0.92rem;
        color: #d1d5db;
        margin: 0;
        line-height: 1.55;
    }
    .legend-strip {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.6rem;
        margin-bottom: 1.15rem;
    }
    .legend-pill {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.65rem 0.75rem;
        text-align: center;
        font-size: 0.84rem;
        font-weight: 700;
        color: #111827;
    }
    .section-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.1rem 1.15rem;
        margin-bottom: 1rem;
    }
    .stButton > button, .stDownloadButton > button {
        width: 100%;
        border-radius: 12px;
        min-height: 2.95rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif;
    }
    @media (max-width: 640px) {
        .legend-strip {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 1.28rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 3. مفتاح Groq وجلب النماذج النشطة تلقائياً
# ==========================================
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
    text_candidates = []
    vision_candidates = []

    if api_key and HAS_GROQ:
        try:
            client = Groq(api_key=api_key)
            models_resp = client.models.list()
            for m in getattr(models_resp, "data", []) or []:
                mid = getattr(m, "id", "") or ""
                if not mid:
                    continue
                low = mid.lower()
                if any(skip in low for skip in ["whisper", "tts", "guard", "embed", "audio"]):
                    continue
                if any(v in low for v in ["vision", "scout", "maverick", "vl"]):
                    vision_candidates.append(mid)
                else:
                    text_candidates.append(mid)
        except Exception:
            pass

    for fb in FALLBACK_MODELS:
        if fb not in text_candidates:
            text_candidates.append(fb)

    for vfb in ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.2-11b-vision-preview"]:
        if vfb not in vision_candidates:
            vision_candidates.append(vfb)

    return text_candidates, vision_candidates


def run_groq_audit(api_key: str, prompt: str, preferred_model: str, candidate_models: list[str]) -> tuple[str, str]:
    client = Groq(api_key=api_key)
    ordered = []
    if preferred_model:
        ordered.append(preferred_model)
    for m in candidate_models:
        if m not in ordered:
            ordered.append(m)

    errors = []
    for model_name in ordered:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=3000,
            )
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt, model_name
        except Exception as e:
            errors.append(f"{model_name}: {e}")
            continue

    raise RuntimeError("لم ينجح أي نموذج نشط على Groq. التفاصيل: " + " | ".join(errors[-2:]))


def extract_image_text(api_key: str, pil_img: Image.Image, filename: str, vision_models: list[str]) -> str:
    rgb_img = pil_img.convert("RGB")
    buf = io.BytesIO()
    rgb_img.save(buf, format="JPEG", quality=85)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

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
                                    "text": (
                                        f"استخرج بدقة كل النصوص والبنود والأرقام والتواريخ من هذه الصورة ({filename}) "
                                        "بنفس لغتها الأصلية دون حذف أو تلخيص."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
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
            ocr_out = pytesseract.image_to_string(rgb_img, lang="ara+fra+eng").strip()
            if ocr_out:
                return ocr_out
        except Exception:
            pass

    return f"(صورة مرفقة {filename} — أبعادها {pil_img.size})"

# ==========================================
# 4. استخراج النصوص من الملفات
# ==========================================
def extract_from_files(uploaded_files, api_key: str, vision_models: list[str]) -> str:
    if not uploaded_files:
        return ""

    chunks = []
    for f in uploaded_files:
        name = f.name
        low = name.lower()
        data = f.getvalue()

        try:
            if low.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(data))
                pages = []
                for idx, page in enumerate(reader.pages, start=1):
                    t = (page.extract_text() or "").strip()
                    if t:
                        pages.append(f"[صفحة {idx}]\n{t}")
                if pages:
                    chunks.append(f"=== PDF: {name} ===\n" + "\n\n".join(pages))
                else:
                    chunks.append(f"=== PDF: {name} ===\n(ملف ممسوح ضوئياً بدون نص رقمي مباشر).")

            elif low.endswith(".docx"):
                doc = Document(io.BytesIO(data))
                lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                for t_idx, tbl in enumerate(doc.tables, start=1):
                    t_rows = []
                    for r in tbl.rows:
                        vals = [c.text.strip() for c in r.cells if c.text.strip()]
                        if vals:
                            t_rows.append(" | ".join(vals))
                    if t_rows:
                        lines.append(f"[جدول {t_idx}]\n" + "\n".join(t_rows))
                chunks.append(f"=== Word (.docx): {name} ===\n" + "\n".join(lines))

            elif low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                img = Image.open(io.BytesIO(data))
                extracted = extract_image_text(api_key, img, name, vision_models)
                chunks.append(f"=== صورة ({name}) ===\n{extracted}")

            elif low.endswith((".txt", ".md", ".csv", ".json")):
                txt = data.decode("utf-8", errors="ignore").strip()
                chunks.append(f"=== نص ({name}) ===\n{txt}")

            else:
                txt = data.decode("utf-8", errors="ignore").strip()
                chunks.append(f"=== ملف ({name}) ===\n" + (txt if txt else "ملف مرفق."))

        except Exception as e:
            chunks.append(f"=== خطأ في قراءة ({name}) ===\n{e}")

    return "\n\n".join(chunks)

# ==========================================
# 5. تصدير التقرير (Word / TXT / PDF / ZIP)
# ==========================================
def to_docx_bytes(report_text: str, track_label: str) -> bytes:
    doc = Document()
    doc.add_heading(f"تقرير التدقيق القانوني — رصين AI ({track_label})", level=1)
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
    paths = [
        "Amiri-Regular.ttf",
        "Cairo-Regular.ttf",
        "NotoNaskhArabic-Regular.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def to_pdf_bytes(report_text: str, track_label: str) -> bytes | None:
    font_file = find_font_file()
    if not font_file:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("RaseenCustom", "", font_file, uni=True)
    pdf.set_font("RaseenCustom", size=13)
    pdf.multi_cell(0, 9, f"تقرير التدقيق القانوني — رصين AI ({track_label})")
    pdf.ln(3)
    pdf.set_font("RaseenCustom", size=10)
    pdf.multi_cell(0, 7, report_text)
    res = pdf.output(dest="S")
    return bytes(res) if isinstance(res, (bytes, bytearray)) else str(res).encode("utf-8", errors="ignore")


def to_zip_bytes(report_text: str, track_label: str, uploaded_files) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("rapport_raseen_ai.txt", report_text.encode("utf-8"))
        zf.writestr("rapport_raseen_ai.docx", to_docx_bytes(report_text, track_label))
        pdf_data = to_pdf_bytes(report_text, track_label)
        if pdf_data:
            zf.writestr("rapport_raseen_ai.pdf", pdf_data)
        if uploaded_files:
            for f in uploaded_files:
                zf.writestr(f"sources/{f.name}", f.getvalue())
    buf.seek(0)
    return buf.getvalue()

# ==========================================
# 6. الواجهة الرئيسية
# ==========================================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-badge">RASEEN AI • LEGAL & COMPLIANCE</div>
        <h1 class="hero-title">⚖️ رصين AI للتدقيق والامتثال القانوني</h1>
        <p class="hero-sub">تحليل النصوص والملفات (PDF • Word • صور • نص) وتصدير التقارير بصيغ متعددة.</p>
    </div>
    <div class="legend-strip">
        <div class="legend-pill">🔴 مخالفة / خطأ قانوني</div>
        <div class="legend-pill">🟠 تنبيه / مراجعة</div>
        <div class="legend-pill">🟢 متوافق / سليم</div>
    </div>
    """,
    unsafe_allow_html=True,
)

api_key = get_groq_api_key()
text_models, vision_models = fetch_available_groq_models(api_key)

with st.sidebar:
    st.markdown("### الإعدادات")
    if not api_key:
        st.text_input(
            "مفتاح GROQ_API_KEY",
            type="password",
            key="manual_groq_key",
        )
        api_key = get_groq_api_key()
        text_models, vision_models = fetch_available_groq_models(api_key)
    else:
        st.success("مفتاح Groq متصل")

    chosen_model = st.selectbox("النموذج النشط", options=text_models, index=0)

with st.container():
    track = st.radio(
        "مسار التدقيق",
        options=["B2G — صفقات عمومية وإدارات", "B2B — عقود وشركات وامتثال"],
        horizontal=True,
    )

    context_note = st.text_input(
        "سياق أو مرجع إضافي (اختياري)",
        placeholder="مثال: دفتر شروط، عقد خدمات، قانون 23-12، شركة مساهمة بسيطة...",
    )

    raw_text = st.text_area(
        "النص القانوني المراد تدقيقه (اختياري إذا رفعتِ ملفاً)",
        height=150,
        placeholder="اكتبي أو الصقي النص هنا...",
    )

    uploaded_files = st.file_uploader(
        "رفع الملفات (PDF، Word، صور، نص — اختياري)",
        type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
        accept_multiple_files=True,
    )

if "report_output" not in st.session_state:
    st.session_state.report_output = ""
if "model_used" not in st.session_state:
    st.session_state.model_used = ""

if st.button("🚀 بدء التدقيق القانوني", type="primary"):
    if not api_key:
        st.error("يرجى ضبط GROQ_API_KEY في Streamlit Secrets أو إدخاله في القائمة الجانبية.")
    elif not HAS_GROQ:
        st.error("مكتبة groq غير مثبّتة في requirements.txt.")
    else:
        with st.spinner("جاري استخراج البيانات والتدقيق القانوني..."):
            extracted = extract_from_files(uploaded_files, api_key, vision_models)
            parts = []
            if context_note.strip():
                parts.append(f"السياق: {context_note.strip()}")
            if raw_text.strip():
                parts.append(f"النص المدخل:\n{raw_text.strip()}")
            if extracted.strip():
                parts.append(f"محتوى الملفات المرفوعة:\n{extracted.strip()}")

            combined = "\n\n".join(parts).strip()
            if not combined:
                st.warning("أدخلي نصاً أو ارفعي ملفاً واحداً على الأقل.")
            else:
                try:
                    prompt_payload = f"المسار: {track}\n\nالمادة المطلوب تدقيقها:\n{combined[:28000]}"
                    report_txt, active_m = run_groq_audit(api_key, prompt_payload, chosen_model, text_models)
                    st.session_state.report_output = report_txt
                    st.session_state.model_used = active_m
                except Exception as exc:
                    st.error(f"تعذر إتمام التدقيق: {exc}")

if st.session_state.report_output:
    st.markdown("---")
    st.markdown("### 📄 تقرير التدقيق")
    if st.session_state.model_used:
        st.caption(f"النموذج المنفّذ: `{st.session_state.model_used}`")
    st.markdown(st.session_state.report_output)

    st.markdown("### ⬇️ تحميل التقرير")
    rep = st.session_state.report_output
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "تحميل Word (.docx)",
            data=to_docx_bytes(rep, track),
            file_name="rapport_raseen_ai.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        pdf_out = to_pdf_bytes(rep, track)
        if pdf_out:
            st.download_button(
                "تحميل PDF (.pdf)",
                data=pdf_out,
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
    with col_b:
        st.download_button(
            "تحميل نص (.txt)",
            data=rep.encode("utf-8"),
            file_name="rapport_raseen_ai.txt",
            mime="text/plain; charset=utf-8",
        )
        st.download_button(
            "تحميل حزمة كاملة (.zip)",
            data=to_zip_bytes(rep, track, uploaded_files),
            file_name="raseen_ai_package.zip",
            mime="application/zip",
        ) 
