from .dataSampler import DataSampler
from .LabelHierarchy import LabelHierarchy
from sklearn.cluster import DBSCAN, SpectralClustering
import numpy as np
import os, time
from queue import PriorityQueue
from scipy.spatial.distance import cdist
from collections import Counter
from .FDLayout import get_FD_layout_centers, getInitPos
from .TreeSlice import getTreeSlice, getPartGrids, get_partition_HV_zoom, copyPartTree
from .label import getLabelMap, solveTopLabels, mergeSmallLabels
from .AssignQAP import AssignQAP
import random
from application.utils.pickle import *

sample_num0 = (30, 30)

def show_stability(info_before, grid_solve_dict):
    grids = np.array(info_before["grids"])[info_before["selected_bf"]]
    show_grid_tmp(grids, np.zeros(len(grids), dtype='int'), "sta_bf.png", True)
    s_map = {}
    for i in range(len(info_before["selected"])):
        s_map[info_before["selected"][i]] = i
    new_grids = np.zeros_like(grids)
    for lb in grid_solve_dict:
        for i in range(len(grid_solve_dict[lb]["sample_ids"])):
            id = grid_solve_dict[lb]["sample_ids"][i]
            if id in s_map:
                new_grids[s_map[id]] = np.array(grid_solve_dict[lb]["grids"][i])
    show_grid_tmp(new_grids, np.zeros(len(new_grids), dtype='int'), "sta_af.png", True)

def show_grid_tmp(grids, grid_labels, path='new.png', showNum=False):
    grids = np.array(grids)
    import matplotlib.pyplot as plt
    plt.switch_backend('agg')
    plt.clf()
    plt.scatter(grids[:, 0], grids[:, 1], color=plt.cm.tab20(grid_labels))
    if showNum:
        for i in range(len(grids)):
            grid = grids[i]
            plt.text(grid[0], grid[1], str(i), color="b")
    plt.savefig(path)

def testNeighbor(a, b, maxk=50, labels=None, type='all'):
    start = time.time()
    order = np.arange(a.shape[0], dtype='int')
    np.random.seed(5)
    np.random.shuffle(order)
    dist_a = cdist(a, a[order], "euclidean")
    dist_b = cdist(b, b[order], "euclidean")
    arg_a = order[np.argsort(dist_a, axis=1)]
    arg_b = order[np.argsort(dist_b, axis=1)]

    # print("dist time", time.time()-start)
    nn = len(a)
    p1 = np.zeros(maxk)
    p2 = np.zeros(maxk)
    if type == 'cross':
        for k in range(maxk):
            for i in range(nn):
                diff = labels[arg_a[i]] != labels[i]
                diff2 = labels[arg_b[i]] != labels[i]
                # p1[k] += len(set(arg_a[i][diff][:k+1]).intersection(set(arg_b[i][diff2][:k+1])))
                p1[k] += (labels[np.array(list(set(arg_a[i][:k + 2]).intersection(set(arg_b[i][:k + 2]))))] !=
                          labels[i]).sum()
                p2[k] += 1
    else:
        for k in range(maxk):
            for i in range(nn):
                p1[k] += len(set(arg_a[i][:k + 2]).intersection(set(arg_b[i][:k + 2]))) - 1
                p2[k] += 1
    ret = p1 / p2

    if labels is not None:
        cnt = 0
        for i in range(nn):
            cnt += (labels[arg_a[i][:maxk]] == labels[i]).sum()
        print(cnt, maxk * nn - cnt)

    return ret

def AUC(y):
    cnt = 0
    a_20 = 0
    a_full = 0
    for i in range(len(y)):
        cnt += y[i]
        if i == 19:
            a_20 = cnt
    a_full = cnt
    return a_full, a_20

def testNeighbor_full(a, b, labels):
    avg_knnp = testNeighbor(a, b)

    # from collections import Counter
    # avg_knnp = 0
    # labels = np.array(labels)
    # label_list = Counter(labels)
    # for label in label_list:
    #     idx = np.arange(len(labels))[labels == label]
    #     knnp = testNeighbor(a[idx], b[idx])
    #     avg_knnp += knnp * len(idx)
    # avg_knnp /= len(labels)

    auc50, auc20 = AUC(avg_knnp)
    return avg_knnp, auc50, auc20

