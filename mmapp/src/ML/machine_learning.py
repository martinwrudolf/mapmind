import docx
import csv
import numpy as np
from collections import Counter
from nltk.corpus import brown
from mittens import GloVe, Mittens
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors
import string
import pickle
import json
import time
import os, sys, glob
from spellchecker import SpellChecker
from nltk.stem import WordNetLemmatizer
import boto3
from io import TextIOWrapper
from smart_open import open

# This is the real machine learning code! woo

# PROCESS USER NOTES
def process_user_notes(notefile, keys):
    ''' Process a user note file to prepare it for machine learning model training.

    Requirements:
        FR#7 -- Upload.Notes
        FR#18 -- MachineLearning.Train

    Arguments:
        notefile -- a file object, either .docx or .txt format, to be processed
        keys -- the keys from the original embeddings (this is used to find oov words)

    Returns:
        oov -- out of vocabulary words contained in this note file
        vocab_scrubbed -- the vocabulary of the user notes, scrubbed to remove stop words and punctuation
        corpus -- the entire user note file in string form
        pics_or_tables -- a boolean value representing whether there are any images or tables in the document, which are automatically skipped
    '''

    # initial translations
    tmp_dict = dict.fromkeys(string.punctuation.replace('-',''))
    # adding because apparently there are different apostrophes smh
    tmp_dict['/'] = ' '
    tmp_dict['’'] = ''
    tmp_dict['`'] = ''
    translator = str.maketrans(tmp_dict)        # map punctuation to space
    corpus = ""
    pics_or_tables = False
    if notefile.content_type in ['application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf']:
        # handling docx files
        doc = docx.Document(notefile)

        docText = []
        for para in doc.paragraphs:
            if len(para.text) > 0:
                print("not text so skipping")
                pics_or_tables = True
            else:
                docText.append(para.text)
        
        for sentence in docText:
            sentence = sentence.translate(translator)
            for word in sentence.split():
                word = word.strip('-')
                corpus+=word.lower()
                corpus+=" "
    elif notefile.content_type == 'text/plain':
        text_f = TextIOWrapper(notefile, encoding='utf-8')
        notes_str = text_f.read()
        notes_str = notes_str.translate(translator)
        for word in notes_str.split():
            # remove '-' if it is on either end of the word; keep it if it is in the middle
            word = word.strip('-')
            corpus += word.lower()
            corpus += " "

    # remove stop words
    vocab_scrubbed = remove_stop_words(corpus)
    # find oov
    oov = [token for token in vocab_scrubbed.split() if token not in keys]
    oov = list(set(oov))
    return oov, vocab_scrubbed, corpus.strip(), pics_or_tables
    
def remove_stop_words(corpus):
    ''' Remove stop words from a corpus.

    Requirements:
        Used in process_user_notes() function.

    Arguments:
        corpus -- a string containing the entire user note file with punctuation removed

    Returns:
        vocab_scrubbed_str -- a string representing the vocabulary for the corpus with any stop words removed
    '''
    stopwords = list(ENGLISH_STOP_WORDS)
    #translator = str.maketrans(dict.fromkeys(string.punctuation))
    vocab_scrubbed = [token.lower() for token in corpus.split() if (token.lower() not in stopwords and token != '')]
    vocab_scrubbed_str = ' '.join(word for word in vocab_scrubbed)
    return vocab_scrubbed_str

