import torch
from tqdm import tqdm
from util import TreeToDevice
# from util import loss_fn
from measure import euclidean_distance
import math

loss_fn = torch.nn.MSELoss()

def validate(model, dataset, device, logger=None):
    print("test")
    model.eval()
    tot = 0
    tot2 = 0
    with torch.no_grad():
        val_loss = 0
        for data in tqdm(dataset):
            tree1, tree2, true_distance = data

            TreeToDevice(tree1, device)
            TreeToDevice(tree2, device)
            true_distance = torch.tensor(true_distance).float().to(device)

            h1, _ = model(tree1)
            h2, _ = model(tree2)

            predicted_distance = euclidean_distance(h1, h2)

            tot = tot + true_distance
            tot2 = tot2 + true_distance*true_distance

            loss = loss_fn(predicted_distance, true_distance)
            val_loss += loss.item()

        info = f'Validation Loss: {val_loss}, Total: {len(dataset)}, Total1: {tot}, Total2: {tot2}'
        print(info)
        # print(f'Validation Loss: {val_loss}')
        if logger is not None:
            logger.info(info)

def validate_with_id(model, dataset, device, logger=None):
    print("test")
    model.eval()
    tot = 0
    tot2 = 0
    feature_dict = {}
    with torch.no_grad():
        val_loss = 0
        for data in tqdm(dataset):
            tree1, tree2, true_distance, i, j = data

            if i not in feature_dict:
                TreeToDevice(tree1, device)
                h1, _ = model(tree1)
                feature_dict[i] = h1
            else:
                h1 = feature_dict[i]
            
            if j not in feature_dict:
                TreeToDevice(tree2, device)
                h2, _ = model(tree2)
                feature_dict[j] = h2
            else:
                h2 = feature_dict[j]

            true_distance = torch.tensor(true_distance).float().to(device)

            predicted_distance = euclidean_distance(h1, h2)

            tot = tot + true_distance
            tot2 = tot2 + true_distance*true_distance

            loss = loss_fn(predicted_distance, true_distance)
            val_loss += loss.item()

        info = f'Validation Loss: {val_loss}, Total: {len(dataset)}, Total1: {tot}, Total2: {tot2}'
        print(info)
        # print(f'Validation Loss: {val_loss}')
        if logger is not None:
            logger.info(info)
        
        return val_loss

def batch_validate_with_id(model, dataset, device, logger=None):
    print("test")
    model.eval()
    tot = 0
    tot2 = 0
    
    tree_dict = {}
    feature_dict = {}
    for data in dataset:
        tree1, tree2, true_distance, i, j = data
        tree_dict[i] = tree1
        tree_dict[j] = tree2
    
    keys = list(tree_dict.keys())
    batch_size = 10
    batch_cnt = math.ceil(len(keys)/batch_size)
    for i in tqdm(range(batch_cnt)):
        items = keys[int(i*len(keys)/batch_cnt):int((i+1)*len(keys)/batch_cnt)]
        trees = []
        for key in items:
            tree = tree_dict[key]
            TreeToDevice(tree, device)
            trees.append(tree)
        hs, _ = model(trees)
        for i in range(len(items)):
            feature_dict[items[i]] = hs[i]
        
    with torch.no_grad():
        val_loss = 0
        for data in tqdm(dataset):
            tree1, tree2, true_distance, i, j = data

            if i not in feature_dict:
                TreeToDevice(tree1, device)
                h1, _ = model([tree1])
                h1 = h1[0]
                feature_dict[i] = h1
            else:
                h1 = feature_dict[i]
            
            if j not in feature_dict:
                TreeToDevice(tree2, device)
                h2, _ = model([tree2])
                h2 = h2[0]
                feature_dict[j] = h2
            else:
                h2 = feature_dict[j]

            true_distance = torch.tensor(true_distance).float().to(device)

            predicted_distance = euclidean_distance(h1, h2)

            tot = tot + true_distance
            tot2 = tot2 + true_distance*true_distance

            loss = loss_fn(predicted_distance, true_distance)
            val_loss += loss.item()

        info = f'Validation Loss: {val_loss}, Total: {len(dataset)}, Total1: {tot}, Total2: {tot2}'
        print(info)
        # print(f'Validation Loss: {val_loss}')
        if logger is not None:
            logger.info(info)
        
        return val_loss