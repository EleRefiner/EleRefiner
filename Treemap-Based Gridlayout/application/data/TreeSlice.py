import numpy as np
import time
from scipy.spatial.distance import cdist
import application.data.GridBasedTreeMap as GridBasedTreeMap
from .TreeSlice_baseline import _tree_partition_Naive, _tree_partition_WeightedMap, _tree_partition_SOT

def copyPartTree(item, item2, tree_list):
    item['id'] = item2['id']
    item['axis'] = item2['axis']

    if item2['child'] is None:
        item['part_id'] = item2['part_id']
        item['size'] = item2['size']
        return
    child1, child2 = item2['child']
    new_item1 = {'id': None, 'child': None, 'axis': None}
    new_item2 = {'id': None, 'child': None, 'axis': None}
    tree_list.append(new_item1)
    tree_list.append(new_item2)
    item['child'] = (new_item1, new_item2)
    copyPartTree(new_item1, child1, tree_list)
    copyPartTree(new_item2, child2, tree_list)

def dfsPartTree(item, tree_list):
    tree_list.append(item)
    if item['child'] is None:
        return
    child1, child2 = item['child']
    dfsPartTree(child1, tree_list)
    dfsPartTree(child2, tree_list)

def reducePartTreeItem(item2, label_list):
    # print('reduce item', item2, label_list)
    item = {'id': None, 'child': None, 'axis': None}
    item['id'] = item2['id']
    item['axis'] = item2['axis']

    if item2['child'] is None:
        item['part_id'] = item2['part_id']
        item['size'] = item2['size']
        if item['part_id'] in label_list:
            return item
        return None

    child1, child2 = item2['child']
    new_item1 = reducePartTreeItem(child1, label_list)
    new_item2 = reducePartTreeItem(child2, label_list)

    if new_item1 is not None and new_item2 is not None:
        item['child'] = (new_item1, new_item2)
        return item
    elif new_item1 is not None:
        return new_item1
    else:
        return new_item2

def get_partition_HV_zoom(grid_size, labels, zoom_partition_map, all_tree_bf):
    maxLabel = labels.max() + 1

    label_list = np.arange(maxLabel, dtype='int')

    tmp_cut = {}
    tmp_cut['axis'] = 'tree'
    tmp_cut['ways'] = []
    part_list = np.array(list(map(lambda x: zoom_partition_map[x], label_list)))
    top_item = reducePartTreeItem(all_tree_bf[0], part_list)
    dfsPartTree(top_item, tmp_cut['ways'])

    labelmap = {}
    for lb in zoom_partition_map:
        labelmap[zoom_partition_map[lb]] = lb

    for item in tmp_cut['ways']:
        if item['child'] is None:
            item['part_id'] = labelmap[item['part_id']]
            item['size'] = (labels == item['part_id']).sum()
    for item in reversed(tmp_cut['ways']):
        if item['child'] is not None:
            child1, child2 = item['child']
            item['size'] = child1['size'] + child2['size']

    grid_dict = getPartGrids(tmp_cut, labels, [0, 0, grid_size[0], grid_size[1]])

    for item in tmp_cut['ways']:
        if item['child'] is None:
            item['part_id'] = str(item['part_id']) + "-top"

    return grid_dict, tmp_cut

def cutGrid(grid_box, ratio, axis):
    bounds = grid_box
    bottom = bounds[0]
    top = bounds[2]
    left = bounds[1]
    right = bounds[3]
    width = right-left
    height = top-bottom
    aim_area = width*height*ratio
    if axis == 'x':
        cut_line = round(height*ratio) + bottom
        if height >= 2:
            if cut_line == bottom:
                cut_line += 1
            if cut_line == top:
                cut_line -= 1

        CutP = [bottom, left, cut_line, right]
        CutP2 = [cut_line, left, top, right]
        return CutP, CutP2
    else:
        cut_line = round(width*ratio) + left
        if width >= 2:
            if cut_line == left:
                cut_line += 1
            if cut_line == right:
                cut_line -= 1

        CutP = [bottom, left, top, cut_line]
        CutP2 = [bottom, cut_line, top, right]
        return CutP, CutP2

def getPartGridsDFS(item, grid_box):
    grid_dict = {}
    if item['child'] is None:
        grid_dict[item["part_id"]] = grid_box
        return grid_dict
    child1, child2 = item['child']
    grid_box1, grid_box2 = cutGrid(grid_box, child1['size']/item['size'], item['axis'])
    new_dict1 = getPartGridsDFS(child1, grid_box1)
    grid_dict.update(new_dict1)
    new_dict2 = getPartGridsDFS(child2, grid_box2)
    grid_dict.update(new_dict2)
    return grid_dict

