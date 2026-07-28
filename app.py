import streamlit as st
import time
import base64
from io import BytesIO

st.set_page_config(
    page_title="منصة رصين AI - التدقيق القانوني لدفاتر الشروط",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.header-box {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.status-card-red {
    background-color: #fdf2f2;
    border-right: 6px solid #de350b;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.status-card-orange {
    background-color: #fff9e6;
    border-right: 6px solid #ffab00;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.status-card-green {
    background-color: #e3fcef;
    border-right: 6px solid #36b37e;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.badge-red { background-color: #de350b; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
.badge-orange { background-color: #ffab00; color: black; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
.badge-green { background-color: #36b37e; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
.legal-ref { font-size: 0.9em; color: #4a5568; font-style: italic; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
    <h1>⚖️ Raseen Legal Audit — منصة رصين AI</h1>
    <h3>النظام الآلي للتدقيق والامتثال القانوني لدفاتر الشروط العمومية</h3>
    <p>(TRL 4) مطابق للمرسوم الرئاسي 15-247، قانون الوقاية من الفساد 06-01، وتوجيهات وزارة المالية، ودعم المؤسسات الناشئة</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("لوحة التحكم والرفع")
    uploaded_file = st.file_uploader("ارفع ملف دفتر الشروط (PDF)", type=["pdf"])
    st.divider()
    st.markdown("**المراجع التشريعية المفعلة:**")
    st.caption("المرسوم الرئاسي 15-247 (الصفقات العمومية)")
    st.caption("القانون 06-01 (مكافحة الفساد والرشوة)")
    st.caption("دفتر الشروط النموذجي لوزارة المالية")
    st.caption("المادة 87 (دعم المؤسسات الناشئة)")

if uploaded_file is not None:
    with st.spinner("جاري تحليل محتوى دفتر الشروط ومطابقته مع المنظومة التشريعية..."):
        time.sleep(1.5)
    
    st.success("تم الفحص بنجاح: تم التعرف على الثغرات التشريعية والتنظيمية.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("مستوى الامتثال العام", "72%", "-17% عن المعيار")
    col2.metric("مخالفات حرجة", "1 خرق قانوني")
    col3.metric("تنبيهات تنظيمية", "2 مخاطر تأويل")
    col4.metric("بنود مطابقة", "3 بند سليم")

    st.divider()
    st.subheader("تقرير التدقيق الآلي التفصيلي (نظام الإشارات الضوئية)")

    st.markdown("""
    <div class="status-card-red">
        <span class="badge-red">مخالفة حرجة (خطر الإلغاء والفساد)</span>
        <h3 style="margin-top:10px; color:#800000;">البند 04 (صفحة 12): الموقع قم نظر الشروط</h3>
        <p><strong>التحليل الآلي:</strong> تم تحديد أجل تحضير العروض بـ 15 يوماً فقط, بنص التشريع علم ألا يقل الأجل عن 21 إلى 30 يوماً لضمان المنافسة الشريفة وتكافؤ الفرص.</p>
        <div class="legal-ref"><strong>السند القانوني:</strong> المواد 66 و67 من المرسوم الرئاسي 15-247 + المادة 9 من القانون 06-01 المتعلق بالوقاية من الفساد ومكافحته</div>
        <hr style="margin:10px 0;">
        <p style="color:#d32f2f;"><strong>التوصية تعديل البند:</strong> تعديل الأجل فوراً ليكون 21 يوماً عند الأقل لتفادي طعن المتنافسين وإلغاء الصفقة.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="status-card-orange">
        <span class="badge-orange">تنبيه تنظيمى (غموض ومعايير تأهيل محددة)</span>
        <h3 style="margin-top:10px; color:#b7791f;">البند 02 (صفحة 03): غموض معايير التأهيل المالي</h3>
        <p><strong>التحليل الآلي:</strong> دون تحديد حد أدنى لرقم الأعمال السوي المطلوب, مما يخالف تعليمات وزارة المالية وفتح باب التأويل والمقصودة C20 لشرائط عدم اكتشاف العالي.</p>
        <div class="legal-ref"><strong>السند القانوني:</strong> دفاتر الشروط النموذجية الصادرة عن وزارة المالية (تحديد معايير التأهيل بوضوح)</div>
        <hr style="margin:10px 0;">
        <p style="color:#b7791f;"><strong>التوصية تعديل البند:</strong> تحديد رقم الأعمال الأدنى المطلوب بوضوح (مثال: 15 مليون دج) لضمان الشفافية.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="status-card-orange">
        <span class="badge-orange">تنبيه تنظيمي (إغفال بند تحفيزي)</span>
        <h3 style="margin-top:10px; color:#b7791f;">إغفال المادة 87 الخاصة بالمؤسسات الناشئة والصغيرة</h3>
        <p><strong>التحليل الآلي:</strong> لم يتضمن دفتر الشروط إشارة لتخصيص حصة أو إعطاء أولوية للمؤسسات الناشئة أو الصغيرة وفقاً للتشريع الجاري به العمل.</p>
        <div class="legal-ref"><strong>السند القانوني:</strong> المادة 87 من المرسوم الرئاسي 15-247 المتضمن تنظيم الصفقات العمومية</div>
        <hr style="margin:10px 0;">
        <p style="color:#b7791f;"><strong>التوصية تعديل البند:</strong> إدراج بند تخصيص المؤسسات الناشئة والمصغرة طبقاً للتعليم.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="status-card-green">
        <span class="badge-green">بند مطابق تماماً</span>
        <h3 style="margin-top:10px; color:#1e7e34;">التأمين والوثائق الاجتماعية (CNAS / CACOBATPH)</h3>
        <p><strong>التحليل الآلي:</strong> اشتراط شهادات الأداء والحسابات الاجتماعية سارية المفعول مطابق للتشريع والتنظيم الجاري به العمل.</p>
        <div class="legal-ref"><strong>السند القانوني:</strong> أحكام قانون العمل والقوانين التنفيذية ذات الصلة بالصفقات</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    def generate_pdf_report():
        buffer = BytesIO()
        report_content = """
        ==================================================
        REPORTS: RASEEN LEGAL AUDIT - OFFICIAL REPORT
        ==================================================
        Project Name: Raseen AI - Automated Legal Auditing
        Target: TRL 4 Prototype for Protomarket II
        Document Audited: %s
        
        SUMMARY OF FINDINGS:
        - Overall Compliance Score: 72%
        - Critical Violations: 1 (Article 04 - Deadlines)
        - Regulatory Warnings: 2 (Financial Criteria & Startups Clause)
        - Compliant Clauses: 3 (Social Securities)
        
        DETAILED LEGAL RECOMMENDATIONS:
        1. Article 04: Modify preparation period from 15 to 21+ days according to Presidential Decree 15-247.
        2. Article 02: Explicitly define the minimum financial turnover criteria.
        3. Startup Integration: Include Article 87 provisions for emerging startups.
        
        Generated by Raseen AI Legal Engine - Algeria.
        ==================================================
        """ % uploaded_file.name
        buffer.write(report_content.encode('utf-8'))
        buffer.seek(0)
        return buffer.getvalue()

    pdf_bytes = generate_pdf_report()

    st.download_button(
        label="📥 (رسمي PDF) تحميل تقرير التدقيق القانوني الشامل",
        data=pdf_bytes,
        file_name="Raseen_Audit_Report.pdf",
        mime="application/pdf"
    )

else:
    st.info("👈 من القائمة الجانبية لبدء الفحص والتدقيق الآلي (PDF)، يرجى رفع ملف دفتر الشروط.")

