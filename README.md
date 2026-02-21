# 🎯 ResuMate — AI Recruitment Assistant

> Upload bulk resumes → Define job requirements → Get ranked shortlist + tailored interview questions instantly.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 What It Does

ResuMate is a recruiter-facing AI tool that:

1. Takes job role + required skills + number of candidates to shortlist
2. Optionally filters by education, experience, and certifications
3. Accepts multiple resume PDFs uploaded at once
4. Scores and ranks every resume using dynamic weighted criteria
5. Shortlists the top N candidates (up to 100) automatically
6. Generates 10 tailored interview questions per shortlisted candidate
7. Exports the full report as Excel or PDF

---

## 🖥️ Live Demo

[🚀 Try it on Streamlit Cloud →](#) *(add your link after deployment)*

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend & Backend | Streamlit (Python) |
| AI Engine | Groq API — Llama 3.3 70B |
| PDF Parsing | pdfplumber |
| Report Export | fpdf2 + openpyxl |
| Deployment | Streamlit Cloud (Free) |

---

## 📁 Project Structure

```
ResuMate/
│
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── config.toml     # Streamlit theme config
└── README.md
```

---

## ⚡ Local Setup (Step by Step)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Yuva-Teja-ctrl/ResuMate.git
cd ResuMate
```

### Step 2 — Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Get Free Groq API Key

1. Go to https://console.groq.com/keys
2. Sign up for free (no credit card needed)
3. Click "Create API Key"
4. Copy the key

### Step 5 — Run the App

```bash
streamlit run app.py
```

App opens at `http://localhost:8501` 🎉

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push your code to a **public GitHub repository**
2. Go to https://share.streamlit.io
3. Click **"New App"**
4. Select your repo → Branch: `main` → File: `app.py`
5. Click **Deploy** — live in 2 minutes!

> **Note:** Users enter their own Groq API key in the sidebar — no secrets need to be stored.

---

## 🎮 How to Use

1. Open the app
2. Enter your **Groq API Key** in the sidebar
3. Fill in the required fields:
   - **Job Role** (e.g. "Full Stack Developer")
   - **Required Skills** (e.g. "React, Node.js, PostgreSQL")
   - **Shortlist Top N** (e.g. 5)
4. Optionally fill in preferences:
   - **Education** (e.g. "B.Tech Computer Science")
   - **Min Experience** (e.g. "2")
   - **Certifications** (e.g. "AWS Certified")
5. Upload PDF resumes (select multiple at once)
6. Click **"Analyse & Shortlist"**
7. View ranked results → expand each candidate for full details
8. Download the full report as **Excel or PDF**

---

## 📊 Smart Scoring System

Scores are dynamically weighted based on what the recruiter specifies:

| Filters Specified | Skills | Experience | Education | Certifications |
|---|---|---|---|---|
| None | 100 pts | — | — | — |
| Any 1 optional | 60 pts | 40 pts | 40 pts | 40 pts |
| Any 2 optional | 40 pts | 30 pts | 30 pts | 30 pts |
| All 3 optional | 40 pts | 20 pts | 20 pts | 20 pts |

---

## 📊 Output Example

| Rank | Status | Candidate | Score | Experience | Education |
|------|--------|-----------|-------|------------|-----------|
| #1 | ✅ Shortlisted | John Smith | 87/100 | 3 years | B.Tech CSE |
| #2 | ✅ Shortlisted | Priya Nair | 81/100 | 2 years | B.Tech IT |
| #3 | ✅ Shortlisted | Alex Lee | 74/100 | Fresher | B.Sc CS |
| #4 | ❌ Not Shortlisted | Raj Kumar | 45/100 | 1 year | Diploma |

---

## 🔒 Privacy

- Resumes are processed **in memory only** — nothing stored on any server
- API calls go directly to Groq's servers
- No database, no user accounts, no data retention

---

## 🤝 Contributing

Pull requests welcome! Ideas for future improvements:
- [ ] Support DOCX resumes
- [ ] Email integration to notify shortlisted candidates
- [ ] LinkedIn profile URL extraction
- [ ] Multi-language resume support
- [ ] ATS simulation mode

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 👨‍💻 Built By

**Yuva Teja** — Built as part of an internship portfolio project.

> *"Most resume screeners target job seekers. ResuMate targets recruiters — making hiring 10x faster."*
