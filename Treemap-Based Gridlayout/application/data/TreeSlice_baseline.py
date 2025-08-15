import numpy as np
import time
from scipy.spatial.distance import cdist

def _tree_partition_Naive(label_list, label_embeds, n, m, cur_idx=0, split_by="middle"):
    n, m = n*1.0, m*1.0
    sample_num = 0
    label_num = 0
    avg_embed = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)

    sort_x = np.argsort(avg_embed[:, 0])
    sort_y = np.argsort(avg_embed[:, 1])
    rank_x = np.arange(len(avg_embed))
    rank_y = np.arange(len(avg_embed))
    rank_x[sort_x] = np.arange(len(avg_embed))
    rank_y[sort_y] = np.arange(len(avg_embed))

    nums_label = np.array(nums_label)

    k = label_num

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([n, m]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def getAspectRatio(now_range):
        return max(now_range[0]/now_range[1], now_range[1]/now_range[0])

    def part_two(now_labels, now_range, pre_axis=-1):
        best_axis = -1
        best_part1 = None
        best_part2 = None
        best_ranges = None

        c_flag = False
        for axis in range(2):
            if axis == 0:
                sorted_id = np.argsort(rank_x[now_labels])
            else:
                sorted_id = np.argsort(rank_y[now_labels])
            for i in range(len(now_labels)-1):
                if abs(avg_embed[now_labels[sorted_id[i]], axis]-avg_embed[now_labels[sorted_id[i+1]], axis]) >= 0.005:
                    c_flag = True

        for axis in range(2):
            if axis == 0:
                sorted_id = np.argsort(rank_x[now_labels])
            else:
                sorted_id = np.argsort(rank_y[now_labels])

            if split_by == "middle":
                tot_size = len(now_labels)
                best_cut = 0
                best_diff = tot_size
                now_size = 0
                for i in range(len(now_labels)-1):
                    now_size += 1
                    if c_flag and abs(avg_embed[now_labels[sorted_id[i]], axis]-avg_embed[now_labels[sorted_id[i+1]], axis]) < 0.005:
                        continue
                    if abs(now_size*2-tot_size) < best_diff or best_cut == 0:
                        best_cut = i+1
                        best_diff = abs(now_size*2-tot_size)
                    if now_size*2-tot_size > 0:
                        break
            else:
                tot_size = nums_label[now_labels].sum()
                best_cut = 0
                best_diff = tot_size
                now_size = 0
                for i in range(len(now_labels)-1):
                    now_size += nums_label[now_labels[sorted_id[i]]]
                    if c_flag and abs(avg_embed[now_labels[sorted_id[i]], axis]-avg_embed[now_labels[sorted_id[i+1]], axis]) < 0.005:
                        continue
                    if abs(now_size*2-tot_size) < best_diff or best_cut == 0:
                        best_cut = i+1
                        best_diff = abs(now_size*2-tot_size)
                    if now_size*2-tot_size > 0:
                        break

            if best_cut == 0:
                continue
            part1 = now_labels[sorted_id[0:best_cut]]
            part2 = now_labels[sorted_id[best_cut:]]
            range1 = now_range.copy()
            range2 = now_range.copy()
            range1[axis] *= nums_label[part1].sum()/nums_label[now_labels].sum()
            range2[axis] *= nums_label[part2].sum()/nums_label[now_labels].sum()

            if best_axis == -1 or (best_axis != pre_axis and axis == pre_axis):
                best_axis = axis
                best_part1 = part1
                best_part2 = part2
                best_ranges = [range1, range2]
            elif not (best_axis == pre_axis and axis != pre_axis):
                if max(getAspectRatio(range1), getAspectRatio(range2)) < max(getAspectRatio(best_ranges[0]), getAspectRatio(best_ranges[1])):
                    best_axis = axis
                    best_part1 = part1
                    best_part2 = part2
                    best_ranges = [range1, range2]

        if best_axis == 0:
            best_axis = 'x'
        else:
            best_axis = 'y'

        return best_part1, best_part2, best_axis, best_ranges[0], best_ranges[1]

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([n, m])}]

    part = 1
    id_cnt = [1]
    cut_id = [0]

    def dfs_part_two(chosen):
        if len(chosen['labels']) <= 1:
            return
        pre_axis = -1
        if split_by == "middle":
            pre_axis = 0
            if "father_axis" in chosen:
                pre_axis = 1-chosen["father_axis"]
        part1, part2, axis, range1, range2 = part_two(chosen['labels'], chosen['range'], pre_axis=pre_axis)
        cut_id[0] += 1

        chosen['axis'] = axis

        new_item1 = {'id': id_cnt[0], 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1, 'father_axis': pre_axis}
        id_cnt[0] += 1
        new_item2 = {'id': id_cnt[0], 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2, 'father_axis': pre_axis}
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


