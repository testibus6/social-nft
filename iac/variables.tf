variable "project_name" {
   description = "The project ID where all resources will be launched."
  type = string
}
variable "region" {
  description = "The location region to deploy the Cloud IOT services."
  type        = string
}

variable "zone" {
  description = "The location zone to deploy the Cloud IOT services."
  type        = string
}

variable "environment" {
  description = "environment of deplyoment prod,dev,.."
  type        = string
}
variable "etherscan_api_key" {
  type = string
}