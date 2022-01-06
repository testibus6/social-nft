variable "filename" {
  description = "The name of the file"
  type        = string
}
variable "bucketname" {
  description = "The name of the bucket for the file"
  type        = string
}
variable "filepath" {
  description = "The local path of the file"
  type        = string
}

variable "content_type" {
  description = "The content-type of the file"
  type        = string
  default = "text/plain; charset=utf-8"
}

variable "cache_control" {
  description = "The cache_control for the file"
  type        = string
}

variable "entities" {
  description = "The access-entities for the file"
  type        = list(string)
}