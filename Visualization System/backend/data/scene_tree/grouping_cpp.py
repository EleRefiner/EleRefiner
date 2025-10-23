import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
import random
import time
import math
import shapely
from scipy.optimize import linear_sum_assignment
from collections import Counter
from .eval2 import Group, getSubType

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
b_dir = os.path.join(current_dir, "scene_tree_cpp")
sys.path.append(b_dir)
print("b_dir", b_dir)
import SceneTreeCPP


def hierarchy_merge_with_cpp(obj_list):
    # print("start merge hierarchy")
    if len(obj_list) <= 1:
        return obj_list

    bounds = []
    categories = []
    for obj in obj_list:
        bounds.append(obj.box)
        categories.append(obj.type)
    merge_ways = SceneTreeCPP.HierarchyMerge(bounds, categories)

    tot_idx = [0]

    def dfsMerge():
        now_idx = tot_idx[0]
        tot_idx[0] += 1
        if merge_ways[now_idx][1] > 0:
            new_obj = Group()
            min_x = 10000000
            min_y = 10000000
            max_x = -10000000
            max_y = -10000000
            for i in range(merge_ways[now_idx][1]):
                obj = dfsMerge()
                new_obj.children.append(obj)
                min_x = min(min_x, obj.box[0])
                min_y = min(min_y, obj.box[1])
                max_x = max(max_x, obj.box[2])
                max_y = max(max_y, obj.box[3])
                new_obj.box = [min_x, min_y, max_x, max_y]
                new_obj.type = 'group'
                getSubType(new_obj)
            return new_obj
        else:
            return obj_list[merge_ways[now_idx][0]]

    obj_list = [dfsMerge()]

    # print("end merge hierarchy")
    return obj_list