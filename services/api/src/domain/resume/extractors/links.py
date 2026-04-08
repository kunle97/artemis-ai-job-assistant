"""
Resume link extractor.

Extracts visible URLs from resume text and classifies likely profile links
such as LinkedIn, GitHub, and portfolio URLs. Also supports PDF hyperlink
annotation extraction when a file path is provided.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from src.domain.resume.constants import URL_PATTERN


class ResumeLinkExtractor:
    """
    Extract and classify resume URLs.
    """

    def extract(self, text: str, file_path: str | None = None) -> dict:
        """
        Extract and classify URLs from resume text and, when possible,
        from PDF hyperlink annotations.
        """
        visible_urls = self._extract_visible_urls(text)
        file_urls = self._extract_file_urls(file_path)

        urls = self._merge_urls(visible_urls, file_urls)
        web_urls = [url for url in urls if self._is_web_url(url)]

        linkedin_url = self._find_url_containing(web_urls, "linkedin.com")
        github_url = self._find_url_containing(web_urls, "github.com")
        portfolio_url = self._find_portfolio_url(web_urls, linkedin_url, github_url)

        return {
            "urls": urls,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
        }

    def _extract_visible_urls(self, text: str) -> list[str]:
        urls = URL_PATTERN.findall(text)
        return self._dedupe_and_clean(urls)

    def _extract_file_urls(self, file_path: str | None) -> list[str]:
        if not file_path:
            return []

        path = Path(file_path)
        if path.suffix.lower() != ".pdf":
            return []

        try:
            reader = PdfReader(str(path))
            urls: list[str] = []

            for page in reader.pages:
                annotations = page.get("/Annots")
                if not annotations:
                    continue

                for annotation in annotations:
                    annotation_obj = annotation.get_object()
                    action = annotation_obj.get("/A")
                    if not action:
                        continue

                    uri = action.get("/URI")
                    if uri:
                        urls.append(str(uri))

            return self._dedupe_and_clean(urls)
        except Exception:
            return []

    def _merge_urls(self, visible_urls: list[str], file_urls: list[str]) -> list[str]:
        return self._dedupe_and_clean(visible_urls + file_urls)

    def _dedupe_and_clean(self, urls: list[str]) -> list[str]:
        seen: list[str] = []

        for url in urls:
            cleaned = url.rstrip(".,);]")
            if cleaned and cleaned not in seen:
                seen.append(cleaned)

        return seen

    def _is_web_url(self, url: str) -> bool:
        lowered = url.lower()
        return (
            lowered.startswith("http://")
            or lowered.startswith("https://")
            or lowered.startswith("www.")
        )

    def _find_url_containing(self, urls: list[str], match_text: str) -> str | None:
        for url in urls:
            if match_text in url.lower():
                return url
        return None

    def _find_portfolio_url(
        self,
        urls: list[str],
        linkedin_url: str | None,
        github_url: str | None,
    ) -> str | None:
        for url in urls:
            if url == linkedin_url or url == github_url:
                continue
            return url

        return None