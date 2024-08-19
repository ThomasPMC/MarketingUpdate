import requests
from datetime import datetime, timedelta
import pytz

# Remplacez par votre token API
API_TOKEN = '5a0fee4f0e9bdadafabdc51c6db96c1838ee4f9f'
BASE_URL_LEADS = f'https://api.pipedrive.com/v1/leads?api_token={API_TOKEN}'
BASE_URL_PERSON = f'https://api.pipedrive.com/v1/persons/{{person_id}}?api_token={API_TOKEN}'
UPDATE_PERSON_URL = f'https://api.pipedrive.com/v1/persons/{{person_id}}?api_token={API_TOKEN}'

# Calcul de la date limite (J-1) en UTC
utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
yesterday = utc_now - timedelta(days=1)

# Obtenir la liste des labels disponibles
labels_url = f'https://api.pipedrive.com/v1/leadLabels?api_token={API_TOKEN}'
labels_response = requests.get(labels_url)
labels_data = labels_response.json().get('data', [])
label_map = {label['id']: label['name'] for label in labels_data}

# Trouver l'ID du label "Email Blasts"
email_blasts_label_id = None
for label in labels_data:
    if label['name'] == "Email Blasts":
        email_blasts_label_id = label['id']
        break

# Vérifier si le label "Email Blasts" a été trouvé
if email_blasts_label_id is None:
    print("Label 'Email Blasts' non trouvé.")
    exit()

# Fonction pour mettre à jour le marketing status d'une personne
def update_person_marketing_status(person_id, new_status):
    update_url = UPDATE_PERSON_URL.format(person_id=person_id)
    payload = {'marketing_status': new_status}
    response = requests.put(update_url, json=payload)
    if response.status_code == 200:
        print(f"Person {person_id} updated successfully.")
    else:
        print(f"Error updating person {person_id}: {response.status_code} - {response.json().get('error', 'Unknown error')}")

# Initialiser une liste pour stocker les leads filtrés
filtered_leads = []

start = 0
limit = 100  # Limite de 100 leads par page

# Variable pour suivre le nombre total de leads traités
leads_processed = 0

while True:
    # Effectuer la requête pour récupérer les leads par lot
    url = f'{BASE_URL_LEADS}&start={start}&limit={limit}'
    response = requests.get(url)

    if response.status_code == 200:
        leads = response.json().get('data', [])
        
        if not leads:
            break  # Sortir de la boucle si aucun lead n'est renvoyé
        
        # Traiter les leads récupérés
        for lead in leads:
            add_time_str = lead.get('add_time')
            update_time_str = lead.get('update_time')
            person_id = lead.get('person_id')
            label_ids = lead.get('label_ids', [])  # Récupérer les ID des labels
            
            # Conversion des chaînes de date en objets datetime (en UTC)
            add_time_dt = datetime.strptime(add_time_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc) if add_time_str else None
            update_time_dt = datetime.strptime(update_time_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc) if update_time_str else None
            
            # Obtenir les noms des labels à partir des ID
            labels = [label_map.get(label_id, 'Unknown Label') for label_id in label_ids]
            
            # Filtrer les leads avec add_time ou update_time supérieur à J-1 et ayant le label "Email Blasts"
            if (add_time_dt and add_time_dt > yesterday) or (update_time_dt and update_time_dt > yesterday):
                if email_blasts_label_id in label_ids:
                    # Récupérer les détails de la personne associée
                    person_response = requests.get(BASE_URL_PERSON.format(person_id=person_id))
                    
                    if person_response.status_code == 200:
                        person_data = person_response.json().get('data', {})
                        marketing_status = person_data.get('marketing_status', 'No marketing status available')
                        
                        # Mettre à jour le marketing status en 'subscribed' si nécessaire
                        if marketing_status != 'subscribed':
                            update_person_marketing_status(person_id, 'subscribed')
                    
                    else:
                        print(f"Error retrieving person: {person_response.status_code} - {person_response.json().get('error', 'Unknown error')}")
        
            leads_processed += 1
        
        start += limit  # Passer au lot suivant
    else:
        print(f"Erreur: {response.json().get('error', 'Une erreur est survenue')}")
        break

print("Traitement terminé.")
