from json import dumps

from skills.information.wiki.wiki import search_wikipedia as run_search


def search_wikipedia(params):
    result = run_search(params.get("utterance", ""), params.get("entities", []))
    print(
        dumps(
            {
                "domain": "information",
                "skill": "wiki",
                "action": "search_wikipedia",
                "lang": params.get("lang", "en"),
                "utterance": params.get("utterance", ""),
                "entities": params.get("entities", []),
                "slots": params.get("slots", {}),
                "output": {
                    "type": "end",
                    "codes": [result.get("key", "summary")],
                    "speech": result.get(
                        "speech", "I could not find a useful Wikipedia summary."
                    ),
                    "core": {},
                    "options": {},
                },
            }
        )
    )
