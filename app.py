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
MAX_RESPONSE_TOKENS = 4096

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
    .sig-red {
        display: inline-block;
        background-color: #fdecea;
        color: #b71c1c;
        border: 1px solid #ef9a9a;
        border-radius: 6px;
        padding: 1px 8px;
        font-weight: 700;
    }
    .sig-amber {
        display: inline-block;
        background-color: #fff3e0;
        color: #e65100;
        border: 1px solid #ffcc80;
        border-radius: 6px;
        padding: 1px 8px;
        font-weight: 700;
    }
    .sig-green {
        display: inline-block;
        background-color: #e8f5e9;
        color: #1b5e20;
        border: 1px solid #a5d6a7;
        border-radius: 6px;
        padding: 1px 8px;
        font-weight: 700;
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


def colorize_traffic_report(report_text: str) -> str:
    # استبدال الرموز غير المرسومة أو المربعات المكسورة وعرض الإشارات بألوان واضحة
    text = report_text.replace("🟠", "برتقالي").replace("🟢", "أخضر").replace("🔴", "أحمر")
    text = re.sub(r"أحمر\s*:\s*خطأ(?:\s*جسيم)?", r'<span class="sig-red">● أحمر: خطأ</span>', text)
    text = re.sub(r"برتقالي\s*:\s*تنبيه", r'<span class="sig-amber">● برتقالي: تنبيه</span>', text)
    text = re.sub(r"أخضر\s*:\s*صحيح", r'<span class="sig-green">● أخضر: صحيح</span>', text)
    return text


def count_traffic_signals(report_text: str) -> tuple[int, int, int]:
    red_matches = re.findall(r"(?:🔴|أحمر)\s*:\s*خطأ", report_text)
    amber_matches = re.findall(r"(?:🟠|برتقالي)\s*:\s*تنبيه", report_text)
    green_matches = re.findall(r"(?:🟢|أخضر)\s*:\s*صحيح", report_text)
    return len(red_matches), len(amber_matches), len(green_matches)


def build_system_prompt(language: str, circuit: str, has_contractor_file: bool) -> str:
    if language == "العربية":
        lang_rule = "اكتب كامل التقرير باللغة العربية القانونية الواضحة والدقيقة، وأتمّ جميع الفقرات والجداول والقسم الخاص بالإلغاء والخاتمة دون أي بتر أو اختصار أو توقف في منتصف الجملة."
    elif language == "Français":
        lang_rule = "Rédige l'intégralité du rapport en français juridique précis, clair et complet, sans interruption ni troncature."
    else:
        lang_rule = "اكتب التقرير باللغة العربية مع إدراج المصطلحات والتحليلات المقابلة بالفرنسية (عربي / فرنسي) بوضوح، وأتمّه بالكامل دون أي توقف أو اختصار."

    mandatory_rules = """
قواعد إلزامية في جميع الحالات وفي كلا المسارين (B2G وB2B):
1. الإشارات الضوئية في كل بند أو عنصر أو مقارنة: اكتب الصيغة النصية الواضحة حرفياً:
   - أحمر: خطأ (مخالفة قانونية أو خلل جسيم أو نقص مؤثر في الوثائق أو التواقيع أو الشروط).
   - برتقالي: تنبيه (نقطة تحتاج إلى مراجعة أو توضيح أو استكمال أو تحقق إضافي).
   - أخضر: صحيح (بند أو وثيقة أو توقيع أو إجراء مطابق ومستوفٍ).
   لا تستخدم مربعات أو رموزاً غير نصية بدلاً من هذه التسميات.
2. تحديد العدد الدقيق في بداية التقرير: يجب أن يبدأ التقرير بفقرة أو جدول "حصيلة الإشارات الضوئية بالأرقام" يذكر صراحة عدد (أحمر: خطأ)، وعدد (برتقالي: تنبيه)، وعدد (أخضر: صحيح)، بحيث يطابق العدد المذكور عدد العناصر المفصّلة في التقرير.
3. عند ظهور أي (أحمر: خطأ) أو (برتقالي: تنبيه): يجب فوراً ذكر القانون أو النص القانوني الصحيح الواجب تطبيقه من المدونة القانونية المعتمدة مع بيان الحكم القانوني الصحيح.
4. في كل حالة تتعلق بالإلغاء (إلغاء الإجراء، إلغاء الصفقة أو المناقصة، إلغاء العقد أو الفسخ أو الإبطال، أو إلغاء بند أو شرط أو عرض أو وثيقة أو توقيع): يجب تحديد القانون الصحيح الواجب تطبيقه بوضوح، وبيان الشروط والأحكام القانونية الصحيحة للإلغاء وآثاره.
5. إتمام التقرير بالكامل: لا تتوقف أبداً قبل إنهاء كل مادة أو بند مذكور في النص وحالات الإلغاء والقانون الصحيح الواجب تطبيقه فيها.
""".strip()

    if circuit.startswith("B2G"):
        circuit_rule = """
المسار المختار هو B2G (الصفقات العمومية والمناقصات العمومية):
ابدأ بحصيلة عددية واضحة (عدد أحمر: خطأ، عدد برتقالي: تنبيه، عدد أخضر: صحيح)، ثم فصّل كل خطأ وكل تنبيه وكل بند صحيح مع ذكر القانون الصحيح الواجب تطبيقه، وخصص قسماً واضحاً لحالات الإلغاء والقانون الصحيح الواجب تطبيقه فيها.
""".strip()
    elif has_contractor_file:
        circuit_rule = """
المسار المختار هو B2B (دراسة دفتر الشروط / العقد ومقارنته بملف المقاول أو المؤسسة الاقتصادية المرفوع):
يستفيد من هذا المسار: المقاولون والمؤسسات الاقتصادية، المؤسسات الناشئة وحاملو المشاريع المبتكرة، شركات المساهمة البسيطة والشركات التجارية، مكاتب الدراسات والاستشارة، المتعاملون من الباطن، والمستشارون القانونيون ومديرو العقود.
ابدأ بحصيلة عددية واضحة (عدد أحمر: خطأ، عدد برتقالي: تنبيه، عدد أخضر: صحيح)، ثم قارن بدقة بين متطلبات دفتر الشروط أو العقد وبين ما يملكه المقاول أو المؤسسة الاقتصادية من وثائق وتواقيع، مع التركيز على:
- السجل التجاري، البطاقة الجبائية والرقم الإحصائي وشهادات الأداء والضرائب، شهادات شبه الضمان الاجتماعي، القانون الأساسي وتفويض التوقيع، شهادات التأهيل والتصنيف أو الاعتماد، المراجع المهنية والقدرات، والتواقيع والأختام والتصريحات.
ووضّح هل يناسب دفتر الشروط هذا العميل أم لا، مع ذكر القانون الصحيح الواجب تطبيقه فوراً عند أي خطأ أو تنبيه أو حالة إلغاء.
""".strip()
    else:
        circuit_rule = """
المسار المختار هو B2B (فهم دفتر الشروط / العقد وكشف ثغراته ومدى ملاءمته للعميل بدون رفع ملفه الخاص):
يستفيد من هذا المسار: المقاولون والمؤسسات الاقتصادية، المؤسسات الناشئة وحاملو المشاريع المبتكرة، شركات المساهمة البسيطة والشركات التجارية، مكاتب الدراسات والاستشارة، المتعاملون من الباطن، والمستشارون القانونيون ومديرو العقود.
العميل لم يرفع ملفه الخاص بعد؛ لذلك يجب:
1. البدء بحصيلة عددية واضحة (عدد أحمر: خطأ، عدد برتقالي: تنبيه، عدد أخضر: صحيح).
2. شرح مضمون دفتر الشروط أو العقد بوضوح وكشف ثغراته القانونية والتعاقدية والتنظيمية دون اشتراط رفع ملف العميل.
3. الإجابة بوضوح: هل يلائم هذا الدفتر أو العقد هذه الفئة من العملاء أم لا وما هي الشروط أو المخاطر التي ينبغي الانتباه إليها قبل المشاركة أو التعاقد؟
4. بيان الوثائق الأساسية (السجل التجاري، الضرائب، شبه الضمان الاجتماعي، القانون الأساسي، التأهيل، المراجع، والتواقيع والأختام) التي سيحتاجها العميل إذا قرر المشاركة، مع ذكر القانون الصحيح الواجب تطبيقه في كل خطأ أو تنبيه أو حالة إلغاء.
""".strip()

    return f"""
أنت المستشار القانوني الذكي لمنصة رصين AI المتخصصة في تدقيق العقود والصفقات العمومية والمناقصات وفق القانون الجزائري.
{lang_rule}

{mandatory_rules}

{circuit_rule}

المرجعية القانونية المعتمدة:
{LEGAL_REFERENCES_CORPUS}
""".strip()


def build_text_prompt(
    language: str,
    circuit: str,
    sector: str,
    b2b_profile: str,
    tender_label: str,
    tender_text: str,
    contractor_summary: str,
) -> str:
    safe_tender_text = _trim_text(tender_text, MAX_TENDER_CHARS)
    user_content = f"""
اللغة المطلوبة: {language}
المسار: {circuit}
القطاع: {sector}
ملف دفتر الشروط / العقد / المناقصة: {tender_label}

محتوى دفتر الشروط / العقد / المناقصة:
\"\"\"
{safe_tender_text}
\"\"\"
""".strip()

    if circuit.startswith("B2B"):
        user_content += f"""

الفئة المستفيدة في مسار B2B: {b2b_profile}
الوثائق الأساسية ذات الصلة: {", ".join(B2B_KEY_DOCUMENTS)}

ملف المقاول / المؤسسة الاقتصادية المرفوع:
\"\"\"
{contractor_summary if contractor_summary else "لم يرفع العميل ملفه الخاص؛ قم بدراسة دفتر الشروط أو العقد، وكشف ثغراته، وتوضيح مدى ملاءمته للعميل والوثائق والتواقيع المطلوبة منه مستقبلاً، مع ذكر العدد الدقيق للأخطاء والتنبيهات والبنود الصحيحة والقانون الصحيح الواجب تطبيقه."}
\"\"\"
"""
    return user_content


def run_audit(
    client: Groq,
    language: str,
    circuit: str,
    sector: str,
    b2b_profile: str,
    payload: dict,
    contractor_summary: str,
) -> tuple[str, str]:
    sys_prompt = build_system_prompt(language, circuit, bool(contractor_summary))

    if payload["kind"] == "text":
        user_content = build_text_prompt(
            language=language,
            circuit=circuit,
            sector=sector,
            b2b_profile=b2b_profile,
            tender_label=payload["label"],
            tender_text=payload["text"],
            contractor_summary=contractor_summary,
        )
        models_to_try = get_available_models_order(client, CANDIDATE_TEXT_MODELS, vision_only=False)
        last_error = None
        for model_name in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.2,
                    max_tokens=MAX_RESPONSE_TOKENS,
                )
                content = (completion.choices[0].message.content or "").strip()
                if content:
                    return content, model_name
            except Exception as exc:
                last_error = exc
                continue
        raise RuntimeError(f"تعذر تشغيل التدقيق النصي على Groq. آخر خطأ: {last_error}")

    vision_instruction = build_text_prompt(
        language=language,
        circuit=circuit,
        sector=sector,
        b2b_profile=b2b_profile,
        tender_label=payload["label"],
        tender_text="[اقرأ النص الموجود في الصورة/الصور المرفقة لدفتر الشروط أو العقد أو المناقصة بدقة ثم قم بتدقيقه قانونياً]",
        contractor_summary=contractor_summary,
    )
    content_blocks = [{"type": "text", "text": vision_instruction}]
    for mime_type, b64_str in payload["images"]:
        content_blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_str}"},
            }
        )

    vision_models = get_available_models_order(client, CANDIDATE_VISION_MODELS, vision_only=True)
    last_error = None
    for v_model in vision_models:
        try:
            completion = client.chat.completions.create(
                model=v_model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": content_blocks},
                ],
                temperature=0.2,
                max_tokens=MAX_RESPONSE_TOKENS,
            )
            content = (completion.choices[0].message.content or "").strip()
            if content:
                return content, v_model
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        "الملف المرفوع عبارة عن صورة أو PDF مصور ولا يحتوي على نص قابل للنسخ، ونماذج الرؤية غير متاحة حالياً. يُرجى رفع ملف PDF نصي أو لصق نص الوثيقة في خانة النص البديلة أدناه."
    )


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

