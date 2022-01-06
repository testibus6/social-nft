#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 18:25:13 2021

@author: 
"""

CHAIN="POLYGON"
TARGET_ADDRESS="0x703091392E1BEa715d9F93DaB57DAfA8bB0f45bF".lower()
EPOCH_COOLDOWN=1*3600*1000
T0=1631541640

import csv
import time

import os
import json
import sys
from google.api_core.exceptions import Conflict
#from web3.types import Timestamp

if(CHAIN=="ETHERUM"):
    #etherscan-python
    from etherscan import Etherscan
    #eth = Etherscan(os.getenv('ETHERSCAN-API-KEY'),net='kovan')
    blockchain_client = Etherscan(os.getenv('ETHERSCAN-API-KEY'))

if(CHAIN=="POLYGON"):
    #pip install polygonscan-python
    from polygonscan import PolygonScan
    #blockchain_client = PolygonScan(os.getenv('POLYSCAN-API-KEY')) # key in quotation marks
    from polygonscan.core.sync_client import SyncClient
    from requests import Session
    blockchain_client = SyncClient.from_session(
            api_key=os.getenv('POLYSCAN-API-KEY'),
            session=Session(),
        )
init_block=blockchain_client.get_block_number_by_timestamp(timestamp=T0, closest="before")

WEI=1000000000000000000
from google.cloud import storage
storage_client = storage.Client()
PROJECT_NAME="create-nft"
BUCKET_NAME=os.getenv('DATA_BUCKET')
APP_BUCKET_NAME=os.getenv('SERVICE_BUCKET')
REGION=os.environ.get("REGION","")


from google.cloud import bigquery
bigquery_client = bigquery.Client()
epoch_filename='epoch.json'
epoch_file_age=0
epoch=None
epoch_dataset=None
epoch_times=dict()
epoch_px=list()
epoch_time=dict()

BASE_PATH="/tmp/"
block_file='handled_blocks.csv'


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:
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

def upload_blob(bucket_name, source_file_name, destination_blob_name,public):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.cache_control = 'no-store'
    blob.upload_from_filename(source_file_name)
    if(public):
        blob.make_public()

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

def increase_epoch():    
    download_blob(APP_BUCKET_NAME, epoch_filename, BASE_PATH+epoch_filename)
    with open(BASE_PATH+epoch_filename,"r") as f: 
        epoch_info=json.loads(f.read())
    try:
        #generate dataset for next epoch    
        dataset = bigquery.Dataset(PROJECT_NAME+".nft_epoch"+str(epoch_info["epoch"]+1))
        dataset.location = REGION
        dataset = bigquery_client.create_dataset(dataset, timeout=30)  # Make an API request.


        #generate table-votes for next epoch
        table_id = PROJECT_NAME+".nft_epoch"+str(epoch_info["epoch"]+1)+".nft_votes"
        schema = [
            bigquery.SchemaField("address", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("amount", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("px", "STRING", mode="REPEATED"),
            bigquery.SchemaField("verified", "BOOL", mode="REQUIRED"),
            bigquery.SchemaField("time", "INT64", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table = bigquery_client.create_table(table)  # Make an API request.

        #generate table-transactions for next epoch
        table_id = PROJECT_NAME+".nft_epoch"+str(epoch_info["epoch"]+1)+".nft_transactions"
        schema = [
            bigquery.SchemaField("address", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("amount", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("matched", "BOOL", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table = bigquery_client.create_table(table)  # Make an API request.
    except Conflict:
        print("duplicated epoch-dataset")
    epoch_info["epoch"]=1+epoch_info["epoch"]
    with open(BASE_PATH+epoch_filename, 'w') as f:
        json.dump(epoch_info, f)
    upload_blob(APP_BUCKET_NAME, BASE_PATH+epoch_filename, epoch_filename,public=True)

def end_epoch():
    update_epoch()
    print("End of epoch ",epoch_time["end_epoch"],"time",epoch)
    if (time.time()*1000 >  epoch_time["end_epoch"]+EPOCH_COOLDOWN):
        #get winner 
        winner_vote=get_biggest_voter()
        # updat image - to do at end of epoch
        update_nft(winner_vote)
        #reset biggest vote 
        reset_biggest_voter()
        #create new epoch
        increase_epoch()
    elif(time.time()*1000 >  epoch_time["end_epoch"]):
        print("Timeslot for transactions not over")
    else:
        print("Current epoch not over")
        

def update_file(time_now,last_block):
    csv_row=list()
    csv_row.append(time_now)
    csv_row.append(last_block)    
    csv_row.append(epoch)    
    with open(BASE_PATH+block_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(csv_row)
    upload_blob(BUCKET_NAME, BASE_PATH+block_file, block_file,public=False)

def get_last_handled_block():
    try:
        download_blob(BUCKET_NAME, block_file, BASE_PATH+block_file)
        f=open(BASE_PATH+block_file,"r")
        block_info=f.read()
        data=block_info.split("\n")[-2].split(",")
        return int(data[1])
    except ValueError:
        return 
    except IOError:        
        return init_block

def get_last_transactions(start_block,last_block):
    print("start: ",start_block," end-block: ",last_block)
    try:
        transactions=blockchain_client.get_normal_txs_by_address(TARGET_ADDRESS,start_block,last_block,"asc")
        print(transactions)
    except:
        transactions=list()
    return transactions

def remove_duplicate_transactions():
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_votes = dataset_ref.table("nft_votes")
    #table_ref_transactions = dataset_ref.table("nft_transactions")
    #table = bigquery_client.get_table(table_ref_votes)
    query_str="""
            CREATE OR REPLACE TABLE `{project_name}.{epoch_dataset}.nft_transactions_red`
            AS SELECT DISTINCT * FROM `{project_name}.{epoch_dataset}.nft_transactions`
           """.format(project_name=PROJECT_NAME,epoch_dataset=epoch_dataset)
    print(query_str)
    query_job = bigquery_client.query(query_str) 
    results = query_job.result() # Wait for the job to complete.


def match_transactions_with_votes_in_bigquery():
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_votes = dataset_ref.table("nft_votes")
    #table_ref_transactions = dataset_ref.table("nft_transactions")
    #table = bigquery_client.get_table(table_ref_votes)
    query_str="""
            UPDATE `{project_name}.{epoch_dataset}.nft_transactions` t
            SET matched = true
            FROM `{project_name}.{epoch_dataset}.nft_votes` v
            WHERE v.address = t.address AND v.amount = t.amount """.format(project_name=PROJECT_NAME,epoch_dataset=epoch_dataset)
    print(query_str)
    query_job = bigquery_client.query(query_str) 
    results = query_job.result() # Wait for the job to complete.

def get_number_verfied_votes():
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_votes = dataset_ref.table("nft_votes")
    #table = bigquery_client.get_table(table_ref_votes)
    query_str='''SELECT * FROM `{project_name}.{epoch_dataset}.nft_votes` WHERE verified=TRUE'''.format(project_name=PROJECT_NAME,epoch_dataset=epoch_dataset)
    query_job = bigquery_client.query(query_str) 
    results = query_job.result() # Wait for the job to complete.
    print("verfied votes",results.total_rows)
    return results.total_rows


def get_biggest_voter():
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_votes = dataset_ref.table("nft_votes")
    #table = bigquery_client.get_table(table_ref_votes)
    query_str='''SELECT * FROM `{project_name}.{epoch_dataset}.nft_votes` WHERE verified=TRUE  ORDER BY amount DESC, time ASC LIMIT 1'''.format(project_name=PROJECT_NAME,epoch_dataset=epoch_dataset)
    query_job = bigquery_client.query(query_str) 
    results = query_job.result() # Wait for the job to complete.
    print(results)
    for result in results:
        print(result)
        return result
    return None


from PIL import Image
from PIL import ImageColor
import random
def update_nft(vote):
    nft_filename="nft_temp.png"
    download_blob(APP_BUCKET_NAME, nft_filename, BASE_PATH+nft_filename)
    im = Image.open(BASE_PATH+nft_filename) # Can be many different formats.
    pix = im.load()
    left_top=epoch_px[0]
    right_bottom=epoch_px[1]
    tile_size=right_bottom[0]-left_top[0]+1

    if (vote ==None):
        vote=dict()
        vote["px"]=list()
        for x in range(int(tile_size)):
            for y in range(int(tile_size)):
                vote["px"].append("#{:06x}".format(random.randint(0, 0xFFFFFF)))              
    counter=0 
    for y in range(int(tile_size)):
        for x in range(int(tile_size)):
            px=vote.get("px")[counter]
            pix[x+left_top[0],y+left_top[1]] = ImageColor.getcolor(px, "RGB")  # Set the RGBA Value of the image (tuple)
            counter=counter+1
    im.save(BASE_PATH+nft_filename)  # Save the modified pixels as .png
    upload_blob(APP_BUCKET_NAME, BASE_PATH+nft_filename, nft_filename,public=True)
    #Store winner
    vote={
        "address":vote.get("address","dummy"),
        "amount":vote.get("amount",0),
        "px":vote.get("px"),
        "timestamp":int(time.time()*1000)
        }
    vote_file="lead_vote"+str(epoch)+".json"
    with open(BASE_PATH+vote_file, 'w') as f:
        json.dump(vote, f)
    upload_blob(APP_BUCKET_NAME, BASE_PATH+vote_file, vote_file,public=False)

def reset_biggest_voter():
    vote_file="lead_vote.json"
    vote={
        #"address":result_vote.get("address"),
        "amount":0,
        "px":"",
        "timestamp":int(time.time()*1000),
        "verfied_votes":0
        }
    with open(BASE_PATH+vote_file, 'w') as f:
        json.dump(vote, f)
    upload_blob(APP_BUCKET_NAME, BASE_PATH+vote_file, vote_file,public=True)

def update_epoch():
    global epoch,epoch_file_age,epoch_dataset,epoch_px,epoch_time
    if (time.time()-epoch_file_age > 30):
        #storage_client = storage.Client()
        download_blob(APP_BUCKET_NAME, epoch_filename, BASE_PATH+epoch_filename)
        with open(BASE_PATH+epoch_filename,"r") as f: 
            epoch_info=json.loads(f.read())
        epoch_file_age=time.time()
        try:
            epoch=epoch_info["epoch"]
            epoch_dataset="nft_epoch"+str(epoch)
            epoch_px=epoch_info["epoch_"+str(epoch)]["px"]
            epoch_time=epoch_info["epoch_"+str(epoch)]["time"]
            return True
        except:
            print("Last Episode. Use previous epoch-values")
            epoch=epoch_info["epoch"]-1
            epoch_dataset="nft_epoch"+str(epoch)
            epoch_px=epoch_info["epoch_"+str(epoch)]["px"]
            epoch_time=epoch_info["epoch_"+str(epoch)]["time"]
            return False


def store_biggest_voter(result_vote):
    verfied_votes=get_number_verfied_votes()
    vote_file="lead_vote.json"
    if (result_vote ==None):
        vote={
        #"address":result_vote.get("address"),
        "amount":0,
        "px":"",
        "timestamp":int(time.time()*1000),
        "verfied_votes":verfied_votes
        }
    else:
        vote={
            #"address":result_vote.get("address"),
            "amount":result_vote.get("amount",0),
            "px":result_vote.get("px",[]),
            "timestamp":int(time.time()*1000),
            "verfied_votes":verfied_votes
            }
    with open(BASE_PATH+vote_file, 'w') as f:
        json.dump(vote, f)
    upload_blob(APP_BUCKET_NAME, BASE_PATH+vote_file, vote_file,public=True)

def update_votes_in_bigquery():
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_votes = dataset_ref.table("nft_votes")
    #table = bigquery_client.get_table(table_ref_votes)
    query_str="""
            UPDATE `{project_name}.{epoch_dataset}.nft_votes` v
            SET verified = true
            FROM `{project_name}.{epoch_dataset}.nft_transactions_red` t
            WHERE v.address = t.address AND v.amount = t.amount AND t.matched= TRUE""".format(project_name=PROJECT_NAME,epoch_dataset=epoch_dataset)
    print(query_str)
    query_job = bigquery_client.query(query_str) 
    results = query_job.result() # Wait for the job to complete.

def export_transactions_to_bigquery(transactions):
    dataset_ref = bigquery_client.dataset(epoch_dataset)
    #table_ref_transactions = dataset_ref.table("nft_transactions")
    #table = bigquery_client.get_table(table_ref_transactions)

    if len(transactions)>0:
        query_str="""INSERT `{project_name}.{epoch_dataset}.nft_transactions` (address,amount,matched) VALUES""".format(epoch_dataset=epoch_dataset)
        for transaction in transactions:            
            query_str=query_str+"""('{address}', {amount},FALSE),""".format(address=transaction["from"].lower(),amount=int(transaction["value"])/WEI)
        query_str=query_str[:-1]#remove last comma
        print(query_str)
        query_job = bigquery_client.query(query_str) 
        results = query_job.result() # Wait for the job to complete.
    else:
        print("No transactions to submit")


def check_transactions(request):
    ret= update_epoch()
    time_now=int(time.time()*1000)
    
    #get last handled block
    last_block=get_last_handled_block()

    if(time_now > EPOCH_COOLDOWN+epoch_time["end_epoch"]):
        #Set maximum time to end-epoch+overlap
        time_now=EPOCH_COOLDOWN+epoch_time["end_epoch"]

    #get last blockchain-block
    current_block=blockchain_client.get_block_number_by_timestamp(timestamp=int(time_now/1000), closest="before")
    if(type(current_block)==str):
        time.sleep(1)
        current_block=blockchain_client.get_block_number_by_timestamp(timestamp=int(time_now/1000), closest="before")

    if(type(current_block)!=str):
        #get all incoming transactions of address
        transactions=get_last_transactions(last_block,current_block)

        #enter all transactions into bigquery
        export_transactions_to_bigquery(transactions)

        #mark matched transactions
        match_transactions_with_votes_in_bigquery()

        remove_duplicate_transactions()

        #update bigquery in batch
        update_votes_in_bigquery()

        #get current lead-vote 
        lead_vote=get_biggest_voter()

        #store-current lead vote
        store_biggest_voter(lead_vote)
        #upload update file with last block
        update_file(time_now,current_block)

        end_epoch()
    else:
        print("TO DO : Alert dev")