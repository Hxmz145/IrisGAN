
import os
from torchvision.utils import save_image
from IPython.display import Image
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import torch
import torchvision
from torchvision.datasets import ImageFolder
from torchvision.transforms import ToTensor, Normalize, Compose

data_dir = "/Users/hamza1/desktop/IrisDataset"
dataset = ImageFolder(data_dir, transform=ToTensor())

img, label = dataset[0]
print("label:", label)
print(img[:, 10:15, 10:15])
torch.min(img), torch.max(img)


def denorm(x):
    out = (x + 1) / 2
    return out.clamp(0, 1)


# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

img_norm = denorm(img)
plt.imshow(img_norm[0], cmap='gray')
print("label", label)

batch_size = 2
print(len(dataset))
data_loader = DataLoader(dataset, batch_size, shuffle=True)
print(len(data_loader))
for img_batch, label_batch in data_loader:
    print("first batch")

    print(img_batch.shape)
    plt.imshow(img_batch[0][0], cmap="gray")
    print(label_batch)
    break

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

image_size = 921600
hidden_size = 20

D = nn.Sequential(
    nn.Linear(image_size, hidden_size),
    nn.LeakyReLU(0, 1),
    nn.Linear(hidden_size, hidden_size),
    nn.LeakyReLU(0, 1),
    nn.Linear(hidden_size, 1),
    nn.Sigmoid()
)

D.to(device)

latent_size = 4
G = nn.Sequential(
    nn.Linear(latent_size, 12),
    nn.ReLU(),
    nn.Linear(12, hidden_size),
    nn.ReLU(),
    nn.Linear(hidden_size, 50),
    nn.ReLU(),
    nn.Linear(50, 550),
    nn.ReLU(),
    nn.Linear(550, image_size),
    nn.Tanh()
)

"""Generator"""

y = G(torch.rand(1, latent_size))
print(y.shape)
gen_imgs = denorm(y.reshape(3, 480, 640).detach())
plt.imshow(gen_imgs[1], cmap='gray')

"""Discriminator Training"""

criterion = nn.BCELoss()
d_optimizer = torch.optim.Adam(D.parameters(), lr=0.00006)


def rest_grad():
    d_optimizer.zero_grad()
    g_optimizer.zero_grad()


def train_dicriminator(images):
    real_labels = torch.ones(batch_size, 1).to(device)
    fake_labels = torch.zeros(batch_size, 1).to(device)
    outputs = D(images)
    d_loss_real = criterion(outputs, real_labels)
    real_score = outputs
    z = torch.randn(batch_size, latent_size).to(device)
    fake_images = G(z)
    outputs = D(fake_images)
    d_loss_fake = criterion(outputs, fake_labels)
    fake_score = outputs
    d_loss = d_loss_real + d_loss_fake
    rest_grad()
    d_loss.backward()
    d_optimizer.step()

    return d_loss, real_score, fake_score


"""Generator Training"""

g_optimizer = torch.optim.Adam(G.parameters(), lr=0.0019)


def train_generator():
    z = torch.randn(batch_size, latent_size).to(device)
    fake_images = G(z)
    labels = torch.ones(batch_size, 1).to(device)
    g_loss = criterion(D(fake_images), labels)
    rest_grad()
    g_loss.backward()
    g_optimizer.step()
    return g_loss, fake_images


sample_dir = 'samples'
if not os.path.exists(sample_dir):
    os.makedirs(sample_dir)

"""Training the Model"""


for images, _ in data_loader:
    print(images.shape)  # Print the shape of the input tensor

    # Adjust the reshaping operation to match the actual size of the input tensor
    Images = images.reshape(images.size(0), images.size(
        1), images.size(2), images.size(3))
    print(Images.shape)  # Print the shape of the reshaped tensor

    save_image(denorm(images), os.path.join(
        sample_dir, 'real_images.png'), nrow=10)

Image(os.path.join(sample_dir, 'real_images.png'))

"""Create a helper function"""

sample_vectors = torch.randn(batch_size, latent_size).to(device)


def save_fake_images(index):
    fake_images = G(sample_vectors)
    fake_images = fake_images.reshape(fake_images.size(0), 3, 480, 640)
    fake_fname = 'fake_images-{0:0=4d}.png'.format(index)
    print("saving", fake_fname)
    save_image(denorm(fake_images), os.path.join(
        sample_dir, fake_fname), nrow=10)


save_fake_images(0)
Image(os.path.join(sample_dir, 'fake_images-0000.png'))

num_epochs = 50
total_step = len(data_loader)
d_losses, g_losses, real_scores, fake_scores = [], [], [], []

for epoch in range(num_epochs):
    for i, (images, _) in enumerate(data_loader):

        images = images.reshape(batch_size, -1).to(device)
        d_loss, real_score, fake_score = train_dicriminator(images)
        g_loss, fake_images = train_generator()
        if (i+1) % 5 == 0:
            d_losses.append(d_loss.item())
            g_losses.append(g_loss.item())
            real_scores.append(real_score.mean().item())
            fake_scores.append(fake_score.mean().item())
            print('Epoch [{}/{}], step[{}/{}], d_loss: {:4f}, g_loss: {:4f}, D(x): {:.2f}, D(G(Z)): {:.2f}'.format(epoch,
                  num_epochs, i+1, total_step, d_loss.item(), g_loss.item(), real_score.mean().item(), fake_score.mean().item()))

    save_fake_images(epoch+1)
