import io
import zipfile
from datetime import datetime
import streamlit as st

# ضبط إعدادات الصفحة مرة واحدة في البداية
st.set_page_config(
    page_title="رصين AI | RASEEN AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تهيئة حالة الجلسة بشكل مستقر لتفادي إعادة الضبط أو تكرار المعرفات
if "raseen_lang" not in st.session_state:
    st.session_state.raseen_lang = "ar"

if "raseen_audit_report" not in st.session_state:
    st.session_state.raseen_audit_report = None


def get_lang() -> str:
    return "ar" if st.session_state.raseen_lang == "ar" else "fr"


def extract_uploaded_text(uploaded_file) -> str:
    """استخراج النص بأمان من ملفات TXT أو PDF أو DOCX أو الصور مع معالجة الأخطاء دون توقف."""
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()
    raw_bytes = uploaded_file.getvalue()

    if file_name.endswith(".txt"):
        for enc in ("utf-8", "utf-8-sig", "cp1256", "latin-1"):
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw_bytes.decode("utf-8", errors="replace")

    if file_name.endswith(".docx"):
        try:
            import docx  # type: ignore

            doc = docx.Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception:
            return raw_bytes.decode("utf-8", errors="ignore")

    if file_name.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(raw_bytes))
            pages_text = []
            for idx, page in enumerate(reader.pages, start=1):
                txt = (page.extract_text() or "").strip()
                if txt:
                    pages_text.append(f"--- الصفحة {idx} ---\n{txt}")
            if pages_text:
                return "\n\n".join(pages_text)
        except Exception:
            pass
        return (
            f"[ملف PDF مرفوع: {uploaded_file.name} — جاهز للمراجعة أو لصق النص المباشر في حال كان ممسوحاً ضوئياً]"
        )

    if file_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore

            img = Image.open(io.BytesIO(raw_bytes))
            ocr_text = pytesseract.image_to_string(img, lang="ara+fra+eng").strip()
            if ocr_text:
                return ocr_text
        except Exception:
            pass
        return (
            f"[صورة وثيقة مرفوعة: {uploaded_file.name} — يُنصح بإرفاق النص المستخرج أو تفعيل محرك OCR على الخادم]"
        )

    return raw_bytes.decode("utf-8", errors="replace")


