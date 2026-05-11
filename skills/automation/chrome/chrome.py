import utils
import webbrowser

SITES = {
    "youtube": ("https://www.youtube.com", "YouTube"),
    "github": ("https://www.github.com", "GitHub"),
    "gmail": ("https://mail.google.com", "Gmail"),
    "google": ("https://www.google.com", "Google"),
    "maps": ("https://maps.google.com", "Google Maps"),
    "stackoverflow": ("https://stackoverflow.com", "Stack Overflow"),
    "netflix": ("https://www.netflix.com", "Netflix"),
    "whatsapp": ("https://web.whatsapp.com", "WhatsApp"),
    "instagram": ("https://www.instagram.com", "Instagram"),
    "linkedin": ("https://www.linkedin.com", "LinkedIn"),
    "twitter": ("https://www.twitter.com", "Twitter"),
    "spotify": ("https://open.spotify.com", "Spotify"),
}


def open_website(string, entities):
    """Open a website by name"""
    text = string.lower()

    for name, (url, label) in SITES.items():
        if name in text:
            webbrowser.open(url)
            return utils.output("end", {"key": "opened", "data": {"site": label}})

    search_url = f"https://www.google.com/search?q={string}"
    webbrowser.open(search_url)
    return utils.output("end", {"key": "searched", "data": {"query": string}})


def search_web(string, entities):
    """Search the web"""
    search_url = f"https://www.google.com/search?q={string}"
    webbrowser.open(search_url)
    return utils.output("end", {"key": "searched", "data": {"query": string}})
