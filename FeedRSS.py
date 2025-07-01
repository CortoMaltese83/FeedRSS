import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime
import urllib3

# Disabilita i warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://iissvoltadegemmis.edu.it"
INDEX_URL = urljoin(BASE_URL, "/circolare/")

def estrai_circolari():
    response = requests.get(INDEX_URL, verify=False)
    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.select("div.card-article-content")
    circolari = []

    for item in items:
        numero_tag = item.find("small", class_="h6 text-coloreNotizie")
        titolo_tag = item.find("h2", class_="h3")
        descrizione_tag = item.find("p")

        if not numero_tag or not titolo_tag:
            continue

        numero = numero_tag.get_text(strip=True)
        titolo = titolo_tag.get_text(strip=True)
        descrizione = descrizione_tag.get_text(strip=True) if descrizione_tag else ""
        full_title = f"{numero} – {titolo}: {descrizione}"

        circolari.append({
            "title": full_title,
            "link": INDEX_URL,
            "date": datetime.now().astimezone(),
        })

    return circolari

def genera_feed(circolari):
    fg = FeedGenerator()
    fg.id(INDEX_URL)
    fg.title("IISS Volta-De Gemmis – Circolari")
    fg.link(href=INDEX_URL, rel="alternate")
    fg.description("Feed RSS delle ultime circolari pubblicate")

    for c in circolari:
        fe = fg.add_entry()
        fe.id(c["link"])
        fe.title(c["title"])
        fe.link(href=c["link"])
        fe.published(c["date"])

    fg.rss_file("circolari.xml")

def main():
    circolari = estrai_circolari()
    genera_feed(circolari)
    print(f"Generato RSS con {len(circolari)} circolari.")

if __name__ == "__main__":
    main()