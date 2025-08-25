from tqdm import tqdm
import numpy as np
import sys

import json
import torch
import random
import os

use_ratio = 0.2
category_dict = { 1: "HRO", 2: "text", 3: "chart"}  # TO FILL


def PrepareData(input_json_path, dist_mtx_path, train_ratio=0.15, test_ratio=0.03, with_id=False, with_info=False, info_path=None):
    with open(info_path, 'r') as file:
        annotations_data = json.load(file)
    
    image_size_dict = {}
    for item in annotations_data["images"]:
        image_size_dict[item["file_name"]] = (item["width"], item["height"])

    with open(input_json_path, "r") as file:
        data = json.load(file)
    dist_mtx = np.load(dist_mtx_path)

    use_len = int(len(data)*use_ratio)

    trees = []
    for item in tqdm(data[:use_len]):
        id_cnt = [0]
        # print(item)
        boxes = []

        image_pre = "YOUR/PUBLIC/IMAGE/FOLDER/PATH/" # TO FILL
        tmp_size = image_size_dict[item["image"][len(image_pre):]]
        for box in item["boxes"]:
            id_cnt[0] += 1
            boxes.append({
                "id": id_cnt[0]-1,
                "bbox": [box["x"], box["y"], box["width"], box["height"]],
                "type": 'pred',
                "class": box["class"],
                "score": box["score"],
                "iscrowd": 0,
                "feature": [0.0]*(len(category_names)+1),
                "pos": [box["x"]/tmp_size[0], box["y"]/tmp_size[1], (box["x"]+box["width"])/tmp_size[0], (box["y"]+box["height"])/tmp_size[1]],
            })
            if "unselected" in box:
                boxes[-1]["unselected"] = box["unselected"]
            
            tmp_dict = category_names
            
            for key in tmp_dict:
                if box["class"] == tmp_dict[key]:
                    boxes[-1]["feature"][key] = 1.0
            
            # print(boxes[-1]["feature"]) 

        def dfs(hierarchy, deep):
            if isinstance(hierarchy, int):
                if "unselected" in boxes[hierarchy] and boxes[hierarchy]["unselected"]:
                    return None
                boxes[hierarchy]["deep"] = deep
                return {"children": [], "input": torch.tensor(boxes[hierarchy]["feature"]+boxes[hierarchy]["pos"]), "pos": boxes[hierarchy]["pos"]}
            id_cnt[0] += 1
            tmp_list = []
            tmp_pos = [1.0, 1.0, 0.0, 0.0]
            for child in hierarchy["children"]:
                tmp_child = dfs(child, hierarchy["deep"]-1)
                if tmp_child is None:
                    continue
                tmp_list.append(tmp_child)
                tmp_pos[0] = min(tmp_pos[0], tmp_child["pos"][0])
                tmp_pos[1] = min(tmp_pos[1], tmp_child["pos"][1])
                tmp_pos[2] = max(tmp_pos[2], tmp_child["pos"][2])
                tmp_pos[3] = max(tmp_pos[3], tmp_child["pos"][3])
            if len(tmp_list) == 0:
                return None
            if len(tmp_list) == 1:
                return tmp_list[0]
            return {"children": tmp_list, "input": torch.tensor([0.0]*len(category_names)+[1.0]+tmp_pos), "pos": tmp_pos}

        if "hierarchy" in item and item["hierarchy"] is not None:
            tmp_tree = dfs(item["hierarchy"], item["hierarchy"]["deep"])
            if tmp_tree is None:
                tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}

        elif len(boxes) >= 1:
            if "unselected" in boxes[0] and boxes[0]["unselected"]:
                tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}
            else:
                tmp_tree = {"children": [], "input": torch.tensor(boxes[0]["feature"]+boxes[0]["pos"])}
        else:
            tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}

        trees.append({"tree": tmp_tree})

    tree_list = np.arange(len(trees), dtype='int').tolist()
    random.seed(10)
    # print(tree_list)
    random.shuffle(tree_list)
    # print(tree_list)

    train_num = int(len(tree_list)*train_ratio)
    test_num = int(len(tree_list)*test_ratio)
    train_list = tree_list[:train_num]
    test_list = tree_list[train_num:train_num+test_num]

    check_list = []
    for i in range(len(train_list)):
        for j in range(i+1, len(train_list)):
            check_list.append((train_list[i], train_list[j]))
    random.seed(0)
    random.shuffle(check_list)
    train_dataset = []
    for i, j in check_list:
        if with_id:
            train_dataset.append((trees[i]["tree"], trees[j]["tree"], dist_mtx[i][j], i, j))
        else:
            train_dataset.append((trees[i]["tree"], trees[j]["tree"], dist_mtx[i][j]))
    
    check_list = []
    for i in range(len(test_list)):
        for j in range(i+1, len(test_list)):
            check_list.append((test_list[i], test_list[j]))
    random.seed(0)
    random.shuffle(check_list)
    test_dataset = []
    for i, j in check_list:
        if with_id:
            test_dataset.append((trees[i]["tree"], trees[j]["tree"], dist_mtx[i][j], i, j))
        else:
            test_dataset.append((trees[i]["tree"], trees[j]["tree"], dist_mtx[i][j]))

    if with_info:
        return train_dataset, test_dataset, trees, dist_mtx, train_list, test_list
    return train_dataset, test_dataset


