"""
Platform detector.
"""


class AutomationPlatformDetector:
    def detect(self, application_url: str) -> str:
        url = application_url.lower()

        if "greenhouse.io" in url or "job-boards.greenhouse.io" in url:
            return "greenhouse"
        if "lever.co" in url or "jobs.lever.co" in url:
            return "lever"
        if "ashbyhq.com" in url or "ashby" in url:
            return "ashby"
        if "myworkdayjobs.com" in url or "workday" in url:
            return "workday"

        return "generic"