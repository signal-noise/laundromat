# Laundromat 🧺
> Service to allow non-technical users to automatically commit google sheets CSVs into specific repositories

# User flow

Once set up, users will need to take the following set of steps

1. Allow the Laundromat G Suite App access to your account
2. Ensure the sheet document has the right settings set up
3. Allow the Laundromat Github App access to your account
4. Run the script:
    * Export CSV
    * Commit to GitHub
    * Open PR
5. Confirm

# Initial setup

## Hosting

Cloud Run? DB?

## G Suite App

## Github App

# Project setup

G Suite / Github permissions?

# Developing

Set up a GCP Project. Set up a [Firestore](https://console.cloud.google.com/firestore/data) (native) database. You'll need a service account and JSON file along with it. The service account needs thr `Firebase Rules System` permission.

Use the [Library](https://console.developers.google.com/apis/library) page to select the Sheets API and enable it. 

On the [Credentials](https://console.developers.google.com/apis/credentials) page click **Create Credentials > OAuth client ID**. Choose a Web Application type and give it a name. You'll need to set `http://localhost:8080` as an authorized URI during development, and update this once you deploy to a live environment.

Download the client secret JSON file from the API Console and save it to `/config/client_secret.json`. Don't commit this file!

`docker compose up`

