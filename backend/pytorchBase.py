# imports
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split, Subset
import os
import json
import sys

# default config if issues persist
DEFAULT_CONFIG = {
    "batch_size": 32,
    "epochs": 20,
    "learning_rate": 0.001
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # goes up one folder
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f).get("current", DEFAULT_CONFIG)
else:
    print("config.json not found, using defaults.")
    config = DEFAULT_CONFIG

BATCH_SIZE = config["batch_size"]
EPOCHS = config["epochs"]
LEARNING_RATE = config["learning_rate"]
FOLDER_NAME = "test_model.pth"
KERNEL_SIZE = 3

# Accept mode from command line (for Flask) or interactive input
if len(sys.argv) > 1:
    choice = sys.argv[1].strip().lower()
else:
    while True:
        print("Using Hand or Object Dataset? (h/o)")
        choice = input().strip().lower()
        if choice in ("h", "o"):
            break
        print("Invalid choice. Please enter 'h' or 'o'.")

if choice == "h":
    DIRECTORY = os.path.join(PROJECT_ROOT, "pytorch_dataset_hand")
else:
    DIRECTORY = os.path.join(PROJECT_ROOT, "pytorch_dataset_object")
    
# pre-flight check: remove empty folders that would crash ImageFolder
import shutil
if os.path.exists(DIRECTORY):
    for d in os.listdir(DIRECTORY):
        d_path = os.path.join(DIRECTORY, d)
        if os.path.isdir(d_path):
            count = len([f for f in os.listdir(d_path) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
            if count == 0:
                print(f"Removing empty folder: {d}")
                shutil.rmtree(d_path)
    
    # Check if we have at least 2 classes
    valid_dirs = [d for d in os.listdir(DIRECTORY) if os.path.isdir(os.path.join(DIRECTORY, d))]
    if len(valid_dirs) < 2:
        print("Error: Need at least 2 populated classes to train.", file=sys.stderr)
        sys.exit(1)

# before starting the processing
train_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),              # fix: added more augmentation
    transforms.RandomGrayscale(p=0.1),            # fix: added more augmentation
    transforms.RandomPerspective(distortion_scale=0.2), # fix: added more augmentation
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], # RGB mean
                         [0.229, 0.224, 0.225]) # RGB std
])

# validation images
val_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# Pre-flight: remove empty class folders (triggers that were created but never populated)
if os.path.exists(DIRECTORY):
    for sub in os.listdir(DIRECTORY):
        sub_path = os.path.join(DIRECTORY, sub)
        if os.path.isdir(sub_path):
            files = [f for f in os.listdir(sub_path) if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.tiff','.webp'))]
            if len(files) == 0:
                print(f"Removing empty class folder: {sub}")
                os.rmdir(sub_path)

# Validate we have at least 2 classes
remaining = [d for d in os.listdir(DIRECTORY) if os.path.isdir(os.path.join(DIRECTORY, d))]
if len(remaining) < 2:
    print(f"ERROR: Need at least 2 gesture classes to train. Found: {remaining}")
    sys.exit(1)

# load dataset and split
full_dataset = datasets.ImageFolder(root=DIRECTORY, transform=train_transforms)
num_classes = len(full_dataset.classes)
print(f"Classes: {full_dataset.classes}")

# fix: proper subset split so val transform doesn't bleed into train
indices  = list(range(len(full_dataset)))
split = int(0.2 * len(full_dataset))
train_set = Subset(full_dataset, indices[split:])
val_set = Subset(full_dataset, indices[:split])
val_set.dataset.transform = val_transforms

train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_set,   batch_size=BATCH_SIZE, shuffle=False)

# model
class neural_network(nn.Module):
    def __init__(self, num_tags):
        super(neural_network, self).__init__()
        self.model = nn.Sequential(

            nn.Conv2d(3, 16, KERNEL_SIZE, padding=1),   # (B, 16, 256, 256)
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # (B, 16, 128, 128)

            nn.Conv2d(16, 32, KERNEL_SIZE, padding=1),  # (B, 32, 128, 128)
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # (B, 32, 64, 64)

            nn.Conv2d(32, 64, KERNEL_SIZE, padding=1),  # (B, 64, 64, 64)
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # (B, 64, 32, 32)

            nn.Conv2d(64, 128, KERNEL_SIZE, padding=1), # (B, 128, 32, 32)
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # (B, 128, 16, 16)

            nn.Conv2d(128, 256, KERNEL_SIZE, padding=1), # (B, 256, 16, 16)
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # (B, 256, 8, 8)

            nn.Flatten(), # (B, 16384)
            nn.Linear(16384, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_tags)
        )

    def forward(self, x):
        return self.model(x)


import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = neural_network(num_classes).to(device)
error_stuff = nn.CrossEntropyLoss()
optimizer_algo = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer_algo, step_size=5, gamma=0.5)

least_loss = float('inf')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "training_progress.json")
start_time = time.time()

for epoch in range(EPOCHS):
    # Write progress for UI
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump({
                "epoch": epoch,
                "total_epochs": EPOCHS,
                "elapsed_seconds": time.time() - start_time
            }, f)
    except:
        pass

    model.train()
    total_loss = 0.0
    correct = 0 
    total = 0

    for images, labels in train_loader:
        # print(images)
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

    train_accuracy = (correct / total) * 100

    model.eval()
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            val_correct += (predicted == labels).sum().item()
            val_total += labels.size(0)

    val_accuracy = (val_correct / val_total) * 100

    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss:.4f} | Train Acc: {train_accuracy:.2f}% | Val Acc: {val_accuracy:.2f}%")

    if total_loss < least_loss:
        torch.save(model.state_dict(), FOLDER_NAME)
        least_loss = total_loss
        print(f"Saved best model ({val_accuracy:.2f}%)")

    scheduler.step()

print(f"Best loss: {least_loss:.2f}%")