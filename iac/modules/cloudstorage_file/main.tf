resource "google_storage_bucket_object" "file" {  
  name   = "${var.filename}"
  bucket = var.bucketname
  source = "${var.filepath}"
  content_type ="${var.content_type}"
  cache_control = "${var.cache_control}"
}

resource "google_storage_object_access_control" "file" {
  bucket = var.bucketname
  object = google_storage_bucket_object.file.output_name
  role   = "READER"
  count= length(var.entities)
  entity = "${var.entities[count.index]}"
  depends_on = [
    google_storage_bucket_object.file
  ]
}
