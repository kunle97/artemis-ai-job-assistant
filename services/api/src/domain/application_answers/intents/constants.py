"""
Intent-related constants.

Defines intent keys, detection patterns, and default fallback answers.
"""

INTENT_WHY_THIS_ROLE = "why_this_role"
INTENT_WHY_THIS_COMPANY = "why_this_company"
INTENT_PROUD_PROJECT = "proud_project"
INTENT_RECENT_LEARNING = "recent_learning"
INTENT_REFERRAL_SOURCE = "referral_source"

INTENT_PATTERNS: dict[str, set[str]] = {
    INTENT_WHY_THIS_ROLE: {
        "excites you most",
        "excites you about this role",
        "why are you interested in this role",
        "why are you interested in this opportunity",
        "why this role",
        "why do you want this role",
        "what about this role excites you",
    },
    INTENT_WHY_THIS_COMPANY: {
        "why this company",
        "why do you want to work here",
        "why do you want to work at",
        "what excites you about the company",
        "what about the company excites you",
    },
    INTENT_PROUD_PROJECT: {
        "most proud of",
        "project or accomplishment",
        "accomplishment you are most proud of",
        "project you are most proud of",
        "proudest project",
    },
    INTENT_RECENT_LEARNING: {
        "learned recently",
        "something you learned recently",
        "recently that you're excited about",
        "recently that you are excited about",
    },
    INTENT_REFERRAL_SOURCE: {
        "how did you hear about",
        "where did you hear about",
        "how did you find",
        "referral source",
    },
}

DEFAULT_INTENT_ANSWERS: dict[str, str] = {
    INTENT_WHY_THIS_ROLE: (
        "I’m excited about this role because it aligns closely with the kind of work I enjoy most: "
        "building reliable backend and full-stack systems that have clear product and business impact. "
        "I’m especially motivated by opportunities where I can combine strong engineering execution with "
        "thoughtful problem-solving and ownership."
    ),
    INTENT_WHY_THIS_COMPANY: (
        "I’m drawn to companies where the product has a clear real-world impact and where engineering plays "
        "a meaningful role in product quality, speed, and scale. I’m especially excited by environments where "
        "I can contribute both technically and strategically while helping build systems that matter to users."
    ),
    INTENT_PROUD_PROJECT: (
        "One project I’m especially proud of is KeyFlow, a property management platform I designed and built "
        "end to end myself. I built the React frontend, Django backend, payments and document workflows, and "
        "the supporting automation around leases, rent collection, and tenant operations. It stands out to me "
        "because it reflects both my ability to ship full products independently and my focus on solving real "
        "operational problems."
    ),
    INTENT_RECENT_LEARNING: (
        "Recently I’ve been especially excited about building agent-style workflows that combine structured "
        "application logic with LLM reasoning. I’m interested in how systems can inspect state, decide what "
        "to do next, and safely take action in a way that is reliable enough for real production workflows."
    ),
    INTENT_REFERRAL_SOURCE: "Google Job board",
}