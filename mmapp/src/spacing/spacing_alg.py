import numpy as np
import time
import random

# Define the Fruchterman-Reingold algorithm
def fruchterman_reingold(cosine_similarities, dim=3, iterations=50, temperature=1.0, cooling_factor=0.95):
    ''' Run the Fruchterman-Reingold Force Directed Graphing algorithm on a set of words.

    Requirements:
        FR#20 -- MachineLearning.Visualize

    Arguments:
        cosine_similarities -- an nxn matrix where n is the number of words to display, and position (i,j) contains the similarity
            value between word i and word j
        dim -- the dimensions of the result points (default 3)
        iterations -- the number of iterations to perform (default 50)
        temperature -- the starting temperature of the system (default 1.0)
        cooling_factor -- the amount by which to cool the system after each iteration (default 0.95)

    Returns:
        positions -- a 3D point for each word
    '''
    # Initialize the positions randomly in a 3D space
    positions = np.random.rand(len(cosine_similarities), dim)
    # Calculate the initial distance matrix
    distances = np.sqrt(np.sum((positions[:, np.newaxis, :] - positions[np.newaxis, :, :]) ** 2, axis=-1))

    # Apply the Fruchterman-Reingold algorithm
    for _ in range(iterations):
        # Calculate the attractive and repulsive forces
        attractive_forces = np.zeros((len(cosine_similarities), dim))
        repulsive_forces = np.zeros((len(cosine_similarities), dim))
        for i in range(len(cosine_similarities)):
            for j in range(len(cosine_similarities)):
                if i == j:
                    continue
                attractive_force = (distances[i, j] ** 2) / (1-cosine_similarities[i][j])
                if distances[i,j] == 0:
                    # special case to prevent divide by 0 error
                    repulsive_force = (1-cosine_similarities[i][j])** 2 / 0.01
                else:
                    repulsive_force = (1-cosine_similarities[i][j])** 2 / distances[i, j]
                attractive_forces[i] += attractive_force * (positions[j] - positions[i])
                repulsive_forces[i] -= repulsive_force * (positions[j] - positions[i])
        forces = attractive_forces + repulsive_forces
        # Update the positions
        positions += temperature * forces / np.sqrt(np.sum(forces ** 2, axis=-1))[:, np.newaxis]
        # Apply bounds to the positions
        positions = np.clip(positions, 0, 1)
        distances = np.sqrt(np.sum((positions[:, np.newaxis, :] - positions[np.newaxis, :, :]) ** 2, axis=-1))
        # Cool down the temperature
        temperature *= cooling_factor

    # normalize the positions so that they are centered around the origin
    positions -= positions.mean(axis=0)
    return positions

def similarity_scores(num_words, num_scores, words):
    ''' Calculate random similarity scores for a group of words - not used, for testing purposes only '''
    num_scores += 1
    scores = np.zeros((num_words, num_scores))

    for i in range(num_words):
        random_word = random.randint(0, len(words) - 1)
        scores[i][0] = random_word

        for j in range(1, num_scores):
            scores[i][j] = random.uniform(0, 1)

    return scores

if __name__ == "__main__":
    # import sys
    # # sys.path.append(r'C:\Users\clair\Documents\Year 5\ECE 493\Project\Testing_ML\mapmind\ML')
    # import machine_learning
    # Generate cosine similarity scores
    # words = ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape', 'honeydew', 'kiwi', 'lemon', 'mango', 'nectarine', 'orange', 'pear', 'quince', 'raspberry', 'strawberry', 'tangerine', 'watermelon', 'cat', 'dog', 'mouse']
    # words = ['computer', 'microprocessor', 'fortran', 'cpu', 'apple', 'fruit', 'man', 'woman', 'keyboard', 'mouse']
    # words = ['semaphore', 'microprocessor', 'cpu', 'computer', 'chip', 'lock', 'unlock', 'binary']
    # words = ['word', 'job', 'note', 'application', 'pencil']
    # # kv = machine_learning.load_kv(r"C:\Users\clair\Documents\Year 5\ECE 493\Project\Testing_ML\mapmind\ML\finetuned_embed.kv")
    # scores = np.zeros(shape=(len(words),len(words)+1), dtype=object)
    # for i in range(len(words)):
    #     #scores[i][0] = words[i]
    #     for j in range(len(words)):
    #         scores[i][j] = kv.similarity(words[i],words[j])

    # print(scores)

    # matrix = scores[:,1:].astype(float)
    # pos = fruchterman_reingold(scores)

    """ cos_sim = similarity_scores(20, 20, words)
    # Extract the cosine similarity scores
    fr_matrix = cos_sim[:, 1:].astype(float)
    # Apply the Fruchterman-Reingold algorithm to the graph
    pos = fruchterman_reingold(fr_matrix) """

