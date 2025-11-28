#!/bin/bash

# Exit on any error
set -e

# --- Configuration ---
# Replace with your project ID and desired region
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPO_NAME="personalized-consumer-product"
export IMAGE_NAME="app-server"
export SERVICE_NAME="personalized-consumer-product"

# --- Setup ---
echo "--- Configuring gcloud ---"
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

echo "--- Enabling required services ---"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# --- Artifact Registry ---
echo "--- Creating Artifact Registry repository (if it doesn't exist) ---"
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker repository for our application" || echo "Repository $REPO_NAME already exists."

# --- Cloud Build ---
echo "--- Building the Docker image with Cloud Build ---"
# The full image path in Artifact Registry
export IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

# Submit the build to Cloud Build
gcloud builds submit --tag $IMAGE_PATH .

# --- Cloud Run Deployment ---
echo "--- Deploying to Cloud Run ---"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_PATH \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 5000

echo "--- Deployment Complete ---"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Application is available at: $SERVICE_URL"
