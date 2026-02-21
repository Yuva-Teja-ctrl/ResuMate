import streamlit as st
import pdfplumber
from groq import Groq
import json
import re
import pandas as pd
from fpdf import FPDF
import io
import time

st.set_page_config(page_title="ResuMate – AI Recruitment Assistant", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #f8fafc; }
    .hero { background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); border-radius: 16px; padding: 2.5rem 2rem; color: white; margin-bottom: 2rem; text-align: center; }
    .hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0; }
    .hero p  { font-size: 1.1rem; opacity: 0.85; margin: 0.5rem 0 0; }
    .card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 1rem; }
    .score-high { background:#dcfce7; color:#166534; border-radius:8px; padding:4px 12px; font-weight:600; }
    .score-mid  { background:#fef9c3; color:#854d0e; border-radius:8px; padding:4px 12px; font-weight:600; }
    .score-low  { background:#fee2e2; color:#991b1b; border-radius:8px; padding:4px 12px; font-weight:600; }
    .shortlisted-badge { background:#2563eb; color:white; border-radius:20px; padding:3px 14px; font-size:0.78rem; font-weight:600; margin-left:8px; }
    .section-title { font-size:1.3rem; font-weight:700; color:#1e3a5f; margin:1.5rem 0 0.8rem; border-left:4px solid #2563eb; padding-left:10px; }
    .question-item { background:#f1f5f9; border-radius:8px; padding:0.7rem 1rem; margin:0.4rem 0; font-size:0.95rem; border-left:3px solid #2563eb; }
    .cert-item { background:#ede9fe; border-radius:8px; padding:4px 12px; display:inline-block; margin:3px 4px; font-size:0.85rem; color:#5b21b6; }
    .optional-label { font-size:0.75rem; color:#94a3b8; font-weight:400; margin-left:4px; }
    div[data-testid="stExpander"] > div { border:none !important; }
    .stButton > button { background:linear-gradient(135deg,#1e3a5f,#2563eb); color:white; border:none; border-radius:8px; padding:0.6rem 2rem; font-weight:600; transition:opacity .2s; }
    .stButton > button:hover { opacity:0.88; color:white; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div style="display:flex;align-items:center;justify-content:center;gap:18px;margin-bottom:10px">
        <!-- SVG Logo -->
        <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Outer ring -->
          <circle cx="36" cy="36" r="34" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
          <!-- Document body -->
          <rect x="20" y="16" width="28" height="36" rx="4" fill="rgba(255,255,255,0.15)" stroke="white" stroke-width="1.8"/>
          <!-- Folded corner -->
          <path d="M40 16 L48 24 L40 24 Z" fill="white" opacity="0.4"/>
          <path d="M40 16 L48 24 H40 V16 Z" fill="white" opacity="0.6"/>
          <!-- Lines on document -->
          <line x1="26" y1="30" x2="42" y2="30" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
          <line x1="26" y1="36" x2="42" y2="36" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
          <line x1="26" y1="42" x2="36" y2="42" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.8"/>
          <!-- Checkmark circle -->
          <circle cx="52" cy="52" r="11" fill="#22c55e"/>
          <path d="M46.5 52 L50.5 56 L57.5 48" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div style="text-align:left">
            <h1 style="margin:0;font-size:2.6rem;letter-spacing:-1px">ResuMate</h1>
            <p style="margin:0;font-size:0.78rem;opacity:0.7;letter-spacing:3px;text-transform:uppercase">AI Recruitment Assistant</p>
        </div>
    </div>
    <p style="margin-top:8px;opacity:0.8">Upload Resumes &nbsp;·&nbsp; Rank Candidates &nbsp;·&nbsp; Generate Interview Questions</p>
</div>
""", unsafe_allow_html=True)

# Load API key from Streamlit secrets
api_key = st.secrets["GROQ_API_KEY"]

with st.sidebar:
    st.markdown("""
<div style="text-align:center;padding:10px 0 5px">
    <svg width="48" height="48" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="36" cy="36" r="34" stroke="#2563eb" stroke-width="2"/>
      <rect x="20" y="16" width="28" height="36" rx="4" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <path d="M40 16 L48 24 H40 V16 Z" fill="#2563eb" opacity="0.6"/>
      <line x1="26" y1="30" x2="42" y2="30" stroke="#2563eb" stroke-width="1.8" stroke-linecap="round"/>
      <line x1="26" y1="36" x2="42" y2="36" stroke="#2563eb" stroke-width="1.8" stroke-linecap="round"/>
      <line x1="26" y1="42" x2="36" y2="42" stroke="#2563eb" stroke-width="1.8" stroke-linecap="round"/>
      <circle cx="52" cy="52" r="11" fill="#22c55e"/>
      <path d="M46.5 52 L50.5 56 L57.5 48" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div style="font-weight:700;font-size:1.1rem;color:#1e3a5f;margin-top:4px">ResuMate</div>
</div>
<hr style="border:none;border-top:1px solid #e2e8f0;margin:8px 0">
""", unsafe_allow_html=True)
    st.markdown("### 📖 How to Use")
    st.markdown("""
1. Fill in **required** job details
2. Optionally set Education, Experience & Certification preferences
3. Upload PDF resumes
4. Click **Analyse & Shortlist**
5. View results & download report
""")
    st.markdown("---")
    st.markdown("### 👨‍💻 Built By")
    st.markdown("**Yuva Teja** · [GitHub](https://github.com/Yuva-Teja-ctrl/ResuMate)")

# ── HELPERS ──────────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()

def score_resume(resume_text, job_role, skills, min_experience="", education_pref="", certifications=""):
    # Dynamic weights — only active when recruiter specifies that criterion
    num_optional = sum([bool(min_experience), bool(education_pref), bool(certifications)])

    if num_optional == 0:
        w_skills, w_exp, w_edu, w_cert = 100, 0, 0, 0
    elif num_optional == 1:
        w_skills = 60
        w_exp  = 40 if min_experience else 0
        w_edu  = 40 if education_pref else 0
        w_cert = 40 if certifications  else 0
    elif num_optional == 2:
        w_skills = 40
        w_exp  = 30 if min_experience else 0
        w_edu  = 30 if education_pref else 0
        w_cert = 30 if certifications  else 0
    else:
        w_skills, w_exp, w_edu, w_cert = 40, 20, 20, 20

    # Build requirements block
    req_lines = [f"- Required Skills: {skills}"]
    if min_experience: req_lines.append(f"- Minimum Experience: {min_experience} years")
    if education_pref: req_lines.append(f"- Preferred Education: {education_pref}")
    if certifications:  req_lines.append(f"- Preferred Certifications: {certifications}")
    requirements = "\n".join(req_lines)

    # Build scoring weights block
    weight_lines = [
        f"- Skills match:        {w_skills} pts" + (" (ONLY criterion)" if num_optional == 0 else ""),
        f"- Experience match:    {w_exp} pts" + (" (NOT specified — award 0)" if not min_experience else f" (required: {min_experience}+ yrs)"),
        f"- Education match:     {w_edu} pts" + (" (NOT specified — award 0)" if not education_pref else f" (preferred: {education_pref})"),
        f"- Certification match: {w_cert} pts" + (" (NOT specified — award 0)" if not certifications else f" (preferred: {certifications})"),
    ]
    weights = "\n".join(weight_lines)

    # Build JSON template as a plain string (no f-string brace issues)
    json_template = (
        '{\n'
        '  "score": <integer 0-100>,\n'
        '  "score_breakdown": {\n'
        f'    "skills_score": <integer 0-{w_skills}>,\n'
        f'    "experience_score": <integer 0-{w_exp}>,\n'
        f'    "education_score": <integer 0-{w_edu}>,\n'
        f'    "certification_score": <integer 0-{w_cert}>\n'
        '  },\n'
        '  "candidate_name": "<full name or Unknown>",\n'
        '  "matched_skills": ["skill1", "skill2"],\n'
        '  "missing_skills": ["skill1", "skill2"],\n'
        '  "experience_years": "<e.g. 2 years or Fresher>",\n'
        '  "education": {\n'
        '    "highest_degree": "<e.g. B.Tech Computer Science or Not mentioned>",\n'
        '    "institution": "<university/college or Not mentioned>",\n'
        '    "graduation_year": "<year or Not mentioned>"\n'
        '  },\n'
        '  "certifications": ["cert1", "cert2"],\n'
        '  "strengths": "<2-3 sentence summary of candidate strengths>",\n'
        '  "weaknesses": "<1-2 sentence summary of gaps>",\n'
        '  "education_match": "<Good Match / Partial Match / Not Mentioned>",\n'
        '  "certification_match": "<Good Match / Partial Match / None Found>"\n'
        '}'
    )

    prompt = f"""You are an expert senior recruiter with 15 years of experience.

Carefully analyze the resume below against the job requirements.
Calculate a score out of 100 using EXACTLY the weights provided.

JOB ROLE: {job_role}

REQUIREMENTS:
{requirements}

SCORING WEIGHTS (must total 100):
{weights}

IMPORTANT RULES:
1. Calculate each sub-score first, then add them for the final score.
2. For any criterion with 0 pts weight, always set its score to 0.
3. The final "score" must equal the sum of all four sub-scores.
4. skills_score + experience_score + education_score + certification_score = score

RESUME:
{resume_text[:3500]}

Return ONLY this JSON object, no markdown fences, no explanation:
{json_template}
"""

    client = st.session_state.get('groq_client') or Groq(api_key=st.session_state.get('api_key',''))
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content.strip()
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(20 + attempt * 10)
            else:
                raise e
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    try:
        data = json.loads(raw)
        # Server-side validation: enforce score = sum of breakdown
        sb = data.get("score_breakdown", {})
        computed = (sb.get("skills_score", 0) + sb.get("experience_score", 0) +
                    sb.get("education_score", 0) + sb.get("certification_score", 0))
        if abs(computed - data.get("score", 0)) > 2:
            data["score"] = computed  # correct drift
        return data
    except Exception:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                sb = data.get("score_breakdown", {})
                computed = (sb.get("skills_score", 0) + sb.get("experience_score", 0) +
                            sb.get("education_score", 0) + sb.get("certification_score", 0))
                data["score"] = computed
                return data
            except Exception:
                pass
        return {
            "score": 0, "candidate_name": "Parse Error",
            "matched_skills": [], "missing_skills": [],
            "experience_years": "N/A",
            "score_breakdown": {"skills_score": 0, "experience_score": 0,
                                "education_score": 0, "certification_score": 0},
            "education": {"highest_degree": "N/A", "institution": "N/A", "graduation_year": "N/A"},
            "certifications": [], "strengths": "Parse error.", "weaknesses": "Parse error.",
            "education_match": "N/A", "certification_match": "N/A"
        }

def generate_interview_questions(resume_text, job_role, skills, candidate_name, min_experience="", education_pref="", certifications=""):
    ctx = ""
    if min_experience: ctx += f"\nExpected Experience: {min_experience}+ years"
    if education_pref: ctx += f"\nEducation Background: {education_pref}"
    if certifications:  ctx += f"\nCertifications to probe: {certifications}"

    prompt = f"""
You are an expert technical interviewer.
Generate exactly 10 interview questions for this candidate.
Mix technical, behavioral, and situational questions.
Include questions about education and certifications if provided.

Candidate: {candidate_name}
Job Role: {job_role}
Required Skills: {skills}
{ctx}

Resume:
{resume_text[:2500]}

Return ONLY a JSON array of 10 strings. No markdown, no numbering.
["Question 1", ..., "Question 10"]
"""
    client = st.session_state.get("groq_client") or Groq(api_key=st.session_state.get("api_key",""))
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            raw = response.choices[0].message.content.strip()
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(20 + attempt * 10)
            else:
                raise e
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        q = json.loads(raw)
        return q if isinstance(q, list) else []
    except:
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
        return [l.strip().lstrip("0123456789.-) ") for l in raw.split("\n") if l.strip()][:10]

def score_badge(score):
    if score >= 70: return f'<span class="score-high">⭐ {score}/100</span>'
    elif score >= 40: return f'<span class="score-mid">🔶 {score}/100</span>'
    else: return f'<span class="score-low">🔴 {score}/100</span>'

def match_badge(label, text):
    if "Good" in text: st_color = "background:#dcfce7;color:#166534"
    elif "Partial" in text: st_color = "background:#ffedd5;color:#9a3412"
    elif "None" in text or "N/A" in text: st_color = "background:#fee2e2;color:#991b1b"
    else: st_color = "background:#f1f5f9;color:#64748b"
    return f'<span style="{st_color};border-radius:8px;padding:3px 10px;font-size:0.82rem;font-weight:600;margin-right:6px">{label}: {text}</span>'

def safe(text):
    return str(text).encode("latin-1", "replace").decode("latin-1")

def wrap(text, max_chars=90):
    """Truncate long text to avoid FPDF horizontal overflow."""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."

def pdf_line(pdf, label, value, max_chars=85):
    """Safe single line — truncates if too long."""
    text = safe(f"{label}{value}")
    if len(text) > max_chars:
        text = text[:max_chars - 3] + "..."
    pdf.cell(0, 7, text, ln=True)

def pdf_multi(pdf, label, value):
    """Safe multi-line cell for long text."""
    text = safe(f"{label}{value}")
    pdf.multi_cell(0, 6, text)
    pdf.ln(1)

def generate_pdf_report(results, job_role, skills, shortlist_count, min_experience="", education_pref="", certifications=""):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Title ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "ResuMate - Recruitment Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, safe(f"Job Role: {job_role}  |  Skills: {wrap(skills, 80)}"), align="C")
    if min_experience: pdf.cell(0, 5, safe(f"Min Experience: {min_experience} yrs"), ln=True, align="C")
    if education_pref: pdf.cell(0, 5, safe(f"Education: {wrap(education_pref, 80)}"), ln=True, align="C")
    if certifications:  pdf.cell(0, 5, safe(f"Certifications: {wrap(certifications, 80)}"), ln=True, align="C")
    pdf.cell(0, 6, f"Total Analysed: {len(results)}  |  Shortlisted: {shortlist_count}", ln=True, align="C")
    pdf.ln(3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    for i, r in enumerate(results):
        d = r["score_data"]
        edu = d.get("education", {})
        certs = d.get("certifications", [])
        shortlisted = i < shortlist_count

        # ── Candidate Header ──
        pdf.set_font("Helvetica", "B", 12)
        label = "[SHORTLISTED] " if shortlisted else ""
        name = wrap(d.get("candidate_name", "Unknown"), 40)
        score = d.get("score", 0)
        pdf.cell(0, 9, safe(f"{label}#{i+1}  {name}  |  Score: {score}/100"), ln=True)

        # ── Score Breakdown ──
        sb = d.get("score_breakdown", {})
        pdf.set_font("Helvetica", "", 8)
        breakdown = (f"Skills: {sb.get('skills_score',0)}  |  "
                     f"Experience: {sb.get('experience_score',0)}  |  "
                     f"Education: {sb.get('education_score',0)}  |  "
                     f"Certifications: {sb.get('certification_score',0)}")
        pdf.cell(0, 5, safe(breakdown), ln=True)
        pdf.ln(1)

        # ── Details ──
        pdf.set_font("Helvetica", "", 9)
        pdf_line(pdf, "Experience:       ", d.get("experience_years", "N/A"))

        degree   = wrap(edu.get("highest_degree", "Not mentioned"), 50)
        institut = wrap(edu.get("institution", "Not mentioned"), 40)
        grad     = edu.get("graduation_year", "")
        edu_str  = degree
        if institut and institut != "Not mentioned": edu_str += f", {institut}"
        if grad and grad != "Not mentioned": edu_str += f" ({grad})"
        pdf_line(pdf, "Education:        ", edu_str)
        pdf_line(pdf, "Education Match:  ", d.get("education_match", "N/A"))

        cert_str = wrap(", ".join(certs) if certs else "None found", 80)
        pdf_line(pdf, "Certifications:   ", cert_str)
        pdf_line(pdf, "Cert Match:       ", d.get("certification_match", "N/A"))

        matched  = wrap(", ".join(d.get("matched_skills", [])), 80)
        missing  = wrap(", ".join(d.get("missing_skills", [])), 80)
        pdf_line(pdf, "Matched Skills:   ", matched or "None")
        pdf_line(pdf, "Missing Skills:   ", missing or "None")

        pdf.ln(1)
        pdf_multi(pdf, "Strengths: ", d.get("strengths", ""))
        pdf_multi(pdf, "Gaps:      ", d.get("weaknesses", ""))

        # ── Interview Questions ──
        if shortlisted and r.get("questions"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 7, "Interview Questions:", ln=True)
            pdf.set_font("Helvetica", "", 8)
            for j, q in enumerate(r["questions"], 1):
                q_safe = safe(f"  Q{j}. {wrap(q, 100)}")
                pdf.multi_cell(0, 5, q_safe)
                pdf.ln(1)

        pdf.ln(2)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    return bytes(pdf.output())

# ── FORM ─────────────────────────────────────────────────────

st.markdown('<div class="section-title">📋 Job Requirements <span style="font-size:0.85rem;color:#94a3b8;font-weight:400">(required)</span></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2,2,1])
with col1:
    job_role = st.text_input("🎯 Job Role", placeholder="e.g. Full Stack Developer, Data Scientist")
with col2:
    skills = st.text_input("🛠️ Required Skills", placeholder="e.g. Python, React, SQL, Docker")
with col3:
    shortlist_count = st.number_input("👥 Shortlist Top N", min_value=1, max_value=100, value=3)

st.markdown('<div class="section-title">🔧 Additional Preferences <span class="optional-label">— optional, leave blank if not needed</span></div>', unsafe_allow_html=True)

opt1, opt2, opt3 = st.columns(3)
with opt1:
    st.markdown("##### 🎓 Education Preference")
    education_pref = st.text_input("Education", placeholder="e.g. B.Tech, Computer Science, MBA", label_visibility="collapsed")
    st.caption("Leave blank to accept any education background")
with opt2:
    st.markdown("##### 💼 Minimum Experience (years)")
    min_experience = st.text_input("Experience", placeholder="e.g. 2  (means 2+ years preferred)", label_visibility="collapsed")
    st.caption("Leave blank to consider freshers too")
with opt3:
    st.markdown("##### 🏅 Preferred Certifications")
    certifications = st.text_input("Certifications", placeholder="e.g. AWS Certified, PMP, GCP", label_visibility="collapsed")
    st.caption("Leave blank if certifications are not required")

active = []
if education_pref: active.append(f"🎓 {education_pref}")
if min_experience:  active.append(f"💼 {min_experience}+ yrs")
if certifications:  active.append(f"🏅 {certifications}")
if active:
    st.success("**Active Filters:** " + "  |  ".join(active))

st.markdown('<div class="section-title">📂 Upload Resumes</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload PDF resumes (select multiple)", type=["pdf"], accept_multiple_files=True)
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
        st.warning(f"⚠️ Adjusted shortlist to {len(uploaded_files)}.")
        shortlist_count = len(uploaded_files)

    groq_client = Groq(api_key=api_key)
    st.session_state['groq_client'] = groq_client
    st.session_state['api_key'] = api_key
    results = []

    st.markdown('<div class="section-title">⏳ Analysing Resumes...</div>', unsafe_allow_html=True)
    progress = st.progress(0)
    status_text = st.empty()

    for idx, file in enumerate(uploaded_files):
        status_text.markdown(f"🔍 Analysing **{file.name}** ({idx+1}/{len(uploaded_files)})...")
        try:
            resume_text = extract_text_from_pdf(file)
            if not resume_text:
                st.warning(f"⚠️ No text in {file.name}. Skipping."); continue
            score_data = score_resume(resume_text, job_role, skills, min_experience, education_pref, certifications)
            results.append({"filename": file.name, "resume_text": resume_text, "score_data": score_data, "questions": []})
        except Exception as e:
            st.error(f"Error on {file.name}: {e}")
        progress.progress((idx+1)/len(uploaded_files))

    if not results:
        st.error("No resumes processed. Check your files."); st.stop()

    results.sort(key=lambda x: x["score_data"].get("score",0), reverse=True)
    shortlist_count = min(shortlist_count, len(results))

    status_text.markdown("🧠 Generating interview questions for shortlisted candidates...")
    for i in range(shortlist_count):
        r = results[i]
        try:
            results[i]["questions"] = generate_interview_questions(
                r["resume_text"], job_role, skills,
                r["score_data"].get("candidate_name","Candidate"),
                min_experience, education_pref, certifications
            )
        except Exception as e:
            results[i]["questions"] = [f"Could not generate: {e}"]

    progress.progress(1.0)
    status_text.markdown("✅ Analysis complete!")

    # ── METRICS ──
    st.markdown('<div class="section-title">📊 Results — Ranked Candidates</div>', unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total Analysed", len(results))
    m2.metric("Shortlisted", shortlist_count)
    m3.metric("Average Score", f"{sum(r['score_data'].get('score',0) for r in results)//len(results)}/100")
    m4.metric("Top Score", f"{results[0]['score_data'].get('score',0)}/100")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABLE ──
    table_data = []
    for i,r in enumerate(results):
        d = r["score_data"]; edu = d.get("education",{}); certs = d.get("certifications",[])
        table_data.append({
            "Rank": f"#{i+1}",
            "Status": "✅ Shortlisted" if i < shortlist_count else "❌ Not Shortlisted",
            "Candidate": d.get("candidate_name","Unknown"),
            "Score": d.get("score",0),
            "Experience": d.get("experience_years","N/A"),
            "Education": edu.get("highest_degree","N/A"),
            "Institution": edu.get("institution","N/A"),
            "Grad Year": edu.get("graduation_year","N/A"),
            "Certifications": ", ".join(certs) if certs else "None",
            "Edu Match": d.get("education_match","N/A"),
            "Cert Match": d.get("certification_match","N/A"),
            "Matched Skills": ", ".join(d.get("matched_skills",[])),
            "Missing Skills": ", ".join(d.get("missing_skills",[])),
            "File": r["filename"]
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── DETAIL CARDS ──
    st.markdown('<div class="section-title">🔍 Detailed Candidate Analysis</div>', unsafe_allow_html=True)
    for i,r in enumerate(results):
        d = r["score_data"]; edu = d.get("education",{}); certs = d.get("certifications",[])
        shortlisted = i < shortlist_count
        badge = '<span class="shortlisted-badge">✅ SHORTLISTED</span>' if shortlisted else ""
        cert_html = "".join([f'<span class="cert-item">🏅 {c}</span>' for c in certs]) if certs else '<span style="color:#94a3b8;font-size:0.9rem">None found</span>'
        degree = edu.get("highest_degree","Not mentioned")
        institution = edu.get("institution","")
        grad_year = edu.get("graduation_year","")
        edu_str = degree
        if institution and institution != "Not mentioned": edu_str += f" — {institution}"
        if grad_year and grad_year != "Not mentioned": edu_str += f" ({grad_year})"

        with st.expander(f"#{i+1}  {d.get('candidate_name','Unknown')}  —  Score: {d.get('score',0)}/100"):
            sb = d.get("score_breakdown", {})
            sk = sb.get("skills_score", 0)
            ex = sb.get("experience_score", 0)
            ed = sb.get("education_score", 0)
            ce = sb.get("certification_score", 0)
            num_opt = sum([bool(min_experience), bool(education_pref), bool(certifications)])
            if num_opt == 0:   wsk,wex,wed,wce = 100,0,0,0
            elif num_opt == 1: wsk=60; wex=40 if min_experience else 0; wed=40 if education_pref else 0; wce=40 if certifications else 0
            elif num_opt == 2: wsk=40; wex=30 if min_experience else 0; wed=30 if education_pref else 0; wce=30 if certifications else 0
            else: wsk,wex,wed,wce = 40,20,20,20
            def bar(value, max_val, color):
                if max_val == 0: return '<span style="color:#94a3b8;font-size:0.8rem">Not weighted</span>'
                pct = int((value / max_val) * 100) if max_val else 0
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
    <b>✅ Matched Skills:</b> {', '.join(d.get('matched_skills',[])) or 'None'}<br><br>
    <b>❌ Missing Skills:</b> {', '.join(d.get('missing_skills',[])) or 'None'}<br><br>
    <b>💪 Strengths:</b> {d.get('strengths','')}<br><br>
    <b>⚠️ Gaps:</b> {d.get('weaknesses','')}
</div>
""", unsafe_allow_html=True)

            if shortlisted and r.get("questions"):
                st.markdown("#### 🎤 Interview Questions")
                for j,q in enumerate(r["questions"],1):
                    st.markdown(f'<div class="question-item"><b>Q{j}.</b> {q}</div>', unsafe_allow_html=True)

    # ── DOWNLOADS ──
    st.markdown('<div class="section-title">⬇️ Download Report</div>', unsafe_allow_html=True)
    dl1,dl2 = st.columns(2)
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
