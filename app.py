import streamlit as st
import time

st.set_page_config(
    page_title="رصين AI — منصة التدقيق والامتثال القانوني للصفقات العمومية",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
<style>
.main { background-color: #f8f9fa; }
.header-box {
    background: linear-gradient(135deg, #0f294a 0%, #1e4e8c 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(15, 41, 74, 0.15);
}
.card-red {
    background-color: #fdf2f2;
    border-right: 6px solid #d92d20;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-orange {
    background-color: #fffbeb;
    border-right: 6px solid #d97706;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-green {
    background-color: #ecfdf3;
    border-right: 6px solid #16a34a;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-blue {
    background-color: #eff6ff;
    border-right: 6px solid #1d4ed8;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.badge-red { background-color: #d92d20; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-orange { background-color: #d97706; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-green { background-color: #16a34a; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-blue { background-color: #1d4ed8; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.ref-text { color: #475569; font-size: 0.9em; margin-top: 6px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="header-box">
    <h1>⚖️ RASEEN AI — منصة رصين للتدقيق القانوني والصفقات العمومية</h1>
    <p>منصة ذكاء اصطناعي متكاملة (B2B &amp; B2G) — متوافقة مع القانون 23-12، القانون 06-01، وحماية المعطيات (القانون 18-07 المعدل بالقانون 25-11)</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("إعدادات التجريب")
    mode = st.radio(
        "اختر مسار الاستخدام:",
        [
            "فضاء المقاول والمتعامل الاقتصادي (B2B)",
            "فضاء الإدارة العمومية (B2G)",
        ],
        key="mode-radio-1"
    )
    
    use_sample = st.checkbox("أو جرّب فوراً بنموذج دفتر شروط تجريبي")
    st.divider()
    st.markdown("**المراجع التشريعية المفعلة:**")
    st.caption("• القانون 23-12 المتعلق بالصفقات العمومية")
    st.caption("• المرسوم الرئاسي 15-247 وتوجيهات وزارة المالية")
    st.caption("• القانون 06-01 المتعلق بالوقاية من الفساد")
    st.caption("• القانون 18-07 (المعدل بالقانون 25-11) لحماية المعطيات")

doc_name = None

uploaded_file = None
if uploaded_file is not None:
    doc_name = uploaded_file.name
elif use_sample:
    doc_name = "Cahier_des_Charges_Travaux_Commune_Exemple.pdf"

if doc_name is None:
    st.info(
        "👈 ارفع ملف دفتر الشروط من القائمة الجانبية، أو فعّل خيار **«أو جرّب فوراً بنموذج دفتر شروط تجريبي»** لبدء المعاينة المباشرة."
    )
else:
    with st.spinner("جاري تحليل الوثيقة ومطابقتها مع المنظومة القانونية..."):
        time.sleep(0.8)

    st.success(f"تمت معالجة الملف بنجاح: **{doc_name}**")

    if mode == "فضاء المقاول والمتعامل الاقتصادي (B2B)":
        st.subheader("🏗️ مسار المقاول (عمل مستقل دون الحاجة لولوج نظام الإدارة)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("مؤشر جاهزية العرض", "84%", "+12% بعد المعالجة")
        m2.metric("وثائق إقصائية مستخرجة", "6 وثائق")
        m3.metric("بنود تعسفية مرصودة", "2 بند")
        m4.metric("الأجل القانوني للتحضير", "15 يوماً (تنبيه)")

        tab1, tab2, tab3 = st.tabs(
            [
                "1. فك الشفرة والشروط الإقصائية",
                "2. رصد البنود التعسفية وطلب التوضيح",
                "3. مسودة العرض والمحاكاة قبل الإيداع",
            ]
        )

        with tab1:
            st.markdown(
                """
            <div class="card-blue">
                <span class="badge-blue">استخراج آلي (OCR &amp; Requirements)</span>
                <h4 style="margin-top:10px;">الملخص التنفيذي لمتطلبات دفتر الشروط</h4>
                <ul>
                    <li><strong>موضوع الصفقة:</strong> أشغال تهيئة وصيانة منشآت عمومية.</li>
                    <li><strong>الوثائق الإقصائية الحساسة:</strong> السجل التجاري المحيّن، شهادة التأهيل والتصنيف المهني، التحديث الجبائي وشبه الجبائي (CNAS / CACOBATPH / CASNOS)، الكفالة البنكية، والتصريحات القانونية الموقعة.</li>
                    <li><strong>تنبيه المواعيد:</strong> ضرورة التحقق من تاريخ الإيداع النهائي لتفادي رفض الظرف خارج الآجال.</li>
                </ul>
                <div class="ref-text">السند المرجعي: أحكام القانون 23-12 المتعلقة بتقديم العروض وفتح الأظرفة.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with tab2:
            st.markdown(
                """
            <div class="card-red">
                <span class="badge-red">بند مقيد للمنافسة / أجل غير كافٍ</span>
                <h4 style="margin-top:10px;">تحديد أجل تحضير العروض بـ 15 يوماً وتضخيم معايير التأهيل</h4>
                <p>رصدت المنصة أجل تحضير يقل عن المدة المعقولة لمشروع يتطلب زيارة ميدانية وتحضير عرض تقني ومالي متكامل، إضافة إلى شرط قد يحد من مشاركة المؤسسات المؤهلة.</p>
                <div class="ref-text">السند القانوني: مبادئ حرية الوصول للطلب العمومي، المساواة، وشفافية الإجراءات وفق القانون 23-12.</div>
            </div>
            """,
                unsafe_allow_html=True)

            st.markdown("**مسودة جاهزة لطلب توضيح أو طعن إداري مسبق قبل الإيداع:**")
            petition_draft = f"""إلى السيد/السيدة رئيس المصلحة المتعاقدة
الموضوع: طلب توضيح ومراجعة لبعض بنود دفتر الشروط المتعلق بـ ({doc_name})

تحية طيبة وبعد،
بصفتنا متعاملاً اقتصادياً مهتماً بالمشاركة في هذه الاستشارة/المناقصة، نلتمس من سيادتكم توضيح ومراجعة الآجال والمعايير الواردة في دفتر الشروط بما يكفل تكافؤ الفرص وحرية المنافسة طبقاً لأحكام القانون رقم 23-12 المتعلق بالصفقات العمومية.

تقبلوا فائق الاحترام والتقدير."""
            st.text_area("مسودة طلب التوضيح (قابلة للنسخ):", value=petition_draft, height=190)

        with tab3:
            st.markdown("**ملف المقاول للمحاكاة السريعة:**")
            c1, c2 = st.columns(2)
            with c1:
                company_name = st.text_input("اسم المؤسسة / المقاولة", value="مؤسسة الأوراش والخدمات التقنية")
                legal_form = st.selectbox("الشكل القانوني", ["مؤسسة ذات شخص وحيد (EURL)", "شركة ذات مسؤولية محدودة (SARL)", "مؤسسة ناشئة حاملة للوسم", "مقاول ذاتي"])
            with c2:
                has_tax = st.checkbox("الوثائق الجبائية وشبه الجبائية سارية المفعول", value=True)
                has_qual = st.checkbox("شهادة التأهيل / المراجع المهنية جاهزة", value=True)
                has_sig = st.checkbox("التوقيع والختم على كافة التصريحات مؤكد", value=False)

            if not has_sig:
                st.warning("⚠️ تنبيه محاكاة لجنة فتح الأظرفة: تأكد من التوقيع والختم على التصريحات القانونية قبل إيداع الظرف لتفادي الإقصاء الشكلي.")
            else:
                st.success("✅ جميع عناصر الجاهزية الأساسية مكتملة في المحاكاة.")

            offer_draft = f"""مسودة ملف الترشح — {company_name} ({legal_form})
الوثيقة المرجعية: {doc_name}
- التصريح بالترشح والتصريح بالنزاهة: جاهز للمراجعة والتوقيع.
- الحالة الجبائية والاجتماعية: {"مطابقة" if has_tax else "تحتاج تحيين"}.
- التأهيل والخبرة المهنية: {"متوفرة" if has_qual else "تحتاج استكمال"}.
ملاحظة: هذه المسودة أولية وتُراجع قانونياً وتقنياً قبل الإيداع الرسمي."""
            st.text_area("مسودة أولية لملف الترشح:", value=offer_draft, height=160)

            st.download_button(
                label="📥 تحميل ملخص المسار (B2B) بصيغة TXT",
                data=offer_draft,
                file_name="Raseen_B2B_Summary.txt",
                mime="text/plain",
            )

    else:
        st.subheader("🏛️ مسار الإدارة العمومية (التدقيق الوقائي قبل النشر)")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("نسبة الامتثال الأولي", "72%", "-17% عن المعيار")
        k2.metric("مخالفات حرجة", "1 خرق")
        k3.metric("تنبيهات تنظيمية", "2 تنبيه")
        k4.metric("بنود مطابقة", "3 بنود")

        st.markdown(
            """
        <div class="card-red">
            <span class="badge-red">مخالفة حرجة — خطر الإلغاء والمنازعة</span>
            <h4 style="margin-top:10px;">آجال تحضير العروض غير كافية (15 يوماً)</h4>
            <p>تحديد أجل قصير يحد من المنافسة الفعالة ويعرّض الإجراء للطعن أو الإلغاء.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المرسوم الرئاسي 15-247، والمادة 9 من القانون 06-01.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-orange">
            <span class="badge-orange">تنبيه تنظيمي — وضوح المعايير وحصة المؤسسات الناشئة</span>
            <h4 style="margin-top:10px;">تحديد معايير التأهيل بدقة وإدراج أحكام المؤسسات الناشئة والمصغرة</h4>
            <p>يجب صياغة معايير التأهيل المالية والتقنية بشكل موضوعي ومقاس، وتضمين الأحكام التحفيزية المقررة للمؤسسات الناشئة والمصغرة.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المادة 87 من المرسوم الرئاسي 15-247، وتوجيهات وزارة المالية.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-green">
            <span class="badge-green">بند مطابق</span>
            <h4 style="margin-top:10px;">اشتراط الوثائق الاجتماعية والجبائية سارية المفعول</h4>
            <p>مطابق للتنظيم المعمول به في الصفقات العمومية.</p>
            <div class="ref-text">السند القانوني: النصوص التنظيمية المؤطرة لملف الترشح.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        audit_report = f"""تقرير التدقيق القانوني الوقائي — منصة رصين AI (B2G)
الملف المدقق: {doc_name}
نسبة الامتثال الأولي: 72%
- المخالفات الحرجة: 1 (مراجعة آجال تحضير العروض وضمان تكافؤ الفرص).
- التنبيهات التنظيمية: 2 (توضيح معايير التأهيل وإدراج أحكام المؤسسات الناشئة والمصغرة).
- البنود المطابقة: 3.
المرجعية: القانون 23-12، المرسوم الرئاسي 15-247، القانون 06-01، والقانون 18-07 المعدل بالقانون 25-11."""

        st.text_area("ملخص تقرير التدقيق الإداري:", value=audit_report, height=170)

        st.download_button(
            label="📥 تحميل تقرير التدقيق (B2G) بصيغة TXT",
            data=audit_report,
            file_name="Raseen_B2G_Audit_Report.txt",
            mime="text/plain",
        ) 
import streamlit as st
import time

st.set_page_config(
    page_title="رصين AI — منصة التدقيق والامتثال القانوني للصفقات العمومية",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
<style>
.main { background-color: #f8f9fa; }
.header-box {
    background: linear-gradient(135deg, #0f294a 0%, #1e4e8c 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(15, 41, 74, 0.15);
}
.card-red {
    background-color: #fdf2f2;
    border-right: 6px solid #d92d20;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-orange {
    background-color: #fffbeb;
    border-right: 6px solid #d97706;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-green {
    background-color: #ecfdf3;
    border-right: 6px solid #16a34a;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-blue {
    background-color: #eff6ff;
    border-right: 6px solid #1d4ed8;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.badge-red { background-color: #d92d20; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-orange { background-color: #d97706; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-green { background-color: #16a34a; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-blue { background-color: #1d4ed8; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.ref-text { color: #475569; font-size: 0.9em; margin-top: 6px; }
</style>
""",
    unsafe_allow_html=True,
)



with st.sidebar:
    st.header("إعدادات التجريب")
    mode = st.radio(
        "اختر مسار الاستخدام:",
        [
            "فضاء المقاول والمتعامل الاقتصادي (B2B)",
            "فضاء الإدارة العمومية (B2G)",
        ],
        key="mode-radio-2"
    )
    
    use_sample = st.checkbox("أو جرّب فوراً بنموذج دفتر شروط تجريبي")
    st.divider()
    st.markdown("**المراجع التشريعية المفعلة:**")
    st.caption("• القانون 23-12 المتعلق بالصفقات العمومية")
    st.caption("• المرسوم الرئاسي 15-247 وتوجيهات وزارة المالية")
    st.caption("• القانون 06-01 المتعلق بالوقاية من الفساد")
    st.caption("• القانون 18-07 (المعدل بالقانون 25-11) لحماية المعطيات")

doc_name = None
if uploaded_file is not None:
    doc_name = uploaded_file.name
elif use_sample:
    doc_name = "Cahier_des_Charges_Travaux_Commune_Exemple.pdf"

if doc_name is None:
    st.info(
        "👈 ارفع ملف دفتر الشروط من القائمة الجانبية، أو فعّل خيار **«أو جرّب فوراً بنموذج دفتر شروط تجريبي»** لبدء المعاينة المباشرة."
    )
else:
    with st.spinner("جاري تحليل الوثيقة ومطابقتها مع المنظومة القانونية..."):
        time.sleep(0.8)

    st.success(f"تمت معالجة الملف بنجاح: **{doc_name}**")

    if mode == "فضاء المقاول والمتعامل الاقتصادي (B2B)":
        st.subheader("🏗️ مسار المقاول (عمل مستقل دون الحاجة لولوج نظام الإدارة)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("مؤشر جاهزية العرض", "84%", "+12% بعد المعالجة")
        m2.metric("وثائق إقصائية مستخرجة", "6 وثائق")
        m3.metric("بنود تعسفية مرصودة", "2 بند")
        m4.metric("الأجل القانوني للتحضير", "15 يوماً (تنبيه)")

        tab1, tab2, tab3 = st.tabs(
            [
                "1. فك الشفرة والشروط الإقصائية",
                "2. رصد البنود التعسفية وطلب التوضيح",
                "3. مسودة العرض والمحاكاة قبل الإيداع",
            ]
        )

        with tab1:
            st.markdown(
                """
            <div class="card-blue">
                <span class="badge-blue">استخراج آلي (OCR &amp; Requirements)</span>
                <h4 style="margin-top:10px;">الملخص التنفيذي لمتطلبات دفتر الشروط</h4>
                <ul>
                    <li><strong>موضوع الصفقة:</strong> أشغال تهيئة وصيانة منشآت عمومية.</li>
                    <li><strong>الوثائق الإقصائية الحساسة:</strong> السجل التجاري المحيّن، شهادة التأهيل والتصنيف المهني، التحديث الجبائي وشبه الجبائي (CNAS / CACOBATPH / CASNOS)، الكفالة البنكية، والتصريحات القانونية الموقعة.</li>
                    <li><strong>تنبيه المواعيد:</strong> ضرورة التحقق من تاريخ الإيداع النهائي لتفادي رفض الظرف خارج الآجال.</li>
                </ul>
                <div class="ref-text">السند المرجعي: أحكام القانون 23-12 المتعلقة بتقديم العروض وفتح الأظرفة.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with tab2:
            st.markdown(
                """
            <div class="card-red">
                <span class="badge-red">بند مقيد للمنافسة / أجل غير كافٍ</span>
                <h4 style="margin-top:10px;">تحديد أجل تحضير العروض بـ 15 يوماً وتضخيم معايير التأهيل</h4>
                <p>رصدت المنصة أجل تحضير يقل عن المدة المعقولة لمشروع يتطلب زيارة ميدانية وتحضير عرض تقني ومالي متكامل، إضافة إلى شرط قد يحد من مشاركة المؤسسات المؤهلة.</p>
                <div class="ref-text">السند القانوني: مبادئ حرية الوصول للطلب العمومي، المساواة، وشفافية الإجراءات وفق القانون 23-12.</div>
            </div>
            """,
                unsafe_allow_html=True)

            st.markdown("**مسودة جاهزة لطلب توضيح أو طعن إداري مسبق قبل الإيداع:**")
            petition_draft = f"""إلى السيد/السيدة رئيس المصلحة المتعاقدة
الموضوع: طلب توضيح ومراجعة لبعض بنود دفتر الشروط المتعلق بـ ({doc_name})

تحية طيبة وبعد،
بصفتنا متعاملاً اقتصادياً مهتماً بالمشاركة في هذه الاستشارة/المناقصة، نلتمس من سيادتكم توضيح ومراجعة الآجال والمعايير الواردة في دفتر الشروط بما يكفل تكافؤ الفرص وحرية المنافسة طبقاً لأحكام القانون رقم 23-12 المتعلق بالصفقات العمومية.

تقبلوا فائق الاحترام والتقدير."""
            st.text_area("مسودة طلب التوضيح (قابلة للنسخ):", value=petition_draft, height=190)

        with tab3:
            st.markdown("**ملف المقاول للمحاكاة السريعة:**")
            c1, c2 = st.columns(2)
            with c1:
                company_name = st.text_input("اسم المؤسسة / المقاولة", value="مؤسسة الأوراش والخدمات التقنية")
                legal_form = st.selectbox("الشكل القانوني", ["مؤسسة ذات شخص وحيد (EURL)", "شركة ذات مسؤولية محدودة (SARL)", "مؤسسة ناشئة حاملة للوسم", "مقاول ذاتي"])
            with c2:
                has_tax = st.checkbox("الوثائق الجبائية وشبه الجبائية سارية المفعول", value=True)
                has_qual = st.checkbox("شهادة التأهيل / المراجع المهنية جاهزة", value=True)
                has_sig = st.checkbox("التوقيع والختم على كافة التصريحات مؤكد", value=False)

            if not has_sig:
                st.warning("⚠️ تنبيه محاكاة لجنة فتح الأظرفة: تأكد من التوقيع والختم على التصريحات القانونية قبل إيداع الظرف لتفادي الإقصاء الشكلي.")
            else:
                st.success("✅ جميع عناصر الجاهزية الأساسية مكتملة في المحاكاة.")

            offer_draft = f"""مسودة ملف الترشح — {company_name} ({legal_form})
الوثيقة المرجعية: {doc_name}
- التصريح بالترشح والتصريح بالنزاهة: جاهز للمراجعة والتوقيع.
- الحالة الجبائية والاجتماعية: {"مطابقة" if has_tax else "تحتاج تحيين"}.
- التأهيل والخبرة المهنية: {"متوفرة" if has_qual else "تحتاج استكمال"}.
ملاحظة: هذه المسودة أولية وتُراجع قانونياً وتقنياً قبل الإيداع الرسمي."""
            st.text_area("مسودة أولية لملف الترشح:", value=offer_draft, height=160)

            st.download_button(
                label="📥 تحميل ملخص المسار (B2B) بصيغة TXT",
                data=offer_draft,
                file_name="Raseen_B2B_Summary.txt",
                mime="text/plain",
            )

    else:
        st.subheader("🏛️ مسار الإدارة العمومية (التدقيق الوقائي قبل النشر)")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("نسبة الامتثال الأولي", "72%", "-17% عن المعيار")
        k2.metric("مخالفات حرجة", "1 خرق")
        k3.metric("تنبيهات تنظيمية", "2 تنبيه")
        k4.metric("بنود مطابقة", "3 بنود")

        st.markdown(
            """
        <div class="card-red">
            <span class="badge-red">مخالفة حرجة — خطر الإلغاء والمنازعة</span>
            <h4 style="margin-top:10px;">آجال تحضير العروض غير كافية (15 يوماً)</h4>
            <p>تحديد أجل قصير يحد من المنافسة الفعالة ويعرّض الإجراء للطعن أو الإلغاء.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المرسوم الرئاسي 15-247، والمادة 9 من القانون 06-01.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-orange">
            <span class="badge-orange">تنبيه تنظيمي — وضوح المعايير وحصة المؤسسات الناشئة</span>
            <h4 style="margin-top:10px;">تحديد معايير التأهيل بدقة وإدراج أحكام المؤسسات الناشئة والمصغرة</h4>
            <p>يجب صياغة معايير التأهيل المالية والتقنية بشكل موضوعي ومقاس، وتضمين الأحكام التحفيزية المقررة للمؤسسات الناشئة والمصغرة.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المادة 87 من المرسوم الرئاسي 15-247، وتوجيهات وزارة المالية.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-green">
            <span class="badge-green">بند مطابق</span>
            <h4 style="margin-top:10px;">اشتراط الوثائق الاجتماعية والجبائية سارية المفعول</h4>
            <p>مطابق للتنظيم المعمول به في الصفقات العمومية.</p>
            <div class="ref-text">السند القانوني: النصوص التنظيمية المؤطرة لملف الترشح.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        audit_report = f"""تقرير التدقيق القانوني الوقائي — منصة رصين AI (B2G)
الملف المدقق: {doc_name}
نسبة الامتثال الأولي: 72%
- المخالفات الحرجة: 1 (مراجعة آجال تحضير العروض وضمان تكافؤ الفرص).
- التنبيهات التنظيمية: 2 (توضيح معايير التأهيل وإدراج أحكام المؤسسات الناشئة والمصغرة).
- البنود المطابقة: 3.
المرجعية: القانون 23-12، المرسوم الرئاسي 15-247، القانون 06-01، والقانون 18-07 المعدل بالقانون 25-11."""

        st.text_area("ملخص تقرير التدقيق الإداري:", value=audit_report, height=170)

        st.download_button(
            label="📥 تحميل تقرير التدقيق (B2G) بصيغة TXT",
            data=audit_report,
            file_name="Raseen_B2G_Audit_Report.txt",
            mime="text/plain",
        ) 
import streamlit as st
import time

st.set_page_config(
    page_title="رصين AI — منصة التدقيق والامتثال القانوني للصفقات العمومية",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
<style>
.main { background-color: #f8f9fa; }
.header-box {
    background: linear-gradient(135deg, #0f294a 0%, #1e4e8c 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 22px;
    box-shadow: 0 4px 14px rgba(15, 41, 74, 0.15);
}
.card-red {
    background-color: #fdf2f2;
    border-right: 6px solid #d92d20;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-orange {
    background-color: #fffbeb;
    border-right: 6px solid #d97706;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-green {
    background-color: #ecfdf3;
    border-right: 6px solid #16a34a;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.card-blue {
    background-color: #eff6ff;
    border-right: 6px solid #1d4ed8;
    padding: 18px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.badge-red { background-color: #d92d20; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-orange { background-color: #d97706; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-green { background-color: #16a34a; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.badge-blue { background-color: #1d4ed8; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
.ref-text { color: #475569; font-size: 0.9em; margin-top: 6px; }
</style>
""",
    unsafe_allow_html=True,
)



with st.sidebar:
    st.header("إعدادات التجريب")
    mode = st.radio(
        "اختر مسار الاستخدام:",
        [
            "فضاء المقاول والمتعامل الاقتصادي (B2B)",
            "فضاء الإدارة العمومية (B2G)",
        ],
        key="mode-radio-3"
    )
    
    use_sample = st.checkbox("أو جرّب فوراً بنموذج دفتر شروط تجريبي")
    st.divider()
    st.markdown("**المراجع التشريعية المفعلة:**")
    st.caption("• القانون 23-12 المتعلق بالصفقات العمومية")
    st.caption("• المرسوم الرئاسي 15-247 وتوجيهات وزارة المالية")
    st.caption("• القانون 06-01 المتعلق بالوقاية من الفساد")
    st.caption("• القانون 18-07 (المعدل بالقانون 25-11) لحماية المعطيات")

doc_name = None
if uploaded_file is not None:
    doc_name = uploaded_file.name
elif use_sample:
    doc_name = "Cahier_des_Charges_Travaux_Commune_Exemple.pdf"

if doc_name is None:
    st.info(
        "👈 ارفع ملف دفتر الشروط من القائمة الجانبية، أو فعّل خيار **«أو جرّب فوراً بنموذج دفتر شروط تجريبي»** لبدء المعاينة المباشرة."
    )
else:
    with st.spinner("جاري تحليل الوثيقة ومطابقتها مع المنظومة القانونية..."):
        time.sleep(0.8)

    st.success(f"تمت معالجة الملف بنجاح: **{doc_name}**")

    if mode == "فضاء المقاول والمتعامل الاقتصادي (B2B)":
        st.subheader("🏗️ مسار المقاول (عمل مستقل دون الحاجة لولوج نظام الإدارة)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("مؤشر جاهزية العرض", "84%", "+12% بعد المعالجة")
        m2.metric("وثائق إقصائية مستخرجة", "6 وثائق")
        m3.metric("بنود تعسفية مرصودة", "2 بند")
        m4.metric("الأجل القانوني للتحضير", "15 يوماً (تنبيه)")

        tab1, tab2, tab3 = st.tabs(
            [
                "1. فك الشفرة والشروط الإقصائية",
                "2. رصد البنود التعسفية وطلب التوضيح",
                "3. مسودة العرض والمحاكاة قبل الإيداع",
            ]
        )

        with tab1:
            st.markdown(
                """
            <div class="card-blue">
                <span class="badge-blue">استخراج آلي (OCR &amp; Requirements)</span>
                <h4 style="margin-top:10px;">الملخص التنفيذي لمتطلبات دفتر الشروط</h4>
                <ul>
                    <li><strong>موضوع الصفقة:</strong> أشغال تهيئة وصيانة منشآت عمومية.</li>
                    <li><strong>الوثائق الإقصائية الحساسة:</strong> السجل التجاري المحيّن، شهادة التأهيل والتصنيف المهني، التحديث الجبائي وشبه الجبائي (CNAS / CACOBATPH / CASNOS)، الكفالة البنكية، والتصريحات القانونية الموقعة.</li>
                    <li><strong>تنبيه المواعيد:</strong> ضرورة التحقق من تاريخ الإيداع النهائي لتفادي رفض الظرف خارج الآجال.</li>
                </ul>
                <div class="ref-text">السند المرجعي: أحكام القانون 23-12 المتعلقة بتقديم العروض وفتح الأظرفة.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with tab2:
            st.markdown(
                """
            <div class="card-red">
                <span class="badge-red">بند مقيد للمنافسة / أجل غير كافٍ</span>
                <h4 style="margin-top:10px;">تحديد أجل تحضير العروض بـ 15 يوماً وتضخيم معايير التأهيل</h4>
                <p>رصدت المنصة أجل تحضير يقل عن المدة المعقولة لمشروع يتطلب زيارة ميدانية وتحضير عرض تقني ومالي متكامل، إضافة إلى شرط قد يحد من مشاركة المؤسسات المؤهلة.</p>
                <div class="ref-text">السند القانوني: مبادئ حرية الوصول للطلب العمومي، المساواة، وشفافية الإجراءات وفق القانون 23-12.</div>
            </div>
            """,
                unsafe_allow_html=True)

            st.markdown("**مسودة جاهزة لطلب توضيح أو طعن إداري مسبق قبل الإيداع:**")
            petition_draft = f"""إلى السيد/السيدة رئيس المصلحة المتعاقدة
الموضوع: طلب توضيح ومراجعة لبعض بنود دفتر الشروط المتعلق بـ ({doc_name})

تحية طيبة وبعد،
بصفتنا متعاملاً اقتصادياً مهتماً بالمشاركة في هذه الاستشارة/المناقصة، نلتمس من سيادتكم توضيح ومراجعة الآجال والمعايير الواردة في دفتر الشروط بما يكفل تكافؤ الفرص وحرية المنافسة طبقاً لأحكام القانون رقم 23-12 المتعلق بالصفقات العمومية.

تقبلوا فائق الاحترام والتقدير."""
            st.text_area("مسودة طلب التوضيح (قابلة للنسخ):", value=petition_draft, height=190)

        with tab3:
            st.markdown("**ملف المقاول للمحاكاة السريعة:**")
            c1, c2 = st.columns(2)
            with c1:
                company_name = st.text_input("اسم المؤسسة / المقاولة", value="مؤسسة الأوراش والخدمات التقنية")
                legal_form = st.selectbox("الشكل القانوني", ["مؤسسة ذات شخص وحيد (EURL)", "شركة ذات مسؤولية محدودة (SARL)", "مؤسسة ناشئة حاملة للوسم", "مقاول ذاتي"])
            with c2:
                has_tax = st.checkbox("الوثائق الجبائية وشبه الجبائية سارية المفعول", value=True)
                has_qual = st.checkbox("شهادة التأهيل / المراجع المهنية جاهزة", value=True)
                has_sig = st.checkbox("التوقيع والختم على كافة التصريحات مؤكد", value=False)

            if not has_sig:
                st.warning("⚠️ تنبيه محاكاة لجنة فتح الأظرفة: تأكد من التوقيع والختم على التصريحات القانونية قبل إيداع الظرف لتفادي الإقصاء الشكلي.")
            else:
                st.success("✅ جميع عناصر الجاهزية الأساسية مكتملة في المحاكاة.")

            offer_draft = f"""مسودة ملف الترشح — {company_name} ({legal_form})
الوثيقة المرجعية: {doc_name}
- التصريح بالترشح والتصريح بالنزاهة: جاهز للمراجعة والتوقيع.
- الحالة الجبائية والاجتماعية: {"مطابقة" if has_tax else "تحتاج تحيين"}.
- التأهيل والخبرة المهنية: {"متوفرة" if has_qual else "تحتاج استكمال"}.
ملاحظة: هذه المسودة أولية وتُراجع قانونياً وتقنياً قبل الإيداع الرسمي."""
            st.text_area("مسودة أولية لملف الترشح:", value=offer_draft, height=160)

            st.download_button(
                label="📥 تحميل ملخص المسار (B2B) بصيغة TXT",
                data=offer_draft,
                file_name="Raseen_B2B_Summary.txt",
                mime="text/plain",
            )

    else:
        st.subheader("🏛️ مسار الإدارة العمومية (التدقيق الوقائي قبل النشر)")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("نسبة الامتثال الأولي", "72%", "-17% عن المعيار")
        k2.metric("مخالفات حرجة", "1 خرق")
        k3.metric("تنبيهات تنظيمية", "2 تنبيه")
        k4.metric("بنود مطابقة", "3 بنود")

        st.markdown(
            """
        <div class="card-red">
            <span class="badge-red">مخالفة حرجة — خطر الإلغاء والمنازعة</span>
            <h4 style="margin-top:10px;">آجال تحضير العروض غير كافية (15 يوماً)</h4>
            <p>تحديد أجل قصير يحد من المنافسة الفعالة ويعرّض الإجراء للطعن أو الإلغاء.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المرسوم الرئاسي 15-247، والمادة 9 من القانون 06-01.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-orange">
            <span class="badge-orange">تنبيه تنظيمي — وضوح المعايير وحصة المؤسسات الناشئة</span>
            <h4 style="margin-top:10px;">تحديد معايير التأهيل بدقة وإدراج أحكام المؤسسات الناشئة والمصغرة</h4>
            <p>يجب صياغة معايير التأهيل المالية والتقنية بشكل موضوعي ومقاس، وتضمين الأحكام التحفيزية المقررة للمؤسسات الناشئة والمصغرة.</p>
            <div class="ref-text">السند القانوني: القانون 23-12، المادة 87 من المرسوم الرئاسي 15-247، وتوجيهات وزارة المالية.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="card-green">
            <span class="badge-green">بند مطابق</span>
            <h4 style="margin-top:10px;">اشتراط الوثائق الاجتماعية والجبائية سارية المفعول</h4>
            <p>مطابق للتنظيم المعمول به في الصفقات العمومية.</p>
            <div class="ref-text">السند القانوني: النصوص التنظيمية المؤطرة لملف الترشح.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        audit_report = f"""تقرير التدقيق القانوني الوقائي — منصة رصين AI (B2G)
الملف المدقق: {doc_name}
نسبة الامتثال الأولي: 72%
- المخالفات الحرجة: 1 (مراجعة آجال تحضير العروض وضمان تكافؤ الفرص).
- التنبيهات التنظيمية: 2 (توضيح معايير التأهيل وإدراج أحكام المؤسسات الناشئة والمصغرة).
- البنود المطابقة: 3.
المرجعية: القانون 23-12، المرسوم الرئاسي 15-247، القانون 06-01، والقانون 18-07 المعدل بالقانون 25-11."""

        st.text_area("ملخص تقرير التدقيق الإداري:", value=audit_report, height=170)

        st.download_button(
            label="📥 تحميل تقرير التدقيق (B2G) بصيغة TXT",
            data=audit_report,
            file_name="Raseen_B2G_Audit_Report.txt",
            mime="text/plain",
        ) 
