import torch

def TreeToDevice(tree, device):
    tree["input"] = tree["input"].to(device)
    for subtree in tree["children"]:
        TreeToDevice(subtree, device)

def loss_fn(a, b):
    epsilon = 0.1
    return torch.pow(torch.abs(a - b) / (torch.abs(b) + epsilon), 2)