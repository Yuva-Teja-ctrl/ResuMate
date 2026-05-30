import streamlit as st
import pdfplumber
from groq import Groq
import json, re, io, time, unicodedata
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

st.set_page_config(page_title="ResuMate – AI Recruitment Assistant", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #f8fafc; }
    .hero { background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); border-radius: 16px; padding: 2.5rem 2rem; color: white; margin-bottom: 2rem; text-align: center; }
    .card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 1rem; }
    .score-high { background:#dcfce7; color:#166534; border-radius:8px; padding:4px 12px; font-weight:600; }
    .score-mid  { background:#fef9c3; color:#854d0e; border-radius:8px; padding:4px 12px; font-weight:600; }
    .score-low  { background:#fee2e2; color:#991b1b; border-radius:8px; padding:4px 12px; font-weight:600; }
    .shortlisted-badge { background:#2563eb; color:white; border-radius:20px; padding:3px 14px; font-size:0.78rem; font-weight:600; margin-left:8px; }
    .section-title { font-size:1.3rem; font-weight:700; color:#1e3a5f; margin:1.5rem 0 0.8rem; border-left:4px solid #2563eb; padding-left:10px; }
    .question-item { background:#f1f5f9; border-radius:8px; padding:0.7rem 1rem; margin:0.4rem 0; font-size:0.95rem; border-left:3px solid #2563eb; }
    .cert-item { background:#ede9fe; border-radius:8px; padding:4px 12px; display:inline-block; margin:3px 4px; font-size:0.85rem; color:#5b21b6; }
    .optional-label { font-size:0.75rem; color:#94a3b8; font-weight:400; margin-left:4px; }
    .stButton > button { background:linear-gradient(135deg,#1e3a5f,#2563eb); color:white; border:none; border-radius:8px; padding:0.6rem 2rem; font-weight:600; }
    .stButton > button:hover { opacity:0.88; color:white; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div style="display:flex;align-items:center;justify-content:center;gap:18px;margin-bottom:10px">
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="36" cy="36" r="34" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
      <rect x="20" y="16" width="28" height="36" rx="4" fill="rgba(255,255,255,0.15)" stroke="white" stroke-width="1.8"/>
      <path d="M40 16 L48 24 H40 V16 Z" fill="white" opacity="0.6"/>
      <line x1="26" y1="30" x2="42" y2="30" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
      <line x1="26" y1="36" x2="42" y2="36" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
      <line x1="26" y1="42" x2="36" y2="42" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
      <circle cx="52" cy="52" r="11" fill="#22c55e"/>
      <path d="M46.5 52 L50.5 56 L57.5 48" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div style="text-align:left">
      <h1 style="margin:0;font-size:2.6rem;letter-spacing:-1px">ResuMate</h1>
      <p style="margin:0;font-size:0.78rem;opacity:0.7;letter-spacing:3px;text-transform:uppercase">AI Recruitment Assistant</p>
    </div>
  </div>
  <p style="margin-top:8px;opacity:0.8">Upload Resumes · Rank Candidates · Generate Interview Questions</p>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]

with st.sidebar:
    st.markdown("### 📖 How to Use")
    st.markdown("1. Fill in **required** job details\n2. Optionally set preferences\n3. Upload PDF resumes\n4. Click **Analyse & Shortlist**\n5. View results & download report")
    st.markdown("---")
    st.markdown("**👨‍💻 Built By**\n\nYuva Teja · [GitHub](https://github.com/Yuva-Teja-ctrl/ResuMate)")

# ── HELPERS ──────────────────────────────────────────────────

def safe_edu(edu):
    if isinstance(edu, dict): return edu
    if isinstance(edu, str): return {"highest_degree": edu, "institution": "N/A", "graduation_year": "N/A"}
    return {"highest_degree": "N/A", "institution": "N/A", "graduation_year": "N/A"}

def safe_list(val):
    if isinstance(val, list): return [str(v) for v in val]
    if isinstance(val, str) and val: return [val]
    return []

def safe_str(val, default="N/A"):
    return str(val) if val is not None else default

def normalize_result(data):
    edu = safe_edu(data.get("education", {}))
    sb = data.get("score_breakdown", {})
    if not isinstance(sb, dict):
        sb = {"skills_score": 0, "experience_score": 0, "education_score": 0, "certification_score": 0}
    computed = sum([sb.get("skills_score",0), sb.get("experience_score",0),
                    sb.get("education_score",0), sb.get("certification_score",0)])
    score = data.get("score", computed)
    if abs(computed - score) > 2: score = computed
    return {
        "score": int(score), "score_breakdown": sb,
        "candidate_name": safe_str(data.get("candidate_name"), "Unknown"),
        "matched_skills": safe_list(data.get("matched_skills")),
        "missing_skills": safe_list(data.get("missing_skills")),
        "experience_years": safe_str(data.get("experience_years"), "N/A"),
        "education": edu,
        "certifications": safe_list(data.get("certifications")),
        "strengths": safe_str(data.get("strengths"), "N/A"),
        "weaknesses": safe_str(data.get("weaknesses"), "N/A"),
        "education_match": safe_str(data.get("education_match"), "N/A"),
        "certification_match": safe_str(data.get("certification_match"), "N/A"),
    }

def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t and t.strip():
                    text += t + "\n"
                else:
                    words = page.extract_words()
                    if words:
                        text += " ".join([w["text"] for w in words]) + "\n"
    except Exception as e:
        st.warning(f"⚠️ Could not open PDF: {e}")
        return ""
    if not text or len(text.strip()) < 50:
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            st.info("🔍 Detected scanned PDF — running OCR...")
            uploaded_file.seek(0)
            images = convert_from_bytes(uploaded_file.read(), dpi=200)
            ocr_text = "".join(pytesseract.image_to_string(img) + "\n" for img in images)
            if ocr_text.strip():
                st.success("✅ OCR completed successfully.")
                return ocr_text.strip()
        except Exception as e:
            st.warning(f"⚠️ OCR failed: {e}")
    return text.strip()

def parse_json_safe(raw):
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try: return json.loads(raw)
    except Exception: pass
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m: return json.loads(m.group())
    except Exception: pass
    try:
        fixed = raw
        fixed += ']' * max(0, raw.count('[') - raw.count(']'))
        fixed += '}' * max(0, raw.count('{') - raw.count('}'))
        return json.loads(fixed)
    except Exception: pass
    return None

def get_weights(min_experience, education_pref, certifications):
    n = sum([bool(min_experience), bool(education_pref), bool(certifications)])
    if n == 0: return 100, 0, 0, 0
    elif n == 1: return 60, (40 if min_experience else 0), (40 if education_pref else 0), (40 if certifications else 0)
    elif n == 2: return 40, (30 if min_experience else 0), (30 if education_pref else 0), (30 if certifications else 0)
    else: return 40, 20, 20, 20

def call_groq(client, messages, max_tokens=800, temperature=0.1):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(5 + attempt * 5)
            else:
                raise e
    return ""

def score_resume(resume_text, job_role, skills, min_experience="", education_pref="", certifications=""):
    w_skills, w_exp, w_edu, w_cert = get_weights(min_experience, education_pref, certifications)
    prompt = f"""You are a resume scoring API. Respond with ONLY a valid JSON object.

JOB ROLE: {job_role}
REQUIRED SKILLS: {skills}
EXPERIENCE REQUIRED: {min_experience or "Any"}
EDUCATION PREFERRED: {education_pref or "Any"}
CERTIFICATIONS PREFERRED: {certifications or "None"}
WEIGHTS: Skills={w_skills} Exp={w_exp} Edu={w_edu} Cert={w_cert} (total=100)

RESUME:
{resume_text[:2000]}

Respond ONLY with this JSON:
{{"score":0,"score_breakdown":{{"skills_score":0,"experience_score":0,"education_score":0,"certification_score":0}},"candidate_name":"Full Name","matched_skills":["skill1"],"missing_skills":["skill1"],"experience_years":"X years","education":{{"highest_degree":"Degree","institution":"University","graduation_year":"Year"}},"certifications":["cert1"],"strengths":"Summary.","weaknesses":"Gaps.","education_match":"Good Match","certification_match":"None Found"}}"""

    client = st.session_state.get('groq_client') or Groq(api_key=api_key)
    raw = call_groq(client, [
        {"role": "system", "content": "You are a resume scoring API. Always respond with valid JSON only. No text outside the JSON."},
        {"role": "user", "content": prompt}
    ], max_tokens=800, temperature=0.1)

    data = parse_json_safe(raw)
    if data and isinstance(data, dict):
        return normalize_result(data)
    st.warning("⚠️ Could not parse AI response for one resume.")
    return normalize_result({})

def generate_interview_questions(resume_text, job_role, skills, candidate_name, min_experience="", education_pref="", certifications=""):
    ctx = "".join([
        (f" | Exp: {min_experience}+ yrs" if min_experience else ""),
        (f" | Edu: {education_pref}" if education_pref else ""),
        (f" | Certs: {certifications}" if certifications else ""),
    ])
    prompt = f"""Generate exactly 10 interview questions. Return ONLY a JSON array of 10 strings.
Job: {job_role} | Skills: {skills}{ctx}
Resume: {resume_text[:800]}
Return ONLY: ["Question 1?","Question 2?",...,"Question 10?"]"""

    client = st.session_state.get("groq_client") or Groq(api_key=api_key)
    raw = call_groq(client, [
        {"role": "system", "content": "You are an interviewer API. Respond with a JSON array of exactly 10 questions. No other text."},
        {"role": "user", "content": prompt}
    ], max_tokens=1200, temperature=0.3)

    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    if raw.count('[') > raw.count(']'):
        raw = raw.rstrip(',').rstrip() + ']'
    try:
        q = json.loads(raw)
        return [item for item in q if isinstance(item, str) and len(item) > 10]
    except Exception: pass
    try:
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            return [item for item in json.loads(m.group()) if isinstance(item, str) and len(item) > 10]
    except Exception: pass
    return [l.strip().lstrip("0123456789.-) ") for l in raw.split("\n") if l.strip()][:10]

def score_badge(score):
    if score >= 70: return f'<span class="score-high">⭐ {score}/100</span>'
    elif score >= 40: return f'<span class="score-mid">🔶 {score}/100</span>'
    else: return f'<span class="score-low">🔴 {score}/100</span>'

def match_badge(label, text):
    if "Good" in text: c = "background:#dcfce7;color:#166534"
    elif "Partial" in text: c = "background:#ffedd5;color:#9a3412"
    elif "None" in text or "N/A" in text: c = "background:#fee2e2;color:#991b1b"
    else: c = "background:#f1f5f9;color:#64748b"
    return f'<span style="{c};border-radius:8px;padding:3px 10px;font-size:0.82rem;font-weight:600;margin-right:6px">{label}: {text}</span>'

def clean(text):
    text = unicodedata.normalize("NFKD", str(text))
    return re.sub(r" +", " ", "".join(ch if (32 <= ord(ch) < 127 or ch in "\n\t") else " " for ch in text)).strip()

def generate_pdf_report(results, job_role, skills, shortlist_count, min_experience="", education_pref="", certifications=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    sn  = ParagraphStyle("n",  parent=styles["Normal"], fontSize=9,  leading=14, spaceAfter=4)
    st2 = ParagraphStyle("t",  parent=styles["Title"],  fontSize=18, leading=22, spaceAfter=6, alignment=TA_CENTER)
    ss  = ParagraphStyle("s",  parent=styles["Normal"], fontSize=9,  leading=13, spaceAfter=3, alignment=TA_CENTER)
    sh2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=12, leading=16, spaceAfter=4, fontName="Helvetica-Bold")
    sh3 = ParagraphStyle("h3", parent=styles["Normal"], fontSize=9,  leading=14, spaceAfter=2, fontName="Helvetica-Bold")
    sq  = ParagraphStyle("q",  parent=styles["Normal"], fontSize=9,  leading=14, spaceAfter=4, leftIndent=10)
    story = [Paragraph("ResuMate - Recruitment Report", st2)]
    for line in [f"Job Role: {job_role}", f"Required Skills: {skills}",
                 (f"Min Experience: {min_experience} yrs" if min_experience else ""),
                 (f"Education: {education_pref}" if education_pref else ""),
                 (f"Certifications: {certifications}" if certifications else ""),
                 f"Total: {len(results)}  |  Shortlisted: {shortlist_count}"]:
        if line: story.append(Paragraph(clean(line), ss))
    story += [Spacer(1, 4*mm), HRFlowable(width="100%", thickness=1, color=colors.grey), Spacer(1, 4*mm)]
    for i, r in enumerate(results):
        d = r["score_data"]
        edu = safe_edu(d.get("education", {}))
        certs = safe_list(d.get("certifications"))
        sb = d.get("score_breakdown", {})
        status = "[SHORTLISTED]" if i < shortlist_count else "[NOT SHORTLISTED]"
        story.append(Paragraph(f"{status} #{i+1} {clean(d.get('candidate_name','Unknown'))} | Score: {d.get('score',0)}/100", sh2))
        story.append(Paragraph(clean(f"Skills: {sb.get('skills_score',0)} | Exp: {sb.get('experience_score',0)} | Edu: {sb.get('education_score',0)} | Cert: {sb.get('certification_score',0)}"), sn))
        story.append(Spacer(1, 2*mm))
        def row(label, value): story.append(Paragraph(f"<b>{clean(label)}</b> {clean(str(value))}", sn))
        row("Experience:", d.get("experience_years", "N/A"))
        edu_str = edu.get("highest_degree", "N/A")
        if edu.get("institution") not in ("N/A","Not mentioned",""): edu_str += f", {edu['institution']}"
        if edu.get("graduation_year") not in ("N/A","Not mentioned",""): edu_str += f" ({edu['graduation_year']})"
        row("Education:", edu_str)
        row("Certifications:", ", ".join(certs) if certs else "None")
        row("Matched Skills:", ", ".join(safe_list(d.get("matched_skills"))) or "None")
        row("Missing Skills:", ", ".join(safe_list(d.get("missing_skills"))) or "None")
        story.append(Paragraph(f"<b>Strengths:</b> {clean(d.get('strengths',''))}", sn))
        story.append(Paragraph(f"<b>Gaps:</b> {clean(d.get('weaknesses',''))}", sn))
        if i < shortlist_count and r.get("questions"):
            story += [Spacer(1,2*mm), Paragraph("Interview Questions:", sh3)]
            for j, q in enumerate(r["questions"], 1):
                story.append(Paragraph(clean(f"Q{j}. {q}"), sq))
        story += [Spacer(1,4*mm), HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), Spacer(1,4*mm)]
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# ── FORM ─────────────────────────────────────────────────────

st.markdown('<div class="section-title">📋 Job Requirements <span style="font-size:0.85rem;color:#94a3b8;font-weight:400">(required)</span></div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2,2,1])
with col1: job_role = st.text_input("🎯 Job Role", placeholder="e.g. Full Stack Developer, Data Scientist")
with col2: skills = st.text_input("🛠️ Required Skills", placeholder="e.g. Python, React, SQL, Docker")
with col3: shortlist_count = st.number_input("👥 Shortlist Top N", min_value=1, max_value=100, value=3)

st.markdown('<div class="section-title">🔧 Additional Preferences <span class="optional-label">— optional</span></div>', unsafe_allow_html=True)
opt1, opt2, opt3 = st.columns(3)
with opt1:
    st.markdown("##### 🎓 Education Preference")
    education_pref = st.text_input("Education", placeholder="e.g. B.Tech, Computer Science", label_visibility="collapsed")
    st.caption("Leave blank to accept any background")
with opt2:
    st.markdown("##### 💼 Minimum Experience (years)")
    min_experience = st.text_input("Experience", placeholder="e.g. 2", label_visibility="collapsed")
    st.caption("Leave blank to consider freshers too")
with opt3:
    st.markdown("##### 🏅 Preferred Certifications")
    certifications = st.text_input("Certifications", placeholder="e.g. AWS Certified, PMP", label_visibility="collapsed")
    st.caption("Leave blank if not required")

active = []
if education_pref: active.append(f"🎓 {education_pref}")
if min_experience: active.append(f"💼 {min_experience}+ yrs")
if certifications: active.append(f"🏅 {certifications}")
if active:
    st.success("**Active Filters:** " + "  |  ".join(active))

st.markdown('<div class="section-title">📂 Upload Resumes</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload PDF resumes (multiple allowed)", type=["pdf"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} resume(s) ready for analysis")

st.markdown("<br>", unsafe_allow_html=True)
run = st.button("🚀 Analyse & Shortlist", use_container_width=True)

if run:
    if not job_role or not skills:
        st.error("⚠️ Job Role and Required Skills are mandatory."); st.stop()
    if not uploaded_files:
        st.error("⚠️ Please upload at least one resume PDF."); st.stop()
    if shortlist_count > len(uploaded_files):
        shortlist_count = len(uploaded_files)

    groq_client = Groq(api_key=api_key)
    st.session_state['groq_client'] = groq_client
    results = []

    st.markdown('<div class="section-title">⏳ Analysing Resumes...</div>', unsafe_allow_html=True)
    progress = st.progress(0)
    status_text = st.empty()

    for idx, file in enumerate(uploaded_files):
        status_text.markdown(f"🔍 Analysing **{file.name}** ({idx+1}/{len(uploaded_files)})...")
        try:
            resume_text = extract_text_from_pdf(file)
            if not resume_text or len(resume_text) < 50:
                st.warning(f"⚠️ '{file.name}' — no readable text found. Skipping.")
                progress.progress((idx+1)/len(uploaded_files))
                continue
            score_data = score_resume(resume_text, job_role, skills, min_experience, education_pref, certifications)
            results.append({"filename": file.name, "resume_text": resume_text, "score_data": score_data, "questions": []})
        except Exception as e:
            st.error(f"Error on {file.name}: {e}")
        progress.progress((idx+1)/len(uploaded_files))

    if not results:
        st.error("No resumes processed successfully."); st.stop()

    results.sort(key=lambda x: x["score_data"].get("score", 0), reverse=True)
    shortlist_count = min(shortlist_count, len(results))

    status_text.markdown("🧠 Generating interview questions for shortlisted candidates...")
    for i in range(shortlist_count):
        r = results[i]
        try:
            results[i]["questions"] = generate_interview_questions(
                r["resume_text"], job_role, skills,
                r["score_data"].get("candidate_name", "Candidate"),
                min_experience, education_pref, certifications
            )
        except Exception as e:
            results[i]["questions"] = [f"Could not generate: {e}"]

    progress.progress(1.0)
    status_text.markdown("✅ Analysis complete!")

    # ── METRICS ──
    st.markdown('<div class="section-title">📊 Results — Ranked Candidates</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Analysed", len(results))
    m2.metric("Shortlisted", shortlist_count)
    m3.metric("Average Score", f"{sum(r['score_data'].get('score',0) for r in results)//len(results)}/100")
    m4.metric("Top Score", f"{results[0]['score_data'].get('score',0)}/100")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABLE ──
    table_data = []
    for i, r in enumerate(results):
        d = r["score_data"]
        edu = safe_edu(d.get("education", {}))
        certs = safe_list(d.get("certifications"))
        table_data.append({
            "Rank": f"#{i+1}",
            "Status": "✅ Shortlisted" if i < shortlist_count else "❌ Not Shortlisted",
            "Candidate": d.get("candidate_name", "Unknown"),
            "Score": d.get("score", 0),
            "Experience": d.get("experience_years", "N/A"),
            "Education": edu.get("highest_degree", "N/A"),
            "Institution": edu.get("institution", "N/A"),
            "Grad Year": edu.get("graduation_year", "N/A"),
            "Certifications": ", ".join(certs) if certs else "None",
            "Edu Match": d.get("education_match", "N/A"),
            "Cert Match": d.get("certification_match", "N/A"),
            "Matched Skills": ", ".join(safe_list(d.get("matched_skills"))),
            "Missing Skills": ", ".join(safe_list(d.get("missing_skills"))),
            "File": r["filename"]
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── DETAIL CARDS ──
    st.markdown('<div class="section-title">🔍 Detailed Candidate Analysis</div>', unsafe_allow_html=True)
    for i, r in enumerate(results):
        d = r["score_data"]
        edu = safe_edu(d.get("education", {}))
        certs = safe_list(d.get("certifications"))
        shortlisted = i < shortlist_count
        badge = '<span class="shortlisted-badge">✅ SHORTLISTED</span>' if shortlisted else ""
        cert_html = "".join([f'<span class="cert-item">🏅 {c}</span>' for c in certs]) if certs else '<span style="color:#94a3b8">None found</span>'
        edu_str = edu.get("highest_degree", "N/A")
        if edu.get("institution") not in ("N/A","Not mentioned",""): edu_str += f" — {edu['institution']}"
        if edu.get("graduation_year") not in ("N/A","Not mentioned",""): edu_str += f" ({edu['graduation_year']})"

        with st.expander(f"#{i+1}  {d.get('candidate_name','Unknown')}  —  Score: {d.get('score',0)}/100"):
            sb = d.get("score_breakdown", {})
            sk, ex, ed, ce = sb.get("skills_score",0), sb.get("experience_score",0), sb.get("education_score",0), sb.get("certification_score",0)
            wsk, wex, wed, wce = get_weights(min_experience, education_pref, certifications)

            def bar(value, max_val, color):
                if max_val == 0: return '<span style="color:#94a3b8;font-size:0.8rem">Not weighted</span>'
                pct = int((value / max_val) * 100)
                return f'<div style="background:#e2e8f0;border-radius:6px;height:10px;width:100%;margin-top:4px"><div style="background:{color};width:{pct}%;height:10px;border-radius:6px"></div></div><span style="font-size:0.78rem;color:#64748b">{value}/{max_val} pts</span>'

            st.markdown(f"""
<div class="card">
  <h3 style="margin:0">{d.get('candidate_name','Unknown')} {badge}</h3>
  <p style="color:#64748b;margin:4px 0 12px;font-size:0.88rem">{r['filename']}</p>
  <div style="margin-bottom:14px">
    {score_badge(d.get('score',0))}&nbsp;&nbsp;
    {match_badge("Edu", d.get("education_match","N/A"))}
    {match_badge("Certs", d.get("certification_match","N/A"))}
  </div>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0">
  <b>📊 Score Breakdown</b>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 16px">
    <div><span style="font-size:0.85rem;font-weight:600">🛠️ Skills</span>{bar(sk,wsk,"#2563eb")}</div>
    <div><span style="font-size:0.85rem;font-weight:600">💼 Experience</span>{bar(ex,wex,"#16a34a")}</div>
    <div><span style="font-size:0.85rem;font-weight:600">🎓 Education</span>{bar(ed,wed,"#9333ea")}</div>
    <div><span style="font-size:0.85rem;font-weight:600">🏅 Certifications</span>{bar(ce,wce,"#ea580c")}</div>
  </div>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px">
    <div><b>💼 Experience</b><br><span style="color:#475569">{d.get('experience_years','N/A')}</span></div>
    <div><b>🎓 Education</b><br><span style="color:#475569">{edu_str}</span></div>
  </div>
  <b>🏅 Certifications</b><br>
  <div style="margin:6px 0 14px">{cert_html}</div>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0">
  <b>✅ Matched Skills:</b> {', '.join(safe_list(d.get('matched_skills'))) or 'None'}<br><br>
  <b>❌ Missing Skills:</b> {', '.join(safe_list(d.get('missing_skills'))) or 'None'}<br><br>
  <b>💪 Strengths:</b> {d.get('strengths','')}<br><br>
  <b>⚠️ Gaps:</b> {d.get('weaknesses','')}
</div>
""", unsafe_allow_html=True)

            if shortlisted and r.get("questions"):
                st.markdown("#### 🎤 Interview Questions")
                for j, q in enumerate(r["questions"], 1):
                    st.markdown(f'<div class="question-item"><b>Q{j}.</b> {q}</div>', unsafe_allow_html=True)

    # ── DOWNLOADS ──
    st.markdown('<div class="section-title">⬇️ Download Report</div>', unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("📊 Download Excel Report", data=buf.getvalue(),
                           file_name="resumate_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with dl2:
        try:
            pdf_bytes = generate_pdf_report(results, job_role, skills, shortlist_count, min_experience, education_pref, certifications)
            st.download_button("📄 Download PDF Report", data=pdf_bytes,
                               file_name="resumate_report.pdf", mime="application/pdf",
                               use_container_width=True)
        except Exception as e:
            st.warning(f"PDF error: {e}")

    st.session_state["results"] = results
