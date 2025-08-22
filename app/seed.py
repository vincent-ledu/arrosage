# seed.py
import random
import time
import uuid
from db.db import init_db, add_task

# Initialisation
init_db()

# Timestamp actuel
now = time.time()

# Remplir les 30 derniers jours
for day_offset in range(30):
    # Génère entre 0 et 2 sessions d’arrosage aléatoires par jour
    for _ in range(random.randint(0, 2)):
        # Date du jour simulé (à minuit)
        day_ts = now - day_offset * 86400
        hour_offset = random.randint(5, 20)  # Heure de déclenchement dans la journée
        duration = random.randint(60, 300)  # Durée entre 1 et 5 min
        task_id = str(uuid.uuid4())
        status = random.choices(["completed", "canceled", "error"], weights=[0.8, 0.1, 0.1])[0]
        min_temp = random.uniform(10.0, 20.0)  # Température min entre 10 et 20 °C
        max_temp = random.uniform(20.0, 30.0)  # Température max entre 20 et 30 °C
        precipitation = random.uniform(0.0, 5.0)  # Précipitation entre 0 et 5 mm

        add_task(duration, status, min_temp=min_temp, max_temp=max_temp, precipitation=precipitation)

print("✅ Fake data inserted.")
