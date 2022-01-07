#gcloud auth application-default login
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.77.0"
    }
  }
  backend "gcs"{
    bucket      = "social-nft-backend-tf_state" 
    prefix      = "dev"
    credentials = "social-nft-backend.json"
  }
}
provider "google" {
  credentials = file("social-nft-backend.json")
  project     = var.project_name
  region      = var.region
  zone        = var.zone
}

module "project_services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "11.1.1"
  project_id    = var.project_name
  activate_apis =  [
   "cloudresourcemanager.googleapis.com",
   "iamcredentials.googleapis.com",
   "iam.googleapis.com",
   "cloudfunctions.googleapis.com",
   "iam.googleapis.com",
   "cloudbuild.googleapis.com",
   "cloudscheduler.googleapis.com",
   "storage.googleapis.com"
  ]
  disable_services_on_destroy = false
  disable_dependent_services  = false
}

resource "google_service_account" "service_account" {
  account_id   = "cloud-function-invoker"
  display_name = "Cloud Function Tutorial Invoker Service Account"
}

#Bucket
resource "google_storage_bucket" "service_bucket" {
  name     = "${var.project_name}-service_src"
  location = var.region
}
resource "google_storage_bucket" "tf_state" {
  name     = "${var.project_name}-tf_state"
  location = var.region
}

resource "google_storage_bucket" "app_bucket" {
  name     = "${var.project_name}-app_src"
  location = var.region
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 30
  }
}

##BIGQUERY
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = "nft_epoch0"
  friendly_name               = "test"
  description                 = "This is a test description"
  location                    = var.region
}

resource "google_bigquery_table" "nft_votes" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "nft_votes"
  schema = <<EOF
    [
      {
        "name": "address",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Address of vote"
      },
      {
        "name": "amount",
        "type": "FLOAT64",
        "mode": "REQUIRED",
        "description": "Amount of coins"
      },
      {
        "name": "px",
        "type": "STRING",
        "mode": "REPEATED",
        "description": "Value of pixels"
      },
      {
        "name": "verified",
        "type": "BOOL",
        "mode": "REQUIRED",
        "description": "Transaction verified"
      },
      {
        "name": "time",
        "type": "INT64",
        "mode": "REQUIRED",
        "description": "Timestamp-voting"
      }
    ]
    EOF
}
resource "google_bigquery_table" "nft_transactions" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "nft_transactions"
  schema = <<EOF
    [
      {
        "name": "address",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Address of vote"
      },
      {
        "name": "amount",
        "type": "FLOAT64",
        "mode": "REQUIRED",
        "description": "Amount of coins"
      },
      {
        "name": "matched",
        "type": "BOOL",
        "mode": "REQUIRED",
        "description": "Transaction matched"
      }
    ]
    EOF
}

#Upload file into buckets
module "handled_blocks"{
  source="./modules/cloudstorage_file"
  filename="handled_blocks.csv"
  filepath="${path.root}/../public/handled_blocks.csv"
  content_type ="text/csv"
  bucketname=google_storage_bucket.service_bucket.name
  entities=[]
  cache_control="no-store"
}

module "epochs_png"{
  source="./modules/cloudstorage_file"
  filename="epochs.png"
  filepath="${path.root}/../public/epochs.png"
  content_type ="image/png"
  bucketname=google_storage_bucket.app_bucket.name
  entities=["allUsers"]
  cache_control="no-store"
}

module "epoch_info"{
  source="./modules/cloudstorage_file"
  filename="epoch.json"
  filepath="${path.root}/../public/epoch.json"
  content_type ="application/json"
  bucketname=google_storage_bucket.app_bucket.name
  entities=["allUsers"]
  cache_control="no-store"
}
module "lead_vote"{
  source="./modules/cloudstorage_file"
  filename="lead_vote.json"
  filepath="${path.root}/../public/lead_vote.json"
  content_type ="application/json"
  bucketname=google_storage_bucket.app_bucket.name
  entities=["allUsers"]
  cache_control="no-store"
}
module "nft_temp_img"{
  source="./modules/cloudstorage_file"
  filename="nft_temp.png"
  filepath="${path.root}/../public/nft_temp.png"
  content_type ="image/png"
  bucketname=google_storage_bucket.app_bucket.name
  entities=["allUsers"]
  cache_control="no-store"
}

