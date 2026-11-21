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
# 1. إعدادات الصفحة والنماذج النشطة في Groq
# ==========================================
st.set_page_config(
    page_title="رصين AI — التدقيق والامتثال القانوني",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.2-11b-vision-preview",
]

SYSTEM_PROMPT = """أنت مساعد التدقيق القانوني والامتثال لمنصة "رصين AI" في الجزائر (مساري B2G وB2B).
مهمتك تحليل النصوص والوثائق والملفات المرفوعة بدقة قانونية ومنهجية، وتقديم تقرير واضح ومنظم يتضمن:
1. ملخص تنفيذي للحالة والمخاطر القانونية.
2. الإشارات الضوئية للتدقيق القانوني:
   - 🔴 أحمر (خطأ / مخالفة جوهرية): توضيح المخالفة والنص القانوني الجزائري الواجب تطبيقه.
   - 🟠 برتقالي (تنبيه / نقطة تحتاج مراجعة أو توضيح): توضيح التحفظ والمرجع القانوني المناسب.
   - 🟢 أخضر (صحيح / متوافق): تأكيد البنود السليمة.
3. عدادات وملخص كمي للنقاط المرصودة (عدد المخالفات الحمراء، التنبيهات البرتقالية، النقاط السليمة الخضراء).
4. توصيات عملية فورية للتصحيح والصياغة القانونية.

اعتمد المرجعية القانونية الجزائرية ذات الصلة حسب طبيعة الملف أو النص (مثل قانون الصفقات العمومية 23-12، قانون مكافحة الفساد 06-01، حماية المعطيات ذات الطابع الشخصي 18-07، التوقيع والتصديق الإلكتروني 15-04، القانون التجاري / شركة المساهمة البسيطة 22-09، وغيرها من النصوص السارية).
أجب بلغة واضحة ودقيقة وبنفس لغة النص المدقق (العربية أو الفرنسية)."""

# ==========================================
# 2. تنسيق CSS للهاتف والشاشات المختلفة
# ==========================================
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1100px;
    }
    .raseen-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 1.1rem 1.25rem;
        border-radius: 14px;
        border-right: 6px solid #f59e0b;
        margin-bottom: 1rem;
    }
    .raseen-header h1 {
        margin: 0;
        font-size: 1.45rem;
        color: #ffffff;
    }
    .raseen-header p {
        margin: 0.35rem 0 0 0;
        font-size: 0.92rem;
        color: #cbd5e1;
    }
    .signal-box {
        padding: 0.7rem 0.95rem;
        border-radius: 10px;
        margin-bottom: 0.55rem;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .signal-red {
        background-color: rgba(220, 38, 38, 0.14);
        border-right: 5px solid #dc2626;
    }
    .signal-orange {
        background-color: rgba(217, 119, 6, 0.16);
        border-right: 5px solid #d97706;
    }
    .signal-green {
        background-color: rgba(22, 163, 74, 0.15);
        border-right: 5px solid #16a34a;
    }
    .stButton > button, .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 3. الحصول على مفتاح Groq واستدعاء النماذج
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


def run_groq_text_audit(api_key: str, prompt: str, preferred_model: str) -> tuple[str, str]:
    client = Groq(api_key=api_key)
    models_to_try = [preferred_model] + [m for m in TEXT_MODELS if m != preferred_model]
    last_err = None

    for model_name in models_to_try:
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
            content = (resp.choices[0].message.content or "").strip()
            if content:
                return content, model_name
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"تعذر إكمال التدقيق النصي عبر Groq: {last_err}")


