import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
import numpy as np
import math
import matplotlib.pyplot as plt

############## TENSORBOARD ########################
import sys
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter

# Hyper-parameters
input_size = 12
hidden_size = 100
num_classes = 32
num_epochs = 200
batch_size = 10
learning_rate = 0.001


############## DATASET ########################
file_name_train = "output/Datasets/FeasRest_Train_Set1.CSV"
file_name_test = "output/Datasets/FeasRest_Test_Set1.CSV"

class FeasRestDataset(Dataset):

    def __init__(self, **kwargs):
        # Initialize data, download, etc.
        self.isTrain = kwargs["Train"] if "Train" in kwargs else False

        if self.isTrain:
            file_name = "output/Datasets/FeasRest_Train_Set1.CSV"
        else:
            file_name = "output/Datasets/FeasRest_Test_Set1.CSV"


        # read with numpy or pandas
        xy = np.loadtxt(file_name, delimiter=',', dtype=np.float32, skiprows=1)
        self.n_samples = xy.shape[0]

        # here the first column is the class label, the rest are the features
        self.x_data = torch.from_numpy(xy[:, 1:]) # size [n_samples, n_features]
        self.y_data = torch.from_numpy(xy[:, [0]]) # size [n_samples, 1]
        self.y_data = torch.squeeze(self.y_data)
        self.y_data = self.y_data.type(torch.LongTensor)

    # support indexing such that dataset[i] can be used to get i-th sample
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    # we can call len(dataset) to return the size
    def __len__(self):
        return self.n_samples

# default `log_dir` is "runs" - we'll be more specific here
writer = SummaryWriter('runs/FeasRest1')
###################################################

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')




# create dataset
# Feasibility Restoration dataset
train_dataset = FeasRestDataset(Train=True)
test_dataset = FeasRestDataset(Train=False)

# Data loader
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, 
                                           batch_size=batch_size, 
                                           shuffle=True)

test_loader = torch.utils.data.DataLoader(dataset=test_dataset, 
                                          batch_size=batch_size, 
                                          shuffle=False)

examples = iter(test_loader)
example_data, example_targets = next(examples)

# Fully connected neural network with one hidden layer
class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.input_size = input_size
        self.l1 = nn.Linear(input_size, hidden_size) 
        self.relu = nn.ReLU()
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
    
    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        # no activation and no softmax at the end
        return out

model = NeuralNet(input_size, hidden_size, num_classes).to(device)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

############## TENSORBOARD ########################
writer.add_graph(model, example_data)
#writer.close()
#sys.exit()
###################################################

# Train the model
running_loss = 0.0
running_correct = 0
n_total_steps = len(train_loader)
for epoch in range(num_epochs):
    for i, (features, labels) in enumerate(train_loader):
        features = features.to(device)
        labels = labels.to(device)
        
        # Forward pass
        outputs = model(features)
        loss = criterion(outputs, labels)
        
        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()

        _, predicted = torch.max(outputs.data, 1)
        running_correct += (predicted == labels).sum().item()

        if (i+1) % n_total_steps == 0 and (epoch+1) % 10 == 0:
            print (f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{n_total_steps}], Loss: {loss.item():.4f}')
            ############## TENSORBOARD ########################
            writer.add_scalar('Training Loss', loss.item(), epoch * n_total_steps + i)
            running_accuracy = 100 * running_correct / (10 * train_dataset.n_samples)
            writer.add_scalar('Prediction Accuracy', running_accuracy, epoch * n_total_steps + i)
            running_correct = 0
            running_loss = 0.0

        # if (i+1) % n_total_steps == 0:
        #     print (f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{n_total_steps}], Loss: {loss.item():.4f}')
        #     ############## TENSORBOARD ########################
        #     writer.add_scalar('Training Loss', running_loss / batch_size, epoch * n_total_steps + i)
        #     running_accuracy = 100 * running_correct / batch_size / predicted.size(0)
        #     writer.add_scalar('Prediction Accuracy', running_accuracy, epoch * n_total_steps + i)
        #     running_correct = 0
        #     running_loss = 0.0
            ###################################################

# Test the model
# In test phase, we don't need to compute gradients (for memory efficiency)
class_labels = []
class_preds = []
with torch.no_grad():
    n_correct = 0
    n_samples = 0
    for features, labels in test_loader:
        features = features.to(device)
        labels = labels.to(device)
        outputs = model(features)
        # max returns (value ,index)
        values, predicted = torch.max(outputs.data, 1)
        n_samples += labels.size(0)
        n_correct += (predicted == labels).sum().item()

        class_probs_batch = [F.softmax(output, dim=0) for output in outputs]

        class_preds.append(class_probs_batch)
        class_labels.append(predicted)

    # 10000, 10, and 10000, 1
    # stack concatenates tensors along a new dimension
    # cat concatenates tensors in the given dimension
    class_preds = torch.cat([torch.stack(batch) for batch in class_preds])
    class_labels = torch.cat(class_labels)

    acc = 100.0 * n_correct / n_samples
    print(f'Accuracy of the network on the test samples: {acc} %')

    # ############## TENSORBOARD ########################
    # classes = range(10)
    # for i in classes:
    #     labels_i = class_labels == i
    #     preds_i = class_preds[:, i]
    #     writer.add_pr_curve(str(i), labels_i, preds_i, global_step=0)
    #     writer.close()
    # ###################################################