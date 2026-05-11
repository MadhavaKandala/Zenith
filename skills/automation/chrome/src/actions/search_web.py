from skills.automation.chrome.chrome import search_web as search_web_impl


def search_web(params):
    return search_web_impl(params["utterance"], params["entities"])