def PrepareDataTree(input_json_path, info_path):
    with open(info_path, 'r') as file:
        annotations_data = json.load(file)

    image_size_dict = {}
    for item in annotations_data["images"]:
        image_size_dict[item["file_name"]] = (item["width"], item["height"])

    with open(input_json_path, "r") as file:
        data = json.load(file)

    use_len = int(len(data))

    trees = []
    for item in tqdm(data[:use_len]):
        id_cnt = [0]
        # print(item)
        boxes = []
        image_pre = "YOUR/PUBLIC/IMAGE/FOLDER/PATH/" # TO FILL
        tmp_size = image_size_dict[item["image"][len(image_pre):]]
        for box in item["boxes"]:
            id_cnt[0] += 1
            boxes.append({
                "id": id_cnt[0]-1,
                "bbox": [box["x"], box["y"], box["width"], box["height"]],
                "type": 'pred',
                "class": box["class"],
                "score": box["score"],
                "iscrowd": 0,
                "feature": [0.0]*(len(category_names)+1),
                "pos": [box["x"]/tmp_size[0], box["y"]/tmp_size[1], (box["x"]+box["width"])/tmp_size[0], (box["y"]+box["height"])/tmp_size[1]],
            })
            if "unselected" in box:
                boxes[-1]["unselected"] = box["unselected"]
            
            tmp_dict = category_names
            
            for key in tmp_dict:
                if box["class"] == tmp_dict[key]:
                    boxes[-1]["feature"][key] = 1.0
            
            # print(boxes[-1]["feature"]) 

        def dfs(hierarchy, deep):
            if isinstance(hierarchy, int):
                if "unselected" in boxes[hierarchy] and boxes[hierarchy]["unselected"]:
                    return None
                boxes[hierarchy]["deep"] = deep
                return {"children": [], "input": torch.tensor(boxes[hierarchy]["feature"]+boxes[hierarchy]["pos"]), "pos": boxes[hierarchy]["pos"]}
            id_cnt[0] += 1
            tmp_list = []
            tmp_pos = [1.0, 1.0, 0.0, 0.0]
            for child in hierarchy["children"]:
                tmp_child = dfs(child, hierarchy["deep"]-1)
                if tmp_child is None:
                    continue
                tmp_list.append(tmp_child)
                tmp_pos[0] = min(tmp_pos[0], tmp_child["pos"][0])
                tmp_pos[1] = min(tmp_pos[1], tmp_child["pos"][1])
                tmp_pos[2] = max(tmp_pos[2], tmp_child["pos"][2])
                tmp_pos[3] = max(tmp_pos[3], tmp_child["pos"][3])
            if len(tmp_list) == 0:
                return None
            if len(tmp_list) == 1:
                return tmp_list[0]
            return {"children": tmp_list, "input": torch.tensor([0.0]*len(category_names)+[1.0]+tmp_pos), "pos": tmp_pos}

        if "hierarchy" in item and item["hierarchy"] is not None:
            tmp_tree = dfs(item["hierarchy"], item["hierarchy"]["deep"])
            if tmp_tree is None:
                tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}

        elif len(boxes) >= 1:
            if "unselected" in boxes[0] and boxes[0]["unselected"]:
                tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}
            else:
                tmp_tree = {"children": [], "input": torch.tensor(boxes[0]["feature"]+boxes[0]["pos"])}
        else:
            tmp_tree = {"children": [], "input": torch.tensor([0.0]*(len(category_names)+5))}

        trees.append({"tree": tmp_tree})

    return trees