def load_embeddings_from_txt(path2txt):
    ''' Load NLP word embeddings from a text file. This is for creating the GloVe embedding file outside of the application.'''
    with open(path2txt, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
        embed = {line[0]: list(map(float,line[1:])) for line in reader}
    return embed

def save_embeddings(embed, path2pkl):
    ''' Save word embeddings to a pickle file. '''
    with open(path2pkl,"wb") as f:
        pickle.dump(embed,f)

def load_embeddings(path2pkl):
    ''' Load word embeddings from a pickle file. '''
    with open(path2pkl, "rb") as f:
        embed = pickle.load(f)
    return embed

# https://towardsdatascience.com/fine-tune-glove-embeddings-using-mittens-89b5f3fe4c39
def create_cooccurrence(vocab_scrubbed, oov):
    ''' Create a co-occurrence matrix on a set of notes. This matrix is needed for later training steps.

    Requirements:
        FR#18 -- MachineLearning.Train

    Arguments:
        vocab_scrubbed -- a string containing the vocabulary for the user notes with all stop words removed
        oov -- a list of the words from the user notes that are not already in the model

    Returns:
        coocc_arr -- a matrix of the co-occurrences of each word in the user vocabulary
    '''
    #my_doc = [' '.join(vocab_scrubbed)]
    #new_oov = oov.split()
    cv = CountVectorizer(ngram_range=(1,1), vocabulary=oov)
    X = cv.fit_transform([vocab_scrubbed])
    Xc = (X.T * X)
    Xc.setdiag(0)
    coocc_arr = Xc.toarray()
    return coocc_arr

# https://towardsdatascience.com/fine-tune-glove-embeddings-using-mittens-89b5f3fe4c39
def train_mittens(coocc_arr, oov, embed):
    ''' Fine-tune the GloVe model on a set of user notes.

    Requirements:
        FR#18 -- MachineLearning.Train

    Arguments:
        coocc_arr -- a matrix of the co-occurrences of each word in the user vocabulary
        oov -- a list of the words from the user notes that are not already in the model
        embed -- the original GloVe embeddings as a dictionary

    Returns:
        embed -- the updated version of the embeddings with the oov words inserted
    '''
    model = Mittens(n=300, max_iter=1000)
    new_embed = model.fit(
        coocc_arr,
        vocab=oov,
        initial_embedding_dict=embed
    )
    result_embed = dict(zip(oov, new_embed))
    embed.update(result_embed)
    return embed

def create_kv_from_embed(embed):
    ''' Create a KeyedVectors object from a dictionary. '''
    kv = KeyedVectors(300)
    kv.add_vectors(list(embed.keys()), list(embed.values()))
    return kv

def save_kv(kv, path2model):
    ''' Save a KeyedVectors object to a given path. '''
    kv.save(path2model)

def load_kv(path2model):
    ''' Load a KeyedVectors object. '''
    kv = KeyedVectors.load(path2model)
    return kv

def search(searched_words, kv, num_results, vocab):
    ''' Fine-tune the GloVe model on a set of user notes.

    Requirements:
        FR#12 -- Search.Word
        FR#13 -- Update.Search
        FR#19 -- MachineLearning.Search

    Arguments:
        searched_words -- a list of words that were searched
        kv -- the KeyedVectors object representing the model for the current notebook
        num_results -- the number of results to retrieve for each search term
        vocab -- the vocabulary of the user notes; if None, we displaying results from the entire model

    Returns:
        results_matrix -- a matrix of the similarity values between each result word
        result_words -- a list of the result words, including search terms
        skipwords -- a list of the words that were skipped because they were not in the model
    '''
    n = 10000
    result_words = []
    skipwords = []
    if vocab:
        vocab_list = vocab.split()
    for word in searched_words:
        # for each word do the search
        # search for more words than we need because we are filtering by words in our vocab
        try:
            similar_words = kv.most_similar(positive=word, topn=n)
        except:
            # word not in model, probably misspelled or super weird obscure word
            # just skip it
            skipwords.append(word)
            continue
        if word not in result_words:
            result_words.append(word)
        count = 0
        for sim_word, sim_val in similar_words:
            if vocab:
                if sim_word in vocab_list and sim_word not in result_words and sim_word not in searched_words:
                    result_words.append(sim_word)
                    count+=1
                if count == num_results:
                    break
            else:
                if sim_word not in result_words and sim_word not in searched_words:
                    result_words.append(sim_word)
                    count+=1
                if count == num_results:
                    break
    if len(result_words) == 1:
        # didn't get enough results
        # do again with like all the words
        similar_words = kv.most_similar(result_words[0],topn=400000)
        for sim_word, sim_val in similar_words:
            if vocab:
                if sim_word in vocab_list and sim_word not in result_words and sim_word not in searched_words:
                    result_words.append(sim_word)
                    count+=1
                if count == num_results:
                    break
            else:
                if sim_word not in result_words and sim_word not in searched_words:
                    result_words.append(sim_word)
                    count+=1
                if count == num_results:
                    break

    # NUMPY ARRAYS: (ROW, COLUMN) OR [ROW][COLUMN]
    nrows = len(result_words)

    results_matrix = np.zeros(shape=(nrows,nrows), dtype=object)

    # now we have list of all the words that will be displayed
    for i in range(nrows):
        for j in range(nrows):
            results_matrix[i][j] = kv.similarity(result_words[i],result_words[j])

    return results_matrix, result_words, skipwords

def inspect_node(word, searched_words, user_notes, kv, num_results=10):
    ''' Given a single word, find a list of text samples from the full corpus where that word is found.

    Requirements:
        FR#17 -- Inspect.Node

    Arguments:
        word -- the word that was clicked
        searched_words -- a list of words that were searched
        user_notes -- the full user corpus
        kv -- the KeyedVectors object representing the model for the current notebook
        num_results -- the number of results to display

    Returns:
        results -- a list of text sample strings from the corpus
    '''
    # get indices for all searched words
    user_notes = user_notes.split()
    searched_words_dict = {}
    clicked_word = [i for i,x in enumerate(user_notes) if x==word]

    # which word is closest?
    search_sorted_by_sim = []
    for search in searched_words:
        sim = kv.similarity(word, search)
        search_sorted_by_sim.append((search, sim))
        searched_words_dict[search] = [i for i, x in enumerate(user_notes) if x == search]

    search_sorted_by_sim.sort(key=lambda a: a[1], reverse=True)

    # start with most similar search term and then go down from there
    results = []
    thresh = 100

    i=0 # which word index
    j=0 # the index of the current search word
    k=0 # which search word
    # IF WE WANT TO SORT RESULTS BY ONES THAT ARE CLOSE TO THE SEARCHED WORDS, KEEP THIS UNCOMMENTED
    while (i < len(clicked_word) and k < len(search_sorted_by_sim)):
        compare_indices = searched_words_dict[search_sorted_by_sim[k][0]]

        if j == len(compare_indices):
            j = 0
            i=0
            k += 1
            continue
        if abs(clicked_word[i] - compare_indices[j]) < thresh:
            # found some that are close
            st = clicked_word[i]-10
            en = clicked_word[i]+10
            if clicked_word[i] < 10:
                st = 0
            elif clicked_word[i] > (len(user_notes)-10):
                en = len(user_notes)
            sl = user_notes[st:en] 
            if sl not in results:
                results.append(sl)
            i+=1
        if i == len(clicked_word):
            break
        if clicked_word[i] > compare_indices[j] + 100:
            j+=1
        elif compare_indices[j] > clicked_word[i] + 100:
            i += 1
        if len(results) >= num_results:
            break

    # JUST USE THIS PART IF WE WANT TO JUST DO A BASIC SEARCH OF THE CLICKED WORD IN THE NOTES
    # DON'T COMMENT THIS OUT THO WE NEED IT WITH THE WHILE LOOP
    i = 0
    while len(results) < num_results and i < len(clicked_word):
        st = clicked_word[i]-10
        en = clicked_word[i]+10
        if clicked_word[i] < 10:
            st = 0
        elif clicked_word[i] > (len(user_notes)-10):
            en = len(user_notes)
        sl = user_notes[st:en] 
        if sl not in results:
            results.append(sl)
        i += 1
    for i in range(len(results)):
        temp = ' '.join(results[i])
        results[i] = temp

    return results

if __name__ == "__main__":
    ''' This can be used to test the machine learning module by commenting out individual lines. '''
    # Define paths to various sources
    # TODO: Change these to relative paths
    path2notes = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/Study notes.docx"
    path2glovetxt = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/glove.6B.300d.txt"
    path2glovepickle = "glove_embed.pkl"
    path2glovecompressedpickle = "glove_embed_compressed.bz"
    path2kv = "finetuned_embed.kv"
    
    # LOAD EMBEDDINGS FROM THE ORIGINAL TEXT FILE
    #glove_embeddings = load_embeddings_from_txt(path2glovetxt)

    # SAVE GLOVE EMBEDDINGS TO PICKLE FILE
    #save_embeddings(glove_embeddings, "glove_embed.pkl")

    # LOAD GLOVE EMBEDDINGS FROM PICKLE FILE
    glove_embeddings = load_embeddings(path2glovepickle)

    # LOAD AND PROCESS USER NOTES
    t0 = time.time()
    oov_vocab, scrubbed_vocab, full_corpus, pics_or_tables = process_user_notes(path2notes, glove_embeddings.keys)
    t1 = time.time()
    print("Time to process user input notes: %s"%(t1-t0))

    # TRAIN MODEL
    # t0 = time.time()
    # coocc_arr = create_cooccurrence(scrubbed_vocab, oov_vocab)
    # finetuned_embed = train_mittens(coocc_arr, oov_vocab, glove_embeddings)
    # t1 = time.time()
    # print("Time to train: %s"%(t1-t0))

    # CREATE KEYEDVECTORS OBJECT
    # t0 = time.time()
    # kv = create_kv_from_embed(finetuned_embed)
    # t1 = time.time()
    # print("Time to create kv: %s"%(t1-t0))

    # SAVE KEYEDVECTORS OBJECT
    # t0 = time.time()
    # save_kv(kv, path2kv)
    # t1 = time.time()
    # print("Time to save kv: %s"%(t1-t0))

    # LOAD KEYEDVECTORS OBJECT
    # t0 = time.time()
    # kv = load_kv(path2kv)
    # t1 = time.time()
    # print("Time to load kv: %s"%(t1-t0))

    # SEARCH FOR SOME WORDS AND GET A SIMILARITY MATRIX
    t0 = time.time()
    searched_words = ["semaphore", "lock", "binary"]
    # search function needs SCRUBBED VOCAB only
    #res_matrix, result_words, skipwords = search(searched_words, kv, 5, scrubbed_vocab)
    t1 = time.time()
    print("Time to search: %s"%(t1-t0))

    # INSPECT A NODE
    t0 = time.time()
    # inspect node needs FULL USER CORPUS (not scrubbed) and USER VOCAB (scrubbed)
    click_results = inspect_node("parallel", searched_words, full_corpus, kv, 5)
    t1 = time.time()
    print("Time to inspect: %s"%(t1-t0))