def describe_image_with_groq(api_key: str, pil_img: Image.Image, filename: str) -> str:
    img_buf = io.BytesIO()
    rgb_img = pil_img.convert("RGB")
    rgb_img.save(img_buf, format="JPEG", quality=85)
    import base64
    b64_img = base64.b64encode(img_buf.getvalue()).decode("utf-8")

    client = Groq(api_key=api_key)
    last_err = None
    for v_model in VISION_MODELS:
        try:
            resp = client.chat.completions.create(
                model=v_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"استخرج بدقة كل النصوص والبنود والأرقام والتواريخ والملاحظات الظاهرة في هذه الصورة ({filename}) "
                                    "واحفظ لغتها الأصلية دون تلخيص مخل."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_img}",
                                },
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=1800,
            )
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt
        except Exception as e:
            last_err = e
            continue

    if HAS_OCR:
        try:
            ocr_txt = pytesseract.image_to_string(rgb_img, lang="ara+fra+eng").strip()
            if ocr_txt:
                return ocr_txt
        except Exception:
            pass

    raise RuntimeError(f"تعذر قراءة محتوى الصورة ({filename}): {last_err}")

# ==========================================
# 4. استخراج النصوص من الملفات (PDF / Word / صور / نص)
# ==========================================
def extract_content_from_files(uploaded_files, api_key: str) -> str:
    if not uploaded_files:
        return ""

    blocks = []
    for f in uploaded_files:
        fname = f.name
        lower = fname.lower()
        raw = f.getvalue()

        try:
            if lower.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(raw))
                pages_txt = []
                for idx, page in enumerate(reader.pages, start=1):
                    pt = (page.extract_text() or "").strip()
                    if pt:
                        pages_txt.append(f"[صفحة {idx}]\n{pt}")
                if pages_txt:
                    blocks.append(f"=== ملف PDF: {fname} ===\n" + "\n\n".join(pages_txt))
                else:
                    blocks.append(
                        f"=== ملف PDF: {fname} ===\n(الملف ممسوح ضوئياً كصور ولا يحتوي على طبقة نصية رقمية مباشرة)."
                    )

            elif lower.endswith(".docx"):
                doc = Document(io.BytesIO(raw))
                parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                for t_idx, table in enumerate(doc.tables, start=1):
                    rows_out = []
                    for row in table.rows:
                        cells = [c.text.strip() for c in row.cells if c.text.strip()]
                        if cells:
                            rows_out.append(" | ".join(cells))
                    if rows_out:
                        parts.append(f"[جدول {t_idx}]\n" + "\n".join(rows_out))
                blocks.append(f"=== ملف Word (.docx): {fname} ===\n" + "\n".join(parts))

            elif lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
                pil_img = Image.open(io.BytesIO(raw))
                if api_key:
                    try:
                        vision_txt = describe_image_with_groq(api_key, pil_img, fname)
                        blocks.append(f"=== محتوى مستخرج من صورة ({fname}) ===\n{vision_txt}")
                    except Exception as img_err:
                        blocks.append(
                            f"=== صورة مرفقة ({fname}) | الأبعاد: {pil_img.size} ===\nملاحظة: {img_err}"
                        )
                else:
                    ocr_txt = ""
                    if HAS_OCR:
                        try:
                            ocr_txt = pytesseract.image_to_string(pil_img, lang="ara+fra+eng").strip()
                        except Exception:
                            ocr_txt = ""
                    if ocr_txt:
                        blocks.append(f"=== نص OCR من صورة ({fname}) ===\n{ocr_txt}")
                    else:
                        blocks.append(
                            f"=== صورة مرفقة ({fname}) | الأبعاد: {pil_img.size} ===\n(أدخلي مفتاح Groq API لقراءة نص الصورة تلقائياً)."
                        )

            elif lower.endswith((".txt", ".md", ".csv", ".json")):
                text_data = raw.decode("utf-8", errors="ignore").strip()
                blocks.append(f"=== ملف نصي ({fname}) ===\n{text_data}")

            else:
                fallback_txt = raw.decode("utf-8", errors="ignore").strip()
                blocks.append(
                    f"=== ملف مرفق ({fname}) ===\n"
                    + (fallback_txt if fallback_txt else "تم إرفاق الملف ضمن المرفقات.")
                )

        except Exception as e:
            blocks.append(f"=== خطأ في قراءة الملف ({fname}) ===\n{e}")

    return "\n\n".join(blocks)

