# imports
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import os
import json

if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)["current"]
else:
    print("file not found.")

BATCH_SIZE = config["batch_size"]
EPOCHS = config["epochs"]
FOLDER_NAME = "test"
DIRECTORY = "pytorch_dataset" # make this the OpenCV generated one
KERNEL_SIZE = 3

LEARNING_RATE = config["learning_rate"]

# preprocessing of images to 200x200, tensor format
preprocess = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

# make sure to load the opencv image folder
train_set = datasets.ImageFolder(root=DIRECTORY, transform=preprocess)
train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)

class neural_network(nn.Module):
    def __init__(self, num_tags):
        super(neural_network, self).__init__()
        self.model = nn.Sequential(
                
                nn.Conv2d(3,16,KERNEL_SIZE,padding=1), # (B, 16, 256, 256)
                nn.BatchNorm2d(16),
                nn.ReLU(),
                nn.MaxPool2d(2,2), # (B, 16, 128, 128)
                
                nn.Conv2d(16,32,KERNEL_SIZE,padding=1), # (B, 32, 128, 128)
                nn.BatchNorm2d(32),
                nn.ReLU(),
                nn.MaxPool2d(2,2), # (B, 32, 64, 64)
                
                nn.Conv2d(32,64,KERNEL_SIZE,padding=1), # (B, 64, 64, 64)
                nn.BatchNorm2d(64),
                nn.ReLU(),
                nn.MaxPool2d(2,2), # (B, 64, 32, 32)
                
                nn.Conv2d(64,128,KERNEL_SIZE,padding=1), # (B, 128, 32, 32)
                nn.BatchNorm2d(128),
                nn.ReLU(),
                nn.MaxPool2d(2,2), # (B, 128, 16, 16)

                nn.Conv2d(128,256,KERNEL_SIZE,padding=1), # (B, 256, 16, 16)
                nn.BatchNorm2d(256),
                nn.ReLU(),
                nn.MaxPool2d(2,2), # (B, 256, 8, 8)

                nn.Flatten(16384, 256),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(256, num_tags)
                
        )
    
    # to step
    def forward(self, x):
         return self.model(x)
    
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

model = neural_network.to(device)

# error loss
error_stuff = nn.CrossEntropyLoss()

# learning model
optimizer_algo = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

accuracy_bench = 0 # to keep track of overfitting, if it gets worse then its overfitting?

for epoch in range(EPOCHS):
    total_loss = 0.0
    completed = 0.0
    total = 0

    model.train()

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device) # send image tensors to GPU
        optimizer_algo.zero_grad() # reset the gradients for the training algo
        outputs = model(images)
        loss = error_stuff(outputs, labels) # compares the raw data to the expected ones, sees how off they are
        loss.backward()
        optimizer_algo.step()

        total_loss += loss.item() # adds the loss to the total loss

        _, predicted = torch.max(outputs, 1) # indexes of the max values
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        accuracy = (correct / total) * 100

        print(f"Epoch {epoch+1}/{EPOCHS} \nLoss: {total_loss:.4f}\nAccuracy: {accuracy:.2f}%")

        if accuracy > accuracy_bench:
            torch.save(model.state_dict(), FOLDER_NAME)
            accuracy_bench = accuracy