def getPartGrids(cut_way, labels, grid_box):
    num = len(labels)
    maxLabel = labels.max()+1
    capacity = np.zeros(maxLabel)
    for i in range(maxLabel):
        capacity[i] = (labels == i).sum() / num
    grid_dict = getPartGridsDFS(cut_way['ways'][0], grid_box)

    return grid_dict

def getTreeSlice(labels, centers, grid_size, label_list=None, treemap_type="grid"):
    if label_list is None:
        maxLabel = labels.max() + 1
        label_list = np.arange(maxLabel, dtype='int')
    label_embeds = {}
    for lb in label_list:
        label_embeds[lb] = np.vstack([centers[lb]] * (labels == lb).sum())

    if treemap_type == "grid":
        partition, k, cut_ways = _tree_partition_grid(label_list, label_embeds, grid_size[0], grid_size[1], 0)
    elif treemap_type == "grid2":
        partition, k, cut_ways = _tree_partition_grid2(label_list, label_embeds, grid_size[0], grid_size[1], 0)
    elif treemap_type == "AC":
        partition, k, cut_ways = _tree_partition_Naive(label_list, label_embeds, grid_size[0], grid_size[1], 0, split_by="middle")
    elif treemap_type == "EW":
        partition, k, cut_ways = _tree_partition_Naive(label_list, label_embeds, grid_size[0], grid_size[1], 0, split_by="weight")
    elif treemap_type == "weighted":
        partition, k, cut_ways = _tree_partition_WeightedMap(label_list, label_embeds, grid_size[0], grid_size[1], 0)
    elif treemap_type == "SOT":
        partition, k, cut_ways = _tree_partition_SOT(label_list, label_embeds, grid_size[0], grid_size[1], 0)

    # partition, k, cut_ways = _tree_partition2(label_list, label_embeds, 0)
    labelmap = {}
    for lb in partition:
        labelmap[partition[lb]] = lb
    tmp_cut = cut_ways
    for item in tmp_cut['ways']:
        if item['child'] is None:
            item['part_id'] = labelmap[item['part_id']]
            item['size'] = (labels == item['part_id']).sum()
    for item in reversed(tmp_cut['ways']):
        if item['child'] is not None:
            child1, child2 = item['child']
            item['size'] = child1['size'] + child2['size']
    return tmp_cut

