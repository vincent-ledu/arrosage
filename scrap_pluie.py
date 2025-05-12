import requests
from bs4 import BeautifulSoup

# Exemple : historique du 1er mai 2024 à Annecy-Meythet (station ID : 74010001)
url = "https://www.infoclimat.fr/observations-meteo/archives/1-mai-2024/annecy-meythet/07410.html"

response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Recherche des précipitations dans la page (à adapter si Infoclimat modifie le format)
table = soup.find("table", class_="table table-striped table-hover table-sm archive-table")
rows = table.find_all("tr") if table else []

print("Heure\tPrécipitations")
for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 8:
        heure = cols[0].text.strip()
        pluie = cols[7].text.strip()  # La colonne "RR" (précipitations en mm)
        print(f"{heure}\t{pluie}")
