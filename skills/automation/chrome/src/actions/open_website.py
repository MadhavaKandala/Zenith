from skills.automation.chrome.chrome import open_website as open_website_impl


def open_website(params):
    return open_website_impl(params["utterance"], params["entities"])
