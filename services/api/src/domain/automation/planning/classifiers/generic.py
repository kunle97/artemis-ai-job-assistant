"""
Generic automation field classifier.
"""

from __future__ import annotations

from src.domain.automation.planning.constants import (
    FIELD_ROLE_AREA_OF_EXPERTISE,
    FIELD_ROLE_COMPLIANCE,
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_CURRENT_COMPANY,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_FIRST_NAME,
    FIELD_ROLE_FULL_NAME,
    FIELD_ROLE_GITHUB_URL,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_JOB_SEARCH_STATUS,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_PORTFOLIO_URL,
    FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RELOCATION,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_STATE_OF_RESIDENCE,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_WORK_ARRANGEMENT,
    FIELD_ROLE_WORK_AUTHORIZATION,
    FIELD_ROLE_ZIP_CODE,
)


class GenericAutomationFieldClassifier:
    def classify(
        self,
        field_type: str | None,
        label: str | None,
        name: str | None,
        placeholder: str | None,
    ) -> str:
        normalized_label = self._normalize(label)
        normalized_name = self._normalize(name)
        normalized_placeholder = self._normalize(placeholder)
        haystack = " ".join(
            value
            for value in [normalized_label, normalized_name, normalized_placeholder]
            if value
        )

        if not haystack:
            if field_type == "button":
                return FIELD_ROLE_IGNORE
            return "unknown"

        if self._is_submit(haystack):
            return FIELD_ROLE_SUBMIT

        if self._is_ignore_button(field_type, haystack):
            return FIELD_ROLE_IGNORE

        if self._is_resume_upload(field_type, haystack):
            return FIELD_ROLE_RESUME_UPLOAD

        if self._is_cover_letter_upload(field_type, haystack):
            return FIELD_ROLE_COVER_LETTER_UPLOAD

        if self._is_first_name(haystack):
            return FIELD_ROLE_FIRST_NAME

        if self._is_last_name(haystack):
            return FIELD_ROLE_LAST_NAME

        if self._is_full_name(haystack):
            return FIELD_ROLE_FULL_NAME

        if self._is_email(haystack):
            return FIELD_ROLE_EMAIL

        if self._is_phone(haystack):
            return FIELD_ROLE_PHONE

        if self._is_linkedin(haystack):
            return FIELD_ROLE_LINKEDIN_URL

        if self._is_github(haystack):
            return FIELD_ROLE_GITHUB_URL

        if self._is_portfolio(haystack):
            return FIELD_ROLE_PORTFOLIO_URL

        if self._is_zip_code(haystack):
            return FIELD_ROLE_ZIP_CODE

        if self._is_state_of_residence(haystack):
            return FIELD_ROLE_STATE_OF_RESIDENCE

        if self._is_country(haystack):
            return FIELD_ROLE_COUNTRY

        if self._is_relocation(haystack):
            return FIELD_ROLE_RELOCATION

        if self._is_location(haystack):
            return FIELD_ROLE_LOCATION

        if self._is_current_company(haystack):
            return FIELD_ROLE_CURRENT_COMPANY

        if self._is_preferred_programming_language(haystack):
            return FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE

        if self._is_referral_source(haystack):
            return FIELD_ROLE_REFERRAL_SOURCE

        if self._is_job_search_status(haystack):
            return FIELD_ROLE_JOB_SEARCH_STATUS

        if self._is_area_of_expertise(haystack):
            return FIELD_ROLE_AREA_OF_EXPERTISE

        if self._is_salary(haystack):
            return FIELD_ROLE_SALARY_EXPECTATION

        if self._is_work_authorization(haystack):
            return FIELD_ROLE_WORK_AUTHORIZATION

        if self._is_work_arrangement(haystack):
            return FIELD_ROLE_WORK_ARRANGEMENT

        if self._is_compliance(haystack):
            return FIELD_ROLE_COMPLIANCE

        if self._is_consent(haystack):
            return FIELD_ROLE_CONSENT

        if self._is_demographic(haystack):
            return FIELD_ROLE_DEMOGRAPHIC

        if self._is_open_ended(field_type, haystack):
            return FIELD_ROLE_OPEN_ENDED

        return "unknown"

    def _normalize(self, value: str | None) -> str:
        if not value:
            return ""
        return " ".join(value.lower().strip().split())

    def _is_submit(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "submit application",
                "submit",
                "apply now",
                "send application",
                "apply",
            ]
        )

    def _is_ignore_button(self, field_type: str | None, haystack: str) -> bool:
        if field_type != "button":
            return False

        return any(
            token in haystack
            for token in [
                "autofill with mygreenhouse",
                "toggle flyout",
                "locate me",
                "dropbox",
                "google drive",
                "enter manually",
                "upload file",
                "choose file",
                "job details",
                "application",
                "facebook",
                "linkedin",
                "x",
            ]
        )

    def _is_resume_upload(self, field_type: str | None, haystack: str) -> bool:
        if field_type != "file":
            return False
        return any(token in haystack for token in ["resume", "cv", "upload your resume", "resume/cv"])

    def _is_cover_letter_upload(self, field_type: str | None, haystack: str) -> bool:
        if field_type != "file":
            return False
        return "cover letter" in haystack

    def _is_first_name(self, haystack: str) -> bool:
        return "first name" in haystack

    def _is_last_name(self, haystack: str) -> bool:
        return "last name" in haystack

    def _is_full_name(self, haystack: str) -> bool:
        if "first name" in haystack or "last name" in haystack:
            return False
        return "full name" in haystack or haystack == "name"

    def _is_email(self, haystack: str) -> bool:
        return "email" in haystack

    def _is_phone(self, haystack: str) -> bool:
        if any(
            token in haystack
            for token in [
                "receive communications via sms",
                "receive communications via text",
                "text messages",
                "sms from",
                "sms consent",
            ]
        ):
            return False
        return "phone" in haystack or "mobile" in haystack

    def _is_linkedin(self, haystack: str) -> bool:
        return "linkedin" in haystack

    def _is_github(self, haystack: str) -> bool:
        return "github" in haystack

    def _is_portfolio(self, haystack: str) -> bool:
        return any(token in haystack for token in ["portfolio", "personal website", "homepage url"])

    def _is_zip_code(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "zip code",
                "zip/postal code",
                "postal code",
                "postcode",
            ]
        )

    def _is_state_of_residence(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "state where you will reside",
                "state where you will work",
                "select the state where you will reside",
                "state of residence",
                "permanent residency state",
                "state where you reside",
            ]
        )

    def _is_country(self, haystack: str) -> bool:
        if self._is_state_of_residence(haystack):
            return False
        return "country" in haystack and "city, country" not in haystack

    def _is_location(self, haystack: str) -> bool:
        if self._is_state_of_residence(haystack):
            return False
        if self._is_zip_code(haystack):
            return False
        if self._is_relocation(haystack):
            return False
        return any(
            token in haystack
            for token in [
                "location",
                "city",
                "city, country",
                "location/timezone",
                "where are you located",
            ]
        )

    def _is_current_company(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "current company",
                "current employer",
                "company name",
                "employer name",
                "organization",
            ]
        )

    def _is_preferred_programming_language(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "preferred programming language",
                "primary programming language",
                "main programming language",
                "preferred language",
                "primary language",
                "primary skill",
                "main skill",
                "primary technology",
                "main technology",
                "tech stack",
            ]
        )

    def _is_salary(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "salary expectation",
                "salary range",
                "expected salary",
                "desired salary",
                "compensation expectation",
                "expected compensation",
                "desired compensation",
                "compensation range",
                "what is your salary",
                "what are your salary",
                "what compensation",
                "pay expectation",
                "pay range",
            ]
        )

    def _is_referral_source(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "how did you hear about this job",
                "how did you hear about us",
                "referral source",
                "how did you hear",
            ]
        )

    def _is_job_search_status(self, haystack: str) -> bool:
        return "job search status" in haystack

    def _is_area_of_expertise(self, haystack: str) -> bool:
        return "area of expertise" in haystack

    def _is_work_authorization(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "authorized to work",
                "lawfully in the united states",
                "require sponsorship",
                "sponsor an immigration case",
                "employment-based visa",
                "visa status",
                "work authorization",
            ]
        )

    def _is_relocation(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "willing to relocate",
                "open to relocation",
                "able to relocate",
                "relocation",
                "relocate for this role",
                "relocate for the role",
                "relocate to",
                "would you relocate",
                "are you willing to relocate",
                "open to relocating",
            ]
        )

    def _is_work_arrangement(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "work arrangement",
                "work preference",
                "work type",
                "working style",
                "remote or onsite",
                "remote or on-site",
                "remote or in-office",
                "in-office or remote",
                "in office or remote",
                "onsite or remote",
                "on-site or remote",
                "hybrid or remote",
                "remote hybrid onsite",
                "office preference",
                "work location preference",
                "preferred work location",
                "how do you prefer to work",
                "what is your preferred work style",
            ]
        )

    def _is_compliance(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "ai system",
                "language model",
                "automated agent",
                "prepared or submitted in whole or in part by an ai",
            ]
        )

    def _is_consent(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "receive communications via sms",
                "receive communications via text",
                "next steps in the recruitment process",
                "record and transcribe interviews",
                "if you prefer not to be recorded",
                "sms from",
                "consent to text",
                "text consent",
            ]
        )

    def _is_demographic(self, haystack: str) -> bool:
        return any(
            token in haystack
            for token in [
                "gender",
                "race",
                "veteran status",
                "physical disability",
                "disability",
                "ethnicity",
            ]
        )

    def _is_open_ended(self, field_type: str | None, haystack: str) -> bool:
        if field_type != "textarea":
            return False

        return any(
            token in haystack
            for token in [
                "please include",
                "tell us about",
                "what excites you",
                "what have you used most extensively",
                "project or accomplishment",
                "what's something you've learned recently",
            ]
        )