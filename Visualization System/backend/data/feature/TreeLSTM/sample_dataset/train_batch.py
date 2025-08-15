import torch
import torch.optim as optim
from TreeLSTM import BatchTreeLSTM
from measure import euclidean_distance
from dataset_input import PrepareData
from tqdm import tqdm
from eval import validate, batch_validate_with_id
from util import TreeToDevice
# from util import loss_fn
import argparse
import os
import logging
import random
from torch.optim.lr_scheduler import CosineAnnealingLR
import time

def setup_logger(log_file="train.log", log_level=logging.INFO):
    logger = logging.getLogger("TreeLSTM_Logger")
    logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def parse_args():
    parser = argparse.ArgumentParser(description="Train a TreeLSTM model.")

    parser.add_argument('--num_epochs', type=int, default=100000, help="Number of training epochs")
    parser.add_argument('--train_ratio', type=float, default=0.9, help="")
    parser.add_argument('--test_ratio', type=float, default=0.1, help="")
    parser.add_argument('--hidden_size', type=int, default=64, help="Size of hidden state")
    parser.add_argument('--weight_decay', type=float, default=0, help="")
    parser.add_argument('--dropout', type=float, default=0, help="Dropout probability")
    parser.add_argument('--learning_rate', type=float, default=0.001, help="Learning rate for optimizer")

    return parser.parse_args()


args = parse_args()
folder_path = "batch_nodup_checkpoint_mse_" + str(args.train_ratio) + '_' + str(args.test_ratio) + '_' + str(args.hidden_size) + '_' + str(args.weight_decay) + '_' + str(args.dropout)

if not os.path.exists(folder_path):
    os.makedirs(folder_path)
logger = setup_logger(folder_path+"/train.log", logging.DEBUG)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

input_size = 11
hidden_size = args.hidden_size
model = BatchTreeLSTM(input_size, hidden_size, args.dropout).to(device)
optimizer = optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)

loss_fn = torch.nn.MSELoss()

train_dataset, test_dataset, trees, dist_mtx, train_list, test_list = PrepareData("../../../datasets/YOUR_DATASET/hierarchy_without_text.json", "result_new/IoU_dist_full.npy", args.train_ratio, args.test_ratio, with_id=True, with_info=True, info_path="../../../datasets/YOUR_DATASET/annotations.json")  # TO FILL

print(len(train_dataset), len(test_dataset))

seed = int(time.time())
random.seed(seed)

last_epoch = -1
scheduler = None
scheduler2 = None
num_epochs = args.num_epochs

for epoch in range(num_epochs):
    if os.path.exists(folder_path+"/model/model_"+str(epoch+1)+".pth"):
        state_dict = torch.load(folder_path+"/model/model_"+str(epoch+1)+".pth")
        model.load_state_dict(state_dict)
        state_dict = torch.load(folder_path+"/optimizer/optimizer_"+str(epoch+1)+".pth")
        optimizer.load_state_dict(state_dict)
        if os.path.exists(folder_path+"/scheduler/scheduler_"+str(epoch+1)+".pth"):
            state_dict = torch.load(folder_path+"/scheduler/scheduler_"+str(epoch+1)+".pth")
            scheduler = CosineAnnealingLR(optimizer, T_max=1000, eta_min=0)
            scheduler.load_state_dict(state_dict)
        if os.path.exists(folder_path+"/scheduler2/scheduler2_"+str(epoch+1)+".pth"):
            state_dict = torch.load(folder_path+"/scheduler2/scheduler2_"+str(epoch+1)+".pth")
            scheduler2 = CosineAnnealingLR(optimizer, T_max=1000, eta_min=0)
            scheduler2.load_state_dict(state_dict)
        last_epoch = epoch

