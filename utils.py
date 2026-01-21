import re
import pandas as pd
from bs4 import BeautifulSoup

def clean_html(html_content):
    if pd.isna(html_content) or html_content is None:
        return ""

    soup = BeautifulSoup(html_content, "lxml")

    for tag in soup(["script", "style", "meta", "link", "select", "option"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    text = re.sub(r"\s+", " ", text).strip()

    BOILERPLATE_PATTERNS = [
        r"Disclaimer.*",
        r"disclaimer.*",
        r"reasonable efforts have been made.*",
        r"translation.*no legal effect.*",
        r"judgments? in regional languages.*",
        r"supreme court registry.*",
        r"editorial section.*",
        r"for general information only.*",
        r"users are advised to verify.*",
        r"html view.*pdf view.*",
    ]

    boilerplate_texts = [
        "Disclaimer: Reasonable efforts have been made to ensure accuracy of information but no legal effect",
        "Judgments in regional languages are being done for general information only",
        "Translations are being done for general information only",
        "Supreme Court Registry Editorial Section",
        "HTML View PDF View",
        "Users are advised to verify the contents",
        "For general information only not legal advice"
    ]

    for boilerplate in boilerplate_texts:
        text = text.replace(boilerplate, "")

    if len(text.strip()) < 50:
        text = soup.get_text(separator=" ")

    START_MARKERS = [
        r"\bJUDGMENT\b",
        r"\bORDER\b",
        r"\bHELD\b",
        r"\bFACTS\b",
        r"\bWe have heard\b",
        r"\bThe facts of the case\b",
    ]

    start_positions = []
    for marker in START_MARKERS:
        match = re.search(marker, text, flags=re.IGNORECASE)
        if match:
            start_positions.append(match.start())

    text = re.sub(r"\s+", " ", text).strip()

    return text