def _tree_partition_WeightedMap(label_list, label_embeds, n, m, cur_idx=0):
    n, m = n*1.0, m*1.0
    sample_num = 0
    label_num = 0
    avg_embed = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)

    sort_x = np.argsort(avg_embed[:, 0])
    sort_y = np.argsort(avg_embed[:, 1])
    rank_x = np.arange(len(avg_embed))
    rank_y = np.arange(len(avg_embed))
    rank_x[sort_x] = np.arange(len(avg_embed))
    rank_y[sort_y] = np.arange(len(avg_embed))

    nums_label = np.array(nums_label)

    k = label_num

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([n, m]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def getAspectRatio(now_range):
        return max(now_range[0] / now_range[1], now_range[1] / now_range[0])

    def part_two(now_labels, now_range):
        c_flag = [False, False]
        for axis in range(2):
            if axis == 0:
                sorted_id = np.argsort(rank_x[now_labels])
            else:
                sorted_id = np.argsort(rank_y[now_labels])
            for i in range(len(now_labels)-1):
                if abs(avg_embed[now_labels[sorted_id[i]], axis]-avg_embed[now_labels[sorted_id[i+1]], axis]) >= 0.005:
                    c_flag[axis] = True

        if c_flag[0] and not c_flag[1]:
            axis = 0
        elif not c_flag[0] and c_flag[1]:
            axis = 1
        elif now_range[0] >= now_range[1]:
            axis = 0
        else:
            axis = 1

        if axis == 0:
            sorted_id = np.argsort(rank_x[now_labels])
        else:
            sorted_id = np.argsort(rank_y[now_labels])

        cuts = max(2, round(now_range[axis]/now_range[1-axis]))

        tot_size = nums_label[now_labels].sum()
        best_cut = 0
        best_diff = tot_size
        now_size = 0
        for i in range(len(now_labels)-1):
            now_size += nums_label[now_labels[sorted_id[i]]]
            if c_flag[axis] and abs(avg_embed[now_labels[sorted_id[i]], axis] - avg_embed[now_labels[sorted_id[i + 1]], axis]) < 0.005:
                continue
            if abs(now_size * cuts - tot_size) < best_diff or best_cut == 0:
                best_cut = i + 1
                best_diff = abs(now_size * cuts - tot_size)
            if now_size * cuts - tot_size > 0:
                break

        part1 = now_labels[sorted_id[0:best_cut]]
        part2 = now_labels[sorted_id[best_cut:]]
        range1 = now_range.copy()
        range2 = now_range.copy()
        range1[axis] *= nums_label[part1].sum() / nums_label[now_labels].sum()
        range2[axis] *= nums_label[part2].sum() / nums_label[now_labels].sum()

        if axis == 0:
            axis = 'x'
        else:
            axis = 'y'

        return part1, part2, axis, range1, range2

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([n, m])}]

    part = 1
    id_cnt = [1]
    cut_id = [0]

    def dfs_part_two(chosen):
        if len(chosen['labels']) <= 1:
            return
        part1, part2, axis, range1, range2 = part_two(chosen['labels'], chosen['range'])
        cut_id[0] += 1

        chosen['axis'] = axis

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

