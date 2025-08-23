# seed.py
import random
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo  # Python 3.9+
import uuid
from db.db import init_db, add_task

# Initialisation
init_db()

# Timestamp actuel
tz = ZoneInfo("Europe/Paris")
now = datetime.now(tz)

# Remplir les 30 derniers jours
for day_offset in range(30):
    # Génère entre 0 et 2 sessions d’arrosage aléatoires par jour
    for _ in range(random.randint(0, 2)):
        # Date du jour simulé (à minuit)
        hour_offset = random.randint(5, 20)  # Heure de déclenchement dans la journée
        day_dt = now - timedelta(days=day_offset, hours=hour_offset)
        duration = random.randint(60, 300)  # Durée entre 1 et 5 min
        task_id = str(uuid.uuid4())
        status = random.choices(["completed", "canceled", "error"], weights=[0.8, 0.1, 0.1])[0]
        min_temp = random.uniform(10.0, 20.0)  # Température min entre 10 et 20 °C
        max_temp = random.uniform(20.0, 30.0)  # Température max entre 20 et 30 °C
        precipitation = random.uniform(0.0, 5.0)  # Précipitation entre 0 et 5 mm

        add_task(duration, status)

print("✅ Fake data inserted.")
