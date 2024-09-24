import os
import requests
import json
import logging

# Configurazione
SSC_URL = "https://your-ssc-instance-url.com/ssc/api/v1"
SSC_TOKEN = "your-ssc-token"
HEADERS = {
    'Authorization': f'FortifyToken {SSC_TOKEN}',
    'Accept': 'application/json'
}
UPLOAD_FOLDER = './fprs/'
FAILED_UPLOADS_FILE = 'failed_uploads.json'
LOG_FILE = 'upload_log.log'

# Configurazione del logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

failed_uploads = []

def get_or_create_application(app_name):
    url = f"{SSC_URL}/projects?limit=0&q=name:{app_name}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()['data']
    
    if data:
        app_id = data[0]['id']
        logging.info(f"Application {app_name} already exists with ID {app_id}.")
        return app_id
    else:
        create_url = f"{SSC_URL}/projects"
        payload = {
            'name': app_name,
            'description': f"Auto-generated application {app_name}"
        }
        response = requests.post(create_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        app_id = response.json()['data']['id']
        logging.info(f"Created new application {app_name} with ID {app_id}.")
        return app_id

def get_or_create_version(app_id, version_name):
    url = f"{SSC_URL}/projects/{app_id}/versions?limit=0&q=name:{version_name}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()['data']
    
    if data:
        version_id = data[0]['id']
        logging.info(f"Version {version_name} already exists for application ID {app_id}.")
        return version_id
    else:
        create_url = f"{SSC_URL}/projects/{app_id}/versions"
        payload = {
            'name': version_name,
            'description': f"Auto-generated version {version_name}"
        }
        response = requests.post(create_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        version_id = response.json()['data']['id']
        logging.info(f"Created new version {version_name} for application ID {app_id}.")
        return version_id

def upload_fpr(version_id, file_path, app_name, version_name):
    upload_url = f"{SSC_URL}/projectVersions/{version_id}/artifacts"
    files = {'file': open(file_path, 'rb')}
    
    try:
        response = requests.post(upload_url, headers={'Authorization': HEADERS['Authorization']}, files=files)
        response.raise_for_status()
        logging.info(f"Uploaded FPR {file_path} to version ID {version_id}.")
    except Exception as e:
        logging.error(f"Failed to upload FPR {file_path} - {str(e)}")
        failed_uploads.append({
            'application': app_name,
            'version': version_name,
            'file_path': file_path
        })

def process_fprs():
    # Ottieni il numero totale di file FPR
    total_files = len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".fpr")])
    processed_files = 0
    
    for fpr_file in os.listdir(UPLOAD_FOLDER):
        if fpr_file.endswith(".fpr"):
            try:
                # Split del nome del file in NOMEAPPLICATION e NOMEVERSION
                app_name, version_name = os.path.splitext(fpr_file)[0].split(';')
                file_path = os.path.join(UPLOAD_FOLDER, fpr_file)
                
                # Ottieni o crea l'applicazione e la versione
                app_id = get_or_create_application(app_name)
                version_id = get_or_create_version(app_id, version_name)
                
                # Carica il file FPR
                upload_fpr(version_id, file_path, app_name, version_name)
                
                # Aggiorna lo stato di avanzamento
                processed_files += 1
                print(f"Processed {processed_files}/{total_files} files")
                
            except Exception as e:
                logging.error(f"Error processing file {fpr_file}: {str(e)}")
    
    # Salva i tentativi di upload falliti
    if failed_uploads:
        with open(FAILED_UPLOADS_FILE, 'w') as failed_file:
            json.dump(failed_uploads, failed_file, indent=4)
        logging.warning(f"Failed uploads saved in {FAILED_UPLOADS_FILE}")

def retry_failed_uploads():
    if not os.path.exists(FAILED_UPLOADS_FILE):
        logging.info("No failed uploads file found, nothing to retry.")
        return
    
    with open(FAILED_UPLOADS_FILE, 'r') as failed_file:
        failed_uploads = json.load(failed_file)
    
    remaining_failures = []
    total_failed = len(failed_uploads)
    processed_failed = 0
    
    for item in failed_uploads:
        app_name = item['application']
        version_name = item['version']
        file_path = item['file_path']
        
        try:
            app_id = get_or_create_application(app_name)
            version_id = get_or_create_version(app_id, version_name)
            upload_fpr(version_id, file_path, app_name, version_name)
            
            # Aggiorna lo stato di avanzamento dei retry
            processed_failed += 1
            print(f"Retried {processed_failed}/{total_failed} failed files")
            
        except Exception as e:
            logging.error(f"Error retrying upload for file {file_path}: {str(e)}")
            remaining_failures.append(item)
    
    if remaining_failures:
        with open(FAILED_UPLOADS_FILE, 'w') as failed_file:
            json.dump(remaining_failures, failed_file, indent=4)
        logging.warning(f"Remaining failed uploads saved in {FAILED_UPLOADS_FILE}")
    else:
        os.remove(FAILED_UPLOADS_FILE)
        logging.info("All failed uploads retried successfully.")

if __name__ == "__main__":
    process_fprs()
