import gpt_2_simple as gpt2
import shutil
from google.cloud import bigquery
from google.cloud import storage

import os
import datetime

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f'File {source_file_name} uploaded to {destination_blob_name}.')

def rename_blob(bucket_name, blob_name, new_name):
    """Renames a blob."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    new_blob = bucket.rename_blob(blob, new_name)

    print(f'Blob {blob.name} has been renamed to {new_blob.name}')

def list_blobs(bucket_name, prefix):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)

    return blobs

#
# Get the Data
#

client = bigquery.Client()

query = (
    "SELECT article FROM `" + os.environ['PROJECT_ID'] + ".clnn.news`"
)
query_job = client.query(
    query,
)

articles = ""
for row in query_job:
    articles = articles + row.article

textfile = open('clnn.txt', 'w')
textfile.write(articles)
textfile.close()

#
# Finetune the model on the new data
#

model_name = "124M"
gpt2.download_gpt2(model_name=model_name)   # model is saved into current directory under /models/124M/

sess = gpt2.start_tf_sess()
gpt2.finetune(sess,
              'clnn.txt',
              model_name=model_name,
              steps=5)   # steps is max number of training steps

#
# Archive and version the model and upload to storage
#


bucket_name = os.environ['ML_MODELS_BUCKET']
datetime_now = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
model_name = f"clnn_news_{datetime_now}.zip.latest"
bucket_prefix = 'clnn-news'

print(f"Finding previous version in bucket {bucket_name} ...")
blob_names = list_blobs(bucket_name, bucket_prefix)

previous_model_old_name = ""
previous_model_new_name = ""
for blob in blob_names:
    if blob.name.find(".latest", -8) > 0:
        previous_model_old_name = blob.name
        previous_model_new_name = blob.name.replace(".latest","")
        print(f"Renaming previous version {previous_model_old_name} to {previous_model_new_name} ...")
        rename_blob(bucket_name, previous_model_old_name, previous_model_new_name)

destination_blob_name = f"{bucket_prefix}/{model_name}"
print(f"Uploading {model_name} to bucket {bucket_name} as {destination_blob_name} ...")
# zip the model dir and upload to storage
shutil.make_archive('model_archive', 'zip', 'checkpoint')
upload_blob(bucket_name,'model_archive.zip',destination_blob_name)

#
# Generate some text for good measure
#

gpt2.generate(sess)
