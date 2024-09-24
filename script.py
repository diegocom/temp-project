import requests
import json

# Configurazione dell'API Fortify SSC
SSC_BASE_URL = "https://fortify-ssc.example.com/ssc"  # URL base di Fortify SSC
API_VERSION = "v1"  # La versione API di SSC
USERNAME = "your_username"
PASSWORD = "your_password"

# Imposta l'URL per autenticarsi ed ottenere il token
AUTH_URL = f"{SSC_BASE_URL}/api/{API_VERSION}/auth/token"

# Ottieni il token di autenticazione
def get_auth_token():
    response = requests.post(AUTH_URL, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json()["data"]["token"]
    else:
        print(f"Errore durante l'autenticazione: {response.status_code}")
        print(response.text)
        return None

# Recupera le applicazioni nello stato 'Finish Later'
def get_uncommitted_applications(token):
    url = f"{SSC_BASE_URL}/api/{API_VERSION}/projectVersions?filter=commitState:FINISH_LATER"
    headers = {"Authorization": f"FortifyToken {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Errore nel recupero delle applicazioni: {response.status_code}")
        print(response.text)
        return []

# Commit delle applicazioni
def commit_application(app_id, token):
    url = f"{SSC_BASE_URL}/api/{API_VERSION}/projectVersions/{app_id}/commit"
    headers = {"Authorization": f"FortifyToken {token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print(f"Commit completato per l'applicazione {app_id}")
    else:
        print(f"Errore durante il commit dell'applicazione {app_id}: {response.status_code}")
        print(response.text)

def main():
    # Ottieni il token di autenticazione
    token = get_auth_token()
    
    if token:
        # Recupera le applicazioni non completate
        applications = get_uncommitted_applications(token)
        
        if applications:
            # Cicla tra le applicazioni e fai il commit
            for app in applications:
                app_id = app["id"]
                print(f"Effettuo il commit dell'applicazione {app['name']} con ID {app_id}")
                commit_application(app_id, token)
        else:
            print("Nessuna applicazione nello stato 'Finish Later' trovata.")
    else:
        print("Errore durante l'autenticazione. Script terminato.")

if __name__ == "__main__":
    main()
