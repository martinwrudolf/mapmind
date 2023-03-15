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
import time

# WORD2VEC
W2V_SIZE = 300
W2V_WINDOW = 7
W2V_EPOCH = 100
W2V_MIN_COUNT = 2

t0 = time.time()
# collect corpus for training
doc = docx.Document("Study notes.docx")

docText = []
for para in doc.paragraphs:
    docText.append(para.text)

corpus = []
for sentence in docText:
    for word in sentence.replace('/',' ').replace('"',' ').replace("'",' ').split():
        corpus.append(word.lower())
#print(corpus)
t1 = time.time()
print("Time to load corpus: %s"%(t1-t0))
print(len(corpus))

#my_vocab = list(set(corpus))

t0 = time.time()

# use this code if you need to reload glove!
""" glove_path = "glove.6B.300d.txt"
with open(glove_path, encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
    embed = {line[0]: np.array(list(map(float, line[1:]))) for line in reader} """

# i already loaded glove so there is the pickle file
# this is just the results of the above code ^ but I pickled it so we don't have to reload every time
with open("glove_embeddings.pkl", "rb") as f:
    embed = pickle.load(f)

t1 = time.time()


print("Time to load glove corpus: %s"%(t1-t0))

""" print(embed['the'])
print(len(embed)) """

t0 = time.time()
sw = list(ENGLISH_STOP_WORDS)
my_vocab_scrubbed = [token.lower().translate(str.maketrans(dict.fromkeys(string.punctuation))) for token in corpus if (token.lower() not in sw and token != '')]
oov = [token for token in my_vocab_scrubbed if token not in embed.keys()]

oov_vocab = list(set(oov))
t1 = time.time()
print("Time to scrape corpus: %s"%(t1-t0))
print("scrubbed length: %d"%len(my_vocab_scrubbed))
print("out of vocab: %d"%len(oov_vocab))
print(oov_vocab[:20])

my_doc = [' '.join(my_vocab_scrubbed)]

cv = CountVectorizer(ngram_range=(1,1), vocabulary=oov_vocab)
X = cv.fit_transform(my_doc)
Xc = (X.T * X)
Xc.setdiag(0)
coocc_ar = Xc.toarray()

t0 = time.time()
mittens_model = Mittens(n=300, max_iter=1000)

print("training!")
new_embeddings = mittens_model.fit(
    coocc_ar,
    vocab = oov_vocab,
    initial_embedding_dict=embed
)
print("finished training")
t1 = time.time()
print("Time to train model: %s"%(t1-t0))

newglove = dict(zip(oov_vocab, new_embeddings))
f = open("mittens_test.pkl", "wb")
pickle.dump(newglove, f)
f.close()

t0 = time.time()
with open("mittens_test.pkl", "rb") as f:
    newglove = pickle.load(f)
t1 = time.time()
print("Time to load new embeddings from pickle file: %s"%(t1-t0))

embed.update(newglove)

t0 = time.time()
w2v = KeyedVectors(300)
w2v.add_vectors(list(embed.keys()), list(embed.values()))
t1 = time.time()
print("Time to convert ot KeyedVectors: %s"%(t1-t0))

t0 = time.time()
transistor = w2v.most_similar(positive='transistor', topn=10000)
parallel = w2v.most_similar(positive='parallel', topn=10000)
fortran = w2v.most_similar(positive='fortran', topn=10000)
c = w2v.most_similar(positive='c', topn=10000)
microcomputer = w2v.most_similar(positive='microcomputer', topn=10000)
microprocessor = w2v.most_similar(positive='microprocessor', topn=10000)
kernel = w2v.most_similar(positive='kernel', topn=10000)
semaphore = w2v.most_similar(positive='semaphore', topn=10000)
thread = w2v.most_similar(positive='thread', topn=10000)
process = w2v.most_similar(positive='process', topn=10000)
interrupt = w2v.most_similar(positive='interrupt', topn=10000)
memory = w2v.most_similar(positive='memory', topn=10000)
t1 = time.time()
print("Time to search for most similar words for 12 different words: %s"%(t1-t0))