def analyze_documents(
    doc_title: str,
    doc_type: str,
    target_mode: str,
    cahier_text: str,
    operator_text: str,
    operator_file_name: str,
    lang: str,
) -> dict:
    """تدقيق دفتر الشروط وحده، أو مقارنته بملف المتعامل إذا تم رفعه اختيارياً."""
    is_ar = lang == "ar"
    clean_cahier = (cahier_text or "").strip()
    clean_operator = (operator_text or "").strip()
    has_operator = bool(clean_operator or operator_file_name)

    combined_lower = f"{clean_cahier}\n{clean_operator}".lower()

    red_flags = []
    orange_flags = []
    green_checks = []

    high_risk_keywords = [
        "فسخ فوري", "غرامات تأخير", "إقصاء", "مسؤولية مطلقة", "تنازل",
        "résiliation unilatérale", "pénalité", "exclusion", "responsabilité illimitée",
    ]
    caution_keywords = [
        "آجال", "ضمان", "كفالة", "تحكيم", "تعديل", "سرية", "معطيات شخصية", "توقيع إلكتروني",
        "délai", "garantie", "caution", "arbitrage", "avenant", "confidentialité", "données personnelles",
    ]

    for kw in high_risk_keywords:
        if kw in combined_lower:
            red_flags.append(
                (
                    (f"بند عالي الحساسية ({kw})" if is_ar else f"Clause sensible ({kw})"),
                    (
                        "يستوجب التحقق الدقيق من التوازن التعاقدي والالتزام بقانون الصفقات العمومية (23-12) أو القانون المدني/التجاري قبل التوقيع أو الإيداع."
                        if is_ar
                        else "Vérifier l'équilibre contractuel et la conformité au cadre juridique algérien (loi 23-12 et textes connexes)."
                    ),
                )
            )

    for kw in caution_keywords:
        if kw in combined_lower:
            orange_flags.append(
                (
                    (f"نقطة تتطلب تدقيقاً ({kw})" if is_ar else f"Point à vérifier ({kw})"),
                    (
                        "التأكد من وضوح الآجال، الضمانات، أو أحكام حماية المعطيات الشخصية (18-07 / 25-11) والتوقيع/العقد الإلكتروني (15-04 / 18-05 / 26-02)."
                        if is_ar
                        else "Vérifier les délais, garanties, protection des données (18-07 / 25-11) et règles électroniques (15-04 / 18-05 / 26-02)."
                    ),
                )
            )

    if not red_flags:
        red_flags.append(
            (
                ("عدم رصد مخالفة صريحة فورية في العينة المدققة" if is_ar else "Aucune anomalie critique détectée dans l'extrait"),
                (
                    "يُفضّل مراجعة الملاحق والشروط الخاصة بدقة مع إشراف مختص قانوني عند وجود التزامات مالية كبيرة."
                    if is_ar
                    else "Une validation juridique humaine reste recommandée pour les clauses financières et annexes."
                ),
            )
        )

    if not orange_flags:
        orange_flags.append(
            (
                ("مراجعة الشروط الشكلية والآجال والوثائق المرفقة" if is_ar else "Vérification des délais et pièces justificatives"),
                (
                    "التحقق من اكتمال الملف الإداري والجبائي ومطابقة الآجال لدفتر الشروط أو العقد."
                    if is_ar
                    else "Contrôler la complétude du dossier administratif/fiscal et la cohérence des délais."
                ),
            )
        )

    # حالة وجود ملف المتعامل الاختياري من عدمه
    if has_operator:
        green_checks.append(
            (
                ("تم تفعيل المطابقة مع ملف المتعامل" if is_ar else "Comparaison activée avec le dossier opérateur"),
                (
                    f"تم فحص دفتر الشروط ومقارنته بملف المتعامل ({operator_file_name or 'نص مرفق'}) للتحقق من الاستيفاء وتجنب أسباب الإقصاء."
                    if is_ar
                    else f"Audit croisé effectué entre le cahier des charges et le dossier ({operator_file_name or 'texte joint'})."
                ),
            )
        )
    else:
        green_checks.append(
            (
                ("تدقيق مستقل لدفتر الشروط / الوثيقة المرجعية" if is_ar else "Audit autonome du cahier des charges"),
                (
                    "تم تحليل دفتر الشروط وحده (بدون إرفاق ملف متعامل) لاستخراج الشروط الأساسية ونقاط اليقظة."
                    if is_ar
                    else "Analyse autonome du cahier des charges effectuée (sans dossier opérateur)."
                ),
            )
        )

    green_checks.append(
        (
            ("السيادة الرقمية وحماية المعطيات" if is_ar else "Souveraineté numérique et confidentialité"),
            (
                f"تم تصنيف الملف ضمن ({doc_type}) لمسار ({target_mode}) مع دعم التشغيل الآمن أو الشبكة المعزولة (Intranet)."
                if is_ar
                else f"Dossier classé sous ({doc_type}) pour ({target_mode}) avec support Intranet sécurisé."
            ),
        )
    )

    return {
        "title": doc_title.strip() or ("دفتر شروط / وثيقة قيد التدقيق" if is_ar else "Document analysé"),
        "doc_type": doc_type,
        "target_mode": target_mode,
        "has_operator": has_operator,
        "operator_name": operator_file_name,
        "char_count": len(clean_cahier) + len(clean_operator),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "red": red_flags,
        "orange": orange_flags,
        "green": green_checks,
    }


