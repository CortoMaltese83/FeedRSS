import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime
import urllib3
import locale

try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')
    except locale.Error:
        print(
            "Attenzione: Impossibile impostare la locale italiana. La conversione delle date potrebbe non funzionare correttamente.")

# Disabilita i warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://iissvoltadegemmis.edu.it"
INDEX_URL = urljoin(BASE_URL, "/circolare/")


def estrai_circolari():
    response = requests.get(INDEX_URL, verify=False)
    soup = BeautifulSoup(response.content, "html.parser")

    items = soup.select("a.presentation-card-link")

    circolari = []

    ora_corrente = datetime.now().astimezone().time()

    for item in items:
        link = urljoin(BASE_URL, item['href'])

        year_tag = item.find("span", class_="year")
        day_tag = item.find("span", class_="day")
        month_tag = item.find("span", class_="month")

        numero_tag = item.find("small", class_="h6 text-coloreNotizie")
        titolo_tag = item.find("h2", class_="h3")
        descrizione_tag = item.find("p")

        if not numero_tag or not titolo_tag or not year_tag or not day_tag or not month_tag:
            continue

        numero = numero_tag.get_text(strip=True)
        titolo = titolo_tag.get_text(strip=True)
        descrizione = descrizione_tag.get_text(strip=True) if descrizione_tag else ""
        full_title = f"{numero} – {titolo}: {descrizione}"

        year = year_tag.get_text(strip=True)
        day = day_tag.get_text(strip=True)
        month_abbr = month_tag.get_text(strip=True)

        date_str = f"{day} {month_abbr} {year}"

        try:
            parsed_date = datetime.strptime(date_str, "%d %b %Y")

            final_datetime = parsed_date.replace(
                hour=ora_corrente.hour,
                minute=ora_corrente.minute,
                second=ora_corrente.second,
                microsecond=ora_corrente.microsecond
            ).astimezone()
        except ValueError as e:
            print(f"Errore nella parsificazione della data '{date_str}': {e}. Verrà usata la data e ora corrente.")
            final_datetime = datetime.now().astimezone()  # Fallback

        circolari.append({
            "title": full_title,
            "link": link,  # Ora il link è estratto direttamente dal tag <a>
            "date": final_datetime,
        })

    return circolari


def genera_feed(circolari):
    fg = FeedGenerator()
    fg.id(INDEX_URL)  # L'ID del feed può rimanere l'URL della pagina indice
    fg.title("IISS Volta-De Gemmis – Circolari")
    fg.link(href=INDEX_URL, rel="alternate")
    fg.description("Feed RSS delle ultime circolari pubblicate")
    fg.language('it')  # Aggiungi la lingua per il feed

    # Ordina le circolari dalla più recente alla meno recente
    circolari_ordinate = sorted(circolari, key=lambda x: x['date'], reverse=True)

    for c in circolari_ordinate:
        fe = fg.add_entry()
        fe.id(c["link"])
        fe.title(c["title"])
        fe.link(href=c["link"])
        fe.published(c["date"])
        fe.updated(c["date"])

    fg.rss_file("circolari.xml")


def main():
    circolari = estrai_circolari()
    genera_feed(circolari)
    print(f"Generato RSS con {len(circolari)} circolari.")


if __name__ == "__main__":
    main()