data "archive_file" "handle_vote" {
  type        = "zip"
  source_dir  = "../src/handle_vote" # Directory where your Python source code is
  output_path = "../generated/handle_vote/handle_vote.zip"
}

#Upload python package into bucket
resource "google_storage_bucket_object" "handle_vote" {  
  name   = "${data.archive_file.handle_vote.output_md5}.zip"
  bucket = google_storage_bucket.service_bucket.name
  source = "${path.root}/../generated/handle_vote/handle_vote.zip"
}

#Setup Lambda
resource "google_cloudfunctions_function" "handle_vote" {
  name        = "handle_vote"
  description = "handle vote"
  runtime     = "python37"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.service_bucket.name
  source_archive_object = google_storage_bucket_object.handle_vote.name
  trigger_http          = true
  entry_point           = "handle_vote"
  timeout               = 60
  labels                = {}
  environment_variables = {
    PROJECT_ID = var.project_name
    REGION = var.region
    SERVICE_BUCKET      = google_storage_bucket.app_bucket.name

  }
}

resource "google_cloudfunctions_function_iam_member" "handle_vote" {
  project        = google_cloudfunctions_function.handle_vote.project
  region         = google_cloudfunctions_function.handle_vote.region
  cloud_function = google_cloudfunctions_function.handle_vote.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

data "archive_file" "check_transactions" {
  type        = "zip"
  source_dir  = "../src/check_transactions" # Directory where your Python source code is
  output_path = "../generated/check_transactions/check_transactions.zip"
}

#Upload python package into bucket
resource "google_storage_bucket_object" "check_transactions" {  
  name   = "${data.archive_file.check_transactions.output_md5}.zip"
  bucket = google_storage_bucket.service_bucket.name
  source = "${path.root}/../generated/check_transactions/check_transactions.zip"
}

#Setup Lambda
resource "google_cloudfunctions_function" "check_transactions" {
  name        = "check_transactions"
  description = "check_transactions"
  runtime     = "python38"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.service_bucket.name
  source_archive_object = google_storage_bucket_object.check_transactions.name
  trigger_http          = true
  entry_point           = "check_transactions"
  timeout               = 120
  labels                = {}
  environment_variables = {
    PROJECT_ID = var.project_name
    REGION = var.region
    ETHERSCAN-API-KEY   = var.etherscan_api_key,
    POLYSCAN-API-KEY  = var.polyscan_api_key,
    DATA_BUCKET         = google_storage_bucket.service_bucket.name,
    SERVICE_BUCKET      = google_storage_bucket.app_bucket.name
  }
}

resource "google_cloudfunctions_function_iam_member" "check_transactions" {
  project        = google_cloudfunctions_function.check_transactions.project
  region         = google_cloudfunctions_function.check_transactions.region
  cloud_function = google_cloudfunctions_function.check_transactions.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.service_account.email}"
}

#Sheduler
resource "google_cloud_scheduler_job" "job_check_transactions" {
  name             = "trigger-check_transactions"
  description      = "Trigger the ${google_cloudfunctions_function.check_transactions.name} Cloud Function"
  schedule         = "*/5 * * * *" # Every 3 hours "3 */3 * * *"
  time_zone        = "Europe/Dublin"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    headers= {}
    uri         = google_cloudfunctions_function.check_transactions.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.service_account.email
      audience = google_cloudfunctions_function.check_transactions.https_trigger_url
    }
  }
}

resource "null_resource" "example2" {
  provisioner "local-exec" {
    command = " cd ${path.root}/../public/ && firebase deploy"
    
  }
}
