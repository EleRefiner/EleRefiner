import torch

def euclidean_distance(h1, h2):
    return torch.norm(h1 - h2, p=2)  # 计算欧氏距离

def cosine_similarity(h1, h2):
    return F.cosine_similarity(h1, h2, dim=0)  # 计算余弦相似度

def loss_fn(predicted_distance, true_distance):
    return F.mse_loss(predicted_distance, true_distance)