def _tree_partition2(label_list, label_embeds, cur_idx=0):
    sample_num = 0
    label_num = 0
    avg_embed = []
    avg_dists = []
    avg_dists_xy = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)
    for i, label in enumerate(label_list):
        avg_dists.append(np.mean(cdist(np.array(label_embeds[label]), avg_embed[i].reshape((1, 2)))))
        avg_dists_xy.append(np.mean(np.abs(np.array(label_embeds[label]) - avg_embed[i].reshape((1, 2))), axis=0))
    avg_dists_xy = np.array(avg_dists_xy) * 2

    nums_label = np.array(nums_label)

    k = label_num
    # if (tcnt <= 2) or (sample_num > tot_num * 0.5):
    #     k = max(min(label_num, round(sample_num / csize)), 1)
    # else:
    #     k = 1

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        # info['axis'] = 'x'
        # info['divide'] = [[label_list]]
        # info['ways'] = [[cur_idx]]
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([1.0, 1.0]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def get_cut_cost(now_labels, sorted_id, cut, axis):
        left = -1000
        for i in range(cut + 1):
            left = max(left,
                       avg_embed[now_labels[sorted_id[i]]][axis] + avg_dists_xy[now_labels[sorted_id[i]]][axis])
        right = 1000
        for i in range(cut + 1, len(now_labels)):
            right = min(right,
                        avg_embed[now_labels[sorted_id[i]]][axis] - avg_dists_xy[now_labels[sorted_id[i]]][axis])
        return left - right

    def part_two(now_labels, tot_num, now_range=None):
        now_k = len(now_labels)
        divides = [[1 / max(2, min(now_k, 4)), 1 - 1 / max(2, min(now_k, 4))]]
        # divides = [[1/3, 2/3]]
        best_cost = -1
        best_part1 = None
        best_part2 = None
        best_axis = 0
        for i in range(2):
            size = (avg_embed[now_labels] - avg_dists_xy[now_labels]).max(axis=0) - (
                    avg_embed[now_labels] - avg_dists_xy[now_labels]).min(axis=0)
            if now_range is not None and 1 / 2 < size.min() / size.max():
                size = now_range
            if size[i] < size[1 - i] / 2:
                continue
            # if now_range is not None and now_range[i] < now_range[1-i]/2:
            #     continue
            pos = avg_embed[now_labels, i]
            sorted_pos = np.sort(pos)
            sorted_id = np.argsort(pos)
            for divide in divides:
                count = 0
                bf = 0
                cur_divide = 0
                cut_left = 0
                cut_right = len(now_labels) - 2
                for y in range(len(now_labels)):
                    count += nums_label[now_labels[sorted_id[y]]]
                    while count >= divide[cur_divide] * tot_num:
                        if count - divide[cur_divide] * tot_num <= divide[cur_divide] * tot_num - count + \
                                nums_label[
                                    now_labels[sorted_id[y]]] or bf == y:
                            # if cur_divide == 1:
                            gap = y
                            bf = gap + 1
                            # count = 0
                        else:
                            gap = y - 1
                            bf = gap + 1
                            # count = nums_label[now_labels[sorted_id[y]]]

                        if cur_divide == 0:
                            cut_left = min(len(now_labels) - 2, max(0, gap))
                        else:
                            cut_right = max(0, min(len(now_labels) - 2, gap))

                        cur_divide += 1
                        if cur_divide == 2:
                            break

                    if cur_divide == 2:
                        break
                if cut_left > cut_right:
                    cut_right, cut_left = cut_left, cut_right

                best_cut = -1
                best_cut_cost = 0

                best_cut2 = -1
                best_cut_cost2 = 0

                for cut in range(cut_left, cut_right + 1):
                    cut_cost = get_cut_cost(now_labels, sorted_id, cut, i)
                    c_flag = True
                    if cut == 0 or cut == len(now_labels) - 2:
                        now_range1 = now_range.copy()
                        now_range2 = now_range.copy()
                        if i == 0:
                            now_range1[0] = now_range1[0] * nums_label[now_labels[sorted_id[0:cut + 1]]].sum() / tot_num
                            now_range2[0] = now_range2[0] * (
                                        1 - nums_label[now_labels[sorted_id[0:cut + 1]]].sum() / tot_num)
                        else:
                            now_range1[1] = now_range1[1] * nums_label[now_labels[sorted_id[0:cut + 1]]].sum() / tot_num
                            now_range2[1] = now_range2[1] * (
                                        1 - nums_label[now_labels[sorted_id[0:cut + 1]]].sum() / tot_num)
                        if cut == 0 and now_range1.min() * 2 < now_range1.max():
                            c_flag = False
                        if cut == len(now_labels) - 2 and now_range2.min() * 2 < now_range2.max():
                            c_flag = False

                    if c_flag:
                        # if True:
                        if best_cut == -1 or cut_cost < best_cut_cost:
                            best_cut_cost = cut_cost
                            best_cut = cut
                    else:
                        if best_cut2 == -1 or cut_cost < best_cut_cost2:
                            best_cut_cost2 = cut_cost
                            best_cut2 = cut

                if best_cut == -1:
                    best_cut = best_cut2
                    best_cut_cost = best_cut_cost2

                if best_part1 is None or best_cut_cost < best_cost:
                    best_cost = best_cut_cost
                    best_part1 = now_labels[sorted_id[0:best_cut + 1]]
                    best_part2 = now_labels[sorted_id[best_cut + 1:]]
                    best_axis = i
        if best_axis == 0:
            best_axis = 'x'
        else:
            best_axis = 'y'
        return best_part1, best_part2, best_axis

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([1.0, 1.0])}]
    part = 1
    id_cnt = 1
    while True:
        id = -1
        chosen = None
        for item in part_tree:
            if item['child'] is None:
                if len(item['labels']) > 1 and (chosen is None or item['size'] > chosen['size']):
                    chosen = item
                    id = item['id']
        if chosen is None:
            break
        part1, part2, axis = part_two(chosen['labels'], chosen['size'], chosen['range'])
        chosen['axis'] = axis
        range1 = chosen['range'].copy()
        range2 = chosen['range'].copy()
        if axis == 'x':
            range1[0] = range1[0] * nums_label[part1].sum() / chosen['size']
            range2[0] = range2[0] * (1 - nums_label[part1].sum() / chosen['size'])
        else:
            range1[1] = range1[1] * nums_label[part1].sum() / chosen['size']
            range2[1] = range2[1] * (1 - nums_label[part1].sum() / chosen['size'])
        new_item1 = {'id': id_cnt, 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1}
        id_cnt += 1
        new_item2 = {'id': id_cnt, 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2}
        id_cnt += 1
        chosen['child'] = (new_item1, new_item2)
        part_tree.append(new_item1)
        part_tree.append(new_item2)

    partition = {}
    start_idx = 0

    for item in part_tree:
        if item["child"] is None:
            for label in item['labels']:
                partition[label_list[label]] = start_idx + cur_idx
            item["part_id"] = start_idx + cur_idx
            start_idx += 1

    info = {}
    info['axis'] = 'tree'
    info['ways'] = part_tree

    return partition, start_idx, info

