import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torchvision.utils import save_image

######################################################################################################################################
######################################################################################################################################
##
##  Impelementation of GAN on MNIST dataset
##  I referred to the following example to develop this sample :
##  https://github.com/yunjey/pytorch-tutorial/blob/master/tutorials/03-advanced/generative_adversarial_network/main.py
## 
######################################################################################################################################
######################################################################################################################################

def denorm(x):
    out = (x + 1) / 2
    return out.clamp(0, 1)

# Choose GPU or CPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Current Device " , device)


# Change here hyper parameters
batch_size = 50
latent_size = 128
hidden_size = 512
image_size = 784
num_epochs = 100 # Results become interesting from epoch ~20-30
lr = 0.0002


resul_dir = 'ResulGan'
if not os.path.exists(resul_dir):
    os.makedirs(resul_dir)



dataTransform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=(0.5, 0.5, 0.5),   
                                     std=(0.5, 0.5, 0.5))])
# MNIST Train data set
train_loader = torch.utils.data.DataLoader(datasets.MNIST('mnist_data', 
                                                          download=True, 
                                                          train=True,
                                                          transform=dataTransform), 
                                           batch_size=batch_size, 
                                           shuffle=True)


#Discriminator model
class Discriminator(nn.Module):
    def __init__(self , input_size, hidden_size, output_size):
         super(Discriminator, self).__init__()
         self.linear1 = nn.Linear(input_size , hidden_size)
         self.linear2 = nn.Linear(hidden_size , hidden_size)
         self.linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.linear1(x)) 
        x = F.relu(self.linear2(x)) 
        x = self.linear3(x)
        return torch.sigmoid(x)

# Generator Model
class Generator(nn.Module):
    def __init__(self , input_size, hidden_size, output_size):
         super(Generator, self).__init__()
         self.linear1 = nn.Linear(input_size , hidden_size)
         self.linear2 = nn.Linear(hidden_size , hidden_size)
         self.linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.linear1(x)) 
        x = F.relu(self.linear2(x)) 
        x= self.linear3(x)
        return torch.tanh(x) #Tied Sigmoid instead : did not work


#initialize discriminator and generator
D = Discriminator(image_size, hidden_size ,1).to(device) ;
G = Generator(latent_size , hidden_size,image_size).to(device)

#Adam optimization 
optimizerD = torch.optim.Adam(D.parameters(), lr)
optimizerG = torch.optim.Adam(G.parameters(), lr)

# Binary cross entropy loss
criterion = nn.BCELoss()


total_step = len(train_loader)

for epoch in range(num_epochs):
    for batch_idx, (x, target) in enumerate(train_loader):

        images = x.reshape(batch_size, -1).to(device)
        realLabel = torch.ones(batch_size, 1).to(device)
        fakeLabel = torch.zeros(batch_size, 1).to(device)
       
        
        # TRAIN D
        # On true data
        predictR = D(images) #image from the real dataset
        loss_real = criterion(predictR, realLabel)  # compare vs label =1 (D is supposed to "understand" that the image is real)
        real_score = predictR

        # On fake data
        latent_value = torch.randn((batch_size, latent_size)).to(device)
        fake_images = G(latent_value) #generate a fake image
        predictF = D(fake_images)
        loss_fake = criterion(predictF , fakeLabel) # compare vs label =0 (D is supposed to "understand" that the image generated by G is fake)
        fake_score = predictF

        lossD = loss_real + loss_fake 

        optimizerD.zero_grad() 
        optimizerG.zero_grad() 
        lossD.backward()
        optimizerD.step() 
        
        # TRAIN G
        latent_value = torch.randn((batch_size, latent_size)).to(device)
        fake_images= G(latent_value) #Generate a fake image
        predictG = D(fake_images)
        lossG = criterion(predictG , realLabel) # Compare vs label = 1 (We want to optimize G to fool D, predictG must tend to 1)
        optimizerD.zero_grad() 
        optimizerG.zero_grad() 
        lossG.backward()
        optimizerG.step() 

        if (batch_idx+1) % 200 == 0:
            print("Epoch: "+str(epoch)+"/"+str(num_epochs)+ "  -- Batch:"+ str(batch_idx+1)+"/"+str(total_step))
            print("     GenLoss "+str(round(lossG.item(), 3))+ "  --  DiscLoss "+str(round(lossD.item(), 3)))
            print("     D(x): "+str(round(real_score.mean().item(), 3))+ "  -- D(G(z)):"+str(round(fake_score.mean().item(), 3)))

    # Save real images
    if (epoch+1) == 1:
        images = images.reshape(images.size(0), 1, 28, 28)
        save_image(denorm(images), os.path.join(resul_dir, 'real_images.png'))
    
    # Save sampled images
    fake_images = fake_images.reshape(fake_images.size(0), 1, 28, 28)
    save_image(denorm(fake_images), os.path.join(resul_dir, 'fake_images-{}.png'.format(epoch+1)))