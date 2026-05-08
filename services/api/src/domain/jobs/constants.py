"""
Job domain constants.

Shared constants for job normalization and classification.
"""

SUPPORTED_SOURCES = {"greenhouse", "ashby", "lever"}


_GREENHOUSE_RAW: dict = {
	# Fintech / Payments
	"stripe": {"board_token": "stripe", "display_name": "Stripe"},
	"coinbase": {"board_token": "coinbase", "display_name": "Coinbase"},
	"brex": {"board_token": "brex", "display_name": "Brex"},
	"robinhood": {"board_token": "robinhood", "display_name": "Robinhood"},
	"chime": {"board_token": "chime", "display_name": "Chime"},
	"gusto": {"board_token": "gusto", "display_name": "Gusto"},
	"affirm": {"board_token": "affirm", "display_name": "Affirm"},
	"betterment": {"board_token": "betterment", "display_name": "Betterment"},
	"sofi": {"board_token": "sofi", "display_name": "SoFi"},
	"rippling": {"board_token": "rippling", "display_name": "Rippling"},
	# Cloud / Infra / DevTools
	"datadog": {"board_token": "datadog", "display_name": "Datadog"},
	"cloudflare": {"board_token": "cloudflare", "display_name": "Cloudflare"},
	"elastic": {"board_token": "elastic", "display_name": "Elastic"},
	"fastly": {"board_token": "fastly", "display_name": "Fastly"},
	"checkr": {"board_token": "checkr", "display_name": "Checkr"},
	"pagerduty": {"board_token": "pagerduty", "display_name": "PagerDuty"},
	"mongodb": {"board_token": "mongodb", "display_name": "MongoDB"},
	"airtable": {"board_token": "airtable", "display_name": "Airtable"},
	"flexport": {"board_token": "flexport", "display_name": "Flexport"},
	"lattice": {"board_token": "lattice", "display_name": "Lattice"},
	"cockroachlabs": {"board_token": "cockroachlabs", "display_name": "Cockroach Labs"},
	"docker": {"board_token": "docker", "display_name": "Docker"},
	"github": {"board_token": "github", "display_name": "GitHub"},
	"gitlab": {"board_token": "gitlab", "display_name": "GitLab"},
	"hashicorp": {"board_token": "hashicorp", "display_name": "HashiCorp"},
	"newrelic": {"board_token": "newrelic", "display_name": "New Relic"},
	"snowflake": {"board_token": "snowflake", "display_name": "Snowflake"},
	"supabase": {"board_token": "supabase", "display_name": "Supabase"},
	# Consumer / Marketplace
	"airbnb": {"board_token": "airbnb", "display_name": "Airbnb"},
	"lyft": {"board_token": "lyft", "display_name": "Lyft"},
	"doordash": {"board_token": "doordash", "display_name": "DoorDash"},
	"instacart": {"board_token": "instacart", "display_name": "Instacart"},
	"reddit": {"board_token": "reddit", "display_name": "Reddit"},
	"discord": {"board_token": "discord", "display_name": "Discord"},
	"squarespace": {"board_token": "squarespace", "display_name": "Squarespace"},
	"uber": {"board_token": "uber", "display_name": "Uber"},
	"etsy": {"board_token": "etsy", "display_name": "Etsy"},
	"carvana": {"board_token": "carvana", "display_name": "Carvana"},
	"faire": {"board_token": "faire", "display_name": "Faire"},
	"olo": {"board_token": "olo", "display_name": "Olo"},
	"vimeo": {"board_token": "vimeo", "display_name": "Vimeo"},
	"compass": {"board_token": "compass", "display_name": "Compass"},
	# SaaS / Productivity
	"figma": {"board_token": "figma", "display_name": "Figma"},
	"asana": {"board_token": "asana", "display_name": "Asana"},
	"dropbox": {"board_token": "dropbox", "display_name": "Dropbox"},
	"intercom": {"board_token": "intercom", "display_name": "Intercom"},
	"hubspot": {"board_token": "hubspot", "display_name": "HubSpot"},
	"amplitude": {"board_token": "amplitude", "display_name": "Amplitude"},
	"mixpanel": {"board_token": "mixpanel", "display_name": "Mixpanel"},
	"twilio": {"board_token": "twilio", "display_name": "Twilio"},
	"box": {"board_token": "boxinc", "display_name": "Box"},
	"canva": {"board_token": "canva", "display_name": "Canva"},
	"grammarly": {"board_token": "grammarly", "display_name": "Grammarly"},
	"miro": {"board_token": "miro", "display_name": "Miro"},
	"mondaycom": {"board_token": "mondaycom", "display_name": "Monday.com"},
	"shopify": {"board_token": "shopify", "display_name": "Shopify"},
	"webflow": {"board_token": "webflow", "display_name": "Webflow"},
	"zapier": {"board_token": "zapier", "display_name": "Zapier"},
	# AI / ML / Aerospace / Autonomy
	"anthropic": {"board_token": "anthropic", "display_name": "Anthropic"},
	"scaleai": {"board_token": "scaleai", "display_name": "Scale AI"},
	"openai": {"board_token": "openai", "display_name": "OpenAI"},
	"waymo": {"board_token": "waymo", "display_name": "Waymo"},
	"cruise": {"board_token": "cruise", "display_name": "Cruise"},
	"spacex": {"board_token": "spacex", "display_name": "SpaceX"},
	"anduril": {"board_token": "andurilindustries", "display_name": "Anduril"},
	"rivian": {"board_token": "rivian", "display_name": "Rivian"},
	"lucidmotors": {"board_token": "lucidmotors", "display_name": "Lucid Motors"},
	"relativityspace": {"board_token": "relativityspace", "display_name": "Relativity Space"},
	"xai": {"board_token": "xai", "display_name": "xAI"},
	# Health / Wellness
	"headspace": {"board_token": "headspace", "display_name": "Headspace"},
	"hingehealth": {"board_token": "hingehealth", "display_name": "Hinge Health"},
	"springhealth": {"board_token": "springhealth", "display_name": "Spring Health"},
	"modernhealth": {"board_token": "modernhealth", "display_name": "Modern Health"},
	"oscar": {"board_token": "oscar", "display_name": "Oscar Health"},
	"ro": {"board_token": "ro", "display_name": "Ro"},
	"calm": {"board_token": "calm", "display_name": "Calm"},
	# Gaming / Entertainment / Media
	"draftkings": {"board_token": "draftkings", "display_name": "DraftKings"},
	"fanduel": {"board_token": "fanduel", "display_name": "FanDuel"},
	"onepeloton": {"board_token": "onepeloton", "display_name": "Peloton"},
	# EdTech / Gig / Other
	"coursera": {"board_token": "coursera", "display_name": "Coursera"},
	"udemy": {"board_token": "udemy", "display_name": "Udemy"},
	"khanacademy": {"board_token": "khanacademy", "display_name": "Khan Academy"},
	"nerdwallet": {"board_token": "nerdwallet", "display_name": "NerdWallet"},
	"patreon": {"board_token": "patreon", "display_name": "Patreon"},
	"remotecom": {"board_token": "remotecom", "display_name": "Remote"},
	"verkada": {"board_token": "verkada", "display_name": "Verkada"},
	"toast": {"board_token": "toast", "display_name": "Toast"},
	"zillow": {"board_token": "zillow", "display_name": "Zillow"},
	# Moved from Lever
	"samsara": {"board_token": "samsara", "display_name": "Samsara"},
	"opendoor": {"board_token": "opendoor", "display_name": "Opendoor"},
	"pendo": {"board_token": "pendo", "display_name": "Pendo"},
	"duolingo": {"board_token": "duolingo", "display_name": "Duolingo"},
	# Moved from Ashby (corrected token)
	"dbtlabs": {"board_token": "dbtlabsinc", "display_name": "dbt Labs"},
	"togetherai": {"board_token": "togetherai", "display_name": "Together AI"},
}

