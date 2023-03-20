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
import compress_pickle as pickle
import json
import time
import os
from spellchecker import SpellChecker
from nltk.stem import WordNetLemmatizer

# This is the real machine learning code! woo

# PROCESS USER NOTES
def process_user_notes(path2notes, embed):
    translator = str.maketrans(dict.fromkeys(string.punctuation.replace('-',''))) #map punctuation to space
    corpus = []
    if path2notes[-5:] == ".docx":
        doc = docx.Document(path2notes)

        docText = []
        for para in doc.paragraphs:
            docText.append(para.text)
        
        for sentence in docText:
            sentence = sentence.translate(translator)
            #for word in sentence.replace('/',' ').replace('"',' ').replace("'",' ').split():
            for word in sentence.split():
                corpus.append(word.lower())
    elif path2notes[-4:] == ".txt":
        f = open(path2notes, 'r')
        notes_str = f.read()
        notes_str = notes_str.translate(translator)
        for word in notes_str.split():
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
    skipwords = []
    lemmatizer = WordNetLemmatizer()
    for word in searched_words:
        # for each word do the search
        # TODO: GET RID OF STOP WORDS IN RESULTS
        # GET RID OF STOP WORDS IN MODEL ALTOGETHER? COULD MAKE IT SMALLER
        # search for more words than we need because we are filtering by words in our vocab
        try:
            similar_words = kv.most_similar(positive=word, topn=10000)
        except:
            # word not in model, probably misspelled or super weird obscure word
            # just skip it
            skipwords.append(word)
            continue
        if word not in result_words:
            result_words.append(word)
        count = 0
        for sim_word, sim_val in similar_words:
            # TODO: deal with lemmatization?
            if vocab:
                if sim_word in vocab and sim_word not in result_words and sim_word not in searched_words:
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
                
    
    #result_words = list(set(result_words))
    #print(result_words)
    # NUMPY ARRAYS: (ROW, COLUMN) OR [ROW][COLUMN]
    nrows = len(result_words)
    ncols = nrows+1

    results_matrix = np.zeros(shape=(nrows,nrows), dtype=object)

    # now we have list of all the words that will be displayed
    for i in range(nrows):
        results_matrix[i][0] = result_words[i]
        for j in range(nrows):
            results_matrix[i][j] = kv.similarity(result_words[i],result_words[j])

    #print(result_words)
    return results_matrix, result_words, skipwords

def inspect_node(word, searched_words, user_notes, kv, num_results):
    # get indices for all searched words
    searched_words_dict = {}
    clicked_word = [i for i,x in enumerate(user_notes) if x==word]
    # which word is closest?
    best_similarity = -100
    search_sorted_by_sim = []
    for search in searched_words:
        sim = kv.similarity(word, search)
        search_sorted_by_sim.append((search, sim))
        searched_words_dict[search] = [i for i, x in enumerate(user_notes) if x == search]

    search_sorted_by_sim.sort(key=lambda a: a[1], reverse=True)
    print(search_sorted_by_sim)

    # start with most similar search term and then go down from there
    results = []
    thresh = 100

    i=0 # which word index
    j=0 # the index of the current search word
    k=0 # which search word
    # IF WE WANT TO SORT RESULTS BY ONES THAT ARE CLOSE TO THE SEARCHED WORDS, KEEP THIS UNCOMMENTED
    while (i < len(clicked_word) and k < len(search_sorted_by_sim)):
        compare_indices = searched_words_dict[search_sorted_by_sim[k][0]]
        #print(compare_indices)
        if j == len(compare_indices):
            j = 0
            i=0
            k += 1
            continue
        if abs(clicked_word[i] - compare_indices[j]) < thresh:
            #print(clicked_word[i], compare_indices[j])
            # found some that are close
            if user_notes[clicked_word[i]-10:clicked_word[i]+10] not in results:
                results.append(user_notes[clicked_word[i]-10:clicked_word[i]+10])
                i+=1
        if clicked_word[i] > compare_indices[j] + 100:
            j+=1
        elif compare_indices[j] > clicked_word[i] + 100:
            i += 1
        if len(results) >= num_results:
            break

    # JUST USE THIS PART IF WE WANT TO JUST DO A BASIC SEARCH OF THE CLICKED WORD IN THE NOTES
    # DON'T COMMENT THIS OUT THO WE NEED IT WITH THE WHILE LOOP
    if len(results) < num_results:
        for i in clicked_word:
            results.append(user_notes[i-10:i+10])
    print(results)  

if __name__ == "__main__":
    # Define paths to various sources
    path2notes = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/Study notes.docx"
    path2glovetxt = r"C:/Users/clair/Documents/Year 5/ECE 493/Project/Testing_ML/glove.6B.300d.txt"
    path2glovepickle = "glove_embed.pkl"
    path2glovecompressedpickle = "glove_embed_compressed.bz"
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
    t0 = time.time()
    kv = load_kv(path2kv)
    t1 = time.time()
    print("Time to load kv: %s"%(t1-t0))

    # SEARCH FOR SOME WORDS AND GET A SIMILARITY MATRIX
    t0 = time.time()
    searched_words = ["semaphore", "lock", "binary"]
    # search function needs SCRUBBED VOCAB only
    #res_matrix, spell_check = search(searched_words, kv, 5, scrubbed_vocab)
    t1 = time.time()
    print("Time to search: %s"%(t1-t0))

    # INSPECT A NODE
    t0 = time.time()
    # inspect node needs FULL USER CORPUS (not scrubbed) and USER VOCAB (scrubbed)
    click_results = inspect_node("parallel", searched_words, full_corpus, kv, 5)
    t1 = time.time()
    print("Time to inspect: %s"%(t1-t0))