def _tree_partition_SOT(label_list, label_embeds, n, m, cur_idx=0):
    n, m = n*1.0, m*1.0
    sample_num = 0
    label_num = 0
    avg_embed = []
    nums_label = []

    for label in label_list:
        sample_num += len(label_embeds[label])
        nums_label.append(len(label_embeds[label]))
        avg_embed.append(np.mean(np.array(label_embeds[label]), axis=0))
        label_num += 1
    avg_embed = np.array(avg_embed)

    sort_x = np.argsort(avg_embed[:, 0])
    sort_y = np.argsort(avg_embed[:, 1])
    rank_x = np.arange(len(avg_embed))
    rank_y = np.arange(len(avg_embed))
    rank_x[sort_x] = np.arange(len(avg_embed))
    rank_y[sort_y] = np.arange(len(avg_embed))

    nums_label = np.array(nums_label)

    k = label_num

    if k == 1:
        partition = {}
        for i in range(label_num):
            partition[label_list[i]] = cur_idx
        info = {}
        info['axis'] = 'tree'
        part_tree = [{'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
                      'axis': None,
                      'range': np.array([n, m]), 'part_id': cur_idx}]
        info['ways'] = part_tree

        return partition, k, info

    def getAspectRatio(now_range):
        return max(now_range[0] / now_range[1], now_range[1] / now_range[0])

    def part_new_line(now_labels, now_range):
        if now_range[0] >= now_range[1]:
            axis = 0
        else:
            axis = 1

        new_pos = avg_embed[now_labels]-avg_embed[now_labels].min(axis=0)
        new_pos /= np.maximum(0.00001, new_pos.max(axis=0))
        new_pos *= now_range
        tmp_d = np.sqrt(now_range[0]*now_range[1]/len(now_labels))

        score = -1
        tmp_labels = []
        for i in range(len(now_labels)):
            tmp_label = -1
            tmp_dist = 0
            tmp_pos = np.array([0.0, 0.0])
            tmp_pos[1-axis] = i*tmp_d
            for j in range(len(now_labels)):
                if now_labels[j] in tmp_labels:
                    continue
                tmp_dist2 = np.power(new_pos[j] - tmp_pos, 2).sum()
                if tmp_label == -1 or tmp_dist2 < tmp_dist:
                    tmp_label = now_labels[j]
                    tmp_dist = tmp_dist2
            tmp_labels.append(tmp_label)
            tmp_score = 1
            tmp_tot = nums_label[tmp_labels].sum()
            tmp_a = tmp_tot/nums_label[now_labels].sum()*now_range[axis]
            for lb in tmp_labels:
                tmp_b = nums_label[lb]/tmp_tot*now_range[1-axis]
                tmp_score = max(tmp_score, max(tmp_a, tmp_b)/min(tmp_a, tmp_b))
            if 0 < score < tmp_score:
                tmp_labels.pop()
                break
            score = tmp_score

        part1 = np.array(tmp_labels)
        part2 = np.setdiff1d(now_labels, tmp_labels)
        range1 = now_range.copy()
        range2 = now_range.copy()
        range1[axis] *= nums_label[part1].sum() / nums_label[now_labels].sum()
        range2[axis] *= nums_label[part2].sum() / nums_label[now_labels].sum()

        if axis == 0:
            axis = 'x'
        else:
            axis = 'y'

        return part1, part2, axis, range1, range2

    part_tree = [
        {'id': 0, 'labels': np.arange(len(label_list), dtype='int'), 'size': sample_num, 'child': None,
         'axis': None,
         'range': np.array([n, m])}]

    id_cnt = [1]

    def part_line(chosen, axis):
        if len(chosen['labels']) <= 1:
            return

        part1 = chosen['labels'][:1]
        part2 = chosen['labels'][1:]
        range1 = chosen['range'].copy()
        range2 = chosen['range'].copy()
        range1[axis] *= nums_label[part1].sum() / nums_label[chosen['labels']].sum()
        range2[axis] *= nums_label[part2].sum() / nums_label[chosen['labels']].sum()

        if axis == 0:
            chosen['axis'] = 'x'
        else:
            chosen['axis'] = 'y'
        new_item1 = {'id': id_cnt[0], 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1}
        id_cnt[0] += 1
        new_item2 = {'id': id_cnt[0], 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2}
        id_cnt[0] += 1
        chosen['child'] = (new_item1, new_item2)
        part_tree.append(new_item1)
        part_tree.append(new_item2)
        part_line(new_item2, axis)

    def dfs_part_line(chosen):
        if len(chosen['labels']) <= 1:
            return

        part1, part2, axis, range1, range2 = part_new_line(chosen['labels'], chosen['range'])
        new_axis = 0
        if axis == "x":
            new_axis = 1
        if len(part1) == len(chosen['labels']):
            part_line(part1, new_axis)
            return

        chosen['axis'] = axis
        new_item1 = {'id': id_cnt[0], 'labels': part1, 'size': nums_label[part1].sum(), 'child': None, 'axis': None,
                     'range': range1}
        id_cnt[0] += 1
        new_item2 = {'id': id_cnt[0], 'labels': part2, 'size': nums_label[part2].sum(), 'child': None, 'axis': None,
                     'range': range2}
        id_cnt[0] += 1
        chosen['child'] = (new_item1, new_item2)
        part_tree.append(new_item1)
        part_line(new_item1, new_axis)
        part_tree.append(new_item2)
        dfs_part_line(new_item2)

    dfs_part_line(part_tree[0])

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