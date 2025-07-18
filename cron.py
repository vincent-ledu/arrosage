import sys
import requests

# Vérifier si un argument a été passé pour 'morning' ou 'evening'
if len(sys.argv) != 2 or sys.argv[1] not in ['morning', 'evening']:
    print("Usage: python script.py [morning|evening]")
    sys.exit(1)

# Récupérer l'argument 'morning' ou 'evening'
time_of_day = sys.argv[1]

# Coordonnées pour Alex (74290)
latitude = 45.9370
longitude = 6.1710

# URL pour obtenir la température maximale de la journée
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max&forecast_days=1&timezone=Europe/Paris"

# Faire la requête pour obtenir la prévision de la température
response = requests.get(url)
data = response.json()

# Température maximale de la journée
temp_max = data['daily']['temperature_2m_max'][0]

# Déterminer la durée d'arrosage selon la température et le moment de la journée
arrosage_needed = False
duration = 0

# Logique pour l'arrosage en fonction du moment de la journée (matin ou soir)
if temp_max < 15:
    if time_of_day == 'morning':
        arrosage_needed = False
    if time_of_day == 'evening':
        arrosage_needed = False
elif temp_max < 20:
    if time_of_day == 'morning':
        arrosage_needed = True
        duration = 120  # 120 secondes le matin
    if time_of_day == 'evening':
        arrosage_needed = False
elif temp_max < 25:
    if time_of_day == 'morning':
        arrosage_needed = True
        duration = 180  # 180 secondes le matin
    if time_of_day == 'evening':
        arrosage_needed = True
        duration = 120  # 120 secondes le soir
elif temp_max < 30:
    if time_of_day == 'morning':
        arrosage_needed = True
        duration = 300  # 300 secondes le matin
    if time_of_day == 'evening':
        arrosage_needed = True
        duration = 300  # 300 secondes le soir
else:
    if time_of_day == 'morning':
        arrosage_needed = True
        duration = 300  # 300 secondes le matin
    if time_of_day == 'evening':
        arrosage_needed = True
        duration = 300  # 300 secondes le soir

# Affichage de la température et du type d'arrosage
print(f"Température maximale prévue : {temp_max}°C.")
if arrosage_needed:
    print(f"Arrosage recommandé le {time_of_day}: {duration} secondes.")
else:
    print(f"Pas d'arrosage nécessaire le {time_of_day}.")

# Appel conditionnel à l'API d'arrosage
if arrosage_needed:
    print(f"Appel API pour l'arrosage du {time_of_day}...")
    response_arrosage = requests.get(f"http://localhost/api/open-water?duration={duration}")
    print(f"Arrosage effectué le {time_of_day} pour {duration} secondes.")
