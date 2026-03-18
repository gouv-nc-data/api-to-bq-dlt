# API to BigQuery dlt Ingestor

Cette image permet d'ingérer des données depuis n'importe quelle API REST vers Google BigQuery en utilisant la puissance de `dlt`.

## Configuration

La configuration se fait via des variables d'environnement.

### Paramètres GCP
- `GOOGLE_CLOUD_PROJECT` : ID du projet Google Cloud (Requis).
- `BQ_DATASET_ID` : Nom du dataset BigQuery cible (Requis).
- `BQ_LOCATION` : Localisation du dataset (Défaut: `EU`).
- `BUCKET_URL` : (Optionnel) URL GCS pour le staging (ex: `gs://my-bucket/staging`).

### Paramètres API
- `API_BASE_URL` : URL de base de l'API (ex: `https://api.github.com/`).
- `API_SECRET` : Nom du secret dans Secret Manager contenant le token (Optionnel).
- `API_AUTH_TYPE` : Type d'auth (`bearer` ou `api_key`. Défaut: `bearer`).
- `API_CONFIG` : JSON définissant les ressources et l'incrémental.

### Exemple de `API_CONFIG` (Incrémental)
```json
{
  "resources": [
    {
      "name": "issues",
      "endpoint": {
        "path": "repos/owner/repo/issues",
        "params": {
          "since": {
            "type": "incremental",
            "cursor_path": "updated_at",
            "initial_value": "2024-01-01T00:00:00Z"
          }
        }
      }
    }
  ]
}
```

## Build & Run
```bash
docker build -t api-to-bq-dlt .
docker run --env-file .env api-to-bq-dlt
```