def printInput(xy, sxy, rank_x, rank_y, weight):
    print("std::vector < std::vector < double >> xy, sxy;")
    print("std::vector < int > rank_x, rank_y;")
    print("std::vector < double > weight;")

    print("std::vector<double> tmp_xy = {", xy[0][0], ",",  xy[0][1], "};")
    print("xy.push_back(tmp_xy);")
    for i in range(1, len(xy)):
        print("tmp_xy = {", xy[i][0], ",",  xy[i][1], "};")
        print("xy.push_back(tmp_xy);")

    for i in range(0, len(sxy)):
        print("tmp_xy = {", sxy[i][0], ",",  sxy[i][1], "};")
        print("sxy.push_back(tmp_xy);")

    for i in range(len(rank_x)):
        print("rank_x.push_back(", rank_x[i], ");")

    for i in range(len(rank_y)):
        print("rank_y.push_back(", rank_y[i], ");")

    for i in range(len(weight)):
        print("weight.push_back(", weight[i], ");")


def _tree_partition_grid(label_list, label_embeds, n, m, cur_idx=0):
    if len(label_list) > 40:
        return _tree_partition2(label_list, label_embeds, cur_idx)

    sample_num = 0
    label_num = 0
    avg_embed = []
    avg_dists = []
    avg_dists_xy = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)
    for i, label in enumerate(label_list):
        avg_dists.append(np.mean(cdist(np.array(label_embeds[label]), avg_embed[i].reshape((1, 2)))))
        avg_dists_xy.append(np.mean(np.abs(np.array(label_embeds[label]) - avg_embed[i].reshape((1, 2))), axis=0))
    avg_dists_xy = np.array(avg_dists_xy) * 2

    sort_x = np.argsort(avg_embed[:, 0])
    sort_y = np.argsort(avg_embed[:, 1])
    rank_x = np.arange(len(avg_embed))
    rank_y = np.arange(len(avg_embed))
    rank_x[sort_x] = np.arange(len(avg_embed))
    rank_y[sort_y] = np.arange(len(avg_embed))

    start = time.time()
    # print("treemap size", len(avg_embed))
    # printInput(avg_embed, avg_dists_xy/2, rank_x, rank_y, nums_label)
    tree = GridBasedTreeMap.SearchForTree(avg_embed, avg_dists_xy / 2, rank_x, rank_y, n, m, nums_label)
    print("c search time", time.time()-start)

    nums_label = np.array(nums_label)

    k = label_num

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        # info['axis'] = 'x'
        # info['divide'] = [[label_list]]
        # info['ways'] = [[cur_idx]]
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([1.0, 1.0]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def part_two(now_labels, tree_cut):

        i = tree_cut[0]
        if i == 0:
            sorted_id = np.argsort(rank_x[now_labels])
        else:
            sorted_id = np.argsort(rank_y[now_labels])

        best_cut = tree_cut[1]

        best_part1 = now_labels[sorted_id[0:best_cut + 1]]
        best_part2 = now_labels[sorted_id[best_cut + 1:]]
        best_axis = i

        if best_axis == 0:
            best_axis = 'x'
        else:
            best_axis = 'y'

        return best_part1, best_part2, best_axis

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([1.0, 1.0])}]

    part = 1
    id_cnt = [1]
    cut_id = [0]

    def dfs_part_two(chosen):
        if len(chosen['labels']) <= 1:
            return
        part1, part2, axis = part_two(chosen['labels'], tree[cut_id[0]])
        cut_id[0] += 1

        chosen['axis'] = axis
        range1 = chosen['range'].copy()
        range2 = chosen['range'].copy()
        if axis == 'x':
            range1[0] = range1[0] * nums_label[part1].sum() / chosen['size']
            range2[0] = range2[0] * (1 - nums_label[part1].sum() / chosen['size'])
        else:
            range1[1] = range1[1] * nums_label[part1].sum() / chosen['size']
            range2[1] = range2[1] * (1 - nums_label[part1].sum() / chosen['size'])
        new_item1 = {'id': id_cnt[0], 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1}
        id_cnt[0] += 1
        new_item2 = {'id': id_cnt[0], 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2}
        id_cnt[0] += 1
        chosen['child'] = (new_item1, new_item2)
        part_tree.append(new_item1)
        dfs_part_two(new_item1)
        part_tree.append(new_item2)
        dfs_part_two(new_item2)

    dfs_part_two(part_tree[0])

    partition = {}
    start_idx = 0

    for item in part_tree:
        if item["child"] is None:
            for label in item['labels']:
                partition[label_list[label]] = start_idx + cur_idx
            item["part_id"] = start_idx + cur_idx
            start_idx += 1

    info = {}
    info['axis'] = 'tree'
    info['ways'] = part_tree

    return partition, start_idx, info