_LEVER_RAW: dict = {
	"spotify": {"board_token": "spotify", "display_name": "Spotify"},
	"metabase": {"board_token": "metabase", "display_name": "Metabase"},
	# Security / DevTools
	"abnormal": {"board_token": "abnormal", "display_name": "Abnormal Security"},
	"snyk": {"board_token": "snyk", "display_name": "Snyk"},
	"drata": {"board_token": "drata", "display_name": "Drata"},
	"postman": {"board_token": "postman", "display_name": "Postman"},
	# Fintech / HR / Gig
	"carta": {"board_token": "carta", "display_name": "Carta"},
	"dailypay": {"board_token": "dailypay", "display_name": "DailyPay"},
	"earnin": {"board_token": "earnin", "display_name": "EarnIn"},
	"lime": {"board_token": "limebike", "display_name": "Lime"},
	"branch": {"board_token": "branch", "display_name": "Branch"},
	# SaaS / Marketing / Analytics
	"braze": {"board_token": "braze", "display_name": "Braze"},
	"gong": {"board_token": "gong", "display_name": "Gong"},
	"heap": {"board_token": "heap", "display_name": "Heap"},
	"iterable": {"board_token": "iterable", "display_name": "Iterable"},
	"outreach": {"board_token": "outreach", "display_name": "Outreach"},
	"highlevel": {"board_token": "gohighlevel", "display_name": "HighLevel"},
	# Consumer / Marketplace / Media
	"netflix": {"board_token": "netflix", "display_name": "Netflix"},
	"tinder": {"board_token": "tinder", "display_name": "Tinder"},
	"medium": {"board_token": "medium", "display_name": "Medium"},
	"imgur": {"board_token": "imgur", "display_name": "Imgur"},
	"quora": {"board_token": "quora", "display_name": "Quora"},
	"sonder": {"board_token": "sonder", "display_name": "Sonder"},
	"sambatv": {"board_token": "sambatv", "display_name": "Samba TV"},
	# Gaming / Sports / Entertainment
	"epicgames": {"board_token": "epicgames", "display_name": "Epic Games"},
	"hudl": {"board_token": "hudl", "display_name": "Hudl"},
	# EdTech / Data / Other
	"clever": {"board_token": "clever", "display_name": "Clever"},
	"skillshare": {"board_token": "skillshare", "display_name": "Skillshare"},
	"stitchfix": {"board_token": "stitchfix", "display_name": "Stitch Fix"},
	"thumbtack": {"board_token": "thumbtack", "display_name": "Thumbtack"},
	"eventbrite": {"board_token": "eventbrite", "display_name": "Eventbrite"},
	"foursquare": {"board_token": "foursquare", "display_name": "Foursquare"},
	"g2": {"board_token": "g2crowd", "display_name": "G2"},
	"jobgether": {"board_token": "jobgether", "display_name": "Jobgether"},
	"lightcast": {"board_token": "economicmodeling", "display_name": "Lightcast"},
	"mozilla": {"board_token": "mozilla", "display_name": "Mozilla"},
	"unity": {"board_token": "unity", "display_name": "Unity"},
	"welocalize": {"board_token": "welocalize", "display_name": "Welocalize"},
	"appen": {"board_token": "appen-2", "display_name": "Appen"},
	"bird": {"board_token": "bird", "display_name": "Bird"},
	"carbonhealth": {"board_token": "carbonhealth", "display_name": "Carbon Health"},
}

