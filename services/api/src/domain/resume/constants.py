"""
Resume domain constants.

Contains reusable parsing patterns, keyword sets, and configuration values
used by the resume parser and normalizer.
"""

import re


EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,2}[\s\-.]?)?(?:\(?\d{3}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}"
)
URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")

TITLE_KEYWORDS = {
    "engineer",
    "developer",
    "architect",
    "manager",
    "analyst",
    "consultant",
    "designer",
    "lead",
    "specialist",
    "administrator",
    "programmer",
    "scientist",
}

EXPERIENCE_SECTION_HEADERS = {
    "experience",
    "work experience",
    "professional experience",
    "employment history",
}

EDUCATION_SECTION_HEADERS = {
    "education",
    "academic background",
    "academic history",
}

SKILLS_SECTION_HEADERS = {
    "skills",
    "technical skills",
    "core competencies",
    "technologies",
}

EXTRA_SECTION_HEADERS = {
    "projects",
    "certifications",
    "summary",
    "profile",
}

COMMON_SKILLS = {
    "python",
    "django",
    "fastapi",
    "flask",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "nextjs",
    "node.js",
    "nodejs",
    "express",
    "postgresql",
    "mysql",
    "sqlite",
    "docker",
    "kubernetes",
    "aws",
    "redis",
    "graphql",
    "java",
    "spring boot",
    "tailwind",
    "html",
    "css",
    "cypress",
    "playwright",
    "git",
    "swift",
    "bootstrap",
    "electron",
}

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(?P<start_year>\d{4})\s*[–\-]\s*"
    r"(?:(?P<end_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?"
    r"(?P<end_year>\d{4}|Current|Present)"
)

YEAR_RANGE_PATTERN = re.compile(
    r"(?P<start_year>\d{4})\s*[–\-]\s*(?P<end_year>\d{4}|Current|Present)"
)