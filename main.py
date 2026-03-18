import os
import sys
import logging
import json
import dlt
from dlt.sources.rest_api import rest_api_source
from google.cloud.logging.handlers import StructuredLogHandler
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

# Configuration Cloud Logging
handler = StructuredLogHandler()
logging.getLogger().addHandler(handler)
log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logging.getLogger().setLevel(log_level)
logging.captureWarnings(True)

# Configuration dlt
os.environ["RUNTIME__LOG_LEVEL"] = log_level_name
os.environ["RUNTIME__LOG_FORMAT"] = "JSON"

def get_secret(secret_name):
    """Récupère un secret depuis GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    try:
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logging.error(f"Erreur lors de l'accès au secret {secret_name}: {e}")
        return None

def run_pipeline():
    # Paramètres de base
    base_url = os.getenv("API_BASE_URL")
    bq_dataset_id = os.getenv("BQ_DATASET_ID")
    bq_project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    api_config_raw = os.getenv("API_CONFIG", "{}")
    
    if not base_url or not bq_dataset_id:
        logging.error("API_BASE_URL et BQ_DATASET_ID sont requis.")
        sys.exit(1)

    # Récupération de l'authentification (optionnelle)
    api_secret_name = os.getenv("API_SECRET")
    auth_config = {}
    if api_secret_name:
        secret_value = get_secret(api_secret_name)
        if secret_value:
            # On suppose par défaut que c'est un token Bearer ou spécifié par API_AUTH_TYPE
            auth_type = os.getenv("API_AUTH_TYPE", "bearer").lower()
            if auth_type == "bearer":
                auth_config = {"token": secret_value}
            elif auth_type == "api_key":
                auth_config = {
                    "type": "api_key",
                    "api_key": secret_value,
                    "name": os.getenv("API_KEY_NAME", "Authorization"),
                    "location": os.getenv("API_KEY_LOCATION", "header")
                }
            logging.info(f"Authentification {auth_type} configurée via Secret Manager.")

    # Parsing de la configuration des endpoints
    try:
        api_config = json.loads(api_config_raw)
    except json.JSONDecodeError as e:
        logging.error(f"Erreur lors du parsing de API_CONFIG: {e}")
        sys.exit(1)

    logging.info(f"Démarrage de la pipeline API -> BigQuery (Dataset: {bq_dataset_id})")

    # Configuration de la source REST API dlt
    source_config = {
        "client": {
            "base_url": base_url,
            "auth": auth_config if auth_config else None,
            "paginator": api_config.get("paginator", "auto")
        },
        "resource_defaults": api_config.get("resource_defaults", {
            "primary_key": "id",
            "write_disposition": "merge",
        }),
        "resources": api_config.get("resources", [])
    }

    source = rest_api_source(source_config)

    # Destination BigQuery
    destination_params = {"location": os.getenv("BQ_LOCATION", "EU")}
    if bq_project_id:
        destination_params["project_id"] = bq_project_id

    bucket_url = os.getenv("BUCKET_URL")
    staging = 'filesystem' if bucket_url else None

    pipeline_name = os.getenv("PIPELINE_NAME", f"api_to_bq_{bq_dataset_id}")
    
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.bigquery(**destination_params, loader_file_format="parquet"),
        dataset_name=bq_dataset_id,
        staging=staging,
        progress="log",
    )

    try:
        logging.info("Exécution du pipeline dlt...")
        load_info = pipeline.run(source)
        logging.info(f"Pipeline terminée. Info: {load_info}")
    except Exception as e:
        logging.error(f"Erreur fatale lors de l'exécution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
