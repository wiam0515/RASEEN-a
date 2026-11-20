import time
import streamlit as st

st.set_page_config(
    page_title="منصة رصين للتدقيق القانوني والامتثال للصفقات العمومية — RASEEN AI",
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

TEXTS = {
    "ar": {
        "title": "⚖️ منصة رصين للتدقيق القانوني — RASEEN AI والصفقات العمومية",
        "subtitle": "متوافقة مع القانون 23-12، القانون 06-01، وحماية المعطيات (القانون 18-07 المعدل بالقانون 25-11) — (B2B & B2G) منصة ذكاء اصطناعي متكاملة",
        "sidebar_header": "إعدادات التجريب",
        "mode_label": "اختر مسار الاستخدام",
        "mode_b2b": "(B2B) فضاء المقاول والمتعامل الاقتصادي",
        "mode_b2g": "(B2G) فضاء الإدارة العمومية",
        "upload_label": "ارفع ملف دفتر الشروط (PDF أو صورة)",
        "sample_label": "أو جرّب فوراً بنموذج دفتر شروط تجريبي",
        "refs_title": "**المراجع التشريعية المعتمدة**",
        "ref_1": "• القانون 23-12 المتعلق بالصفقات العمومية",
        "ref_2": "• المرسوم الرئاسي 15-247 وتوجيهات وزارة المالية",
        "ref_3": "• القانون 06-01 المتعلق بالوقاية من الفساد",
        "ref_4": "• القانون 18-07 (المعدل بالقانون 25-11) لحماية المعطيات",
        "sample_doc_name": "Cahier_des_Charges_Travaux_Commune_Exemple.pdf",
        "info_empty": "ارفع ملف دفتر الشروط من القائمة الجانبية، أو فعّل خيار **«أو جرّب فوراً بنموذج دفتر شروط تجريبي»** لبدء المعاينة المباشرة.",
        "spinner_msg": "...جاري تحليل الوثيقة ومطابقتها مع المنظومة القانونية",
        "success_prefix": "تمت موثقة الملف بنجاح:",
        "b2b_heading": "نتائج الفحص القانوني للمتعامل الاقتصادي (B2B)",
        "b2b_b1": "- التحقق من شروط التأهيل والتصنيف المهني وتوازن بنود دفتر الشروط.",
        "b2b_b2": "- رصد الشروط التعجيزية أو الغامضة قبل إعداد العرض التقني والمالي.",
        "b2g_heading": "نتائج التدقيق والامتثال للمصلحة المتعاقدة (B2G)",
        "b2g_b1": "- مراجعة مطابقة الإجراءات والآجال لأحكام القانون 23-12.",
        "b2g_b2": "- التحقق من شفافية معايير التقييم والوقاية من شبهات تضارب المصالح.",
        "run_btn": "تشغيل تقرير التدقيق التفصيلي",
        "report_heading": "### ملخص التقرير القانوني",
        "col_axis": "المحور",
        "col_status": "الحالة",
        "row_1_axis": "الامتثال التشريعي",
        "row_1_status": "مطابق مبدئياً للأطر التنظيمية",
        "row_2_axis": "وضوح البنود",
        "row_2_status": "يُنصح بمراجعة المواد الخاصة بالضمانات والآجال",
        "row_3_axis": "المعطيات الشخصية",
        "row_3_status": "خاضع لأحكام القانون 18-07 المعدل بالقانون 25-11",
    },
    "fr": {
        "title": "⚖️ Plateforme RASEEN AI — Audit Juridique et Conformité des Marchés Publics",
        "subtitle": "Conforme à la Loi 23-12, la Loi 06-01 et la protection des données (Loi 18-07 modifiée par la Loi 25-11) — Plateforme IA intégrée (B2B & B2G)",
        "sidebar_header": "Paramètres d'essai",
        "mode_label": "Choisissez le parcours d'utilisation",
        "mode_b2b": "(B2B) Espace opérateur économique / soumissionnaire",
        "mode_b2g": "(B2G) Espace service contractant / administration",
        "upload_label": "Importer le cahier des charges (PDF ou image)",
        "sample_label": "Ou tester immédiatement avec un exemple de cahier des charges",
        "refs_title": "**Références juridiques de référence**",
        "ref_1": "• Loi 23-12 relative aux marchés publics",
        "ref_2": "• Décret présidentiel 15-247 et directives du ministère des Finances",
        "ref_3": "• Loi 06-01 relative à la prévention et à la lutte contre la corruption",
        "ref_4": "• Loi 18-07 (modifiée par la Loi 25-11) relative aux données personnelles",
        "sample_doc_name": "Cahier_des_Charges_Travaux_Commune_Exemple.pdf",
        "info_empty": "Importez un cahier des charges depuis la barre latérale ou activez l'option **« Ou tester immédiatement avec un exemple de cahier des charges »** pour démarrer l'aperçu.",
        "spinner_msg": "Analyse du document et vérification de conformité juridique en cours...",
        "success_prefix": "Document pris en charge avec succès :",
        "b2b_heading": "Résultats de l'analyse juridique — Opérateur économique (B2B)",
        "b2b_b1": "- Vérification des conditions de qualification, classification et équilibre des clauses.",
        "b2b_b2": "- Détection des clauses restrictives ou ambiguës avant préparation de l'offre.",
        "b2g_heading": "Résultats d'audit et de conformité — Service contractant (B2G)",
        "b2g_b1": "- Contrôle de conformité des procédures et délais selon la Loi 23-12.",
        "b2g_b2": "- Vérification de la transparence des critères d'évaluation et prévention des conflits d'intérêts.",
        "run_btn": "Générer le rapport d'audit détaillé",
        "report_heading": "### Synthèse du rapport juridique",
        "col_axis": "Axe",
        "col_status": "Statut",
        "row_1_axis": "Conformité juridique",
        "row_1_status": "Conforme à première vue aux cadres réglementaires",
        "row_2_axis": "Clarté des clauses",
        "row_2_status": "Révision recommandée des clauses de garanties et délais",
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

mode = None
uploaded_file = None
use_sample = False
doc_name = None

with st.sidebar:
    st.header(T["sidebar_header"])

    mode = st.radio(
        T["mode_label"],
        options=[T["mode_b2b"], T["mode_b2g"]],
        key="mode-radio-1",
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
elif use_sample:
    doc_name = T["sample_doc_name"]

if doc_name is None:
    st.info(T["info_empty"])
else:
    with st.spinner(T["spinner_msg"]):
        time.sleep(0.8)

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
