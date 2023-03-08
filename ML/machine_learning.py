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
import os

# This is the real machine learning code! woo

# PROCESS USER NOTES
def process_user_notes(path2notes, embed):
    doc = docx.Document(path2notes)

    docText = []
    for para in doc.paragraphs:
        docText.append(para.text)

    translator = str.maketrans(dict.fromkeys(string.punctuation.replace('-',''))) #map punctuation to space

    corpus = []
    for sentence in docText:
        sentence = sentence.translate(translator)
        #for word in sentence.replace('/',' ').replace('"',' ').replace("'",' ').split():
        for word in sentence.split():
            corpus.append(word.lower())

    vocab_scrubbed = remove_stop_words(corpus)
    oov = [token for token in vocab_scrubbed if token not in embed.keys()]
    return list(set(oov)), vocab_scrubbed, corpus
    
    
def remove_stop_words(corpus):
    stopwords = list(ENGLISH_STOP_WORDS)
    #translator = str.maketrans(dict.fromkeys(string.punctuation))
    vocab_scrubbed = [token.lower() for token in corpus if (token.lower() not in stopwords and token != '')]
    return vocab_scrubbed

def load_embeddings_from_txt(path2txt):
    with open(path2txt, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
        embed = {line[0]: np.array(list(map(float,line[1:]))) for line in reader}
    return embed

def save_embeddings(embed, path2pkl):
    with open(path2pkl,"wb") as f:
        pickle.dump(embed,f)

def load_embeddings(path2pkl):
    with open(path2pkl, "rb") as f:
        embed = pickle.load(f)
    return embed

def create_cooccurrence(vocab_scrubbed, oov):
    my_doc = [' '.join(vocab_scrubbed)]
    cv = CountVectorizer(ngram_range=(1,1), vocabulary=oov)
    X = cv.fit_transform(my_doc)
    Xc = (X.T * X)
    Xc.setdiag(0)
    coocc_arr = Xc.toarray()
    return coocc_arr

def train_mittens(coocc_arr, oov, embed):
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
    kv = KeyedVectors(300)
    kv.add_vectors(list(embed.keys()), list(embed.values()))
    return kv

def save_kv(kv, path2model):
    kv.save(path2model)

def load_kv(path2model):
    kv = KeyedVectors.load(path2model)
    return kv

def search(searched_words, kv, num_results, vocab):
    result_words = []
    for word in searched_words:
        # for each word do the search
        result_words.append(word)
        # TODO: GET RID OF STOP WORDS IN RESULTS
        # GET RID OF STOP WORDS IN MODEL ALTOGETHER? COULD MAKE IT SMALLER
        # search for more words than we need because we are filtering by words in our vocab
        similar_words = kv.most_similar(positive=word, topn=10000)
        count = 0
        for sim_word, sim_val in similar_words:
            # TODO: deal with lemmatization?
            if sim_word in vocab and sim_word not in result_words:
                result_words.append(sim_word)
                count+=1
            if count == num_results:
                break
    
    #result_words = list(set(result_words))
    print(result_words)
    # NUMPY ARRAYS: (ROW, COLUMN) OR [ROW][COLUMN]
    nrows = len(result_words)
    ncols = nrows+1

    results_matrix = np.zeros(shape=(nrows,ncols), dtype=object)

    # now we have list of all the words that will be displayed
    for i in range(nrows):
        results_matrix[i][0] = result_words[i]
        for j in range(1,ncols):
            results_matrix[i][j] = kv.similarity(result_words[i],result_words[j-1])
    
    #print(result_words)
    print(results_matrix)
    return results_matrix

def inspect_node(word, searched_words, user_notes, kv):
    # get indices for all searched words
    searched_indices = {}
    # which word is closest?
    best_similarity = -100
    search_sorted = []
    for search in searched_words:
        sim = kv.similarity(word, search)
        search_sorted.append((search, sim))
        searched_indices[search] = [i for i, x in enumerate(user_notes) if x == search]
    min_val = len(user_notes)
    
    
    

if __name__ == "__main__":
    # Define paths to various sources
    path2notes = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/Study notes.docx"
    path2glovetxt = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/glove.6B.300d.txt"
    path2glovepickle = "glove_embed.pkl"
    path2kv = "finetuned_embed.kv"
    
    # LOAD EMBEDDINGS FROM THE ORIGINAL TEXT FILE
    # glove_embeddings = load_embeddings_from_txt(path2glovetxt)

    # SAVE GLOVE EMBEDDINGS TO PICKLE FILE
    # save_embeddings(glove_embeddings, "glove_embed.pkl")

    # LOAD GLOVE EMBEDDINGS FROM PICKLE FILE
    glove_embeddings = load_embeddings(path2glovepickle)

    # LOAD AND PROCESS USER NOTES
    t0 = time.time()
    oov_vocab, scrubbed_vocab, full_corpus = process_user_notes(path2notes, glove_embeddings)
    t1 = time.time()
    print("Time to process user input notes: %s"%(t1-t0))

    # t0 = time.time()
    # coocc_arr = create_cooccurrence(scrubbed_vocab, oov_vocab)
    # finetuned_embed = train_mittens(coocc_arr, oov_vocab, glove_embeddings)
    # t1 = time.time()
    # print("Time to train: %s"%(t1-t0))

    # t0 = time.time()
    # kv = create_kv_from_embed(finetuned_embed)
    # t1 = time.time()
    # print("Time to create kv: %s"%(t1-t0))

    # t0 = time.time()
    # save_kv(kv, path2kv)
    # t1 = time.time()
    # print("Time to save kv: %s"%(t1-t0))

    t0 = time.time()
    kv = load_kv(path2kv)
    t1 = time.time()
    print("Time to load kv: %s"%(t1-t0))

    t0 = time.time()
    searched_words = ["machine", "learning", "automatic"]
    res_matrix = search(searched_words, kv, 5, scrubbed_vocab)
    t1 = time.time()
    print("Time to search: %s"%(t1-t0))