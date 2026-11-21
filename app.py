import io
import time
from google import genai
from google.genai import types
from pypdf import PdfReader
import streamlit as st

st.set_page_config(
    page_title="منصة رصين التدقيق القانوني والامتثال الصفقات العمومية - RASEEN AI",
    page_icon="⚖️",
    layout="wide",
)

if "lang" not in st.session_state:
    st.session_state.lang = "العربية"

with st.sidebar:
    selected_lang = st.radio(
        "اللغة / Langue",
        options=["العربية", "Français"],
        index=0 if st.session_state.lang == "العربية" else 1,
        key="lang-switcher-radio",
    )
    st.session_state.lang = selected_lang

is_ar = st.session_state.lang == "العربية"

SYSTEM_PROMPT = """
أنت مساعد تدقيق وامتثال قانوني متخصص في المناقصات والدفاتر الشروط والعقود التجارية والإدارية في الجزائر ضمن منصة "رصين AI" (Raseen AI)، المخصصة لدعم ملف وسم "المشروع المبتكر" (Projet Innovant).

المهام والضوابط الصارمة:
1. اللغة: حرر التقرير بنفس لغة المستخدم المطلوبة (العربية أو الفرنسية) بدقة قانونية واضحة واحترافية، مع ذكر المصطلحات القانونية الرسمية بدقة.
2. النطاق: حلل الوثيقة ضمن المسار المحدد (B2B أو B2G) والقطاع القياسي المحدد (البناء / Travaux، اللوازم / Fournitures، التجهيزات / Équipements، الخدمات العامة / Services généraux).
3. المرجعية التشريعية الجزائرية: اعتمد بدقة على:
   - القانون 23-12 المتعلق بالصفقات العمومية (خصوصاً في مسار B2G والالتزامات التعاقدية والإدارية).
   - القانون 06-01 المتعلق بالوقاية من الفساد ومكافحته المعدل والمتمم (رصد مخاطر تضارب المصالح، المحاباة، أو الشروط التقييدية/المشبوهة).
   - القانون 18-07 المتعلق بحماية الأشخاص الطبيعيين في مجال معالجة المعطيات ذات الطابع الشخصي، المعدل والمتمم بالقانون 25-11 (الالتزامات المتعلقة بالمعطيات الشخصية، التصريحات/التراخيص، أمن المعطيات، وتبادل أو نقل البيانات).
4. العناصر الإلزامية في التقرير:
   - ملخص موجز للوثيقة والمسار (B2B/B2G) والقطاع.
   - أبرز المخاطر القانونية والتعاقدية والبنود الحساسة.
   - تنبيه واضح ومفصل إلى النواقص الوثائقية والملاحق والبيانات أو التوقيعات والتأشيرات المطلوبة.
   - توصيات عملية مرتبة حسب الأولوية.
   - تنبيه ختامي بأن المخرجات أداة مساعدة على التدقيق القانوني ولا تغني عن الاستشارة القانونية المختصة.
"""

