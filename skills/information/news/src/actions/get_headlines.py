from json import dumps

from skills.information.news.news import get_headlines as run_headlines


def get_headlines(params):
    result = run_headlines(params.get("utterance", ""), params.get("entities", []))
    print(dumps({
        "domain": "information",
        "skill": "news",
        "action": "get_headlines",
        "lang": params.get("lang", "en"),
        "utterance": params.get("utterance", ""),
        "entities": params.get("entities", []),
        "slots": params.get("slots", {}),
        "output": {
            "type": "end",
            "codes": [result.get("key", "headlines")],
            "speech": result.get("speech", "I couldn't fetch the news right now."),
            "core": {},
            "options": {},
        },
    }))
