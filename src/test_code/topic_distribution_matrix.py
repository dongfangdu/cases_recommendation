from gensim import corpora
import multiprocessing
from gensim.models.ldamulticore import LdaMulticore
from app.libs.common import get_abs_path
from app.libs.deal_func import get_lda_path
import pickle
import faiss
import numpy as np

data_pickle = get_abs_path(get_lda_path()['pickle_path'])
with open(data_pickle, 'rb') as f:
    corpus = pickle.load(f)
# print(len(corpus))
data_dict = get_abs_path(get_lda_path()['dict_path'])
dictionary = corpora.Dictionary.load(data_dict)
# dictionary = corpora.Dictionary(data_pickle)
# corpus = [dictionary.doc2bow(doc) for doc in data_pickle]
num_cores = multiprocessing.cpu_count()
# print(num_cores)
num_topics = 2
lda = LdaMulticore(corpus, num_topics=num_topics, id2word=dictionary, workers=num_cores, alpha=1e-5, eta=5e-1)

d = 2
lenth = len(corpus)
index = faiss.IndexFlatL2(d)
for sim_cor in range(lenth):
    lda_prob = lda[corpus[sim_cor]]
    # print("="*30)
    # print(len(lda_prob))
    # print(lda_prob)
    if len(lda_prob) == 1:
        index.add(np.array([[lda_prob[0][1], 0]]).astype('float32'))
    else:
        index.add(np.array([[lda_prob[0][1], lda_prob[1][1]]]).astype('float32'))
faiss.write_index(index, "./test.index")

index = faiss.read_index("./test.index")

# D, I = index.search(np.array([[0.25, 0.75], [0.9, 0.1]]).astype('float32'), 5)
# lda_prob = np.array(lda[corpus[9]]).astype('float32')
# print(index.ntotal)
lda_prob = np.array([[0.5, 0.5]]).astype('float32')
print(lda_prob)
D, I = index.search(lda_prob, 10)
print(D)
print('*'*10)
print(I)
# print(D[0])

