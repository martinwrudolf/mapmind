import numpy as np
cimport numpy as np

def fruchterman_reingold(np.ndarray[np.float64_t, ndim=2] cosine_similarities, int dim=3, int iterations=50, double k=None, double temperature=1.0, double cooling_factor=0.95):
    cdef int num_docs = cosine_similarities.shape[0]
    cdef np.ndarray[np.float64_t, ndim=2] positions = np.random.rand(num_docs, dim)
    cdef np.ndarray[np.float64_t, ndim=2] distances = np.zeros((num_docs, num_docs))

    # Set default value for k
    if k is None:
        k = np.sqrt(1.0 / num_docs)

    # Calculate the initial distance matrix
    for i in range(num_docs):
        for j in range(i+1, num_docs):
            dist = np.sqrt(np.sum((positions[i] - positions[j])**2))
            distances[i, j] = dist
            distances[j, i] = dist

    # Apply the Fruchterman-Reingold algorithm
    for iteration in range(iterations):
        # Calculate the attractive and repulsive forces
        cdef np.ndarray[np.float64_t, ndim=2] attractive_forces = np.zeros((num_docs, dim))
        cdef np.ndarray[np.float64_t, ndim=2] repulsive_forces = np.zeros((num_docs, dim))
        cdef double attractive_force
        cdef double repulsive_force

        for i in range(num_docs):
            for j in range(i+1, num_docs):
                attractive_force = (distances[i, j] ** 2) / k
                repulsive_force = k ** 2 / distances[i, j]
                attractive_forces[i] += attractive_force * (positions[j] - positions[i])
                repulsive_forces[i] -= repulsive_force * (positions[j] - positions[i])
                attractive_forces[j] += attractive_force * (positions[i] - positions[j])
                repulsive_forces[j] -= repulsive_force * (positions[i] - positions[j])

        forces = attractive_forces + repulsive_forces

        # Update the positions
        positions += temperature * forces / np.sqrt(np.sum(forces ** 2, axis=-1))[:, np.newaxis]

        # Apply bounds to the positions
        positions = np.clip(positions, 0, 1)

        # Update the distance matrix
        for i in range(num_docs):
            for j in range(i+1, num_docs):
                dist = np.sqrt(np.sum((positions[i] - positions[j])**2))
                distances[i, j] = dist
                distances[j, i] = dist

        # Cool down the temperature
        temperature *= cooling_factor

    return positions