def _tree_partition_grid2(label_list, label_embeds, n, m, cur_idx=0):
    if len(label_list) > 40:
        return _tree_partition2(label_list, label_embeds, cur_idx)

    sample_num = 0
    label_num = 0
    avg_embed = []
    avg_dists = []
    avg_dists_xy = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)
    for i, label in enumerate(label_list):
        avg_dists.append(np.mean(cdist(np.array(label_embeds[label]), avg_embed[i].reshape((1, 2)))))
        avg_dists_xy.append(np.mean(np.abs(np.array(label_embeds[label]) - avg_embed[i].reshape((1, 2))), axis=0))
    avg_dists_xy = np.array(avg_dists_xy) * 2

    sort_x = np.argsort(avg_embed[:, 0])
    sort_y = np.argsort(avg_embed[:, 1])
    rank_x = np.arange(len(avg_embed))
    rank_y = np.arange(len(avg_embed))
    rank_x[sort_x] = np.arange(len(avg_embed))
    rank_y[sort_y] = np.arange(len(avg_embed))

    start = time.time()
    # print("treemap size", len(avg_embed))
    # printInput(avg_embed, avg_dists_xy/2, rank_x, rank_y, nums_label)
    tree = GridBasedTreeMap.SearchForTree2(avg_embed, avg_dists_xy / 2, rank_x, rank_y, n, m, nums_label, 0.05)
    print("c search time", time.time()-start)

    nums_label = np.array(nums_label)

    k = label_num

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        # info['axis'] = 'x'
        # info['divide'] = [[label_list]]
        # info['ways'] = [[cur_idx]]
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([1.0, 1.0]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def part_two(now_labels, tree_cut):

        i = tree_cut[0]
        if i == 0:
            sorted_id = np.argsort(rank_x[now_labels])
        else:
            sorted_id = np.argsort(rank_y[now_labels])

        best_cut = tree_cut[1]

        best_part1 = now_labels[sorted_id[0:best_cut + 1]]
        best_part2 = now_labels[sorted_id[best_cut + 1:]]
        best_axis = i

        if best_axis == 0:
            best_axis = 'x'
        else:
            best_axis = 'y'

        return best_part1, best_part2, best_axis

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([1.0, 1.0])}]

    part = 1
    id_cnt = [1]
    cut_id = [0]

    def dfs_part_two(chosen):
        if len(chosen['labels']) <= 1:
            return
        part1, part2, axis = part_two(chosen['labels'], tree[cut_id[0]])
        cut_id[0] += 1

        chosen['axis'] = axis
        range1 = chosen['range'].copy()
        range2 = chosen['range'].copy()
        if axis == 'x':
            range1[0] = range1[0] * nums_label[part1].sum() / chosen['size']
            range2[0] = range2[0] * (1 - nums_label[part1].sum() / chosen['size'])
        else:
            range1[1] = range1[1] * nums_label[part1].sum() / chosen['size']
            range2[1] = range2[1] * (1 - nums_label[part1].sum() / chosen['size'])
        new_item1 = {'id': id_cnt[0], 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1}
        id_cnt[0] += 1
        new_item2 = {'id': id_cnt[0], 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2}
        id_cnt[0] += 1
        chosen['child'] = (new_item1, new_item2)
        part_tree.append(new_item1)
        dfs_part_two(new_item1)
        part_tree.append(new_item2)
        dfs_part_two(new_item2)

    dfs_part_two(part_tree[0])

    partition = {}
    start_idx = 0

    for item in part_tree:
        if item["child"] is None:
            for label in item['labels']:
                partition[label_list[label]] = start_idx + cur_idx
            item["part_id"] = start_idx + cur_idx
            start_idx += 1

    info = {}
    info['axis'] = 'tree'
    info['ways'] = part_tree

    return partition, start_idx, info