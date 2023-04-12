import boto3
from botocore.exceptions import WaiterError
from smart_open import open
import time
from datetime import datetime
#from background_task import background

def s3_download(src, dest): # pragma: no code
    ''' Download an object from the S3 bucket '''
    s3_client = boto3.client('s3')
    s3_client.download_file(Bucket="mapmind-ml-models", Key=src, Filename=dest)

#@background(schedule=1)
def s3_upload(src, dest): # pragma: no code
    ''' Upload an object to the S3 bucket '''
    s3_client = boto3.client('s3')
    s3_client.upload_file(Bucket="mapmind-ml-models", Key=dest, Filename=src)

def s3_delete_file(file): # pragma: no code
    ''' Delete an individual file from the S3 bucket '''
    s3_resource = boto3.resource('s3')
    try:
        s3_resource.Object("mapmind-ml-models", file).delete()
    except:
        print("error while deleteing file from s3", file)

#@background(schedule=1)
def s3_delete_folder(folder): # pragma: no code
    ''' Delete a folder from the S3 bucket, including all subfolders and files within it '''
    s3_resource = boto3.resource('s3')
    try:
        objects_to_delete = s3_resource.meta.client.list_objects(Bucket="mapmind-ml-models", Prefix=folder)
        delete_keys = {'Objects' : []}
        delete_keys['Objects'] = [{'Key' : k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]
        s3_resource.meta.client.delete_objects(Bucket='mapmind-ml-models', Delete=delete_keys)
    except:
        print("error while deleting folder from s3", folder)

#@background(schedule=1)
def s3_write(filename, contents): # pragma: no code
    ''' Write a file to the S3 bucket '''
    s3_client = boto3.client('s3')
    try:
        with open('s3://mapmind-ml-models/' + filename, mode='w', transport_params={'client':s3_client}) as f:
            f.write(contents)
    except:
        print("error while writing to s3")

def s3_read(filename): # pragma: no code
    ''' Read a file from the S3 bucket '''
    s3_client = boto3.client('s3')
    with open('s3://mapmind-ml-models/'+filename, mode='r', transport_params={'client': s3_client}) as f:
        contents = f.read()
    return contents

def notebook_update_files(notebook, notes_list):
    ''' Update notebook files by reading each note file and appending these together to create notebook vocab and corpus files '''
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
def move_file(src, dest): # pragma: no code
    ''' Move a file from one location to another in the S3 bucket '''
    s3_resource = boto3.resource('s3')
    try:
        s3_resource.Object('mapmind-ml-models', dest).copy_from(CopySource='mapmind-ml-models/' + src)
        s3_resource.Object('mapmind-ml-models', src).delete()
    except:
        print("error moving files")

def train_on_ec2(vocab_path, kv_path, kv_vectors_path):
    ''' Train a model on the EC2 instance to avoid high memory usage in Heroku.

    Requirements:
        FR#18 -- MachineLearning.Train

    Arguments:
        vocab_path -- path to the notebook vocabulary in S3
        kv_path -- path in S3 to the KeyedVectors file for the current notebook (.kv)
        kv_vectors_path -- path in S3 to the vectors file for the current notebook (.kv.vectors.npy)
    '''
    print("python3 train_model.py {} {} {}".format(vocab_path, kv_path, kv_vectors_path))
    ec2_id = "i-063cef059dc0f3ca7"
    ec2 = boto3.client("ec2", region_name='us-east-2')

    # start ec2 instance and wait for it to be in a Running state
    resp = ec2.start_instances(
        InstanceIds=[ec2_id]
    )
    waiter = ec2.get_waiter("instance_running")
    print("waiting for ec2 to start")
    try:
        waiter.wait(
            InstanceIds=[ec2_id]
        )
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return
    
    print("instance running")
    ec2 = boto3.client("ssm", region_name='us-east-2')

    # send train command to the ec2 instance and wait for it to finish
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
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return
    print("training on ec2 successful!")

def search_on_ec2(query, kv_path, kv_vectors_path, vocab_path, spellcheck, notesonly):
    ''' Perform search function on the EC2 instance to avoid high memory usage in Heroku.

    Requirements:
        FR#12 -- Search.Word
        FR#13 -- Update.Search
        FR#19 -- MachineLearning.Search

    Arguments:
        query -- the search terms
        kv_path -- path in S3 to the KeyedVectors file for the current notebook (.kv)
        kv_vectors_path -- path in S3 to the vectors file for the current notebook (.kv.vectors.npy)
        vocab_path -- the path to the notebook vocabulary in S3
        spellcheck -- a boolean value that is True if spellcheck is required, False if not
        notesonly -- a boolean value that is True if we are searching only in the user notes, False if we are searching in the entire model

    Returns:
        unique_filename -- a unique filename where the search results have been saved in S3 as a pickle file
    '''

    # convert to integer form for passing into function as command line arguments
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
    ec2 = boto3.client("ec2", region_name='us-east-2')
    
    # start ec2 instance and wait for it to be running
    resp = ec2.start_instances(
        InstanceIds=[ec2_id]
    )
    waiter = ec2.get_waiter("instance_running")
    print("waiting for ec2 to start")
    try:
        waiter.wait(
            InstanceIds=[ec2_id]
        )
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return
    print("instance running")

    # send command to the instance and wait for it to complete
    ec2 = boto3.client("ssm", region_name='us-east-2')
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
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return False
    print("searching on ec2 successful!")

    # get stdout from the ec2 command
    cmd_result = ec2.get_command_invocation(CommandId=command_id, InstanceId=ec2_id)
    print(cmd_result['StandardOutputContent'])
    unique_filename = cmd_result['StandardOutputContent'].strip()
    return unique_filename

def inspect_on_ec2(clicked_word, searched_words, corpus_path, kv_path, kv_vector_path):
    ''' Perform inspect node function on the EC2 instance to avoid high memory usage in Heroku.

    Requirements:
        FR#17 -- Inspect.Node

    Arguments:
        clicked_word -- the word that is being inspected
        searched_words -- the words that were searched
        corpus_path -- the path in S3 to the notebook corpus
        kv_path -- path in S3 to the KeyedVectors file for the current notebook (.kv)
        kv_vectors_path -- path in S3 to the vectors file for the current notebook (.kv.vectors.npy)

    Returns:
        results -- a list of strings, each representing a text sample from the corpus containing the clicked word
    '''
    searched_words = str.join(" ", searched_words)
    print(searched_words)
    searched_words_path = "internal-files/search_queries/{}.txt".format(str(datetime.now())).replace(" ","")
    s3_write(searched_words_path, searched_words)
    command_str = "python3 inspect_node.py {} {} {} {} {}".format(clicked_word, searched_words_path, corpus_path, kv_path, kv_vector_path)
    print(command_str)

    ec2_id = "i-063cef059dc0f3ca7"
    ec2 = boto3.client("ec2", region_name='us-east-2')

    # start ec2 instance and wait for it to be running
    resp = ec2.start_instances(
        InstanceIds=[ec2_id]
    )
    waiter = ec2.get_waiter("instance_running")
    print("waiting for ec2 to start")
    try:
        waiter.wait(
            InstanceIds=[ec2_id]
        )
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return
    print("instance running")

    # send command to ec2 and wait for it to finish
    ec2 = boto3.client("ssm", region_name='us-east-2')
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
    except WaiterError as ex: # pragma: no cover
        print(ex)
        return
    print("inspect on ec2 successful!")

    # read the results from ec2 stdout
    cmd_result = ec2.get_command_invocation(CommandId=command_id, InstanceId=ec2_id)
    print(cmd_result['StandardOutputContent'])
    results = cmd_result['StandardOutputContent'].strip().split("\n")
    print(results)
    return results
