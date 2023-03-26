import boto3
from smart_open import open

def s3_download(s3_client, src, dest):
    s3_client.download_file(Bucket="mapmind-ml-models", Key=src, Filename=dest)

def s3_upload(s3_client, src, dest):
    s3_client.upload_file(Bucket="mapmind-ml-models", Key=dest, Filename=src)

def s3_delete_file(s3_resource, file):
    s3_resource.Object("mapmind-ml-models", file).delete()

def s3_delete_folder(s3_resource, folder):
    objects_to_delete = s3_resource.meta.client.list_objects(Bucket="mapmind-ml-models", Prefix=folder)
    delete_keys = {'Objects' : []}
    delete_keys['Objects'] = [{'Key' : k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]
    s3_resource.meta.client.delete_objects(Bucket='mapmind-ml-models', Delete=delete_keys)

def s3_write(s3_client, filename, contents):
    with open('s3://mapmind-ml-models/' + filename, mode='w', transport_params={'client':s3_client}) as f:
        f.write(contents)

def s3_read(s3_client, filename):
    with open('s3://mapmind-ml-models/'+filename, mode='r', transport_params={'client': s3_client}) as f:
        contents = f.read()
    return contents