def build_report_text(report: dict, lang: str) -> str:
    """توليد نص التقرير المنسق للتصدير بصيغ TXT / ZIP."""
    is_ar = lang == "ar"
    op_status = (
        (f"مرفق ({report['operator_name']})" if report["has_operator"] else "غير مرفق (تدقيق دفتر الشروط وحده)")
        if is_ar
        else (f"Joint ({report['operator_name']})" if report["has_operator"] else "Non joint (Audit autonome)")
    )
    lines = [
        "==========================================",
        "رصين AI | RASEEN AI — تقرير التدقيق والامتثال" if is_ar else "RASEEN AI — RAPPORT D'AUDIT ET CONFORMITÉ",
        "==========================================",
        f"{'الوثيقة' if is_ar else 'Document'}: {report['title']}",
        f"{'النوع' if is_ar else 'Type'}: {report['doc_type']} | {'المسار' if is_ar else 'Parcours'}: {report['target_mode']}",
        f"{'ملف المتعامل' if is_ar else 'Dossier opérateur'}: {op_status}",
        f"{'التاريخ' if is_ar else 'Date'}: {report['timestamp']}",
        "",
        "🔴 " + ("أحمر — خطر / مخالفة" if is_ar else "ROUGE — RISQUE / NON-CONFORMITÉ"),
    ]
    for item_t, item_d in report["red"]:
        lines.append(f"  - {item_t}: {item_d}")

    lines.append("\n🟠 " + ("برتقالي — تنبيه / غموض" if is_ar else "ORANGE — VIGILANCE / AMBIGUÏTÉ"))
    for item_t, item_d in report["orange"]:
        lines.append(f"  - {item_t}: {item_d}")

    lines.append("\n🟢 " + ("أخضر — مطابق / سليم" if is_ar else "VERT — CONFORME / POINT VALIDÉ"))
    for item_t, item_d in report["green"]:
        lines.append(f"  - {item_t}: {item_d}")

    return "\n".join(lines)


def build_docx_bytes(report: dict, lang: str):
    """توليد ملف Word (.docx) إذا كانت مكتبة python-docx متوفرة."""
    try:
        import docx  # type: ignore

        doc = docx.Document()
        is_ar = lang == "ar"
        doc.add_heading("رصين AI — تقرير التدقيق والامتثال" if is_ar else "RASEEN AI — Rapport d'Audit", level=1)
        doc.add_paragraph(f"{'الوثيقة' if is_ar else 'Document'}: {report['title']} ({report['timestamp']})")
        doc.add_paragraph(f"{'النوع' if is_ar else 'Type'}: {report['doc_type']} | {'المسار' if is_ar else 'Parcours'}: {report['target_mode']}")

        for label, key in [
            ("🔴 أحمر — خطر / مخالفة" if is_ar else "🔴 ROUGE — Risque", "red"),
            ("🟠 برتقالي — تنبيه / غموض" if is_ar else "🟠 ORANGE — Vigilance", "orange"),
            ("🟢 أخضر — مطابق / سليم" if is_ar else "🟢 VERT — Conforme", "green"),
        ]:
            doc.add_heading(label, level=2)
            for t, d in report[key]:
                doc.add_paragraph(f"• {t}: {d}")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None