st.subheader("تحميل دفتر الشروط / العقد / المناقصة (PDF أو صورة)")
tender_file = st.file_uploader(
    "اختر ملف دفتر الشروط أو العقد أو المناقصة (PDF أو JPG / PNG)",
    type=["pdf", "png", "jpg", "jpeg"],
    key="tender_file",
)

with st.expander("إدخال نص الوثيقة يدوياً (إذا كان الملف مصوراً بدون نص قابل للنسخ)"):
    manual_tender_text = st.text_area(
        "الصق نص دفتر الشروط أو العقد هنا في حال تعذر استخراج النص تلقائياً من الصورة أو PDF المصور",
        height=140,
        key="manual_tender_text",
    )

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

    st.subheader("تحميل ملف المقاول أو المؤسسة الاقتصادية (اختياري — يمكنكِ دراسة دفتر الشروط وفهم ثغراته بدون رفع ملفكِ)")
    contractor_files = st.file_uploader(
        "ارفع وثائق وتواقيع المقاول أو المؤسسة الاقتصادية إذا أردتِ المقارنة المباشرة (السجل التجاري، الشهادات، القانون الأساسي، التواقيع — PDF أو صور)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="contractor_files",
    )

if st.button("تشغيل التدقيق القانوني", type="primary", use_container_width=True):
    if tender_file is None and not manual_tender_text.strip():
        st.warning("يرجى تحميل ملف دفتر الشروط أو العقد أو المناقصة (أو لصق نص الوثيقة) أولاً.")
        st.stop()

    try:
        payload = prepare_tender_payload(tender_file, manual_tender_text)
    except Exception as exc:
        st.error(f"تعذر قراءة الملف المرفوع: {exc}")
        st.stop()

    if payload["kind"] == "empty":
        st.error(
            f"الملف ({payload['label']}) مصور ولا يحتوي على نص رقمي مباشر. افتحي (إدخال نص الوثيقة يدوياً) والصقي نص الوثيقة هناك، أو ارفعي ملف PDF نصياً."
        )
        st.stop()

    contractor_text = ""
    if circuit.startswith("B2B"):
        contractor_text = extract_contractor_files_text(contractor_files)
        if not contractor_files:
            st.info(
                "تم اختيار دراسة دفتر الشروط وفهم ثغراته ومدى ملاءمته للعميل دون اشتراط رفع ملف المقاول أو المؤسسة الاقتصادية."
            )

    st.markdown("### الإشارات الضوئية للتدقيق القانوني")
    col_red, col_amber, col_green = st.columns(3)
    with col_red:
        st.error("أحمر: خطأ + القانون الصحيح الواجب تطبيقه")
    with col_amber:
        st.warning("برتقالي: تنبيه + القانون الصحيح الواجب تطبيقه")
    with col_green:
        st.success("أخضر: صحيح")

    with st.spinner("جاري إجراء التدقيق القانوني عبر الذكاء الاصطناعي..."):
        try:
            groq_client = get_groq_client()
            report, used_model = run_audit(
                client=groq_client,
                language=selected_language,
                circuit=circuit,
                sector=sector,
                b2b_profile=b2b_profile,
                payload=payload,
                contractor_summary=contractor_text,
            )

            red_cnt, amber_cnt, green_cnt = count_traffic_signals(report)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("عدد الأخطاء (أحمر: خطأ)", red_cnt)
            with m2:
                st.metric("عدد التنبيهات (برتقالي: تنبيه)", amber_cnt)
            with m3:
                st.metric("عدد البنود الصحيحة (أخضر: صحيح)", green_cnt)

            st.caption(f"النموذج المنفّذ: {used_model} | الملف: {payload['label']}")
            st.markdown("### تقرير المستشار القانوني الذكي — رصين AI")
            st.markdown(colorize_traffic_report(report), unsafe_allow_html=True)
            with st.expander("المرجعية القانونية المعتمدة في التدقيق"):
                st.text(LEGAL_REFERENCES_CORPUS)
        except Exception as exc:
            st.error(f"حدث خطأ أثناء تنفيذ التدقيق: {exc}") 
