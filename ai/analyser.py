import json
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, YOUR_RESUME, OPENAI_MODEL
from config import CANDIDATE_NAME, CANDIDATE_EMAIL, CANDIDATE_PHONE, CANDIDATE_LOCATION
from config import CANDIDATE_LINKEDIN, CANDIDATE_GITHUB
from database import update_analysis, save_docs
from ai.parsing import parse_analysis, failed_analysis

client = OpenAI(api_key=OPENAI_API_KEY)

def analyse_job(title, company, description):
    prompt = f"""You are an expert recruiter. Analyse this job against the candidate resume below.

JOB DETAILS:
Title: {title}
Company: {company}
Description: {description[:2500]}

CANDIDATE RESUME:
{YOUR_RESUME}

Return ONLY valid JSON with no markdown or explanation:
{{
  "fit_score": <integer 0-100>,
  "fit_reason": "<2 clear sentences explaining the match score>",
  "key_requirements": ["<req1>", "<req2>", "<req3>"],
  "matching_skills": ["<skill1>", "<skill2>", "<skill3>"],
  "missing_skills": ["<skill1>", "<skill2>"],
  "recommendation": "<apply|consider|skip>"
}}

Scoring guide:
- 80-100: Strong match, candidate clearly meets most requirements
- 60-79: Good match, some gaps but worth applying
- 40-59: Partial match, missing some key requirements
- 0-39: Poor match, significant skill gaps"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        return parse_analysis(resp.choices[0].message.content)
    except Exception as e:
        print(f"    Analysis error: {e}")
        return failed_analysis(str(e))

def tailor_resume(title, company, description):
    prompt = f"""You are an expert resume writer. Rewrite the resume below to be perfectly tailored for this specific job.

TARGET JOB:
Title: {title}
Company: {company}
Description: {description[:2500]}

ORIGINAL RESUME:
{YOUR_RESUME}

STRICT RULES:
1. Keep ALL facts 100% accurate — never invent or exaggerate experience
2. Reorder bullet points to put the most relevant ones first
3. Use exact keywords from the job description naturally in bullet points
4. Keep the same sections and structure
5. The candidate's name is {CANDIDATE_NAME} — use this exactly
6. Make it ATS-optimised by matching terminology from the job description

Return ONLY the complete tailored resume text. No explanations, no markdown."""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1800
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Resume tailor error: {e}")
        return YOUR_RESUME

def generate_cover_letter(title, company, description):
    today = datetime.now().strftime("%d %B %Y")
    prompt = f"""Write a professional, personalised cover letter for this job application.

TARGET JOB:
Title: {title}
Company: {company}
Description: {description[:2500]}

CANDIDATE DETAILS:
Name: {CANDIDATE_NAME}
Email: {CANDIDATE_EMAIL}
Phone: {CANDIDATE_PHONE}
Location: {CANDIDATE_LOCATION}
Date: {today}

RESUME:
{YOUR_RESUME}

STRICT RULES:
1. Start with the candidate's contact details and today's date ({today})
2. Address to "Hiring Manager" at {company}
3. Opening paragraph: Show genuine interest in {company} specifically — reference something real about the company or role
4. Middle paragraph: Connect 2-3 specific projects/experiences to the job requirements — be specific, not generic
5. Closing paragraph: Clear call to action, express enthusiasm
6. Sign off as {CANDIDATE_NAME}
7. Do NOT start with "I am writing to apply" — be more engaging
8. Sound human and enthusiastic, not robotic
9. Keep to 3-4 paragraphs total
10. Use {today} as the date — do not write [Date]

Return ONLY the complete cover letter. No explanations."""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=700
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Cover letter error: {e}")
        return f"{CANDIDATE_NAME}\n{CANDIDATE_LOCATION}\n{CANDIDATE_EMAIL}\n\nCover letter generation failed. Please try again."

def process_job(job_id, title, company, description, min_score=50):
    print(f"  Analysing: {title} @ {company}")

    analysis = analyse_job(title, company, description)
    score = analysis.get('fit_score', 0)
    reason = analysis.get('fit_reason', '')
    key_reqs = ", ".join(analysis.get('key_requirements', []))
    matching = ", ".join(analysis.get('matching_skills', []))
    missing = ", ".join(analysis.get('missing_skills', []))
    recommendation = analysis.get('recommendation', 'skip')

    update_analysis(job_id, score, reason, key_reqs, matching, missing, recommendation)
    print(f"    Score: {score}/100 — {recommendation}")

    if score >= min_score:
        print(f"    Generating tailored resume + cover letter...")
        resume = tailor_resume(title, company, description)
        cover = generate_cover_letter(title, company, description)
        save_docs(job_id, resume, cover)
        print(f"    Documents saved.")
    else:
        print(f"    Below threshold ({min_score}), skipping document generation")

    return score