t0 = time.time()
transistor_list = [word for word in transistor if word[0] in my_vocab_scrubbed]
parallel_list = [word for word in parallel if word[0] in my_vocab_scrubbed]
fortran_list = [word for word in fortran if word[0] in my_vocab_scrubbed]
c_list = [word for word in c if word[0] in my_vocab_scrubbed]
microcomputer_list = [word for word in microcomputer if word[0] in my_vocab_scrubbed]
microprocessor_list = [word for word in microprocessor if word[0] in my_vocab_scrubbed]
kernel_list = [word for word in kernel if word[0] in my_vocab_scrubbed]
semaphore_list = [word for word in semaphore if word[0] in my_vocab_scrubbed]
thread_list = [word for word in thread if word[0] in my_vocab_scrubbed]
process_list = [word for word in process if word[0] in my_vocab_scrubbed]
interrupt_list = [word for word in interrupt if word[0] in my_vocab_scrubbed]
memory_list = [word for word in memory if word[0] in my_vocab_scrubbed]
t1 = time.time()
print("Time to filter results by only those words in the notes: %s"%(t1-t0))
print(len(transistor_list), len(parallel_list), len(microprocessor_list))

t0 = time.time()
indices_1 = [i for i, x in enumerate(corpus) if x == 'cache']
indices_2 = [i for i, x in enumerate(corpus) if x == 'memory']
min_val = len(corpus)
for i in indices_1:
    for j in indices_2:
        if abs(i-j) < min_val:
            min_val = abs(i-j)
            found_memory = i
            found_physical = j
t1 = time.time()
print("Time to find a text snippet with both words in it: %s"%(t1-t0))

print(corpus[found_memory-10:found_memory+10])
#print(corpus[found_physical-10:found_physical+10])

""" print(len(newglove))
print(len(embed))

print(oov[1])

print(cosine_similarity(newglove[oov[1]].reshape(1,-1), embed['problem'].reshape(1,-1)))
print(cosine_similarity(newglove[oov[1]].reshape(1,-1), embed['program'].reshape(1,-1)))
print(cosine_similarity(embed['problem'].reshape(1,-1), embed['program'].reshape(1,-1)))

print("updating") """


""" print(embed['problem'], embed['program'])
print(len(embed))
print(cosine_similarity(embed['problem'].reshape(1,-1), embed['program'].reshape(1,-1)))
print('\n')
print(oov[0],oov[1],oov[2])
print(cosine_similarity(embed['semaphore'].reshape(1,-1),embed['computer'].reshape(1,-1)))
print(cosine_similarity(embed['program'].reshape(1,-1),embed['semaphore'].reshape(1,-1)))
print(cosine_similarity(embed['computer'].reshape(1,-1),embed['program'].reshape(1,-1)))
print(cosine_similarity(embed['type'].reshape(1,-1),embed['semaphore'].reshape(1,-1)))
print(cosine_similarity(embed['lock'].reshape(1,-1),embed['semaphore'].reshape(1,-1)))
print(cosine_similarity(embed['program'].reshape(1,-1),embed['attribute'].reshape(1,-1)))
print(cosine_similarity(embed['program'].reshape(1,-1),embed['method'].reshape(1,-1)))
print(cosine_similarity(embed['function'].reshape(1,-1),embed['attribute'].reshape(1,-1)))
print(cosine_similarity(embed['method'].reshape(1,-1),embed['attribute'].reshape(1,-1)))
print(cosine_similarity(embed['semwait'].reshape(1,-1),embed['semaphore'].reshape(1,-1)))
print(cosine_similarity(embed['8bit'].reshape(1,-1),embed['computer'].reshape(1,-1)))
print(cosine_similarity(embed["software"].reshape(1,-1),embed['programmer'].reshape(1,-1)))
print(cosine_similarity(embed["programmer"].reshape(1,-1),embed['program'].reshape(1,-1)))
print(cosine_similarity(embed["programmer"].reshape(1,-1),embed['computer'].reshape(1,-1)))
print(cosine_similarity(embed["startroutine"].reshape(1,-1),embed['software'].reshape(1,-1)))
print(cosine_similarity(embed["sigquit"].reshape(1,-1),embed['signal'].reshape(1,-1))) """