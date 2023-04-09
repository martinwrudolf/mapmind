import boto3
from botocore.exceptions import WaiterError
from smart_open import open
import time
from datetime import datetime
#from background_task import background

def s3_download(src, dest):
    s3_client = boto3.client('s3')
    s3_client.download_file(Bucket="mapmind-ml-models", Key=src, Filename=dest)

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

def train_on_ec2(vocab_path, kv_path, kv_vectors_path):
    print("python3 train_model.py {} {} {}".format(vocab_path, kv_path, kv_vectors_path))
    ec2_id = "i-063cef059dc0f3ca7"
    ec2 = boto3.client("ssm", region_name='us-east-2')

    resp = ec2.send_command(
        InstanceIds=[ec2_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands':["su ec2-user", 
                                "cd /home/ec2-user", 
                                "source /home/ec2-user/mapmind/env/bin/activate", 
                                "python3 train_model.py {} {} {}".format(vocab_path, kv_path, kv_vectors_path)]
                    })
    command_id = resp['Command']['CommandId']
    print(command_id)

    waiter = ec2.get_waiter("command_executed")
    try:
        waiter.wait(
            CommandId=command_id,
            InstanceId=ec2_id,
        )
    except WaiterError as ex:
        print(ex)
        return
    print("training on ec2 successful!")

def search_on_ec2(query, kv_path, kv_vectors_path, vocab_path, spellcheck, notesonly):
    if spellcheck:
        spellcheck = 1
    else:
        spellcheck = 0
    if notesonly:
        notesonly = 1
    else:
        notesonly = 0
    query = str.join(" ", query)
    print(query)
    query_path = "internal-files/search_queries/{}.txt".format(str(datetime.now())).replace(" ","")
    s3_write(query_path, query)
    command_str = "python3 search.py {} {} {} {} {} {}".format(query_path, kv_path, kv_vectors_path, vocab_path, spellcheck, notesonly)
    print(command_str)
    ec2_id = "i-063cef059dc0f3ca7"
    ec2 = boto3.client("ssm")

    resp = ec2.send_command(
        InstanceIds=[ec2_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands':["su ec2-user", 
                                "cd /home/ec2-user", 
                                "source /home/ec2-user/mapmind/env/bin/activate", 
                                command_str]
                    },
        OutputS3BucketName='mapmind-ml-models',
        OutputS3KeyPrefix='internal-files/search_results',
        )
    command_id = resp['Command']['CommandId']
    print(command_id)

    waiter = ec2.get_waiter("command_executed")
    try:
        waiter.wait(
            CommandId=command_id,
            InstanceId=ec2_id,
        )
    except WaiterError as ex:
        print(ex)
        return False
    print("searching on ec2 successful!")
    cmd_result = ec2.get_command_invocation(CommandId=command_id, InstanceId=ec2_id)
    print(cmd_result['StandardOutputContent'])
    unique_filename = cmd_result['StandardOutputContent'].strip()
    return unique_filename

def inspect_on_ec2(clicked_word, searched_words, corpus_path, kv_path, kv_vector_path):
    searched_words = str.join(" ", searched_words)
    print(searched_words)
    searched_words_path = "internal-files/search_queries/{}.txt".format(str(datetime.now())).replace(" ","")
    s3_write(searched_words_path, searched_words)
    command_str = "python3 inspect_node.py {} {} {} {} {}".format(clicked_word, searched_words_path, corpus_path, kv_path, kv_vector_path)
    print(command_str)
    ec2_id = "i-063cef059dc0f3ca7"
    ec2 = boto3.client("ssm")

    resp = ec2.send_command(
        InstanceIds=[ec2_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands':["su ec2-user", 
                                "cd /home/ec2-user", 
                                "source /home/ec2-user/mapmind/env/bin/activate", 
                                command_str]
                    },
        OutputS3BucketName='mapmind-ml-models',
        OutputS3KeyPrefix='internal-files/search_results',
        )
    command_id = resp['Command']['CommandId']
    print(command_id)

    waiter = ec2.get_waiter("command_executed")
    try:
        waiter.wait(
            CommandId=command_id,
            InstanceId=ec2_id,
        )
    except WaiterError as ex:
        print(ex)
        return False
    print("inspect on ec2 successful!")
    cmd_result = ec2.get_command_invocation(CommandId=command_id, InstanceId=ec2_id)
    print(cmd_result['StandardOutputContent'])
    results = cmd_result['StandardOutputContent'].strip().split("\n")
    print(results)
    return results