TEXTS = {
    "ar": {
        "title": "منصة رصين AI — التدقيق القانوني والامتثال",
        "subtitle": "تدقيق دفاتر الشروط والعقود (B2B / B2G) وفق التشريع الجزائري — ملف المشروع المبتكر (Projet Innovant)",
        "sidebar_header": "إعدادات التدقيق",
        "mode_label": "مسار التعاقد",
        "mode_b2b": "B2B (عقود ومناقصات خاصة)",
        "mode_b2g": "B2G (صفقات وطلبات عمومية)",
        "sector_label": "القطاع القياسي",
        "sectors": [
            "البناء (Travaux)",
            "اللوازم (Fournitures)",
            "التجهيزات (Équipements)",
            "الخدمات العامة (Services généraux)",
        ],
        "upload_label": "رفع وثيقة (PDF أو صورة)",
        "sample_label": "استخدام نموذج دفتر شروط تجريبي",
        "sample_doc_name": "نموذج_دفتر_شروط_تجهيزات_B2G.txt",
        "sample_content": (
            "دفتر شروط خاص باقتناء وتنصيب تجهيزات معلوماتية لفائدة مؤسسة عمومية (مسار B2G).\n"
            "يتضمن الملف معالجة قوائم مستخدمين وموظفين، وشروط آجال التنفيذ والضمان، "
            "مع طلب التصريح بالمصالح والملف الإداري والجبائي والتوقيع والختم الرسمي للمتعهد."
        ),
        "refs_title": "المرجعية التشريعية المعتمدة",
        "ref_1": "• القانون 23-12 المتعلق بالصفقات العمومية",
        "ref_2": "• القانون 06-01 المتعلق بالوقاية من الفساد ومكافحته",
        "ref_3": "• القانون 18-07 المعدل والمتمم بالقانون 25-11 (المعطيات ذات الطابع الشخصي)",
        "ref_4": "• إطار وسم المشروع المبتكر (Projet Innovant) — رصين AI",
        "info_empty": "يرجى رفع وثيقة (PDF أو صورة) أو تفعيل النموذج التجريبي من القائمة الجانبية للبدء.",
        "spinner_msg": "جاري قراءة الوثيقة وإجراء التدقيق القانوني عبر Gemini...",
        "success_prefix": "تم تحميل الوثيقة بنجاح:",
        "b2b_heading": "تحليل مسار B2B (العقود والمناقصات الخاصة)",
        "b2b_b1": "• فحص التوازن التعاقدي، الضمانات، آجال التنفيذ، ومسؤولية الأطراف في القطاع المختار.",
        "b2b_b2": "• التحقق من الامتثال للقانون 18-07 المعدل بالقانون 25-11 والوقاية من شبهات الفساد وفق القانون 06-01.",
        "b2g_heading": "تحليل مسار B2G (الصفقات والطلبات العمومية)",
        "b2g_b1": "• تدقيق الالتزام بأحكام القانون 23-12 المتعلق بالصفقات العمومية وضوابط المنافسة والشفافية.",
        "b2g_b2": "• رصد شبهات تضارب المصالح وفق القانون 06-01 ومتطلبات حماية المعطيات الشخصية وفق القانون 18-07 المعدل بالقانون 25-11.",
        "run_btn": "تشغيل التدقيق القانوني",
        "api_err": "تعذر العثور على GEMINI_API_KEY في st.secrets. يرجى إضافته في إعدادات Secrets على Streamlit Cloud.",
        "call_err": "حدث خطأ أثناء الاتصال بـ Gemini API: ",
        "report_heading": "تقرير التدقيق القانوني والامتثال",
        "col_axis": "محور التدقيق",
        "col_status": "الحالة",
        "row_1_axis": "الامتثال القانوني",
        "row_1_status": "تم فحصه وفق القانون 23-12 والقانون 06-01 (راجع التقرير التفصيلي)",
        "row_2_axis": "وضوح البنود والوثائق والتوقيعات",
        "row_2_status": "مراجعة الضمانات والآجال والنواقص الوثائقية والتوقيعات",
        "row_3_axis": "المعطيات ذات الطابع الشخصي",
        "row_3_status": "خاضع للقانون 18-07 المعدل بالقانون 25-11",
    },
    "fr": {
        "title": "Plateforme Raseen AI — Audit Juridique et Conformité",
        "subtitle": "Audit des cahiers des charges et contrats (B2B / B2G) selon le droit algérien — Dossier Projet Innovant",
        "sidebar_header": "Paramètres d'audit",
        "mode_label": "Parcours contractuel",
        "mode_b2b": "B2B (Contrats et appels d'offres privés)",
        "mode_b2g": "B2G (Marchés et commandes publics)",
        "sector_label": "Secteur standard",
        "sectors": [
            "Travaux (البناء)",
            "Fournitures (اللوازم)",
            "Équipements (التجهيزات)",
            "Services généraux (الخدمات العامة)",
        ],
        "upload_label": "Téléverser un document (PDF ou image)",
        "sample_label": "Utiliser un exemple de cahier des charges",
        "sample_doc_name": "exemple_cahier_des_charges_equipements_B2G.txt",
        "sample_content": (
            "Cahier des charges relatif à l'acquisition et l'installation d'équipements informatiques "
            "pour un organisme public (parcours B2G). Inclut le traitement de données d'utilisateurs et "
            "d'agents, des clauses de délais et de garanties, ainsi que la déclaration d'intérêts, "
            "les pièces administratives/fiscales et les signatures et cachets requis."
        ),
        "refs_title": "Référentiel juridique appliqué",
        "ref_1": "• Loi 23-12 relative aux marchés publics",
        "ref_2": "• Loi 06-01 relative à la prévention et à la lutte contre la corruption",
        "ref_3": "• Loi 18-07 modifiée et complétée par la Loi 25-11 (Données à caractère personnel)",
        "ref_4": "• Cadre du label Projet Innovant — Raseen AI",
        "info_empty": "Veuillez téléverser un document (PDF ou image) ou activer l'exemple dans la barre latérale pour commencer.",
        "spinner_msg": "Lecture du document et audit juridique via Gemini en cours...",
        "success_prefix": "Document chargé avec succès :",
        "b2b_heading": "Analyse du parcours B2B (Contrats et appels d'offres privés)",
        "b2b_b1": "• Examen de l'équilibre contractuel, des garanties, des délais et des responsabilités selon le secteur.",
        "b2b_b2": "• Vérification de la conformité à la Loi 18-07 modifiée par la Loi 25-11 et à la Loi 06-01.",
        "b2g_heading": "Analyse du parcours B2G (Marchés et commandes publics)",
        "b2g_b1": "• Audit du respect de la Loi 23-12 relative aux marchés publics, de la concurrence et de la transparence.",
        "b2g_b2": "• Détection des risques de conflits d'intérêts (Loi 06-01) et des exigences liées aux données personnelles (Lois 18-07 / 25-11).",
        "run_btn": "Lancer l'audit juridique",
        "api_err": "Clé GEMINI_API_KEY introuvable dans st.secrets. Ajoutez-la dans les Secrets de Streamlit Cloud.",
        "call_err": "Erreur lors de l'appel à l'API Gemini : ",
        "report_heading": "Rapport d'audit juridique et de conformité",
        "col_axis": "Axe d'audit",
        "col_status": "Statut",
        "row_1_axis": "Conformité juridique",
        "row_1_status": "Évaluée selon les Lois 23-12 et 06-01 (voir rapport détaillé)",
        "row_2_axis": "Clarté des clauses, pièces et signatures",
        "row_2_status": "Vérification des garanties, délais, lacunes documentaires et signatures",
        "row_3_axis": "Données personnelles",
        "row_3_status": "Soumis à la Loi 18-07 modifiée par la Loi 25-11",
    },
}