class DataCtrler(object):

    def __init__(self, sample_num=sample_num0, info_dict=None):
        super().__init__()
        if info_dict is None:
            info_dict = {}
        self.sample_num = sample_num
        self.labels = None
        self.gt_labels = None
        self.features = None
        self.confs_hierarchy = None
        self.load_samples = None

        self.treemap_type ="grid"
        if "treemap_type" in info_dict:
            self.treemap_type = info_dict["treemap_type"]

        self.sampler = DataSampler(default_sample_num=sample_num)
        self.label_hierarchy = LabelHierarchy()
        self.sample_stack = []
        self.grid_stack = []
        self.label_stack = []
        self.clear_filterlabel = True

        self.scale_alpha = 1/2
        self.ambiguity_threshold = 0.6

    def preprocess(self, filename='xxx.xxx'):
        self.dataset = filename
        self.label_hierarchy.load(filename)
        self.features = self.label_hierarchy.features
        self.labels = self.label_hierarchy.labels
        self.gt_labels = self.label_hierarchy.gt_labels
        self.hierarchy = self.label_hierarchy.label_hierarchy
        # self.grider.set_cache_path(dataset=filename)
        self.sampler.set_cache_path(dataset=filename)
        self.cache_path = self.sampler.cache_path
        self.confs_hierarchy = self.label_hierarchy.confs_hierarchy

    def clean_stacks(self):
        self.sample_stack = []
        self.grid_stack = []
        self.label_stack = []

    def get_now_labels(self, samples):
        if len(samples) == 0:
            return np.array([])
        labels_map = {}
        labels = self.labels[samples]
        hierarchy = self.hierarchy

        def get_label(cur_label):
            if cur_label not in labels_map:
                if len(self.label_stack) > 0 and cur_label in self.label_stack[-1][3]:
                    labels_map[cur_label] = cur_label
                else:
                    father_label_name = hierarchy['hierarchy'][hierarchy['id2label'][cur_label]]['parent']
                    if father_label_name is None:
                        labels_map[cur_label] = cur_label
                    else:
                        father_label = hierarchy['hierarchy'][father_label_name]['id']
                        labels_map[cur_label] = get_label(father_label)
            return labels_map[cur_label]
        
        new_labels = labels.copy()
        for i, label in enumerate(labels):
            new_labels[i] = get_label(label)
        return new_labels

    def reduce_now_labels(self, labels):
        if len(labels) == 0:
            return np.array([])
        labels_map = {}
        hierarchy = self.hierarchy

        def get_label(cur_label):
            if cur_label not in labels_map:
                if len(self.label_stack) > 0 and cur_label in self.label_stack[-1][3]:
                    labels_map[cur_label] = cur_label
                else:
                    father_label_name = hierarchy['hierarchy'][hierarchy['id2label'][cur_label]]['parent']
                    if father_label_name is None:
                        labels_map[cur_label] = cur_label
                    else:
                        father_label = hierarchy['hierarchy'][father_label_name]['id']
                        labels_map[cur_label] = get_label(father_label)
            return labels_map[cur_label]

        new_labels = labels.copy()
        for i, label in enumerate(labels):
            new_labels[i] = get_label(label)
        return new_labels

    def check_can_zoom_in(self):
        if len(self.sample_stack) > 0:
            last_sample_addition = self.sample_stack[-1][1]
            num = 0
            for addition in last_sample_addition:
                num += len(addition)
            if num > 0:
                return True
        return False

    def reduce_labels(self, labels, hierarchy, level1_range=(2, 3), level2_range=(4, 40), filter_ratio=0.01, spilit_ratio=1/6, zoom_without_expand=False):

        spilit_size = spilit_ratio * labels.shape[0]

        # 0. calculate filter boundary
        filter_num = max(1, min(0.1*spilit_size, np.ceil(filter_ratio * labels.shape[0])))
        # filter_num = max(1, np.ceil(filter_ratio * labels.shape[0])/2)
        filter_list = [set(), set()]

        # 1. get hierarchy and label frequency
        label_frequncy = {}
        label_nodes = {}
        for i, label in enumerate(labels):
            cur_label = label
            while True:
                if cur_label not in label_frequncy:
                    label_frequncy[cur_label] = 0
                    label_nodes[cur_label] = []
                label_frequncy[cur_label] += 1
                label_nodes[cur_label].append(i)
                cur_label_name = hierarchy['hierarchy'][hierarchy['id2label'][cur_label]]['parent']
                if cur_label_name is None:
                    break
                cur_label = hierarchy['hierarchy'][cur_label_name]['id']
        
        # 2. prepare score function 
        def getLabelScore(label):
            if not label in label_frequncy:
                label_frequncy[label] = 0
            score = label_frequncy[label]
            if score == 0:
                return -1
            children_list = hierarchy['hierarchy'][hierarchy['id2label'][label]]['children'] 
            if children_list is None or len(children_list) == 0:
                return 0
            return score
        
        def getClusterScore(label):
            # return 1
            if label_frequncy[label] > filter_num:
                return 1
            return 0
        

        # 3. reduce labels level 1
        q = PriorityQueue()
        q_cluster_num = 0

        if len(self.label_stack) > 0:
            tree_cut = self.label_stack[-1][3][:]
            for label in tree_cut:
                # if label not in label_frequncy:
                #     label_frequncy[label] = 0
                q.put((-getLabelScore(label), label))
                q_cluster_num += getClusterScore(label)
            # from IPython import embed; embed()
        else:
            for label_name in hierarchy['first_level']:
                label = hierarchy['hierarchy'][label_name]['id']
                q.put((-getLabelScore(label), label))
                q_cluster_num += getClusterScore(label)

            first_labels = [0 for _ in range(len(labels))]
            for score, label in q.queue:
                if -score < 0:
                    continue
                for node in label_nodes[label]:
                    first_labels[node] = label

            while q_cluster_num < level1_range[0]:
                # from IPython import embed; embed()
                score, label = q.get()
                q_cluster_num -= getClusterScore(label)
                if -score <= 0:
                    q.put((score, label))
                    q_cluster_num += getClusterScore(label)
                    break

                append_list = []
                append_num = 0
                for child_name in hierarchy['hierarchy'][hierarchy['id2label'][label]]['children']:
                    child = hierarchy['hierarchy'][child_name]['id']
                    if child not in label_frequncy:
                        # continue
                        label_frequncy[child] = 0
                    append_list.append((-getLabelScore(child), child))
                    append_num += getClusterScore(child)
                    # print("append", append_list)

                if append_num < getClusterScore(label):
                    q.put((score, label))
                    q_cluster_num += getClusterScore(label)
                    break
            
                if q_cluster_num + append_num < level1_range[1] + (level1_range[0] - q_cluster_num):
                    for item in append_list:
                        q.put(item)
                    q_cluster_num += append_num
                    if q_cluster_num >= level1_range[0]:
                        break
                else:
                    q.put((score, label))
                    q_cluster_num += getClusterScore(label)
                    break

        level1_labels = [-1 for _ in range(len(labels))]
        for score, label in q.queue:
            if -score < 0:
                continue
            # if label_frequncy[label] <= filter_num:
            #     filter_list[0].add(label)
            for node in label_nodes[label]:
                level1_labels[node] = label
        # from IPython import embed; embed();
        # print("p1")
        
        # 4. reduce labels level 2
        q2 = PriorityQueue()
        q2_cluster_num = q_cluster_num
        for score, label in q.queue:
            q2.put((score, label))
            # if -score <= 0:
            #     q2.put((score, label))
            #     continue
            # q2_cluster_num -= getClusterScore(label)
            # append_list = []
            # append_num = 0
            # for child_name in hierarchy['hierarchy'][hierarchy['id2label'][label]]['children']:
            #     child = hierarchy['hierarchy'][child_name]['id']
            #     if child not in label_frequncy:
            #         # continue
            #         label_frequncy[child] = 0
            #     append_list.append((-getLabelScore(child), child))
            #     append_num += getClusterScore(child)
            # for item in append_list:
            #     q2.put(item)
            # q2_cluster_num += append_num

        # from IPython import embed; embed()
        while q2_cluster_num < level2_range[0] or -q2.queue[0][0] > spilit_size:
            score, label = q2.get()
            q2_cluster_num -= getClusterScore(label)
            if -score <= 0: # or len(q2.queue) + len(hierarchy['hierarchy'][hierarchy['id2label'][label]]['children']) > level2_range[1]:
                q2.put((score, label))
                q2_cluster_num += getClusterScore(label)
                break

            append_list = []
            append_num = 0
            for child_name in hierarchy['hierarchy'][hierarchy['id2label'][label]]['children']:
                child = hierarchy['hierarchy'][child_name]['id']
                if child not in label_frequncy:
                    # continue
                    label_frequncy[child] = 0
                append_list.append((-getLabelScore(child), child))
                append_num += getClusterScore(child)

            if append_num < getClusterScore(label):
                q2.put((score, label))
                q2_cluster_num += getClusterScore(label)
                break
                
            if q2_cluster_num + append_num < level2_range[1] + (level2_range[0] - q2_cluster_num) or -score > spilit_size:
                for item in append_list:
                    q2.put(item)
                q2_cluster_num += append_num
                # if q2_cluster_num >= level2_range[0]:
                #     break
            else:
                q2.put((score, label))
                q2_cluster_num += getClusterScore(label)
                break
        # print("p2", filter_list)
        # from IPython import embed; embed()

        # if len(self.label_stack) > 0 and np.load("application/data/use_case.npy")[0]:
        if zoom_without_expand:
            q2 = PriorityQueue()
            q2_cluster_num = q_cluster_num
            for score, label in q.queue:
                q2.put((score, label))

        largest = None
        for score, label in q2.queue:
            if largest is None or label_frequncy[label] > label_frequncy[largest]:
                largest = label
                
        level2_labels = [0 for _ in range(len(labels))]
        tree_cut = []
        for score, label in q2.queue:
            tree_cut.append(label)
            if -score < 0:
                continue
            if (label != largest) and (label_frequncy[label] <= filter_num):
                filter_list[1].add(label)
            for node in label_nodes[label]:
                level2_labels[node] = label

        level1_labels = np.array(level1_labels)
        level2_labels = np.array(level2_labels)

        filter_list = [list(filter_list[0]), list(filter_list[1])]

        if len(self.label_stack) == 0:
            level1_labels = np.array(first_labels)
            filter_list[0] = []

        self.label_stack.append([level1_labels, level2_labels, filter_list, tree_cut])
        return level1_labels, level2_labels, filter_list

    def getSample(self, features, ids, num, select=None, labels=None):
        if select is None:
            # return np.array(random.sample(ids.tolist(), min(len(ids), num)))
            if labels is None:
                return self.sampler.sample(features[ids], ids, num)
            else:
                return self.sampler.sample(features[ids], ids, num, labels[ids])
        else:
            samples = np.intersect1d(ids, select)
            if len(samples) > num:
                samples = samples[:num]
            if len(samples) < num:
                others = np.setdiff1d(ids, select)
                # more = random.sample(others.tolist(), min(len(others), num-len(samples)))
                if labels is None:
                    more = self.sampler.sample(features[others], others, num-len(samples))
                else:
                    more = self.sampler.sample(features[others], others, num-len(samples), labels[others])
                samples = np.concatenate((samples, more)).astype('int')
            return samples

    def adjustGridSize(self, grid_size, tot_num, min_size=None):
        new_grid_size = grid_size
        l = 0
        r = 1
        while l+0.0001<r:
            mid = (l+r)/2
            tmp_grid_size = [round(grid_size[0]*mid), round(grid_size[1]*mid)]
            if min_size is not None:
                tmp_grid_size[0] = max(tmp_grid_size[0], min_size[0])
                tmp_grid_size[1] = max(tmp_grid_size[1], min_size[1])
            if tmp_grid_size[0]*tmp_grid_size[1] >= tot_num:
                new_grid_size = tmp_grid_size
                r = mid
            else:
                l = mid
        return new_grid_size

    def getSpilitRatio(self, n):
        if n>2100:
            return 350/n
        if n>1050:
            return 1/6
        if n>525:
            return 175/n
        return 1/3

    def getTopLayout(self, use_cache=True):

        self.clean_stacks()

        cache_layout = None
        if use_cache and os.path.exists(os.path.join(self.cache_path, "cache_layout.pkl")):
            cache_layout = load_pickle(os.path.join(self.cache_path, "cache_layout.pkl"))

        random.seed(42)
        np.random.seed(42)

        grid_size = self.sample_num

        features = self.features
        labels = self.labels
        gt_labels = self.gt_labels
        full_ids = np.arange(len(labels), dtype='int')

        grid_size = self.adjustGridSize(grid_size, len(full_ids))

        spilit_ratio = self.getSpilitRatio(grid_size[0]*grid_size[1])
        top_labels, labels, filter_labels = self.reduce_labels(labels, self.hierarchy, spilit_ratio=spilit_ratio)
        gt_labels = self.reduce_now_labels(gt_labels)

        merge_labels = mergeSmallLabels(labels, top_labels, filter_labels)

        label_map, label_map_back, new_labels, top_part = getLabelMap(merge_labels)

        layout_time = 0
        start = time.time()

        centers, edge_matrix = get_FD_layout_centers(features, new_labels, None, cache_layout=cache_layout)

        # # np.save("draw_treemap/"+self.dataset+"/centers.npy", centers)
        # # tmp_count = np.zeros(len(centers))
        # # for i in new_labels:
        # #     tmp_count[i] += 1
        # # np.save("draw_treemap/"+self.dataset+"/count.npy", tmp_count)
        # centers = np.load("draw_treemap/"+self.dataset+"/centers.npy")

        # import matplotlib.pyplot as plt
        # plt.switch_backend('agg')
        # plt.clf()
        # plt.scatter(centers[:, 0], centers[:, 1], color=plt.cm.tab20(np.arange(len(centers)).astype('int')))
        # plt.savefig("centers.png")

        start0 = time.time()
        tmp_cut = getTreeSlice(new_labels, centers, grid_size, treemap_type=self.treemap_type)
        tree_time = time.time()-start0

        grid_dict = getPartGrids(tmp_cut, new_labels, [0, 0, grid_size[0], grid_size[1]])

        layout_time += time.time()-start

        grid_solve_dict = {}
        feature_mean = np.zeros((new_labels.max()+1, features.shape[1]))
        grids_mean = np.zeros((new_labels.max()+1, 2))
        for lb in grid_dict:
            grid_box = grid_dict[lb]
            lb_grid_num = (grid_box[2]-grid_box[0])*(grid_box[3]-grid_box[1])
            candi_ids = np.arange(len(new_labels), dtype='int')[new_labels==lb]
            sample_ids = self.getSample(features, candi_ids, lb_grid_num, labels=labels)

            if len(sample_ids) == 0:
                continue

            grids = []
            # cnt = 0
            # for i in range(grid_box[0], grid_box[2]):
            #     for j in range(grid_box[1], grid_box[3]):
            #         if cnt >= len(sample_ids):
            #             break
            #         grids.append((i, j))
            #         cnt += 1
            for i in range(grid_box[0], grid_box[2]):
                for j in range(grid_box[1], grid_box[3]):
                    grids.append((i, j))
            dist = cdist((np.array([grid_size])-1)/2, np.array(grids), "euclidean")[0]
            grids = np.array(grids)
            # sort_ids = np.argsort(dist)
            # grids = grids[sort_ids]
            grids = grids[:len(sample_ids)].tolist()

            grid_solve_dict[lb] = {"grids": grids, "sample_ids": sample_ids, "features": features[sample_ids], "info_before": None}
            feature_mean[lb] = features[sample_ids].mean(axis=0)
            grids_mean[lb] = np.array(grids).mean(axis=0)

        start = time.time()

        for lb in grid_solve_dict:
            grid_solve_dict[lb]["init_pos"] = getInitPos(edge_matrix[lb], grid_solve_dict[lb]["features"], feature_mean, grids_mean)

        # save_pickle(grid_solve_dict, "draw_treemap/"+self.dataset+"/"+self.treemap_type+"_result.pkl")

        AssignQAP(grid_solve_dict)

        layout_time += time.time()-start

        tmp_grids = []
        tmp_labels = []
        tmp_features = []
        tmp_samples = []
        true_samples = []
        for lb in grid_solve_dict:
            grids = grid_solve_dict[lb]["grids"]
            sample_ids = grid_solve_dict[lb]["sample_ids"]
            tmp_grids.extend(grids)
            tmp_samples.extend(sample_ids)
            true_samples.extend(full_ids[sample_ids].tolist())
            tmp_labels.extend([lb]*len(grids))
            tmp_features.extend(grid_solve_dict[lb]["features"].tolist())

        # # EVALUATION
        # _, auc50, auc20 = testNeighbor_full(np.array(tmp_grids), np.array(tmp_features), np.array(tmp_labels))
        # print(auc50, auc20)
        # bias = 0
        # compactness = 0
        # for lb in grid_solve_dict:
        #     grids = grid_solve_dict[lb]["grids"]
        #     bias += len(grids)*np.power(centers[lb]-grids_mean[lb]/np.array([grid_size[0], grid_size[1]]), 2).sum()
        #     for grid in grids:
        #         compactness += np.power((grids_mean[lb]-grid)/np.array([grid_size[0], grid_size[1]]), 2).sum()
        # bias /= len(tmp_grids)
        # compactness /= len(tmp_grids)
        # print("bias:", bias, "compactness:", compactness)
        #
        # area_diff = 0
        # area_dict1 = {}
        # area_dict2 = {}
        # unique_labels = np.unique(labels)
        # for lb in unique_labels:
        #     area1 = (labels == lb).sum()/len(labels)
        #     area2 = (labels[tmp_samples] == lb).sum()/len(tmp_samples)
        #     area_dict1[lb] = area1
        #     area_dict2[lb] = area2
        #     area_diff += abs(area1 - area2)
        #     # area_diff += np.power(abs(area1 - area2)/area1, 2)*area1
        # print("area_diff:", area_diff)
        #
        # order_cnt = 0
        # for lb1 in unique_labels:
        #     for lb2 in unique_labels:
        #         if lb1 != lb2 and lb1 not in filter_labels[1] and lb2 not in filter_labels[1]:
        #             if area_dict1[lb1] > area_dict1[lb2] and area_dict2[lb1] < area_dict2[lb2]:
        #                 order_cnt += 1
        # order_ratio = order_cnt / (len(unique_labels)*(len(unique_labels)-1)/2)
        # print("area order: ", order_cnt, order_ratio)
        # # -------------------------------  all measures  ----------------------------
        # score_dict = {'auc20': auc20, 'auc50': auc50}
        # score_dict.update({'bias': bias, 'comp': compactness, "area_diff": area_diff, "area_order": order_cnt, "area_order_ratio": order_ratio, "time": layout_time, "tree_time": tree_time})
        # name = self.treemap_type + "_" + self.dataset
        # sample_num = "(" + str(self.sample_num[0]) + "," + str(self.sample_num[1]) + ")"
        # name = name + "_" + sample_num
        # name = name + "_0.pkl"
        # name = sample_num + "/" + name
        # if os.path.exists(name):
        #     ans = load_pickle(name)
        # else:
        #     ans = {'top': []}
        # ans['top'].append(score_dict)
        # save_pickle(ans, name)

        # show_grid_tmp(tmp_grids, tmp_labels)

        all_tree = tmp_cut["ways"]
        partition_info = {}
        partition_info['partition_labels'] = new_labels[tmp_samples]
        for item in reversed(all_tree):
            if item['child'] is not None:
                child1, child2 = item['child']
                item['size'] = child1['size'] + child2['size']
            partition_info['part_way'] = all_tree

        hang_samples = np.setdiff1d(full_ids, true_samples)
        sampled_addition = self.sampler.getNearestHangIndex(self.features, np.array(true_samples), hang_samples, getNowlabels=self.get_now_labels)
        self.sample_stack.append([true_samples, sampled_addition])
        self.grid_stack.append([tmp_grids, grid_size, new_labels[tmp_samples], partition_info, features[tmp_samples], top_part, None])

        self.label_stack[-1][1] = labels[tmp_samples]
        self.label_stack[-1][0] = top_labels[tmp_samples]

        if use_cache:
            new_cache = {"grids": tmp_grids, "labels": new_labels[tmp_samples], "sample_ids": np.array(tmp_samples)}
            new_cache.update({"centers": centers, "edge_matrix": edge_matrix})
            save_pickle(new_cache, os.path.join(self.cache_path, "cache_layout.pkl"))

        return tmp_grids, grid_size, labels[tmp_samples], top_labels[tmp_samples], gt_labels[tmp_samples], new_labels[tmp_samples], true_samples, features[tmp_samples], top_part, None

    def getSampleSpace(self, selected, sampled_id_before, sampled_addition_before):
        selected_id = np.array(sampled_id_before)[selected]
        sample_space = selected_id.tolist()
        for i in selected:
            sample_space.extend(sampled_addition_before[i])
        return np.array(sample_space)

    def getMinSize(self, grids, selected):
        x_list = []
        y_list = []
        for grid in grids[selected]:
            if grid[0] not in x_list:
                x_list.append(grid[0])
            if grid[1] not in y_list:
                y_list.append(grid[1])
        return [len(x_list), len(y_list)]

    def gridZoomIn(self, selected, zoom_without_expand=False, zoom_balance=False):
        random.seed(42)
        np.random.seed(42)

        grid_size = self.sample_num

        old_sampled_id = self.sample_stack[-1][0]
        old_sampled_addition = self.sample_stack[-1][1]
        full_ids = self.getSampleSpace(selected, old_sampled_id, old_sampled_addition)

        min_size = self.getMinSize(np.array(self.grid_stack[-1][0]), selected)
        grid_size = self.adjustGridSize(grid_size, len(full_ids), min_size)

        features = self.features[full_ids]
        labels = self.labels[full_ids]
        gt_labels = self.gt_labels[full_ids]

        spilit_ratio = self.getSpilitRatio(grid_size[0]*grid_size[1])
        top_labels, labels, filter_labels = self.reduce_labels(labels, self.hierarchy, zoom_without_expand=zoom_without_expand, spilit_ratio=spilit_ratio)
        gt_labels = self.reduce_now_labels(gt_labels)

        selected_now = list(range(len(selected)))
        info_before = {"selected": selected_now,
                       "selected_bf": selected,
                       "grids": self.grid_stack[-1][0],
                       "partition_info_bf": self.grid_stack[-1][3],
                       "sampled_id": old_sampled_id}

        new_top_labels = solveTopLabels(features, labels, top_labels, filter_labels, info_before)

        merge_labels = mergeSmallLabels(labels, new_top_labels, filter_labels)

        label_map, label_map_back, new_labels, top_part = getLabelMap(merge_labels, new_top_labels)

        centers, edge_matrix = get_FD_layout_centers(features, new_labels, info_before)

        zoom_partition_map = {}
        partition_info_bf = info_before['partition_info_bf']
        partition_labels_bf = partition_info_bf['partition_labels']

        for p in top_part:
            idx = (top_part[new_labels[info_before['selected']]] == p)
            count = Counter(partition_labels_bf[np.array(info_before['selected_bf'])[idx]])
            zoom_partition_map[p] = max(count, key=lambda x:count[x])

        all_tree_bf = partition_info_bf['part_way']
        top_grid_dict, top_cut = get_partition_HV_zoom(grid_size, top_part[new_labels], zoom_partition_map, all_tree_bf)

        all_tree = top_cut['ways']

        grid_dict = {}
        for p in range(top_part.max()+1):
            sub_grid = top_grid_dict[p]
            sub_size = [sub_grid[2]-sub_grid[0], sub_grid[3]-sub_grid[1]]
            idx = (top_part[new_labels]==p)
            sub_cnt = Counter(new_labels[idx])
            # print("sub partition", p, sub_cnt)
            tmp_label_list = np.arange(len(top_part), dtype='int')[top_part==p]

            if len(sub_cnt) > 1:
                sub_cut = getTreeSlice(new_labels, centers, sub_size, tmp_label_list)
                tmp_grid_dict = getPartGrids(sub_cut, new_labels, sub_grid)
                grid_dict.update(tmp_grid_dict)
                for item in all_tree:
                    if 'part_id' in item and item['part_id'] == str(p)+"-top":
                        item['part_id'] = None
                        copyPartTree(item, sub_cut['ways'][0], all_tree)
            else:
                for lb in sub_cnt:
                    grid_dict[lb] = top_grid_dict[p]
                    for item in all_tree:
                        if 'part_id' in item and item['part_id'] == str(p)+"-top":
                            item['part_id'] = lb
                            item['size'] = sub_cnt[lb]

        grid_solve_dict = {}
        feature_mean = np.zeros((new_labels.max()+1, features.shape[1]))
        grids_mean = np.zeros((new_labels.max()+1, 2))
        for lb in grid_dict:
            grid_box = grid_dict[lb]
            lb_grid_num = (grid_box[2]-grid_box[0])*(grid_box[3]-grid_box[1])
            candi_ids = np.arange(len(new_labels), dtype='int')[new_labels==lb]
            sample_ids = self.getSample(features, candi_ids, lb_grid_num, selected_now, labels=labels)

            if len(sample_ids) == 0:
                continue

            grids = []
            # cnt = 0
            # for i in range(grid_box[0], grid_box[2]):
            #     for j in range(grid_box[1], grid_box[3]):
            #         if cnt >= len(sample_ids):
            #             break
            #         grids.append((i, j))
            #         cnt += 1
            for i in range(grid_box[0], grid_box[2]):
                for j in range(grid_box[1], grid_box[3]):
                    grids.append((i, j))
            dist = cdist((np.array([grid_size])-1)/2, np.array(grids), "euclidean")[0]
            grids = np.array(grids)
            # sort_ids = np.argsort(dist)
            # grids = grids[sort_ids]
            grids = grids[:len(sample_ids)].tolist()

            grid_solve_dict[lb] = {"grids": grids, "sample_ids": sample_ids, "features": features[sample_ids], "info_before": info_before}
            feature_mean[lb] = features[sample_ids].mean(axis=0)
            grids_mean[lb] = np.array(grids).mean(axis=0)

        for lb in grid_solve_dict:
            grid_solve_dict[lb]["init_pos"] = getInitPos(edge_matrix[lb], grid_solve_dict[lb]["features"], feature_mean, grids_mean)

        # tmp_grids = []
        # tmp_labels = []
        # tmp_features = []
        # for lb in grid_solve_dict:
        #     grids = grid_solve_dict[lb]["grids"]
        #     tmp_grids.extend(grids)
        #     tmp_labels.extend([lb]*len(grids))
        #     tmp_features.extend(grid_solve_dict[lb]["features"].tolist())
        # print(testNeighbor_full(np.array(tmp_grids), np.array(tmp_features), np.array(tmp_labels)))

        AssignQAP(grid_solve_dict)

        tmp_grids = []
        tmp_labels = []
        tmp_samples = []
        true_samples = []
        tmp_features = []
        for lb in grid_solve_dict:
            grids = grid_solve_dict[lb]["grids"]
            sample_ids = grid_solve_dict[lb]["sample_ids"]
            tmp_grids.extend(grids)
            tmp_samples.extend(sample_ids)
            true_samples.extend(full_ids[sample_ids].tolist())
            tmp_labels.extend([lb]*len(grids))
            tmp_features.extend(grid_solve_dict[lb]["features"].tolist())
        # print(testNeighbor_full(np.array(tmp_grids), np.array(tmp_features), np.array(tmp_labels)))

        # show_grid_tmp(tmp_grids, tmp_labels)

        # show_stability(info_before, grid_solve_dict)

        partition_info = {}
        partition_info['partition_labels'] = new_labels[tmp_samples]
        for item in reversed(all_tree):
            if item['child'] is not None:
                child1, child2 = item['child']
                item['size'] = child1['size'] + child2['size']
            partition_info['part_way'] = all_tree

        hang_samples = np.setdiff1d(full_ids, true_samples)
        sampled_addition = self.sampler.getNearestHangIndex(self.features, np.array(true_samples), hang_samples, getNowlabels=self.get_now_labels)
        self.sample_stack.append([true_samples, sampled_addition])
        self.grid_stack.append([tmp_grids, grid_size, new_labels[tmp_samples], partition_info, features[tmp_samples], top_part, info_before])

        self.label_stack[-1][1] = labels[tmp_samples]
        self.label_stack[-1][0] = top_labels[tmp_samples]

        return tmp_grids, grid_size, labels[tmp_samples], top_labels[tmp_samples], gt_labels[tmp_samples], new_labels[tmp_samples], true_samples, features[tmp_samples], top_part, info_before

    def gridZoomOut(self):
        if len(self.grid_stack) > 1:
            self.grid_stack.pop()
            self.sample_stack.pop()
            self.label_stack.pop()

        grids = self.grid_stack[-1][0]
        grid_size = self.grid_stack[-1][1]
        partition = self.grid_stack[-1][2]
        sampled_id = self.sample_stack[-1][0]
        labels = self.label_stack[-1][1]
        top_labels = self.label_stack[-1][0]
        gt_labels = self.reduce_now_labels(self.gt_labels[sampled_id])
        feature = self.grid_stack[-1][4]
        top_part = self.grid_stack[-1][5]
        info_before = self.grid_stack[-1][6]
        return grids, grid_size, labels, top_labels, gt_labels, partition, sampled_id, feature, top_part, info_before
