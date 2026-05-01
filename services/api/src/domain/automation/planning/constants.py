"""
from __future__ import annotations
"""

FIELD_ROLE_IGNORE = "ignore"

FIELD_ROLE_SUBMIT = "submit_action"

FIELD_ROLE_FIRST_NAME = "first_name"

FIELD_ROLE_LAST_NAME = "last_name"

FIELD_ROLE_FULL_NAME = "full_name"

FIELD_ROLE_EMAIL = "email"

FIELD_ROLE_PHONE = "phone"

FIELD_ROLE_LINKEDIN_URL = "linkedin_url"
FIELD_ROLE_LINKEDIN = "linkedin_url"

FIELD_ROLE_GITHUB_URL = "github_url"
FIELD_ROLE_GITHUB = "github_url"

FIELD_ROLE_PORTFOLIO_URL = "portfolio_url"
FIELD_ROLE_PORTFOLIO = "portfolio_url"

FIELD_ROLE_LOCATION = "location"

FIELD_ROLE_COUNTRY = "country"

FIELD_ROLE_STATE_OF_RESIDENCE = "state_of_residence"

FIELD_ROLE_ZIP_CODE = "zip_code"

FIELD_ROLE_RESUME_UPLOAD = "resume_upload"

FIELD_ROLE_COVER_LETTER_UPLOAD = "cover_letter_upload"

FIELD_ROLE_WORK_AUTHORIZATION = "work_authorization"

FIELD_ROLE_RELOCATION = "relocation"

FIELD_ROLE_WORK_ARRANGEMENT = "work_arrangement"

FIELD_ROLE_COMPLIANCE = "compliance_question"

FIELD_ROLE_CONSENT = "consent_question"

FIELD_ROLE_DEMOGRAPHIC = "demographic_question"

FIELD_ROLE_OPEN_ENDED = "open_ended_question"

FIELD_ROLE_REFERRAL_SOURCE = "referral_source"

FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE = "preferred_programming_language"

FIELD_ROLE_JOB_SEARCH_STATUS = "job_search_status"

FIELD_ROLE_AREA_OF_EXPERTISE = "area_of_expertise"

FIELD_ROLE_SALARY_EXPECTATION = "salary_expectation"

FIELD_ROLE_CURRENT_COMPANY = "current_company"

FIELD_ROLE_UNKNOWN = "unknown"

PLATFORM_LEVER = "lever"
PLATFORM_GREENHOUSE = "greenhouse"
PLATFORM_ASHBY = "ashby"

IGNORE_BUTTON_LABELS = {
    "dropbox",
    "google drive",
    "create alert",
    "autofill with mygreenhouse",
    "locate me",
    "enter manually",
    "upload file",
    "upload",
    "yes",
    "no",
}

SUBMIT_BUTTON_LABELS = {
    "submit",
    "submit application",
    "apply",
}

DEMOGRAPHIC_KEYWORDS = {
    "gender",
    "ethnicity",
    "sexual orientation",
    "transgender",
    "disability",
    "nationality",
    "race",
    "veteran",
    "self-identify",
    "diversity and inclusion",
    "underrepresented demographic",
    "preferred pronouns",
}

COMPLIANCE_KEYWORDS = {
    "non-compete",
    "non solicitation",
    "non-solicitation",
    "confidentiality agreements",
    "acknowledge",
    "confirm",
    "point of data transfer",
    "privacy",
}

CONSENT_KEYWORDS = {
    "i consent",
    "i do not consent",
    "interview recording",
    "consent",
}

WORK_AUTH_KEYWORDS = {
    "authorized to work",
    "work authorization",
    "employment permit",
    "immigration permission",
    "sponsorship",
    "visa",
}