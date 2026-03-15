import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

RSS_URL = "https://pib.gov.in/rss.aspx"
OUTPUT_FILE = "anki_cards.csv"

MAX_CARDS_PER_DAY = 3

KEYWORDS = [
    "ministry",
    "cabinet",
    "government",
    "scheme",
    "policy",
    "act",
    "bill",
    "court",
    "tribunal",
    "constitution",
    "authority",
    "commission",
    "regulation",
    "parliament"
]

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def governance_filter(sentence):
    s = sentence.lower()
    return any(k in s for k in KEYWORDS)

def get_pib_links():

    r = requests.get(RSS_URL)

    soup = BeautifulSoup(r.text, "xml")

    links = []

    for item in soup.find_all("item")[:15]:
        links.append(item.link.text)

    return links

def scrape_article(url):

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    content_div = soup.find("div", {"class": "PressReleaseContent"})

    if not content_div:
        return None

    paragraphs = content_div.find_all("p")

    text = " ".join(p.get_text() for p in paragraphs)

    return clean_text(text)

def extract_sentences(text):

    sentences = re.split(r'(?<=[.!?])\s+', text)

    clean = []

    for s in sentences:

        s = clean_text(s)

        if 60 < len(s) < 200:
            clean.append(s)

    return clean

def build_cards():

    cards = []

    links = get_pib_links()

    for link in links:

        if len(cards) >= MAX_CARDS_PER_DAY:
            break

        article = scrape_article(link)

        if not article:
            continue

        sentences = extract_sentences(article)

        for s in sentences:

            if not governance_filter(s):
                continue

            cards.append({
                "Front": s.replace(".", "?"),
                "Back": s
            })

            if len(cards) >= MAX_CARDS_PER_DAY:
                break

    return cards

def main():

    cards = build_cards()

    if not cards:
        cards.append({
            "Front": "No governance-relevant PIB update today?",
            "Back": "No card generated"
        })

    df = pd.DataFrame(cards)

    df.to_csv(OUTPUT_FILE, sep=";", index=False)

    print("CSV generated")

if __name__ == "__main__":
    main()
