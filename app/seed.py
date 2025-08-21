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

        add_task(duration, status)

print("✅ Fake data inserted.")
