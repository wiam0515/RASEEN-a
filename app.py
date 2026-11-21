import base64
import io
import re
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

CANDIDATE_TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
    "gemma2-9b-it",
]

CANDIDATE_VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
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


def get_available_models_order(client: Groq, candidates: list[str], vision_only: bool = False) -> list[str]:
    ordered = []
    try:
        models_resp = client.models.list()
        available_ids = [m.id for m in getattr(models_resp, "data", []) if getattr(m, "id", None)]
        for preferred in candidates:
            if preferred in available_ids and preferred not in ordered:
                ordered.append(preferred)
        for mid in available_ids:
            if mid in ordered:
                continue
            if vision_only:
                if "scout" in mid or "maverick" in mid or "vision" in mid:
                    ordered.append(mid)
            else:
                if any(k in mid for k in ("llama", "qwen", "gemma")):
                    ordered.append(mid)
    except Exception:
        pass

    for fallback in candidates:
        if fallback not in ordered:
            ordered.append(fallback)
    return ordered


def _trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].strip() + "\n\n[... تم الاقتطاع حفاظاً على حد طول النص المرسل للنموذج ...]"


def extract_pdf_text(raw_bytes: bytes) -> tuple[str, int]:
    reader = PdfReader(io.BytesIO(raw_bytes))
    total_pages = len(reader.pages)
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        txt = (page.extract_text() or "").strip()
        if txt:
            pages.append(f"[صفحة {idx}]\n{txt}")
    return "\n\n".join(pages), total_pages


def extract_images_from_pdf(raw_bytes: bytes, max_images: int = 3) -> list[tuple[str, str]]:
    images_out = []
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        for page in reader.pages:
            for img_file in getattr(page, "images", []):
                data = getattr(img_file, "data", None)
                if data:
                    b64 = base64.b64encode(data).decode("utf-8")
                    images_out.append(("image/jpeg", b64))
                    if len(images_out) >= max_images:
                        return images_out
    except Exception:
        pass
    return images_out


def prepare_tender_payload(uploaded_file, fallback_manual_text: str) -> dict:
    if fallback_manual_text.strip():
        return {
            "kind": "text",
            "label": f"{uploaded_file.name if uploaded_file else 'نص مدخل يدوياً'}",
            "text": fallback_manual_text.strip(),
            "images": [],
        }

    raw_bytes = uploaded_file.getvalue()
    name_lower = uploaded_file.name.lower()

    if name_lower.endswith(".pdf"):
        text, total_pages = extract_pdf_text(raw_bytes)
        if text:
            return {
                "kind": "text",
                "label": f"{uploaded_file.name} ({total_pages} صفحات - نص مباشر)",
                "text": text,
                "images": [],
            }
        embedded_imgs = extract_images_from_pdf(raw_bytes, max_images=3)
        if embedded_imgs:
            return {
                "kind": "images",
                "label": f"{uploaded_file.name} ({total_pages} صفحات - صور مدمجة)",
                "text": "",
                "images": embedded_imgs,
            }
        return {
            "kind": "empty",
            "label": f"{uploaded_file.name} ({total_pages} صفحات)",
            "text": "",
            "images": [],
        }

    mime_type = "image/png" if name_lower.endswith(".png") else "image/jpeg"
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return {
        "kind": "images",
        "label": f"{uploaded_file.name} (صورة وثيقة)",
        "text": "",
        "images": [(mime_type, b64)],
    }


def extract_contractor_files_text(contractor_files) -> str:
    if not contractor_files:
        return ""

    parts = []
    for f in contractor_files:
        name_lower = f.name.lower()
        if name_lower.endswith(".pdf"):
            txt, pages = extract_pdf_text(f.getvalue())
            if txt:
                parts.append(f"=== وثيقة ملف المتعهد: {f.name} ({pages} صفحات) ===\n{txt}")
            else:
                parts.append(
                    f"=== وثيقة ملف المتعهد: {f.name} ({pages} صفحات) ===\n[ملف PDF مرفق ضمن ملف المتعهد بدون نص رقمي مباشر؛ يجب التحقق من الوثائق والتواقيع والأختام المرفقة فيه]"
                )
        else:
            parts.append(
                f"=== مرفق صورة وثيقة/توقيع المتعهد: {f.name} ===\n[صورة مرفقة ضمن ملف المتعهد]"
            )

    return _trim_text("\n\n".join(parts), MAX_CONTRACTOR_CHARS)


def count_traffic_signals(report_text: str) -> tuple[int, int, int]:
    red_matches = re.findall(r"🔴\s*أحمر\s*:\s*خطأ|🔴", report_text)
    amber_matches = re.findall(r"🟠\s*برتقالي\s*:\s*تنبيه|🟠", report_text)
    green_matches = re.findall(r"🟢\s*أخضر\s*:\s*صحيح|🟢", report_text)
    return len(red_matches), len(amber_matches), len(green_matches)


def build_system_prompt(language: str, circuit: str, has_contractor_file: bool) -> str:
    if language == "العربية":
        lang_rule = "اكتب كامل التقرير باللغة العربية القانونية الواضحة والدقيقة."
    elif language == "Français":
        lang_rule = "Rédige l'intégralité du rapport en français juridique précis, clair et structuré."
    else:
        lang_rule = "اكتب التقرير باللغة العربية مع إدراج المصطلحات والتحليلات المقابلة بالفرنسية (عربي / فرنسي) بوضوح."

    mandatory_rules = """
قواعد إلزامية في جميع الحالات وفي كلا المسارين (B2G وB2B):
1. الإشارات الضوئية في كل بند أو عنصر أو مقارنة:
   - 🔴 أحمر: خطأ (مخالفة قانونية أو خلل جسيم أو نقص مؤثر في الوثائق أو التواقيع أو الشروط).
   - 🟠 برتقالي: تنبيه (نقطة تحتاج إلى مراجعة أو توضيح أو استكمال أو تحقق إضافي).
   - 🟢 أخضر: صحيح (بند أو وثيقة أو توقيع أو إجراء مطابق ومستوفٍ).
2. تحديد العدد الدقيق في بداية التقرير: يجب أن يبدأ التقرير بفقرة أو جدول "حصيلة الإشارات الضوئية بالأرقام" يذكر صراحة عدد الأخطاء الجسيمة (🔴 أحمر: خطأ)، وعدد التنبيهات (🟠 برتقالي: تنبيه)، وعدد البنود الصحيحة (