T = TEXTS["ar" if is_ar else "fr"]
direction = "rtl" if is_ar else "ltr"

st.markdown(
    f"""
    <style>
        .main {{
            background-color: #f8f9fa;
            direction: {direction};
        }}
        .header-box {{
            background: linear-gradient(135deg, #0f294a 0%, #1e4e8c 100%);
            color: white;
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            direction: {direction};
        }}
        .header-box h1 {{
            margin: 0 0 8px 0;
            font-size: 28px;
        }}
        .header-box p {{
            margin: 0;
            font-size: 14px;
            opacity: 0.95;
        }}
    </style>
    <div class="header-box">
        <h1>{T["title"]}</h1>
        <p>{T["subtitle"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def get_gemini_client() -> genai.Client:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error(T["api_err"])
        st.stop()
    return genai.Client(api_key=api_key)


def extract_document_payload(file_obj) -> tuple[str, bytes | None, str | None]:
    raw_bytes = file_obj.getvalue()
    mime_type = file_obj.type or ""
    filename_lower = (file_obj.name or "").lower()

    if mime_type == "application/pdf" or filename_lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        joined_text = "\n".join(pages_text).strip()
        if joined_text:
            return joined_text, None, None
        return "", raw_bytes, "application/pdf"

    if mime_type.startswith("image/") or filename_lower.endswith((".png", ".jpg", ".jpeg")):
        resolved_mime = mime_type if mime_type.startswith("image/") else "image/png"
        return "", raw_bytes, resolved_mime

    return raw_bytes.decode("utf-8", errors="ignore"), None, None


def run_gemini_audit(
    doc_text: str,
    binary_bytes: bytes | None,
    mime_type: str | None,
    mode_val: str,
    sector_val: str,
    lang_label: str,
) -> str:
    client = get_gemini_client()
    prompt_header = (
        f"اللغة المطلوبة للتقرير / Langue demandée : {lang_label}\n"
        f"المسار / Parcours : {mode_val}\n"
        f"القطاع / Secteur : {sector_val}\n"
    )

    contents: list = []
    if binary_bytes and mime_type:
        contents.append(types.Part.from_bytes(data=binary_bytes, mime_type=mime_type))
        contents.append(
            f"{prompt_header}\nقم بتدقيق الوثيقة المرفقة بالكامل واستخرج المخاطر القانونية والنواقص الوثائقية والتوقيعات والتوصيات."
        )
    else:
        contents.append(
            f"{prompt_header}\nالنص المراد تدقيقه :\n\"\"\"\n{doc_text}\n\"\"\""
        )

    response = client.models.generate_content(
        model="gemini-4-Hydrogen",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )
    return response.text or ""


mode = None
sector = None
uploaded_file = None
use_sample = False
doc_name = None
doc_text = ""
binary_bytes = None
mime_type = None

with st.sidebar:
    st.header(T["sidebar_header"])

    mode = st.radio(
        T["mode_label"],
        options=[T["mode_b2b"], T["mode_b2g"]],
        key="mode-radio-1",
    )

    sector = st.selectbox(
        T["sector_label"],
        options=T["sectors"],
        key="sector-select-1",
    )

    uploaded_file = st.file_uploader(
        T["upload_label"],
        type=["pdf", "png", "jpg", "jpeg"],
        key="uploaded-file-sidebar",
    )

    use_sample = st.checkbox(
        T["sample_label"],
        key="use-sample-sidebar",
    )

    st.divider()
    st.markdown(T["refs_title"])
    st.caption(T["ref_1"])
    st.caption(T["ref_2"])
    st.caption(T["ref_3"])
    st.caption(T["ref_4"])

if uploaded_file is not None:
    doc_name = uploaded_file.name
    doc_text, binary_bytes, mime_type = extract_document_payload(uploaded_file)
elif use_sample:
    doc_name = T["sample_doc_name"]
    doc_text = T["sample_content"]

if doc_name is None:
    st.info(T["info_empty"])
else:
    with st.spinner(T["spinner_msg"]):
        time.sleep(0.4)

    st.success(f'{T["success_prefix"]} **{doc_name}**')

    if mode == T["mode_b2b"]:
        st.subheader(T["b2b_heading"])
        st.write(T["b2b_b1"])
        st.write(T["b2b_b2"])
    else:
        st.subheader(T["b2g_heading"])
        st.write(T["b2g_b1"])
        st.write(T["b2g_b2"])

    run_audit = st.button(T["run_btn"], key="run-audit-btn")
    if run_audit:
        st.markdown(T["report_heading"])
        st.table(
            {
                T["col_axis"]: [
                    T["row_1_axis"],
                    T["row_2_axis"],
                    T["row_3_axis"],
                ],
                T["col_status"]: [
                    T["row_1_status"],
                    T["row_2_status"],
                    T["row_3_status"],
                ],
            }
        )
        with st.spinner(T["spinner_msg"]):
            try:
                ai_report = run_gemini_audit(
                    doc_text=doc_text,
                    binary_bytes=binary_bytes,
                    mime_type=mime_type,
                    mode_val=mode,
                    sector_val=sector,
                    lang_label=st.session_state.lang,
                )
                st.markdown(ai_report)
            except Exception as exc:
                st.error(f'{T["call_err"]}{exc}') 
