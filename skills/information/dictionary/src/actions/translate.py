from json import dumps

from skills.information.dictionary.diction import translate as run_translate


def translate(params):
    result = run_translate(params.get("utterance", ""), params.get("entities", []))
    print(
        dumps(
            {
                "domain": "information",
                "skill": "dictionary",
                "action": "translate",
                "lang": params.get("lang", "en"),
                "utterance": params.get("utterance", ""),
                "entities": params.get("entities", []),
                "slots": params.get("slots", {}),
                "output": {
                    "type": "end",
                    "codes": [result.get("key", "definition")],
                    "speech": result.get(
                        "speech", "I could not look up that definition right now."
                    ),
                    "core": {},
                    "options": {},
                },
            }
        )
    )
