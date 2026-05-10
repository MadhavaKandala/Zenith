from json import dumps

from skills.information.weather.weather import get_weather as run_weather


def get_weather(params):
    result = run_weather(params.get("utterance", ""), params.get("entities", []))
    print(dumps({
        "domain": "information",
        "skill": "weather",
        "action": "get_weather",
        "lang": params.get("lang", "en"),
        "utterance": params.get("utterance", ""),
        "entities": params.get("entities", []),
        "slots": params.get("slots", {}),
        "output": {
            "type": "end",
            "codes": [result.get("key", "weather")],
            "speech": result.get("speech", "I couldn't fetch the weather right now."),
            "core": {},
            "options": {},
        },
    }))