batch_size = 10
for epoch in range(last_epoch+1, num_epochs):
    total_loss = 0
    print("epoch", epoch+1)
    print("train")
    print(folder_path)
    
    if epoch > 250 and scheduler is None:
        for param_group in optimizer.param_groups:
            param_group['lr'] = args.learning_rate/3
            if args.hidden_size <= 256:
                param_group['lr'] = args.learning_rate
    
    if epoch > 500 and scheduler is None:
        for param_group in optimizer.param_groups:
            param_group['lr'] = args.learning_rate/10
            if args.hidden_size <= 256:
                param_group['lr'] = args.learning_rate/3
    
    if epoch > 1000 and scheduler is None:
        for param_group in optimizer.param_groups:
            param_group['lr'] = args.learning_rate/30
            if args.hidden_size <= 256:
                param_group['lr'] = args.learning_rate/10
                if args.hidden_size <= 64:
                    param_group['lr'] = args.learning_rate/3

    train_dataset2 = []

    random.shuffle(train_list)
    for i in range(int(len(train_list)/2)):
        a = train_list[2*i]
        b = train_list[2*i+1]
        train_dataset2.append((trees[a]['tree'], trees[b]['tree'], dist_mtx[a][b], a, b))

    print(len(train_dataset2))
    model.train()
    tot = 0
    tot2 = 0
    batch_cnt = 0
    optimizer.zero_grad()
    tmp_data_list = []
    for i, data in enumerate(tqdm(train_dataset2)):
        tree1, tree2, true_distance, _, _ = data

        TreeToDevice(tree1, device)
        TreeToDevice(tree2, device)
        true_distance = torch.tensor(true_distance).float().to(device)
        
        tmp_data_list.append((tree1, tree2, true_distance))

        batch_cnt += 1
        if batch_cnt == batch_size or i == len(train_dataset2)-1:
            tmp_trees = []
            for tree1, tree2, _ in tmp_data_list:
                tmp_trees.append(tree1)
                tmp_trees.append(tree2)
            hs, _ = model(tmp_trees)

            batch_loss = None
            for i in range(len(tmp_data_list)):
                h1 = hs[i*2]
                h2 = hs[i*2+1]
                predicted_distance = euclidean_distance(h1, h2)
                true_distance = tmp_data_list[i][2]

                tot = tot + true_distance
                tot2 = tot2 + true_distance*true_distance
                loss = loss_fn(predicted_distance, true_distance)
                total_loss += loss.item()

                if batch_loss is None:
                    batch_loss = loss
                else:
                    batch_loss = batch_loss + loss
            tmp_data_list = []
            
            batch_loss = batch_loss / batch_cnt
            batch_loss.backward()

            batch_cnt = 0
            optimizer.step()
            optimizer.zero_grad()
            if scheduler2 is not None:
                scheduler2.step()
            elif scheduler is not None:
                scheduler.step()

    info = f'Epoch {epoch+1}, Loss: {total_loss}, Total: {len(train_dataset2)}, Total1: {tot}, Total2: {tot2}'
    print(info)
    # print(f'Epoch {epoch+1}, Loss: {total_loss}')
    logger.info(info)
    print("learning rate: "+str(optimizer.param_groups[0]['lr']))

    if epoch%10 == 0:
        batch_validate_with_id(model, test_dataset, device, logger)
        # logger.info("learning rate: "+str(optimizer.param_groups[0]['lr']))

        if not os.path.exists(folder_path+"/model"):
            os.makedirs(folder_path+"/model")
        torch.save(model.state_dict(), folder_path+"/model/model_"+str(epoch+1)+".pth")
        if not os.path.exists(folder_path+"/optimizer"):
            os.makedirs(folder_path+"/optimizer")
        torch.save(optimizer.state_dict(), folder_path+"/optimizer/optimizer_"+str(epoch+1)+".pth")
        if scheduler is not None:
            if not os.path.exists(folder_path+"/scheduler"):
                os.makedirs(folder_path+"/scheduler")
            torch.save(scheduler.state_dict(), folder_path+"/scheduler/scheduler_"+str(epoch+1)+".pth")
        if scheduler2 is not None:
            if not os.path.exists(folder_path+"/scheduler2"):
                os.makedirs(folder_path+"/scheduler2")
            torch.save(scheduler2.state_dict(), folder_path+"/scheduler2/scheduler2_"+str(epoch+1)+".pth")
    