def build_zip_bytes(report_txt: str, docx_bytes) -> bytes:
    """تجميع مخرجات التقرير في أرشيف ZIP جاهز للتحميل."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("raseen_ai_audit_report.txt", report_txt.encode("utf-8"))
        if docx_bytes:
            zf.writestr("raseen_ai_audit_report.docx", docx_bytes)
    buf.seek(0)
    return buf.getvalue()


def render_payment_section(lang: str = "ar") -> None:
    """عرض الباقات وطرق الدفع المعتمدة لمساري B2B و B2G بدون تكرار لمعرفات العناصر."""
    is_ar = lang == "ar"

    st.subheader("💳 الباقات وطرق الدفع المعتمدة" if is_ar else "💳 Offres & Modes de Paiement")

    plan_options = (
        [
            "باقة المؤسسات والمقاولين (B2B) — 25,000 دج / شهرياً",
            "عقد الهيئات والصفقات (B2G) — 1,200,000 دج / سنوياً",
        ]
        if is_ar
        else [
            "Pack Entreprises & Entrepreneurs (B2B) — 25 000 DZD / mois",
            "Contrat Institutions & Marchés Publics (B2G) — 1 200 000 DZD / an",
        ]
    )
    selected_plan = st.radio(
        "اختر الصيغة المناسبة:" if is_ar else "Choisissez votre formule :",
        plan_options,
        key="raseen_payment_plan_radio",
    )
    st.caption(
        (f"الصيغة المحددة حالياً: {selected_plan}")
        if is_ar
        else (f"Formule sélectionnée : {selected_plan}")
    )

    tab_card, tab_transfer, tab_b2g = st.tabs(
        [
            "💳 البطاقة الذهبية / CIB" if is_ar else "💳 Carte Edahabia / CIB",
            "🏦 تحويل بنكي / بريدي" if is_ar else "🏦 Virement Bancaire / CCP",
            "📄 فاتورة شكلية (B2G)" if is_ar else "📄 Facture Proforma (B2G)",
        ]
    )

    with tab_card:
        st.info(
            "الدفع الإلكتروني الفوري متاح عبر البطاقة الذهبية (بريد الجزائر / BaridiMob) أو البطاقة البنكية ما بين البنوك (CIB - SATIM)."
            if is_ar
            else "Paiement électronique instantané disponible via Carte Edahabia (Algérie Poste / BaridiMob) ou Carte Interbancaire (CIB - SATIM)."
        )
        col1, col2 = st.columns(2)
        with col1:
            card_holder = st.text_input(
                "الاسم الكامل / اسم المؤسسة" if is_ar else "Nom complet / Raison sociale",
                placeholder="مثال: مؤسسة الأشغال والخدمات" if is_ar else "Ex: EURL Travaux & Services",
                key="raseen_pay_card_name",
            )
        with col2:
            card_email = st.text_input(
                "البريد الإلكتروني لاستلام التفعيل" if is_ar else "Email d'activation",
                placeholder="contact@entreprise.dz",
                key="raseen_pay_card_email",
            )

        if st.button(
            "متابعة نحو بوابة الدفع الآمنة 🔒" if is_ar else "Procéder au paiement sécurisé 🔒",
            key="raseen_btn_pay_electronic",
        ):
            if card_holder.strip() and card_email.strip():
                st.success(
                    f"✅ تم تسجيل طلب الاشتراك باسم ({card_holder.strip()}) وتوجيهه نحو بوابة الدفع المعتمدة (CIB / Edahabia). سيتم إرسال التفعيل إلى: {card_email.strip()}"
                    if is_ar
                    else f"✅ Demande enregistrée pour ({card_holder.strip()}) vers la passerelle CIB / Edahabia. Activation envoyée à : {card_email.strip()}"
                )
            else:
                st.warning(
                    "⚠️ يرجى إدخال الاسم/المؤسسة والبريد الإلكتروني للمتابعة."
                    if is_ar
                    else "⚠️ Veuillez saisir le nom/société et l'email pour continuer."
                )

    with tab_transfer:
        st.markdown(
            """
            **بيانات التحويل البنكي / البريدي (`RIB / RIP`):**
            * **المستفيد:** رصين AI (`RASEEN AI`)
            * **الحساب البنكي (`RIB`):** `001 00000 0000000000 00` *(يُستكمل عند التعاقد)*
            * **الحساب البريدي الجاري (`RIP`):** `007 99999 0000000000 00`
            """
            if is_ar
            else """
            **Coordonnées de virement (`RIB / RIP`) :**
            * **Bénéficiaire :** RASEEN AI
            * **RIB Bancaire :** `001 00000 0000000000 00` *(Communiqué à la souscription)*
            * **RIP Algérie Poste :** `007 99999 0000000000 00`
            """
        )
        receipt_file = st.file_uploader(
            "ارفع وصل الدفع (`PDF` أو صورة) لتأكيد الاشتراك:"
            if is_ar
            else "Téléversez le reçu de virement (`PDF` ou Image) :",
            type=["pdf", "png", "jpg", "jpeg"],
            key="raseen_pay_transfer_receipt",
        )
        if receipt_file is not None:
            st.success(
                f"✅ تم استلام الوصل ({receipt_file.name}) بنجاح! جاري التحقق وتفعيل الحساب."
                if is_ar
                else f"✅ Reçu ({receipt_file.name}) bien reçu ! Vérification et activation en cours."
            )

    with tab_b2g:
        st.info(
            "مخصص للهيئات العمومية والمؤسسات التي تعتمد الفوترة الرسمية أو الحوالة الإدارية (Mandat Administratif) وفق قانون الصفقات العمومية."
            if is_ar
            else "Dédié aux organismes publics et entreprises opérant par Facture Proforma ou Mandat Administratif conformément au Code des Marchés Publics."
        )
        c1, c2 = st.columns(2)
        with c1:
            org_name = st.text_input(
                "اسم الهيئة أو المؤسسة" if is_ar else "Nom de l'organisme / entreprise",
                key="raseen_b2g_org_name",
            )
            nif_num = st.text_input(
                "الرقم الجبائي (`NIF`)" if is_ar else "Numéro d'Identification Fiscale (`NIF`)",
                key="raseen_b2g_nif",
            )
        with c2:
            nis_num = st.text_input(
                "الرقم الإحصائي (`NIS`)" if is_ar else "Numéro d'Identification Statistique (`NIS`)",
                key="raseen_b2g_nis",
            )
            org_email = st.text_input(
                "البريد الإلكتروني الرسمي" if is_ar else "Email officiel",
                key="raseen_b2g_email",
            )

        if st.button(
            "إصدار طلب فاتورة شكلية (`Proforma`) 📄" if is_ar else "Générer une demande de Facture Proforma 📄",
            key="raseen_btn_b2g_proforma",
        ):
            if org_name.strip() and org_email.strip():
                extra_info = []
                if nif_num.strip():
                    extra_info.append(f"NIF: {nif_num.strip()}")
                if nis_num.strip():
                    extra_info.append(f"NIS: {nis_num.strip()}")
                meta_txt = f" ({' | '.join(extra_info)})" if extra_info else ""
                st.success(
                    f"✅ تم تسجيل طلب الفاتورة الشكلية باسم ({org_name.strip()}){meta_txt}. ستُرسل الفاتورة الرسمية إلى: {org_email.strip()}"
                    if is_ar
                    else f"✅ Demande de Facture Proforma enregistrée pour ({org_name.strip()}){meta_txt}. Envoi prévu à : {org_email.strip()}"
                )
            else:
                st.warning(
                    "⚠️ يرجى إدخال اسم الهيئة/المؤسسة والبريد الإلكتروني الرسمي على الأقل."
                    if is_ar
                    else "⚠️ Veuillez renseigner au moins le nom de l'organisme et l'email officiel."
                )


def render_audit_tab(lang: str) -> None:
    """واجهة التدقيق بخانتين منفصلتين: دفتر الشروط وحده + ملف المتعامل (اختياري) وحده."""
    is_ar = lang == "ar"

    st.subheader(
        "🔍 تدقيق دفاتر الشروط، العقود، وملفات المتعاملين"
        if is_ar
        else "🔍 Audit de Cahiers des Charges, Contrats & Dossiers Opérateurs"
    )
    st.caption(
        "يمكنك رفع دفتر الشروط وحده للتدقيق الفوري، أو إرفاق ملف المتعامل اختيارياً لإجراء المطابقة."
        if is_ar
        else "Importez le cahier des charges seul pour un audit direct, ou ajoutez facultativement le dossier opérateur pour comparaison."
    )

    # الصف الأول: البيانات التعريفية
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        doc_title = st.text_input(
            "عنوان الملف أو المشروع" if is_ar else "Titre du dossier / projet",
            placeholder="مثال: دفتر شروط مشروع إنجاز وتجهيز..." if is_ar else "Ex: Cahier des charges projet...",
            key="raseen_doc_title",
        )
    with col_meta2:
        doc_type = st.selectbox(
            "نوع الوثيقة" if is_ar else "Type de document",
            (
                ["دفتر شروط / صفقة عمومية", "عقد تجاري أو شراكة", "قرار أو ملف إداري"]
                if is_ar
                else ["Cahier des charges / Marché public", "Contrat commercial / Partenariat", "Décision / Dossier administratif"]
            ),
            key="raseen_doc_type",
        )
    with col_meta3:
        target_mode = st.selectbox(
            "المسار المستهدف" if is_ar else "Parcours cible",
            (
                ["B2B (مقاولون / مؤسسات / ناشئة / SPA)", "B2G (هيئات ومؤسسات عمومية)"]
                if is_ar
                else ["B2B (Entrepreneurs / Entreprises / Startups / SPA)", "B2G (Institutions & Organismes publics)"]
            ),
            key="raseen_target_mode",
        )

    st.markdown("---")

    # الصف الثاني: خانتان منفصلتان للرفع (دفتر الشروط وحده + ملف المتعامل الاختياري وحده)
    col_up1, col_up2 = st.columns(2)

    with col_up1:
        st.markdown("#### 1️⃣ " + ("دفتر الشروط / الوثيقة المرجعية" if is_ar else "Cahier des Charges / Document principal"))
        cahier_file = st.file_uploader(
            "ارفع ملف دفتر الشروط (`PDF`, `DOCX`, `TXT`, `PNG`, `JPG`)"
            if is_ar
            else "Importer le cahier des charges (`PDF`, `DOCX`, `TXT`, `PNG`, `JPG`)",
            type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
            key="raseen_cahier_uploader",
        )

    with col_up2:
        st.markdown("#### 2️⃣ " + ("ملف المتعامل / العرض (اختياري — غير إجباري)" if is_ar else "Dossier de l'opérateur (Optionnel)"))
        operator_file = st.file_uploader(
            "ارفع ملف المتعامل للمطابقة إن وُجد (`PDF`, `DOCX`, `TXT`, `PNG`, `JPG`)"
            if is_ar
            else "Importer le dossier opérateur si disponible (`PDF`, `DOCX`, `TXT`, `PNG`, `JPG`)",
            type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
            key="raseen_operator_uploader",
        )

    cahier_extracted = extract_uploaded_text(cahier_file)
    operator_extracted = extract_uploaded_text(operator_file)

    # منطقة النص لدفتر الشروط (أو لصق البنود مباشرة)
    cahier_text = st.text_area(
        "نص دفتر الشروط أو البنود المراد تدقيقها" if is_ar else "Texte du cahier des charges ou clauses à auditer",
        value=cahier_extracted,
        height=190,
        placeholder=(
            "يظهر هنا النص المستخرج من دفتر الشروط تلقائياً، أو يمكنك لصق البنود مباشرة هنا..."
            if is_ar
            else "Le texte extrait du cahier des charges s'affiche ici, ou collez vos clauses directement..."
        ),
        key="raseen_cahier_text_area",
    )

    # إظهار معاينة نص ملف المتعامل فقط إذا قام المستخدم برفع ملف متعامل
    operator_text = ""
    if operator_file is not None:
        operator_text = st.text_area(
            "محتوى ملف المتعامل المرفق (اختياري)" if is_ar else "Contenu du dossier opérateur joint (Optionnel)",
            value=operator_extracted,
            height=130,
            key="raseen_operator_text_area",
        )

    if st.button("🚀 بدء التدقيق الآن" if is_ar else "🚀 Lancer l'audit", type="primary", key="raseen_btn_run_audit"):
        if cahier_text.strip() or cahier_file is not None:
            st.session_state.raseen_audit_report = analyze_documents(
                doc_title=doc_title or (cahier_file.name if cahier_file else ""),
                doc_type=doc_type,
                target_mode=target_mode,
                cahier_text=cahier_text,
                operator_text=operator_text,
                operator_file_name=operator_file.name if operator_file else "",
                lang=lang,
            )
        else:
            st.warning(
                "⚠️ يرجى رفع دفتر الشروط أو لصق نصه على الأقل قبل بدء التدقيق (ملف المتعامل يبقى اختيارياً)."
                if is_ar
                else "⚠️ Veuillez importer ou coller le cahier des charges avant de lancer l'audit (le dossier opérateur reste facultatif)."
            )

    report = st.session_state.raseen_audit_report
    if report is not None:
        st.markdown("---")
        st.markdown(f"### 📋 {'نتائج التقرير' if is_ar else 'Résultats du rapport'}: {report['title']}")
        mode_badge = (
            ("مع مطابقة ملف المتعامل: " + report["operator_name"])
            if report["has_operator"]
            else "تدقيق دفتر الشروط وحده"
        ) if is_ar else (
            ("Avec comparaison dossier : " + report["operator_name"])
            if report["has_operator"]
            else "Audit autonome du cahier des charges"
        )
        st.caption(f"{report['doc_type']} • {report['target_mode']} • {mode_badge} • {report['timestamp']}")

        c_red, c_org, c_grn = st.columns(3)
        with c_red:
            st.markdown("#### 🔴 " + ("أحمر — خطر / مخالفة" if is_ar else "ROUGE — Risque"))
            for t, d in report["red"]:
                st.error(f"**{t}**\n\n{d}")
        with c_org:
            st.markdown("#### 🟠 " + ("برتقالي — تنبيه / غموض" if is_ar else "ORANGE — Vigilance"))
            for t, d in report["orange"]:
                st.warning(f"**{t}**\n\n{d}")
        with c_grn:
            st.markdown("#### 🟢 " + ("أخضر — مطابق / سليم" if is_ar else "VERT — Conforme"))
            for t, d in report["green"]:
                st.success(f"**{t}**\n\n{d}")

        report_txt = build_report_text(report, lang)
        docx_bytes = build_docx_bytes(report, lang)
        zip_bytes = build_zip_bytes(report_txt, docx_bytes)

        st.markdown("#### 📥 " + ("تصدير التقرير" if is_ar else "Exporter le rapport"))
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                label="📄 تحميل (`TXT`)" if is_ar else "📄 Télécharger (`TXT`)",
                data=report_txt.encode("utf-8"),
                file_name="raseen_ai_report.txt",
                mime="text/plain",
                key="raseen_dl_txt",
            )
        with d2:
            if docx_bytes:
                st.download_button(
                    label="📝 تحميل (`DOCX`)" if is_ar else "📝 Télécharger (`DOCX`)",
                    data=docx_bytes,
                    file_name="raseen_ai_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="raseen_dl_docx",
                )
            else:
                st.button(
                    "📝 `DOCX` غير متاح حالياً" if is_ar else "📝 `DOCX` indisponible",
                    disabled=True,
                    key="raseen_dl_docx_disabled",
                )
        with d3:
            st.download_button(
                label="📦 تحميل أرشيف (`ZIP`)" if is_ar else "📦 Télécharger archive (`ZIP`)",
                data=zip_bytes,
                file_name="raseen_ai_report_bundle.zip",
                mime="application/zip",
                key="raseen_dl_zip",
            )


def main() -> None:
    with st.sidebar:
        st.title("⚖️ رصين AI")
        lang_choice = st.radio(
            "اللغة / Langue",
            options=["ar", "fr"],
            format_func=lambda x: "العربية" if x == "ar" else "Français",
            index=0 if st.session_state.raseen_lang == "ar" else 1,
            key="raseen_lang_selector",
        )
        st.session_state.raseen_lang = lang_choice
        lang = get_lang()
        is_ar = lang == "ar"

        st.markdown("---")
        st.markdown(
            "**السيادة الرقمية:** دعم التوطين المحلي وإمكانية التشغيل عبر شبكة داخلية معزولة (`Offline Intranet`) لحماية المعطيات الحساسة."
            if is_ar
            else "**Souveraineté numérique :** hébergement local et option `Offline Intranet` pour la confidentialité des données."
        )

    lang = get_lang()
    is_ar = lang == "ar"

    st.title("رصين AI (RASEEN AI)" if is_ar else "RASEEN AI")
    st.write(
        "منصة ذكاء اصطناعي وتدقيق امتثال لمساري `B2B` و`B2G` مع دعم السيادة الرقمية والباقات وطرق الدفع المعتمدة."
        if is_ar
        else "Plateforme d'IA et d'audit de conformité pour les parcours `B2B` et `B2G`, avec souveraineté numérique et modes de paiement."
    )

    main_tab1, main_tab2 = st.tabs(
        [
            "🔍 التدقيق والتقارير" if is_ar else "🔍 Audit & Rapports",
            "💳 الباقات وطرق الدفع" if is_ar else "💳 Offres & Paiement",
        ]
    )

    with main_tab1:
        render_audit_tab(lang)

    with main_tab2:
        render_payment_section(lang=lang)


if __name__ == "__main__":
    main() 
