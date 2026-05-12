from json import dumps

from skills.knowledge.qa.qa import answer as run_answer


def answer(params):
    result = run_answer(params.get("utterance", ""), params.get("entities", []))
    print(
        dumps(
            {
                "domain": "knowledge",
                "skill": "qa",
                "action": "answer",
                "lang": params.get("lang", "en"),
                "utterance": params.get("utterance", ""),
                "entities": params.get("entities", []),
                "slots": params.get("slots", {}),
                "output": {
                    "type": "end",
                    "codes": [result.get("key", "answered")],
                    "speech": result.get(
                        "speech", "I could not route that question right now."
                    ),
                    "core": {},
                    "options": {},
                },
            }
        )
    )
