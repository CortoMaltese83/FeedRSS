import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime
import urllib3
import locale  # Per gestire i nomi dei mesi in italiano

# Imposta la locale italiana per la corretta interpretazione dei mesi
# Questo è importante per strptime
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')  # Fallback per sistemi senza UTF-8
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

    # Ora selezioniamo direttamente il tag <a> con la classe "presentation-card-link"
    items = soup.select("a.presentation-card-link")

    circolari = []

    # Ottieni l'orario corrente per aggiungerlo alla data della circolare
    ora_corrente = datetime.now().astimezone().time()

    for item in items:
        # Il link della circolare è l'attributo 'href' del tag 'a' stesso
        link = urljoin(BASE_URL, item['href'])

        # Ora cerchiamo gli elementi all'interno dell'articolo (che è figlio del tag <a>)
        # Nonostante `item` sia un tag `<a>`, BeautifulSoup ti permette di navigare i suoi figli.

        # Recupera la data
        year_tag = item.find("span", class_="year")
        day_tag = item.find("span", class_="day")
        month_tag = item.find("span", class_="month")

        numero_tag = item.find("small", class_="h6 text-coloreNotizie")
        titolo_tag = item.find("h2", class_="h3")
        descrizione_tag = item.find("p")

        if not numero_tag or not titolo_tag or not year_tag or not day_tag or not month_tag:
            # Se manca qualche informazione cruciale, saltiamo questa circolare
            continue

        numero = numero_tag.get_text(strip=True)
        titolo = titolo_tag.get_text(strip=True)
        descrizione = descrizione_tag.get_text(strip=True) if descrizione_tag else ""
        full_title = f"{numero} – {titolo}: {descrizione}"

        # Estrai i componenti della data
        year = year_tag.get_text(strip=True)
        day = day_tag.get_text(strip=True)
        month_abbr = month_tag.get_text(strip=True)  # Es. "Mag", "Giu"

        # Costruisci la stringa della data nel formato corretto per strptime
        # Esempio: "30 Mag 2025"
        date_str = f"{day} {month_abbr} {year}"

        try:
            # Parsifica la data usando la locale italiana per i nomi dei mesi abbreviati (%b)
            parsed_date = datetime.strptime(date_str, "%d %b %Y")
            # Combina la data parsificata con l'orario corrente
            final_datetime = parsed_date.replace(
                hour=ora_corrente.hour,
                minute=ora_corrente.minute,
                second=ora_corrente.second,
                microsecond=ora_corrente.microsecond
            ).astimezone()  # Assicurati che sia timezone-aware
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
        # L'ID dell'entry DEVE essere univoco per ogni elemento del feed.
        # Il link della circolare (c["link"]) è ora il candidato perfetto per questo ID.
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