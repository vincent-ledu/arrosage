# Description

🤖 This project automates the watering of a garden using a Raspberry Pi connected to a rainwater collector.

💧 It monitors water levels with floating switches and controls a solenoid valve and pump to distribute water as needed.

The system is designed for reliability and ease of installation, using readily available components and open-source software.

🌱 The goal is to optimize water usage and reduce manual intervention for garden irrigation.

This project is completely inspired by Frederic JELMONI's project, available here: https://www.fred-j.org/index0364.html?p=364

# Features

- Retrieves daily temperature forecasts from Open-Meteo to optimize watering schedules.
- Adjusts watering duration and frequency based on the predicted maximum temperature of the day.
- Displays real-time water tank level using floating switches.
- Shows a history of past watering events for monitoring and analysis.

![Tank monitor and watering control](docs/tank_watering.png)

![Graph of watering history](docs/history.png)

![Settings](image.png)

# Configuration

Tested on raspberry 1 and 4.

Middleware installed:

- nginx

Specific configuration

- Adding www-data user to gpio group

# TODO

- [] add temperature to history graph
- [] give temperature and precipitation forecast for next 3 days
- [] add some pictures of the eletrical device

# Inventory

## Electrical devices

- Raspberry pi (model 3 here)
  https://www.amazon.fr/Raspberry-d%C3%A9marrage-dalimentation-Bo%C3%AEtier-Carte/dp/B0D3FNL84M/ref=sr_1_2?__mk_fr_FR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3S23L4P12PUS0&dib=eyJ2IjoiMSJ9.kT6YfutOjwKMh4swpKAvfe4MWTcL9Qn2eVBMNza9rnmR2xQ8tfBYcpf-S0caQJmbl2ABO_21kc25TW9058TVVvfUxt_OSD6y50Te3-9VgekvnFajobpTCXCRj0c5KpaapXrdeUihgrsBx1yyBUGX3nDXO940POEuJ1ChD_cdvvjfFpSuZ1_5o8RmKQIHwZ-D3aJFmpPgiyVP9-Q5gEvUjNzYuCAbYVcgGf334BKGqKymdjKVJmdczC80vx8PT58iZKldsd90Ro_u0VCVZfivi47VPB11T5h1yZNtO8O0nu4.E7L9ewquZnq-MQsc_QW1mTkKcWBHqUTErdKYFI4JOSY&dib_tag=se&keywords=raspberry+pi+3&qid=1747340366&sprefix=raspberry+pi+3%2Caps%2C145&sr=8-2
  ~ 72€

- 4 floating water switch to detect water level
  https://www.amazon.fr/dp/B0DD6L4QP6?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 2x10€

- Wires to link from the tank to the raspberry
  https://www.amazon.fr/dp/B0087YHNGK?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 20€

- 4 10KOhm Resistors
  https://www.amazon.fr/Innfeeltech-tol%C3%A9rance-r%C3%A9sistance-m%C3%A9tallique-exp%C3%A9riences/dp/B0CL6MDSHV/ref=sr_1_6?crid=SAL7SW5EALSY&dib=eyJ2IjoiMSJ9.2uI5wLbh1ZzeOeeTdK8FdKfEpB2sFTdmTbeF8KiuisjQHOjW-5b3PbFXRzhTGhflagZkvfwF3IT9-uQOBwBJJHSPbKUaamqH6BIdiNp5OeyFMTRZ4cuJeHDFNHBlzbeOTxYVSO5PwnQy24uW5VjUP4GtJ-abmp2ZSh5s4bVJQUct4oXQRUfts5gjoBdd1K2g7mg0vAzgloLncIEwCh4vPf7C-Y9oLvBFzF-6RHCRV503N0_8f3J8x1EbkWWoY7KlUcbIn4S2SYS1qggy4nb3Ar3F0csDVPc5dNkJOBf5yd0.XL2R1j1jQCv8NBD4vNaWzZttinIsnDOU-IobmY37_0s&dib_tag=se&keywords=10k+ohm&qid=1747340488&sprefix=10Ko%2Caps%2C167&sr=8-6
  ~ 7€

