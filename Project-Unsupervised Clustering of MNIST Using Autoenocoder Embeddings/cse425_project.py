# -*- coding: utf-8 -*-
"""CSE425_Project.ipynb

Original file is located at
    https://colab.research.google.com/drive/1y0zGPgJokwBiS2niYskCtzggHMPW-l0_

Please go the link to see the output and results.

"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

input_size = 784
hidden_size = 128
latent_size = 64
batch_size = 256
learning_rate = 1e-3
num_clusters = 10

!pip install --upgrade datasets fsspec -q

!pip install -U "datasets<=2.18.0" "fsspec<2024.3.0"

from datasets import load_dataset

ds = load_dataset("mnist")

print(ds)

print(ds["train"])

print(ds["train"][0])

print(ds["test"])

import numpy as np



train_images = [torch.tensor(np.array(image), dtype=torch.float32) / 255.0 for image in ds['train']['image']]
train_images = torch.stack(train_images)
train_labels = torch.tensor(ds['train']['label'], dtype=torch.long)

test_images = [torch.tensor(np.array(image), dtype=torch.float32) / 255.0 for image in ds['test']['image']]
test_images = torch.stack(test_images)
test_labels = torch.tensor(ds['test']['label'], dtype=torch.long)

print(train_images.shape)
print(train_labels.shape)

class Autoencoder(nn.Module):
    def __init__(self):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, latent_size)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, input_size),
            nn.Tanh()
        )

    def forward(self, x):
        z = self.encoder(x)
        x_recon = self.decoder(z)
        return x_recon, z

model = Autoencoder().to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

epochs = 10
for epoch in range(epochs):
    model.train()

    x = train_images
    x = x.view(x.size(0), -1).to(device)

    x_recon, _ = model(x)
    loss = criterion(x_recon, x)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    loss = loss.item()

    print(f"Epoch [{epoch+1}/{epochs}] Loss: {loss:.4f}")

model.eval()


with torch.no_grad():
    x = train_images
    x = x.view(x.size(0), -1).to(device)
    _, z = model(x)
    embeddings=z.cpu()
    labels= train_labels

embeddings = embeddings.numpy()
labels = labels.numpy()

# Apply K-Means
print("Clustering with K-Means...")
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
cluster_labels = kmeans.fit_predict(embeddings)

# Evaluation
sil_score = silhouette_score(embeddings, cluster_labels)
print(f"Silhouette Score: {sil_score:.4f}")

# Visualization with t-SNE
print("Visualizing with t-SNE...")
tsne = TSNE(n_components=2, random_state=42)
tsne_embeddings = tsne.fit_transform(embeddings)

plt.figure(figsize=(8,6))
plt.scatter(tsne_embeddings[:, 0], tsne_embeddings[:, 1], c=cluster_labels, cmap='tab10', s=10)
plt.colorbar()
plt.title("MNIST Clusters (t-SNE)")
plt.show()