# ==========================================
# 5. بناء ملفات التحميل (Word / TXT / PDF / ZIP)
# ==========================================
def build_docx_report(report_text: str, track_label: str) -> bytes:
    doc = Document()
    doc.add_heading(f"تقرير التدقيق القانوني — رصين AI ({track_label})", level=1)
    for line in report_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("### "):
            doc.add_heading(clean.replace("### ", "", 1), level=3)
        elif clean.startswith("## "):
            doc.add_heading(clean.replace("## ", "", 1), level=2)
        else:
            doc.add_paragraph(clean)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def find_arabic_ttf_font() -> str | None:
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


def build_pdf_report(report_text: str, track_label: str) -> bytes | None:
    font_path = find_arabic_ttf_font()
    if not font_path:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("RaseenFont", "", font_path, uni=True)
    pdf.set_font("RaseenFont", size=13)
    pdf.multi_cell(0, 9, f"تقرير التدقيق القانوني — رصين AI ({track_label})")
    pdf.ln(4)
    pdf.set_font("RaseenFont", size=10)
    pdf.multi_cell(0, 7, report_text)
    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("utf-8", errors="ignore")


def build_zip_report(report_text: str, track_label: str, uploaded_files) -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("rapport_raseen_ai.txt", report_text.encode("utf-8"))
        zf.writestr("rapport_raseen_ai.docx", build_docx_report(report_text, track_label))

        pdf_bytes = build_pdf_report(report_text, track_label)
        if pdf_bytes:
            zf.writestr("rapport_raseen_ai.pdf", pdf_bytes)

        if uploaded_files:
            for f in uploaded_files:
                zf.writestr(f"fichiers_sources/{f.name}", f.getvalue())

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# ==========================================
# 6. واجهة المستخدم الرئيسية
# ==========================================
st.markdown(
    """
    <div class="raseen-header">
        <h1>⚖️ رصين AI — منصة التدقيق والامتثال القانوني</h1>
        <p>تدقيق النصوص والملفات (PDF • Word • صور • نص) وتصدير التقارير (Word • PDF • TXT • ZIP)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("إعدادات المنصة")
    api_key_existing = get_groq_api_key()
    if not api_key_existing:
        st.text_input(
            "مفتاح GROQ_API_KEY (مؤقت للجلسة)",
            type="password",
            key="manual_groq_key",
            help="يُفضّل إضافته في Streamlit Secrets باسم GROQ_API_KEY",
        )
    else:
        st.success("مفتاح Groq مفعّل")

    selected_model = st.selectbox(
        "نموذج التدقيق النصي (Groq)",
        options=TEXT_MODELS,
        index=0,
    )

st.markdown(
    """
    <div class="signal-box signal-red">🔴 أحمر: خطأ أو مخالفة قانونية + النص القانوني الجزائري الواجب تطبيقه</div>
    <div class="signal-box signal-orange">🟠 برتقالي: تنبيه أو نقطة تحتاج مراجعة + المرجع القانوني المناسب</div>
    <div class="signal-box signal-green">🟢 أخضر: بند صحيح ومتوافق قانونياً</div>
    """,
    unsafe_allow_html=True,
)

col_track, col_context = st.columns([1, 2])
with col_track:
    track = st.radio(
        "اختر مسار التدقيق",
        options=["B2G (صفقات عمومية / إدارات)", "B2B (عقود / شركات / امتثال)"],
        horizontal=False,
    )
with col_context:
    extra_notes = st.text_input(
        "ملاحظة أو سياق إضافي (اختياري)",
        placeholder="مثال: دفتر شروط بلدي، عقد خدمات، قانون 23-12، شركة مساهمة بسيطة...",
    )

manual_text = st.text_area(
    "أدخل النص القانوني أو البند المراد تدقيقه (اختياري إذا رفعتِ ملفاً)",
    height=170,
    placeholder="الصقي هنا نص العقد، دفتر الشروط، أو القرار الإداري...",
)

uploaded_files = st.file_uploader(
    "رفع الملفات للتدقيق (PDF، Word، صور، نصوص — اختياري)",
    type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
    accept_multiple_files=True,
)

if "audit_report" not in st.session_state:
    st.session_state.audit_report = ""
if "used_model_label" not in st.session_state:
    st.session_state.used_model_label = ""

run_clicked = st.button("🚀 تشغيل التدقيق القانوني الشامل", type="primary")

if run_clicked:
    active_key = get_groq_api_key()
    if not active_key:
        st.error("يرجى ضبط GROQ_API_KEY في Streamlit Secrets أو إدخاله في القائمة الجانبية.")
    elif not HAS_GROQ:
        st.error("مكتبة groq غير مثبّتة. أضيفي groq إلى ملف requirements.txt.")
    else:
        with st.spinner("جاري استخراج محتوى الملفات وإجراء التدقيق القانوني..."):
            files_text = extract_content_from_files(uploaded_files, active_key)
            combined_parts = []
            if extra_notes.strip():
                combined_parts.append(f"سياق إضافي: {extra_notes.strip()}")
            if manual_text.strip():
                combined_parts.append(f"النص المدخل يدوياً:\n{manual_text.strip()}")
            if files_text.strip():
                combined_parts.append(f"محتوى الملفات المرفوعة:\n{files_text.strip()}")

            full_payload = "\n\n".join(combined_parts).strip()

            if not full_payload:
                st.warning("أدخلي نصاً للتدقيق أو ارفعي ملفاً واحداً على الأقل (PDF / Word / صورة / نص).")
            else:
                try:
                    final_prompt = (
                        f"المسار: {track}\n\n"
                        f"المادة المطلوب تدقيقها:\n{full_payload[:28000]}"
                    )
                    report_out, used_m = run_groq_text_audit(active_key, final_prompt, selected_model)
                    st.session_state.audit_report = report_out
                    st.session_state.used_model_label = used_m
                except Exception as err:
                    st.error(f"حدث خطأ أثناء تنفيذ التدقيق: {err}")

# ==========================================
# 7. عرض التقرير وتحميله بجميع الصيغ
# ==========================================
if st.session_state.audit_report:
    st.divider()
    st.subheader("📋 تقرير التدقيق القانوني")
    if st.session_state.used_model_label:
        st.caption(f"تم التوليد عبر النموذج النشط: `{st.session_state.used_model_label}`")

    st.markdown(st.session_state.audit_report)

    st.divider()
    st.subheader("⬇️ تحميل التقرير والملفات")

    report_str = st.session_state.audit_report
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.download_button(
            label="📄 تحميل Word (.docx)",
            data=build_docx_report(report_str, track),
            file_name="rapport_raseen_ai.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with c2:
        st.download_button(
            label="📝 تحميل نص (.txt)",
            data=report_str.encode("utf-8"),
            file_name="rapport_raseen_ai.txt",
            mime="text/plain; charset=utf-8",
        )

    with c3:
        pdf_bytes = build_pdf_report(report_str, track)
        if pdf_bytes:
            st.download_button(
                label="📕 تحميل PDF (.pdf)",
                data=pdf_bytes,
                file_name="rapport_raseen_ai.pdf",
                mime="application/pdf",
            )
        else:
            st.download_button(
                label="📕 تحميل PDF كملف نصي (.txt)",
                data=report_str.encode("utf-8"),
                file_name="rapport_raseen_ai_pdf_ready.txt",
                mime="text/plain; charset=utf-8",
                help="أضيفي ملف خط عربي مثل Amiri-Regular.ttf في GitHub لتفعيل تصدير PDF المباشر.",
            )

    with c4:
        st.download_button(
            label="🗜️ حزمة كاملة (.zip)",
            data=build_zip_report(report_str, track, uploaded_files),
            file_name="raseen_ai_package.zip",
            mime="application/zip",
        ) 
