import numpy as np
import matplotlib.pyplot as plt

# Define the Fruchterman-Reingold algorithm
import numpy as np

def fruchterman_reingold(cosine_similarities, dim=3, iterations=50, k=None, temperature=1.0, cooling_factor=0.95):
    # Set default value for k
    if k is None:
        k = np.sqrt(1.0 / len(cosine_similarities))

    # Initialize the positions randomly in a 3D space
    positions = np.random.rand(len(cosine_similarities), dim)

    # Calculate the initial distance matrix
    distances = np.sqrt(np.sum((positions[:, np.newaxis, :] - positions[np.newaxis, :, :]) ** 2, axis=-1))

    # Apply the Fruchterman-Reingold algorithm
    for iteration in range(iterations):
        # Calculate the attractive and repulsive forces
        attractive_forces = np.zeros((len(cosine_similarities), dim))
        repulsive_forces = np.zeros((len(cosine_similarities), dim))
        for i in range(len(cosine_similarities)):
            for j in range(len(cosine_similarities)):
                if i == j:
                    continue
                attractive_force = (distances[i, j] ** 2) / k
                repulsive_force = k ** 2 / distances[i, j]
                attractive_forces[i] += attractive_force * (positions[j] - positions[i])
                repulsive_forces[i] -= repulsive_force * (positions[j] - positions[i])
        forces = attractive_forces + repulsive_forces

        # Update the positions
        positions += temperature * forces / np.sqrt(np.sum(forces ** 2, axis=-1))[:, np.newaxis]

        # Apply bounds to the positions
        positions = np.clip(positions, 0, 1)

        # Update the distance matrix
        distances = np.sqrt(np.sum((positions[:, np.newaxis, :] - positions[np.newaxis, :, :]) ** 2, axis=-1))

        # Cool down the temperature
        temperature *= cooling_factor

    return positions



# Generate cosine similarity scores
cos_sim = np.array([[1.0, 0.7, 0.3, 0.1], [0.7, 1.0, 0.2, 0.0], [0.3, 0.2, 1.0, 0.6], [0.1, 0.0, 0.6, 1.0]])

# Apply the Fruchterman-Reingold algorithm to the graph
pos = fruchterman_reingold(cos_sim)

# Extract the 3-dimensional coordinates of each node
x = pos[:, 0]
y = pos[:, 1]
z = pos[:, 2]

# Visualize the graph in 3D space
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z)

# Label each node with its corresponding cosine similarity score
for i in range(cos_sim.shape[0]):
    ax.text(x[i], y[i], z[i], s=round(cos_sim[i][i], 2), fontsize=10)

print("Showing plot 1")
plt.show()

import time
start_time = time.time()
cos_sim_2 = np.random.rand(50, 50)
end_time = time.time()
print("Time taken for cos_sim_2: {} seconds".format(end_time - start_time))

# Time the execution of the Fruchterman-Reingold algorithm
import time
print("Starting plot 2")
start_time = time.time()
pos_2 = fruchterman_reingold(cos_sim_2)
end_time = time.time()
print("Time taken for plot 2: {} seconds".format(end_time - start_time))

x_2 = pos_2[:, 0]
y_2 = pos_2[:, 1]
z_2 = pos_2[:, 2]

fig_2 = plt.figure()
ax_2 = fig_2.add_subplot(111, projection='3d')
ax_2.scatter(x_2, y_2, z_2)

print("Showing plot 2")
plt.show()

# cos_sim_3 = np.random.rand(100, 100)
# cos_sim_3 = (cos_sim_3 + cos_sim_3.T) / 2
# np.fill_diagonal(cos_sim_3, 1.0)

# pos_3 = fruchterman_reingold_layout(cos_sim_3)

# x_3 = pos_3[:, 0]
# y_3 = pos_3[:, 1]
# z_3 = pos_3[:, 2]

# fig_3 = plt.figure()
# ax_3 = fig_3.add_subplot(111, projection='3d')
# ax_3.scatter(x_3, y_3, z_3)

# plt.show()
