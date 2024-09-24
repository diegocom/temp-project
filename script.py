import os
import requests
import json
import logging
from datetime import datetime

# Configurazione
SSC_URL = "https://your-ssc-instance-url.com/ssc/api/v1"
SSC_TOKEN = "your-ssc-token"
HEADERS = {
    'Authorization': f'FortifyToken {SSC_TOKEN}',
    'Accept': 'application/json'
}
DOWNLOAD_FOLDER = './fprs/'
RETRY_FILE = 'retry_downloads.json'
LOG_FILE = 'download_log.log'

# Creazione cartella per gli FPR
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Configurazione del logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

retry_list = []

def get_applications():
    url = f"{SSC_URL}/projects?limit=0"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['data']

def get_versions(app_id):
    url = f"{SSC_URL}/projects/{app_id}/versions?limit=0"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['data']

def download_fpr(app_name, version_name, version_id):
    fpr_filename = f"{app_name}|{version_name}.fpr"
    file_path = os.path.join(DOWNLOAD_FOLDER, fpr_filename)
    
    if os.path.exists(file_path):
        logging.info(f"File already exists: {fpr_filename}, skipping download.")
        return
    
    url = f"{SSC_URL}/projectVersions/{version_id}/issueTemplate"
    
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as fpr_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    fpr_file.write(chunk)
        logging.info(f"Downloaded: {fpr_filename}")
    except Exception as e:
        logging.error(f"Failed to download: {fpr_filename} - {str(e)}")
        retry_list.append({
            'application': app_name,
            'version': version_name,
            'version_id': version_id
        })

def retry_failed_downloads():
    if not os.path.exists(RETRY_FILE):
        logging.info("No retry file found, nothing to retry.")
        return
    
    with open(RETRY_FILE, 'r') as retry_file:
        failed_downloads = json.load(retry_file)
    
    for item in failed_downloads:
        download_fpr(item['application'], item['version'], item['version_id'])
    
    if not retry_list:
        logging.info("All failed downloads retried successfully.")
    else:
        logging.warning(f"{len(retry_list)} downloads still failed. Retry file will be updated.")
        with open(RETRY_FILE, 'w') as retry_file:
            json.dump(retry_list, retry_file, indent=4)

def main():
    applications = get_applications()
    for app in applications:
        app_name = app['name']
        app_id = app['id']
        versions = get_versions(app_id)
        
        for version in versions:
            version_name = version['name']
            version_id = version['id']
            download_fpr(app_name, version_name, version_id)
    
    if retry_list:
        with open(RETRY_FILE, 'w') as retry_file:
            json.dump(retry_list, retry_file, indent=4)
        logging.warning(f"Retry file created: {RETRY_FILE}")
    else:
        logging.info("All downloads completed successfully.")

if __name__ == "__main__":
    main()