- 5V Low level trigger
  https://www.amazon.fr/dp/B07LB2RQYP?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 13€

- Heat shrink tubing
  https://www.amazon.fr/dp/B084GDLSCK?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 15€

- IP55 large box
  https://www.amazon.fr/dp/B003O2X6T8?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 30€

- Solenoid valve
  https://www.amazon.fr/dp/B0BRCPP7ZZ?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 25€

- Dupont cables
  https://www.amazon.fr/Elegoo-Breadboard-Femelle-Longueur-Arduino/dp/B01JD5WCG2/ref=sr_1_6?__mk_fr_FR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3F3VQBLGPD7IE&dib=eyJ2IjoiMSJ9.pd2dzP-V48Zr44UXshWSV2nrC0hngl5tCJM9KuGlRLjkMF9lrKrp7LevhilMgyJv19sxDeQy9mvJg240RSjI-qt9A3v_onx3R7IDdIpz_HNiDA4FFA9zM_4bnVav6mU3TV-x6UyP2t4QXTGZ7DV2pGrNrA6JCqXPd13YCoVDqhC79WO-aVOrChdo6-sF45Ni25QqzdLmWYmKRmfLxIM3cJFOr7DV2MuwLc0M3Val97_4izpj8WREu7an2LaYpWRUHpSeaEKV938cbpFk5rW4qJLn9plfaJm02z61TfhFeMU.6NvihRSiI2gIV4GAuCNdqb86gqzNhMwk0_QYk87JMB0&dib_tag=se&keywords=dupont+cable&qid=1747340279&sprefix=dupont+cabl%2Caps%2C166&sr=8-6
  ~ 10€

- Breadboard
  https://www.amazon.fr/sspa/click?ie=UTF8&spc=MTozODkxOTg0NjM1NTc3MTE1OjE3NDczNDAzMjM6c3BfYXRmOjMwMDE0NDYxNzQ5OTkzMjo6MDo6&url=%2FMMOBIEL-Breadboard-Prototype-Circuit-Imprim%25C3%25A9%2Fdp%2FB0CPJRSLDX%2Fref%3Dsr_1_4_sspa%3F__mk_fr_FR%3D%25C3%2585M%25C3%2585%25C5%25BD%25C3%2595%25C3%2591%26crid%3D27VQGY2Z256Y1%26dib%3DeyJ2IjoiMSJ9.PMPmW7xq7soWcsaxx0d6BAq8GX1BL4vX3mAKIiJ9GI8xJpiMRmYlZpHtCcJEvaVgzMEuMigMkGvrXbjCWkrVxI8hgdgzGB-fVhc3djrMyq9oi8VjjUSmKjw8qflOmLJgGYbQxuBNeG-9E-6VgtBu3HRfJWJQvWu-crT6TOWRRL_78dpBcOH5_9tLDG2LffXjzSofvW1OpWYtOsb3nSVx9DR0MXqyqWJ_z5PVAD9M2vPpf9JYRzOxChEKbWPPdzBysSgh-jIhNZWUMSwaIpBUNds__o9ZMs4NP8V84ZxjWyY.vBnoHkHXB2Jt6lgxRY6SMrdF6muBJ5HJqI0Z5MHOGRQ%26dib_tag%3Dse%26keywords%3Dbreadboard%26qid%3D1747340323%26sprefix%3Dbreadboard%252Caps%252C143%26sr%3D8-4-spons%26sp_csd%3Dd2lkZ2V0TmFtZT1zcF9hdGY%26psc%3D1
  ~ 7€

Total: ~220€

## Garden devices

- Water pump
  https://www.amazon.fr/dp/B08MV3VW7S?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~80€

- Garden hose connection
  https://www.amazon.fr/dp/B0BZKP7CNV?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 10€

- Quick garden hose connection
  https://www.amazon.fr/dp/B09J93FDK2?ref=ppx_yo2ov_dt_b_fed_asin_title
  ~ 10€

Total: 100€
