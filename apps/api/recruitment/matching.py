"""OSS resume–JD matching: skill overlap + semantic similarity."""

from __future__ import annotations

import re

from recruitment.embeddings import encode_texts

# Curated technical skills / tools (extend as needed)
SKILL_DICTIONARY = {
    'python', 'javascript', 'typescript', 'java', 'react', 'next.js', 'nextjs', 'django',
    'fastapi', 'node', 'nodejs', 'sql', 'postgresql', 'postgres', 'mysql', 'mongodb',
    'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'rest', 'api',
    'graphql', 'html', 'css', 'tailwind', 'vue', 'angular', 'spring', 'c++', 'c#',
    'go', 'golang', 'rust', 'kotlin', 'swift', 'flutter', 'react native', 'selenium',
    'pytest', 'jest', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'linux', 'agile',
    'scrum', 'machine learning', 'ml', 'deep learning', 'nlp', 'data science', 'pandas',
    'numpy', 'tensorflow', 'pytorch', 'excel', 'power bi', 'tableau', 'hr', 'payroll',
    'recruitment', 'communication', 'leadership', 'project management',
}


def _normalize_token(token: str) -> str:
    return token.strip().lower()


def extract_skills(text: str) -> set[str]:
    lower = text.lower()
    found = set()
    for skill in SKILL_DICTIONARY:
        if skill in lower:
            found.add(skill)
    # CamelCase / hyphen tokens from resume
    for token in re.findall(r'[a-zA-Z+#.]{2,}', text):
        t = _normalize_token(token)
        if t in SKILL_DICTIONARY:
            found.add(t)
    return found


def _cosine_similarity_percent(a, b) -> float:
    if a is None or b is None:
        return 0.0
    sim = float((a * b).sum())
    return max(0.0, min(100.0, sim * 100))


def compute_match(job_title: str, job_description: str, resume_text: str) -> dict:
    jd = f"{job_title}\n{job_description}"[:12000]
    resume = (resume_text or '')[:12000]
    if not resume.strip():
        return {
            'score': 0,
            'strengths': [],
            'weaknesses': ['Resume text is empty or could not be parsed.'],
            'skills_met': [],
            'skills_missed': [],
            'recommendation': 'Reject — no parseable resume',
        }

    jd_skills = extract_skills(jd)
    resume_skills = extract_skills(resume)
    if not jd_skills:
        jd_skills = extract_skills(job_description)

    met = sorted(jd_skills & resume_skills)
    missed = sorted(jd_skills - resume_skills)
    skill_overlap = (len(met) / len(jd_skills) * 100) if jd_skills else 50.0

    vectors = encode_texts([jd[:8000], resume[:8000]])
    semantic = _cosine_similarity_percent(vectors[0], vectors[1])

    score = int(round(0.6 * skill_overlap + 0.4 * semantic))
    score = max(0, min(100, score))

    strengths = []
    if met:
        strengths.append(f"Matches {len(met)} required skills: {', '.join(met[:8])}")
    if semantic >= 70:
        strengths.append('Strong overall semantic alignment with job description')
    weaknesses = []
    if missed:
        weaknesses.append(f"Missing skills: {', '.join(missed[:8])}")
    if semantic < 50:
        weaknesses.append('Low semantic similarity to job description')

    if score >= 75:
        recommendation = 'Proceed to Interview'
    elif score >= 50:
        recommendation = 'Keep in Pool'
    else:
        recommendation = 'Reject'

    return {
        'score': score,
        'strengths': strengths or ['Some alignment with role requirements'],
        'weaknesses': weaknesses or ['Review manually for niche requirements'],
        'skills_met': met,
        'skills_missed': missed,
        'recommendation': recommendation,
    }
