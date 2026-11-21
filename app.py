import base64
import io
import os
import re
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
    page_title="رصين AI — Raseen AI",
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

UI_STRINGS = {
    "العربية": {
        "dir": "rtl",
        "align": "right",
        "badge": "رصين AI • التدقيق والامتثال القانوني",
        "title": "⚖️ رصين AI — منصة التدقيق والامتثال القانوني",
        "subtitle": "تحليل النصوص والوثائق في الجزائر وفق المسار، الاختصاص، ومرجع القانون — مع عرض كل بند في فقرة واضحة.",
        "red_label": "أحمر — خطأ",
        "orange_label": "برتقالي — تنبيه",
        "green_label": "أخضر — صحيح",
        "settings_title": "⚙️ الإعدادات",
        "track_label": "المسار",
        "b2b_label": "تقسيم B2B حسب النوع",
        "lang_label": "اللغة / Langue",
        "specialty_label": "الاختصاص",
        "law_label": "مرجع القانون",
        "api_label": "مفتاح GROQ_API_KEY",
        "context_label": "سياق إضافي (اختياري)",
        "context_ph": "مثال: دفتر شروط بناء أو تجهيز أو توريد، عقد مقاولة، شركة مساهمة بسيطة...",
        "text_label": "النص القانوني أو البند المراد تدقيقه",
        "text_ph": "اكتبي أو الصقي النص القانوني هنا...",
        "upload_label": "إرفاق ملف أو وثيقة (اختياري — غير إجباري للمتعامل)",
        "run_btn": "🚀 تشغيل التدقيق القانوني",
        "spinner": "جاري قراءة المعطيات وإعداد تقرير التدقيق...",
        "missing_key": "يرجى ضبط GROQ_API_KEY في Streamlit Secrets أو إدخاله في الإعدادات.",
        "missing_groq": "مكتبة groq غير مثبّتة.",
        "empty_input": "أدخلي نصاً قانونياً أو أرفقي ملفاً اختيارياً واحداً على الأقل.",
        "report_heading": "📄 تقرير التدقيق القانوني (فقرات واضحة)",
        "download_heading": "⬇️ تحميل التقرير",
        "dl_docx": "تحميل Word (.docx)",
        "dl_pdf": "تحميل PDF (.pdf)",
        "dl_txt": "تحميل نص (.txt)",
        "dl_zip": "تحميل حزمة كاملة (.zip)",
        "b2b_types": [
            "المقاولون والمؤسسات الاقتصادية (مقاولة، مناولة، شراكة)",
            "المؤسسات الناشئة وشركات المساهمة البسيطة",
            "عقود التوريد والتجهيز والخدمات بين المؤسسات",
            "التعاقد والمعاملات الإلكترونية وحماية المعطيات",
        ],
        "specialties": [
            "الصفقات العمومية — البناء",
            "الصفقات العمومية — التجهيز",
            "الصفقات العمومية — التوريد",
            "الصفقات العمومية — الخدمات",
            "المؤسسات الاقتصادية والمقاولون",
            "المؤسسات الناشئة وشركات المساهمة البسيطة",
        ],
        "laws": [
            "الصفقات العمومية — القانون 23-12",
            "الوقاية من الفساد ومكافحته — القانون 06-01",
            "شركة المساهمة البسيطة — القانون 22-09",
            "التوقيع والتصديق الإلكتروني — القانون 15-04",
            "المعاملات الإلكترونية — القانون 18-05 (والنصوص ذات الصلة مثل 26-02)",
            "حماية المعطيات ذات الطابع الشخصي — القانون 18-07",
        ],
    },
    "Français": {
        "dir": "ltr",
        "align": "left",
        "badge": "RASEEN AI • AUDIT & CONFORMITÉ JURIDIQUE",
        "title": "⚖️ Raseen AI — Audit et Conformité Juridique",
        "subtitle": "Analyse des textes et documents en Algérie selon le parcours, la spécialité et la référence juridique — en paragraphes clairs.",
        "red_label": "Rouge — Erreur",
        "orange_label": "Orange — Avertissement",
        "green_label": "Vert — Conforme",
        "settings_title": "⚙️ Paramètres",
        "track_label": "Parcours",
        "b2b_label": "Classification B2B par type",
        "lang_label": "Langue / اللغة",
        "specialty_label": "Spécialité",
        "law_label": "Référence juridique",
        "api_label": "Clé GROQ_API_KEY",
        "context_label": "Contexte complémentaire (optionnel)",
        "context_ph": "Ex. : cahier des charges (travaux, équipement, fourniture), contrat, SPA...",
        "text_label": "Texte ou clause juridique à auditer",
        "text_ph": "Saisissez ou collez le texte juridique ici...",
        "upload_label": "Joindre un document ou fichier (optionnel — non obligatoire)",
        "run_btn": "🚀 Lancer l'audit juridique",
        "spinner": "Extraction des données et génération du rapport d'audit...",
        "missing_key": "Veuillez configurer GROQ_API_KEY dans Streamlit Secrets ou dans les paramètres.",
        "missing_groq": "La bibliothèque groq n'est pas installée.",
        "empty_input": "Veuillez saisir un texte juridique ou joindre au moins un fichier optionnel.",
        "report_heading": "📄 Rapport d'audit juridique (paragraphes détaillés)",
        "download_heading": "⬇️ Télécharger le rapport",
        "dl_docx": "Télécharger Word (.docx)",
        "dl_pdf": "Télécharger PDF (.pdf)",
        "dl_txt": "Télécharger texte (.txt)",
        "dl_zip": "Télécharger l'archive complète (.zip)",
        "b2b_types": [
            "Entrepreneurs et opérateurs économiques (entreprise, sous-traitance, partenariat)",
            "Start-ups et sociétés par actions simplifiées (SAS)",
            "Contrats de fourniture, d'équipement et de services interentreprises",
            "Transactions électroniques, signature et protection des données",
        ],
        "specialties": [
            "Marchés publics — Bâtiment et travaux",
            "Marchés publics — Équipement",
            "Marchés publics — Fourniture",
            "Marchés publics — Services",
            "Opérateurs économiques et entrepreneurs",
            "Start-ups et sociétés par actions simplifiées",
        ],
        "laws": [
            "Marchés publics — Loi 23-12",
            "Prévention et lutte contre la corruption — Loi 06-01",
            "Société par actions simplifiée — Loi 22-09",
            "Signature et certification électroniques — Loi 15-04",
            "Transactions électroniques — Loi 18-05 (et textes connexes tels que 26-02)",
            "Protection des données à caractère personnel — Loi 18-07",
        ],
    },
}


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
    b2b_part = f"\n- التصنيف الفرعي لـ B2B: {b2b_category}" if track == "B2B" and b2b_category else ""
    if language == "Français":
        return (
            f"Tu es un conseiller juridique expert de la plateforme 'Raseen AI' dédiée à l'audit et à la conformité juridique en Algérie.\n"
            f"Rédige impérativement tout le rapport en FRANÇAIS.\n"
            f"- Parcours: {track}{b2b_part}\n"
            f"- Spécialité: {specialty}\n"
            f"- Référence juridique retenue: {law_reference}\n\n"
            "Présente le rapport sous forme de PARAGRAPHES CLAIRS (sans tableaux larges) :\n"
            "1. Un paragraphe de synthèse générale.\n"
            "2. Chaque point d'audit dans un PARAGRAPHE DISTINCT commençant obligatoirement par l'un des marqueurs suivants :\n"
            "   - 🔴 Erreur : [analyse juridique et référence légale algérienne exacte].\n"
            "   - 🟠 Avertissement : [point de vigilance, réserve ou vérification à effectuer].\n"
            "   - 🟢 Conforme : [disposition conforme aux règles applicables].\n"
            "3. Un paragraphe de recommandation pratique finale.\n\n"
            "Règle stricte : n'invente et ne modifie aucun numéro ou année de loi ; utilise uniquement les références exactes "
            "(23-12, 06-01, 22-09, 15-04, 18-05, 26-02, 18-07) ou mentionne l'intitulé sans numéro incertain."
        )
    return (
        f"أنت مستشار قانوني متخصص في منصة 'رصين AI' للتدقيق والامتثال القانوني في الجزائر.\n"
        f"اكتب كامل التقرير باللغة العربية الفصحى الواضحة.\n"
        f"- المسار: {track}{b2b_part}\n"
        f"- الاختصاص: {specialty}\n"
        f"- مرجع القانون المعتمد: {law_reference}\n\n"
        "اكتب التقرير على شكل فقرات واضحة ومستقلة لكل نقطة أو بند (تجنّب الجداول العريضة):\n"
        "1. فقرة موجزة للملخص العام.\n"
        "2. اجعل كل نقطة تدقيق في فقرة مستقلة تبدأ بوضوح بأحد الوسوم التالية:\n"
        "   - 🔴 خطأ: [شرح المخالفة أو الإشكال القانوني مع ذكر المرجع القانوني الجزائري المناسب].\n"
        "   - 🟠 تنبيه: [ملاحظة أو تحفظ أو إجراء يحتاج مراجعة].\n"
        "   - 🟢 صحيح: [بند متوافق وسليم قانوناً].\n"
        "3. فقرة ختامية تتضمن التوصية العملية للمتعامل.\n\n"
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
                temperature=0.25,
                max_tokens=3000,
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


def classify_paragraph_color(para: str) -> str:
    low = para.lower()
    if (
        "🔴" in para
        or re.search(r"(^|\s)(خطأ|مخالفة|غير قانوني|باطل|erreur|illégal|infraction)\b", low)
    ):
        return "red"
    if (
        "🟠" in para
        or re.search(r"(^|\s)(تنبيه|تحفظ|مراجعة|avertissement|alerte|réserve|vigilance)\b", low)
    ):
        return "orange"
    if (
        "🟢" in para
        or re.search(r"(^|\s)(صحيح|متوافق|سليم|conforme|valide)\b", low)
    ):
        return "green"
    return "neutral"


def render_colored_paragraphs(report_text: str, language: str):
    is_ar = language == "العربية"
    dir_attr = "rtl" if is_ar else "ltr"
    align_css = "right" if is_ar else "left"

    styles_map = {
        "red": {
            "bg": "#fef2f2",
            "border": "#dc2626",
            "badge": "أحمر — خطأ" if is_ar else "Rouge — Erreur",
            "badge_bg": "#fee2e2",
            "badge_fg": "#991b1b",
        },
        "orange": {
            "bg": "#fff7ed",
            "border": "#ea580c",
            "badge": "برتقالي — تنبيه" if is_ar else "Orange — Avertissement",
            "badge_bg": "#ffedd5",
            "badge_fg": "#9a3412",
        },
        "green": {
            "bg": "#f0fdf4",
            "border": "#16a34a",
            "badge": "أخضر — صحيح" if is_ar else "Vert — Conforme",
            "badge_bg": "#dcfce7",
            "badge_fg": "#166534",
        },
        "neutral": {
            "bg": "#f8fafc",
            "border": "#475569",
            "badge": None,
            "badge_bg": "#e2e8f0",
            "badge_fg": "#1e293b",
        },
    }

    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", report_text.strip()) if b.strip()]
    if len(raw_blocks) == 1 and "\n" in raw_blocks[0]:
        raw_blocks = [ln.strip() for ln in raw_blocks[0].splitlines() if ln.strip()]

    for block in raw_blocks:
        clean_block = re.sub(r"^\s*[-*•]+\s*", "", block).strip()
        clean_block = re.sub(r"^\s*#+\s*", "", clean_block).strip()
        if not clean_block:
            continue

        tone = classify_paragraph_color(clean_block)
        st_cfg = styles_map[tone]

        cleaned_body = re.sub(
            r"^(🔴|🟠|🟢)\s*(خطأ|تنبيه|صحيح|erreur|avertissement|conforme)?\s*[:\-–—]?\s*",
            "",
            clean_block,
            flags=re.IGNORECASE,
        ).strip()
        if not cleaned_body:
            cleaned_body = clean_block

        badge_html = ""
        if st_cfg["badge"]:
            badge_html = (
                f'<span style="display:inline-block;background:{st_cfg["badge_bg"]};'
                f'color:{st_cfg["badge_fg"]};font-weight:800;font-size:0.8rem;'
                f'padding:0.18rem 0.6rem;border-radius:999px;margin-bottom:0.45rem;">'
                f'{st_cfg["badge"]}</span><br>'
            )

        st.markdown(
            f'<div dir="{dir_attr}" style="background:{st_cfg["bg"]};'
            f'border-right:{"5px solid " + st_cfg["border"] if is_ar else "none"};'
            f'border-left:{"5px solid " + st_cfg["border"] if not is_ar else "none"};'
            f'border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.75rem;'
            f'text-align:{align_css};line-height:1.7;color:#0f172a;font-size:0.96rem;">'
            f'{badge_html}{cleaned_body}</div>',
            unsafe_allow_html=True,
        )


def build_docx(report_text: str, meta_info: str) -> bytes:
    doc = Document()
    doc.add_heading("تقرير التدقيق القانوني — Raseen AI", level=1)
    doc.add_paragraph(meta_info)
    for para in [p.strip() for p in re.split(r"\n\s*\n", report_text.strip()) if p.strip()]:
        doc.add_paragraph(para)
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
    pdf.multi_cell(0, 9, "تقرير التدقيق القانوني — Raseen AI")
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
# الإعدادات (مع اللغة أولاً لكي تتحدث الواجهة فوراً)
# ==========================================
api_key = get_groq_api_key()
text_models, vision_models = resolve_groq_models(api_key)

with st.sidebar:
    language = st.selectbox(
        "اللغة / Langue",
        options=["العربية", "Français"],
    )
    t = UI_STRINGS[language]

    st.markdown(f"## {t['settings_title']}")

    track = st.radio(
        t["track_label"],
        options=["B2G", "B2B"],
        horizontal=True,
    )

    b2b_category = ""
    if track == "B2B":
        b2b_category = st.selectbox(
            t["b2b_label"],
            options=t["b2b_types"],
        )

    specialty = st.selectbox(
        t["specialty_label"],
        options=t["specialties"],
    )

    law_reference = st.selectbox(
        t["law_label"],
        options=t["laws"],
    )

    if not api_key:
        st.markdown("---")
        st.text_input(t["api_label"], type="password", key="manual_groq_key")
        api_key = get_groq_api_key()
        text_models, vision_models = resolve_groq_models(api_key)

t = UI_STRINGS[language]
is_ar = language == "العربية"
dir_attr = t["dir"]
align_css = t["align"]

# ==========================================
# تصميم الواجهة وتطبيق الاتجاه واللغة والألوان الثلاثة
# ==========================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Cairo', sans-serif;
    }}
    .main .block-container {{
        max-width: 760px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        direction: {dir_attr};
        text-align: {align_css};
    }}
    .top-banner {{
        background: #18222f;
        color: #f8fafc;
        padding: 1.2rem 1.35rem;
        border-radius: 14px;
        margin-bottom: 0.9rem;
        text-align: {align_css};
    }}
    .top-badge {{
        display: inline-block;
        background: rgba(251, 191, 36, 0.16);
        color: #fbbf24;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.45rem;
    }}
    .top-title {{
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
    }}
    .top-sub {{
        font-size: 0.88rem;
        color: #cbd5e1;
        margin: 0;
        line-height: 1.5;
    }}
    .legend-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.55rem;
        margin-bottom: 1rem;
    }}
    .legend-red {{
        background: #fef2f2;
        border: 1.5px solid #dc2626;
        color: #991b1b;
        border-radius: 10px;
        padding: 0.6rem 0.65rem;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 800;
    }}
    .legend-orange {{
        background: #fff7ed;
        border: 1.5px solid #ea580c;
        color: #9a3412;
        border-radius: 10px;
        padding: 0.6rem 0.65rem;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 800;
    }}
    .legend-green {{
        background: #f0fdf4;
        border: 1.5px solid #16a34a;
        color: #166534;
        border-radius: 10px;
        padding: 0.6rem 0.65rem;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 800;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 100%;
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif;
    }}
    @media (max-width: 640px) {{
        .legend-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="top-banner" dir="{dir_attr}">
        <div class="top-badge">{t["badge"]}</div>
        <div class="top-title">{t["title"]}</div>
        <div class="top-sub">{t["subtitle"]}</div>
    </div>
    <div class="legend-grid" dir="{dir_attr}">
        <div class="legend-red">{t["red_label"]}</div>
        <div class="legend-orange">{t["orange_label"]}</div>
        <div class="legend-green">{t["green_label"]}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_summary = (
    f"{t['track_label']}: {track}"
    + (f" ({b2b_category})" if track == "B2B" and b2b_category else "")
    + f" | {t['lang_label']}: {language} | {t['specialty_label']}: {specialty} | {t['law_label']}: {law_reference}"
)
st.caption(meta_summary)

extra_context = st.text_input(
    t["context_label"],
    placeholder=t["context_ph"],
)

input_text = st.text_area(
    t["text_label"],
    height=155,
    placeholder=t["text_ph"],
)

uploaded_docs = st.file_uploader(
    t["upload_label"],
    type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
    accept_multiple_files=True,
)

if "final_report" not in st.session_state:
    st.session_state.final_report = ""
if "final_report_lang" not in st.session_state:
    st.session_state.final_report_lang = "العربية"

if st.button(t["run_btn"], type="primary"):
    if not api_key:
        st.error(t["missing_key"])
    elif not HAS_GROQ:
        st.error(t["missing_groq"])
    else:
        with st.spinner(t["spinner"]):
            extracted_docs = read_uploaded_files(uploaded_docs, api_key, vision_models)
            parts = []
            if extra_context.strip():
                parts.append(f"Contexte / السياق: {extra_context.strip()}")
            if input_text.strip():
                parts.append(f"Texte / النص المدخل:\n{input_text.strip()}")
            if extracted_docs.strip():
                parts.append(f"Documents / محتوى الملفات المرفوعة:\n{extracted_docs.strip()}")

            combined_input = "\n\n".join(parts).strip()
            if not combined_input:
                st.warning(t["empty_input"])
            else:
                try:
                    sys_prompt = build_prompt_system(language, track, b2b_category, specialty, law_reference)
                    usr_prompt = f"Matière à auditer / المادة المطلوب تدقيقها:\n{combined_input[:28000]}"
                    st.session_state.final_report = run_audit_engine(
                        api_key, sys_prompt, usr_prompt, text_models
                    )
                    st.session_state.final_report_lang = language
                except Exception as exc:
                    st.error(f"{exc}")

if st.session_state.final_report:
    st.markdown("---")
    st.markdown(f"### {t['report_heading']}")
    render_colored_paragraphs(st.session_state.final_report, st.session_state.final_report_lang)

    st.markdown(f"### {t['download_heading']}")
    rep_content = st.session_state.final_report
    col_left, col_right = st.columns(2)
    with col_left:
        st.download_button(
            t["dl_docx"],
            data=build_docx(rep_content, meta_summary),
            file_name="rapport_raseen_ai.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        pdf_data = build_pdf(rep_content, meta_summary)
        if pdf_data:
            st.download_button(
                t["dl_pdf"],
                data=pdf_data,
                file_name="rapport_raseen_ai.pdf",
                mime="application/pdf",
            )
        else:
            st.download_button(
                t["dl_txt"],
                data=rep_content.encode("utf-8"),
                file_name="rapport_raseen_ai.txt",
                mime="text/plain; charset=utf-8",
            )
    with col_right:
        st.download_button(
            t["dl_txt"],
            data=rep_content.encode("utf-8"),
            file_name="rapport_raseen_ai.txt",
            mime="text/plain; charset=utf-8",
        )
        st.download_button(
            t["dl_zip"],
            data=build_zip(rep_content, meta_summary, uploaded_docs),
            file_name="raseen_ai_package.zip",
            mime="application/zip",
        ) 
