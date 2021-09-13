#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 18:25:13 2021

@author: 
"""
import os
import json
import datetime
import time
project_id=os.environ.get("PROJECT_ID","")
region=os.environ.get("REGION","")
import json
import re
from google.cloud import bigquery
bigquery_client = bigquery.Client()
dataset_ref=None

BASE_PATH="/tmp/"
epoch_filename='epoch.json'
epoch_file_age=0
epoch=None
epoch_dataset=None
epoch_px=0
epoch_px_amount=0
epoch_times=dict() 
from google.cloud import storage
storage_client = storage.Client()
APP_BUCKET_NAME=os.getenv('SERVICE_BUCKET')

ip_counter=dict()

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:
        print(blob.name)
        if (blob.name == source_blob_name):
            # Construct a client side representation of a blob.
            # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
            # any content from Google Cloud Storage. As we don't need additional data,
            # using `Bucket.blob` is preferred here.
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
        
            print(
                "Blob {} downloaded to {}.".format(
                    source_blob_name, destination_file_name
                )
            )

def update_epoch():
    global epoch,epoch_file_age,epoch_dataset,epoch_px,epoch_px_amount,epoch_times
    if (time.time()-epoch_file_age > 30):
        download_blob(APP_BUCKET_NAME, epoch_filename, BASE_PATH+epoch_filename)
        with open(BASE_PATH+epoch_filename,"r") as f: 
            epoch_info=json.loads(f.read())
        epoch_file_age=time.time()
        epoch=epoch_info["epoch"]
        if not "epoch_"+str(epoch) in epoch_info:
            print("Last epoch is over- end of voting. Set epoch to last epoch")
            epoch=epoch-1
        epoch_px=epoch_info["epoch_"+str(epoch)]["px"]
        epoch_px_amount=epoch_px[1][0]-epoch_px[0][0]+1
        epoch_dataset="nft_epoch"+str(epoch)
        epoch_times=epoch_info["epoch_"+str(epoch)]["time"]

def check_duplicate_address_in_bigquery(address):
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    table_ref = dataset_ref.table("nft_votes")
    table = bigquery_client.get_table(table_ref)
    query_str="""
            SELECT 'address'
            FROM `create-nft.{epoch_dataset}.nft_votes`
            WHERE address='{address}'
            LIMIT 1 """.format(epoch_dataset=epoch_dataset,address=address)
    print(query_str)
    query_job = bigquery_client.query(query_str)
    results = query_job.result() # Wait for the job to complete.
    print(results.total_rows)
    if (results.total_rows==0):
        return False
    else:
        return True


def export_items_to_bigquery(address,amount,px_values):
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    table_ref = dataset_ref.table("nft_votes")
    table = bigquery_client.get_table(table_ref)
    timestamp=int(time.time()*1000)
    query_str="""
            INSERT `create-nft.{epoch_dataset}.nft_votes` (address,amount,px,verified,time)
            VALUES('{address}', {amount},{px},FALSE,{time})
            """.format(epoch_dataset=epoch_dataset,address=address,amount=amount,px=px_values,time=timestamp)
    print(query_str)
    query_job = bigquery_client.query(query_str)
    results = query_job.result() # Wait for the job to complete.

def check_cors(request):
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type,api-key',
            'Access-Control-Max-Age': '3600'
        }
        return headers
        
    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    return headers

def handle_vote(request):
    print(request)
    headers=check_cors(request) 
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    req_ip=request.headers.get("X-Forwarded-For","")
    if not(req_ip==""):
        ipcounter=ip_counter.get(str(req_ip),{}).get("counter",0)+1
        ip_counter[str(req_ip)]={"timestamp":int(time.time()),"counter":ipcounter}
        if ip_counter[str(req_ip)]["counter"] >10:
            if (time.time() - ip_counter[str(req_ip)]["timestamp"] < 5*60):
                return ('rate-limit-reached', 403, headers)
    print(request.args)
    data=request.get_json()
    update_epoch()
    try:
        if (all(key in data for key in ('address', 'amount','px')) and len (data["px"])==epoch_px_amount*epoch_px_amount):
            if (time.time()*1000 > epoch_times["start_epoch"] and time.time()*1000 < epoch_times["end_epoch"]):
                for px in data["px"]:
                    match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', px)
                    if not(match):                    
                        print('Hex is not valid')
                        return ('Invalid px-data.', 400, headers)
                print("handle vote")
                #store vote - unvalidated
                address=data["address"].lower()
                if not(check_duplicate_address_in_bigquery(address)):
                    export_items_to_bigquery(address,data["amount"],data["px"])
                    return ('okay', 200, headers)
                return ('Address already submitted a vote this epoch. Please use another address or wait for next epoch', 400, headers)
            else:
                print("Start: ",epoch_times["start_epoch"]," End ",epoch_times["end_epoch"])
                return ('Voting for this epoch is closed. Retry later', 400, headers)
        else:
            return ('Missing or invalid input data.', 400, headers)
    except:
        return ('not-okay', 403, headers)

        
    