_ASHBY_RAW: dict = {
	# Dev Tools / Infra
	"linear": {"board_token": "linear", "display_name": "Linear"},
	"vercel": {"board_token": "vercel", "display_name": "Vercel"},
	"airbyte": {"board_token": "airbyte", "display_name": "Airbyte"},
	"temporal": {"board_token": "temporal", "display_name": "Temporal"},
	"prefect": {"board_token": "prefect", "display_name": "Prefect"},
	"kaizenlabs": {"board_token": "kaizenlabs", "display_name": "Kaizen Labs"},
	"render": {"board_token": "render", "display_name": "Render"},
	"railway": {"board_token": "railway", "display_name": "Railway"},
	"replit": {"board_token": "replit", "display_name": "Replit"},
	"cursor": {"board_token": "cursor", "display_name": "Cursor"},
	"windsurf": {"board_token": "windsurf", "display_name": "Windsurf"},
	"codeium": {"board_token": "codeium", "display_name": "Codeium"},
	"retool": {"board_token": "retool", "display_name": "Retool"},
	"modal": {"board_token": "modal", "display_name": "Modal"},
	# Fintech / HR
	"ramp": {"board_token": "ramp", "display_name": "Ramp"},
	"mercury": {"board_token": "mercury", "display_name": "Mercury"},
	"deel": {"board_token": "deel", "display_name": "Deel"},
	"pave": {"board_token": "pave", "display_name": "Pave"},
	"check": {"board_token": "check", "display_name": "Check"},
	"moderntreasury": {"board_token": "moderntreasury", "display_name": "Modern Treasury"},
	"finch": {"board_token": "finch", "display_name": "Finch"},
	# AI / ML
	"mistral": {"board_token": "mistral", "display_name": "Mistral AI"},
	"perplexity": {"board_token": "perplexity", "display_name": "Perplexity AI"},
	"cognition": {"board_token": "cognition", "display_name": "Cognition"},
	"anysphere": {"board_token": "anysphere", "display_name": "Anysphere"},
	"hcompany": {"board_token": "hcompany", "display_name": "H Company"},
	"harvey": {"board_token": "harvey", "display_name": "Harvey"},
	"hebbia": {"board_token": "hebbia", "display_name": "Hebbia"},
	"sierra": {"board_token": "sierra", "display_name": "Sierra"},
	"mercor": {"board_token": "mercor", "display_name": "Mercor"},
	"decagon": {"board_token": "decagon", "display_name": "Decagon"},
	# SaaS / Productivity
	"loom": {"board_token": "loom", "display_name": "Loom"},
	"descript": {"board_token": "descript", "display_name": "Descript"},
	"gamma": {"board_token": "gamma", "display_name": "Gamma"},
	"coda": {"board_token": "coda", "display_name": "Coda"},
	"clay": {"board_token": "clay", "display_name": "Clay"},
	"tines": {"board_token": "tines", "display_name": "Tines"},
	"vanta": {"board_token": "vanta", "display_name": "Vanta"},
	"persona": {"board_token": "persona", "display_name": "Persona"},
	"openphone": {"board_token": "openphone", "display_name": "OpenPhone"},
	"orb": {"board_token": "orb", "display_name": "Orb"},
	"ashby": {"board_token": "ashby", "display_name": "Ashby"},
	# Consumer / Media / Health
	"elevenlabs": {"board_token": "elevenlabs", "display_name": "ElevenLabs"},
	"runway": {"board_token": "runway", "display_name": "Runway"},
	"suno": {"board_token": "suno", "display_name": "Suno"},
	"captions": {"board_token": "captions", "display_name": "Captions"},
	"abridge": {"board_token": "abridge", "display_name": "Abridge"},
	"mavenclinic": {"board_token": "mavenclinic", "display_name": "Maven Clinic"},
	# Fintech / Other
	"alloy": {"board_token": "alloy", "display_name": "Alloy"},
	"slope": {"board_token": "slope", "display_name": "Slope"},
	# Moved from Greenhouse
	"notion": {"board_token": "notion", "display_name": "Notion"},
	"cohere": {"board_token": "cohere", "display_name": "Cohere"},
	"plaid": {"board_token": "plaid", "display_name": "Plaid"},
	# Moved from Lever
	"1password": {"board_token": "1password", "display_name": "1Password"},
	# Moved from Greenhouse
	"benchling": {"board_token": "benchling", "display_name": "Benchling"},
	"confluent": {"board_token": "confluent", "display_name": "Confluent"},
}


def _with_careers_url(source: str, source_map: dict) -> dict:
	if source == "greenhouse":
		return {
			slug: {
				**cfg,
				"careers_url": f"https://job-boards.greenhouse.io/{cfg['board_token']}",
			}
			for slug, cfg in source_map.items()
		}
	if source == "lever":
		return {
			slug: {
				**cfg,
				"careers_url": f"https://jobs.lever.co/{cfg['board_token']}",
			}
			for slug, cfg in source_map.items()
		}
	return {
		slug: {
			**cfg,
			"careers_url": f"https://jobs.ashbyhq.com/{cfg['board_token']}",
		}
		for slug, cfg in source_map.items()
	}


JOB_SOURCE_REGISTRY: dict = {
	"greenhouse": _with_careers_url("greenhouse", _GREENHOUSE_RAW),
	"lever": _with_careers_url("lever", _LEVER_RAW),
	"ashby": _with_careers_url("ashby", _ASHBY_RAW),
}
