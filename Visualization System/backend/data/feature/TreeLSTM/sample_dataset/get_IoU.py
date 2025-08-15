from tqdm import tqdm
import numpy as np
import sys
from scipy.optimize import linear_sum_assignment
import os

import json


with open("../../../datasets/YOUR_DATASET/hierarchy_without_text.json", "r") as file:  # TO FILL
    data = json.load(file)

with open("../../../datasets/YOUR_DATASET/annotations.json", 'r') as file:  # TO FILL
    annotations_data = json.load(file)

image_size_dict = {}
for item in annotations_data["images"]:
    image_size_dict[item["file_name"]] = (item["width"], item["height"])


output_folder = "result_new"


use_ratio = 0.1
use_len = int(len(data)*use_ratio)

items = []
for item in tqdm(data[:use_len]):
    # print(item)
    id_cnt = [0]
    boxes = []
    for box in item["boxes"]:
        if box["unselected"]:
            continue
        id_cnt[0] += 1
        boxes.append({
            "id": id_cnt[0]-1,
            "bbox": box,
            "type": 'pred',
            "class": box["class"],
            "score": box["score"],
            "iscrowd": 0,
        })
    # print(id_cnt[0])

    image_pre = "YOUR/PUBLIC/IMAGE/FOLDER/PATH/" # TO FILL
    items.append({"boxes": boxes, "size": image_size_dict[item["image"][len(image_pre):]]})


def getOverlap(size1, size2, show=False):
    # print(size1, size2)
    minx = max(size1[0], size2[0])
    miny = max(size1[1], size2[1])
    maxx = min(size1[2], size2[2])
    maxy = min(size1[3], size2[3])
    if show:
        print(minx, miny, maxx, maxy)
    if maxx>minx and maxy>miny:
        # print("overlap", (maxx-minx)*(maxy-miny))
        return (maxx-minx)*(maxy-miny) + 0.5
    # print("overlap", 0)
    return 0


def get_IoU_dist(item1, item2):
    l1 = len(item1["boxes"])
    l2 = len(item2["boxes"])
    mtx1 = np.zeros((l1, l2))
    mtx2 = np.zeros((l1, l2))
    mtx3 = np.zeros((l1, l2))
    tot_area1 = 0
    tot_area2 = 0
    tot_area3 = 0
    margin2 = 0.05
    margin3 = 0.1
    for box in item1["boxes"]:
        tot_area1 += (box["bbox"]["width"]/item1["size"][0]) * (box["bbox"]["height"]/item1["size"][1]) + 0.5
        tot_area2 += (box["bbox"]["width"]/item1["size"][0]+2*margin2) * (box["bbox"]["height"]/item1["size"][1]+2*margin2) + 0.5
        tot_area3 += (box["bbox"]["width"]/item1["size"][0]+2*margin3) * (box["bbox"]["height"]/item1["size"][1]+2*margin3) + 0.5
    for box in item2["boxes"]:
        tot_area1 += (box["bbox"]["width"]/item2["size"][0]) * (box["bbox"]["height"]/item2["size"][1]) + 0.5
        tot_area2 += (box["bbox"]["width"]/item2["size"][0]+2*margin2) * (box["bbox"]["height"]/item2["size"][1]+2*margin2) + 0.5
        tot_area3 += (box["bbox"]["width"]/item2["size"][0]+2*margin3) * (box["bbox"]["height"]/item2["size"][1]+2*margin3) + 0.5
    
    for i in range(l1):
        box1 = item1["boxes"][i]["bbox"]
        for j in range(l2):
            box2 = item2["boxes"][j]["bbox"]
            if item1["boxes"][i]["class"] != item2["boxes"][j]["class"]:
                continue
            size1_1 = [box1["x"]/item1["size"][0], box1["y"]/item1["size"][1], (box1["x"]+box1["width"])/item1["size"][0], (box1["y"]+box1["height"])/item1["size"][1]]
            size1_2 = [box1["x"]/item1["size"][0]-margin2, box1["y"]/item1["size"][1]-margin2, (box1["x"]+box1["width"])/item1["size"][0]+margin2, (box1["y"]+box1["height"])/item1["size"][1]+margin2]
            size1_3 = [box1["x"]/item1["size"][0]-margin3, box1["y"]/item1["size"][1]-margin3, (box1["x"]+box1["width"])/item1["size"][0]+margin3, (box1["y"]+box1["height"])/item1["size"][1]+margin3]

            size2_1 = [box2["x"]/item2["size"][0], box2["y"]/item2["size"][1], (box2["x"]+box2["width"])/item2["size"][0], (box2["y"]+box2["height"])/item2["size"][1]]
            size2_2 = [box2["x"]/item2["size"][0]-margin2, box2["y"]/item2["size"][1]-margin2, (box2["x"]+box2["width"])/item2["size"][0]+margin2, (box2["y"]+box2["height"])/item2["size"][1]+margin2]
            size2_3 = [box2["x"]/item2["size"][0]-margin3, box2["y"]/item2["size"][1]-margin3, (box2["x"]+box2["width"])/item2["size"][0]+margin3, (box2["y"]+box2["height"])/item2["size"][1]+margin3]
            
            mtx1[i][j] = getOverlap(size1_1, size2_1)
            mtx2[i][j] = getOverlap(size1_2, size2_2)
            mtx3[i][j] = getOverlap(size1_3, size2_3)

    row_ind, col_ind = linear_sum_assignment(-mtx1)
    match1 = mtx1[row_ind, col_ind].sum()
    row_ind, col_ind = linear_sum_assignment(-mtx2)
    match2 = mtx2[row_ind, col_ind].sum()
    row_ind, col_ind = linear_sum_assignment(-mtx3)
    match3 = mtx3[row_ind, col_ind].sum()
    # print("match", match1, match2, match3)

    IoU = 1/3*(1*match1/(tot_area1-match1)+1*match2/(tot_area2-match2)+1*match3/(tot_area3-match3))

    # print("iou", IoU)
    return IoU


part_cnt = 100
arg = 0
args = sys.argv[1:]
if len(args)>0:
    arg = int(args[0])
print(arg)

check_list = []
for i in range(len(items)):
    for j in range(i+1, len(items)):
        check_list.append((i, j))
import random
random.seed(0)
random.shuffle(check_list)

ln = len(check_list)

dist_list = np.zeros((len(check_list[int(arg*ln/part_cnt):int((arg+1)*ln/part_cnt)]), 3), dtype='double')
cnt = 0
for ids, (i, j) in enumerate(tqdm(check_list[int(arg*ln/part_cnt):int((arg+1)*ln/part_cnt)])):
    # print(ids)
    cnt += 1
    dist_list[ids][0] = i
    dist_list[ids][1] = j
    dist_list[ids][2] = get_IoU_dist(items[i], items[j])
    if ids % 1000 == 0:
        np.save(output_folder+"/IoU_dist_"+str(arg), dist_list)
        print(cnt, i, j)

    # print(i, j, items[i], items[j], dist_list[ids][2])
    # if cnt == 2:
    #     break

np.save(output_folder+"/IoU_dist_"+str(arg), dist_list)
