import boto3
from smart_open import open
#from background_task import background

def s3_download(src, dest):
    s3_client = boto3.client('s3')
    try: 
        print("Downloading file from s3: ", src, " to ", dest)
        s3_client.download_file(Bucket="mapmind-ml-models", Key=src, Filename=dest)
    except Exception as e:
        print("AWS Exception: ", e)

#@background(schedule=1)
def s3_upload(src, dest):
    s3_client = boto3.client('s3')
    s3_client.upload_file(Bucket="mapmind-ml-models", Key=dest, Filename=src)

def s3_delete_file(file):
    s3_resource = boto3.resource('s3')
    s3_resource.Object("mapmind-ml-models", file).delete()

#@background(schedule=1)
def s3_delete_folder(folder):
    s3_resource = boto3.resource('s3')
    objects_to_delete = s3_resource.meta.client.list_objects(Bucket="mapmind-ml-models", Prefix=folder)
    delete_keys = {'Objects' : []}
    delete_keys['Objects'] = [{'Key' : k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]
    s3_resource.meta.client.delete_objects(Bucket='mapmind-ml-models', Delete=delete_keys)

#@background(schedule=1)
def s3_write(filename, contents):
    s3_client = boto3.client('s3')
    with open('s3://mapmind-ml-models/' + filename, mode='w', transport_params={'client':s3_client}) as f:
        f.write(contents)

def s3_read(filename):
    s3_client = boto3.client('s3')
    with open('s3://mapmind-ml-models/'+filename, mode='r', transport_params={'client': s3_client}) as f:
        contents = f.read()
    return contents

def notebook_update_files(notebook, notes_list):
    vocab = ""
    corpus = ""
    for note in notes_list:
        vocab += s3_read(note.vocab) + " "
        corpus += s3_read(note.corpus) + " "
    # update notebook text files on s3
    # do this now, don't do it in background because we need it updated right away
    s3_write(notebook.vocab, vocab.strip())
    s3_write(notebook.corpus, corpus.strip())

#@background(schedule=1)
def move_file(src, dest):
    s3_resource = boto3.resource('s3')
    s3_resource.Object('mapmind-ml-models', dest).copy_from(CopySource='mapmind-ml-models/' + src)
    s3_resource.Object('mapmind-ml-models', src).delete()