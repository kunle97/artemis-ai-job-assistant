"""
Application answer matching constants.

Maps canonical question keys to known wording variants.
"""

QUESTION_ALIASES = {
    "next_role_priorities": [
        "what are the three most important factors you’re looking for in your next role",
        "what are the three most important factors you're looking for in your next role",
        "what are the most important factors you are looking for in your next role",
        "what matters most to you in your next role",
        "what are your top priorities in your next job",
    ],
    "highest_impact_project": [
        "briefly describe your highest impact project and what it meant for the business",
        "describe your highest impact project",
        "what is the highest impact project you worked on",
    ],
    "ai_agent_experience": [
        "have you used ai agents such as cursor or claude code to build software",
        "have you used ai agents to build software",
        "have you built systems using large language models",
        "have you used rag to solve a problem",
    ],
    "proudest_accomplishment": [
        "tell us about a project or accomplishment you're most proud of and why",
        "tell us about a project or accomplishment you are most proud of and why",
        "what accomplishment are you most proud of",
    ],
    "recent_learning": [
        "what's something you've learned recently that you're excited about",
        "what is something you have learned recently that excites you",
        "what have you learned recently",
    ],
    "why_company_and_role": [
        "what about the company and this role excites you most",
        "why are you interested in this company and role",
        "what excites you about this role",
    ],
}