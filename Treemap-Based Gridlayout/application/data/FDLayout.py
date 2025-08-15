import numpy as np
import networkx as nx
from scipy.spatial.distance import squareform
from scipy.spatial.distance import cdist
import math
from .utils import kamada_kawai_layout, get_kamada_kawai_costfn_stability

def getInitPos(edges, features, feature_mean, centers):
    f_dist = cdist(features, feature_mean, "euclidean")
    init_pos = np.zeros((len(features), 2))
    for i in range(len(features)):
        tmp_pos = np.array([0.0, 0.0])
        tmp_cnt = 0
        for j in range(len(edges)):
            if not edges[j]:
                continue
            weight = 1/max(0.000001, f_dist[i][j])
            tmp_pos += weight*centers[j]
            tmp_cnt += weight

        if tmp_cnt > 0:
            tmp_pos /= tmp_cnt
        init_pos[i] = tmp_pos
    return init_pos

def get_planar(f_dist, maxLabel):
    tmp_dist = squareform(f_dist)
    sort_id = np.argsort(tmp_dist)
    G = nx.empty_graph(maxLabel)
    cnt = 0
    map = {}
    for i in range(maxLabel):
        for j in range(i + 1, maxLabel):
            map[cnt] = (i, j)
            cnt += 1
    edge_cnt = 0
    for id in sort_id:
        i, j = map[id]
        G.add_edge(i, j, weight=f_dist[i][j])
        if not nx.is_planar(G):
            G.remove_edge(i, j)
            # if nx.is_connected(G):
            #     break
        else:
            edge_cnt += 1
    return G

def get_FD_layout_centers_stability(f_dict, old_pos, keep, goal=2, planer_G=None):

    maxLabel = len(old_pos)

    stability = {"old_pos": old_pos, "keep": keep}
    G_full = nx.complete_graph(maxLabel)
    pos_dict = {}
    for i in range(maxLabel):
        pos_dict[i] = old_pos[i]
    tmp_pos = pos_dict
    if planer_G is not None:
        tmp_pos = kamada_kawai_layout(planer_G, pos=pos_dict, options={"maxiter": 20})
    kk_pos_dict = kamada_kawai_layout(G_full, pos=tmp_pos, dist=f_dict, options={"maxiter": 20})
    kk_pos = np.zeros((maxLabel, 2))
    for i in range(maxLabel):
        kk_pos[i] = np.array(kk_pos_dict[i])

    # kk_scale = (kk_pos.max(axis=0)-kk_pos.min(axis=0)).sum()
    # old_scale = (old_pos.max(axis=0)-old_pos.min(axis=0)).sum()
    kk_scale = kk_pos.std(axis=0).sum()
    old_scale = old_pos.std(axis=0).sum()
    # print("scale", old_scale, kk_scale)
    if old_scale > 0 and kk_scale > 0:
        old_pos = old_pos*kk_scale/old_scale      # scale normalize
        stability["old_pos"] = old_pos

    best_kk, worst_sta = get_kamada_kawai_costfn_stability(G_full, dist=f_dict, pos=kk_pos, old_pos=old_pos, keep=keep)
    worst_kk, best_sta = get_kamada_kawai_costfn_stability(G_full, dist=f_dict, pos=old_pos, old_pos=old_pos, keep=keep)

    norm_ratio = 1
    if worst_sta-best_sta > 1e-12:
        norm_ratio = (worst_kk-best_kk)/(worst_sta-best_sta)
    else:
        return kk_pos

    if worst_kk-best_kk <= 1e-12:
        return old_pos

    stability["norm_ratio"] = norm_ratio

    left, right = 0, 1
    best_pos = None
    best_d = 0
    for i in range(2):
        mid = (left + right) / 2
        stability["sta_alpha"] = mid
        tmp_pos = pos_dict
        if planer_G is not None:
            tmp_pos = kamada_kawai_layout(planer_G, pos=pos_dict, options={"maxiter": 20}, stability=stability)
        new_pos_dict = kamada_kawai_layout(G_full, pos=tmp_pos, dist=f_dict, options={"maxiter": 20}, stability=stability)
        new_pos = np.zeros((maxLabel, 2))
        for i in range(maxLabel):
            new_pos[i] = np.array(new_pos_dict[i])
        new_kk, new_sta = get_kamada_kawai_costfn_stability(G_full, dist=f_dict, pos=new_pos, old_pos=old_pos, keep=keep)

        d1 = (new_kk - worst_kk) / (best_kk - worst_kk)
        d2 = (new_sta - worst_sta) / (best_sta - worst_sta)
        if goal*d1 <= d2:
            left = mid
        else:
            right = mid

        if best_pos is None or abs(goal * d1 - d2) / (d1 + d2) < best_d:
            best_d = abs(goal * d1 - d2) / (d1 + d2)
            best_pos = new_pos.copy()

        # print("FD multitask", mid, d1, d2)

    return best_pos

def get_FD_layout_centers(X_feature, labels, info_before, conf=None, alpha=0.5, cache_layout=None):
    from scipy.stats import entropy
    maxLabel = labels.max() + 1

    if maxLabel == 1:
        return np.array([[0.5, 0.5]]), np.array([[False]])

    feature_mean = []
    for lb in range(maxLabel):
        feature_mean.append(X_feature[labels == lb].mean(axis=0))
    feature_mean = np.array(feature_mean)

    f_dist = cdist(feature_mean, feature_mean, "euclidean")

    if maxLabel > 3:
        f_dist = squareform(f_dist)
        if f_dist.max() > f_dist.min() + 1e-6:
            f_dist = f_dist - f_dist.min()
        f_dist = squareform(f_dist)
    f_dist /= f_dist.max()

    if conf is not None:
        labels_idx = {}
        for i in range(maxLabel):
            labels_idx[i] = (labels == i)
        c_list = []
        for i in range(maxLabel):
            c_list.append(conf[labels_idx[i]].mean(axis=0))
        c_list = np.array(c_list)
        for i in range(maxLabel):
            c_list[i] = np.maximum(c_list[i], 1e-6)
            c_list[i] /= c_list[i].sum()
        c_dist = np.zeros((maxLabel, maxLabel))
        for i in range(maxLabel):
            for j in range(maxLabel):
                c_dist[i][j] = entropy(c_list[i], c_list[j])
        c_dist = (c_dist + c_dist.T) / 2

    if conf is not None:
        if maxLabel > 3:
            c_dist = squareform(c_dist)
            if c_dist.max() > c_dist.min() + 1e-6:
                c_dist = c_dist - c_dist.min()
            c_dist = squareform(c_dist)
        c_dist /= c_dist.max()

    if maxLabel > 3:
        tmp_min = 1 / np.sqrt(2) / (np.sqrt(maxLabel) - 1)
        tmp_delta = 1 - tmp_min

        f_dist = squareform(squareform(f_dist) * tmp_delta + tmp_min)
        if conf is not None:
            c_dist = squareform(squareform(c_dist) * tmp_delta + tmp_min)

    if conf is not None:
        for i in range(maxLabel):
            for j in range(maxLabel):
                f_dist[i][j] = alpha * f_dist[i][j] + (1 - alpha) * c_dist[i][j]

    init = None
    caled = np.zeros(maxLabel, dtype='bool')

    if info_before is not None:
        tmp_embedded2 = np.array(info_before['grids']).astype("float")
        tmp_embedded2[info_before['selected_bf']] -= tmp_embedded2[info_before['selected_bf']].min(axis=0)-0.5
        tmp_embedded2[info_before['selected_bf']] /= tmp_embedded2[info_before['selected_bf']].max(axis=0)+0.5

        centers = np.zeros((maxLabel, 2))
        for p in range(maxLabel):
            idx = (labels[info_before['selected']] == p)
            if idx.sum() > 0:
                centers[p] = tmp_embedded2[info_before['selected_bf']][idx].mean(axis=0)
                caled[p] = True

        caled_list = np.arange(maxLabel, dtype='int')[caled]

        np.random.seed(0)
        if len(caled_list) > 0:
            dist_matrix = cdist(feature_mean, feature_mean[caled_list])
            for p in range(maxLabel):
                if not caled[p]:
                    indices = dist_matrix[p].argsort()
                    if len(indices) > 1:
                        centers[p] = (centers[caled_list[indices[0]]] + centers[
                            caled_list[indices[1]]]) / 2 + np.random.normal(0, 0.05, 2)
                    else:
                        centers[p] = centers[caled_list[indices[0]]] + np.random.normal(0, 0.1, 2)
            init = centers
            init += np.random.normal(0, 0.001, (maxLabel, 2))
        else:
            init = None

    if cache_layout is not None:
        tmp_embedded2 = np.array(cache_layout['grids']).astype("float")
        tmp_embedded2 -= tmp_embedded2.min(axis=0)-0.5
        tmp_embedded2 /= tmp_embedded2.max(axis=0)+0.5
        centers = np.zeros((maxLabel, 2))
        same_flag = True
        for p in range(maxLabel):
            idx = (labels[cache_layout['sample_ids']] == p)
            if (cache_layout["labels"][idx] != p).sum() > 0:
                same_flag = False
            if idx.sum() > 0:
                centers[p] = tmp_embedded2[idx].mean(axis=0)
                caled[p] = True
        caled_list = np.arange(maxLabel, dtype='int')[caled]
        if same_flag:
            # init = None
            return cache_layout["centers"], cache_layout["edge_matrix"]
        else:
            np.random.seed(0)
            if len(caled_list) > 0:
                dist_matrix = cdist(feature_mean, feature_mean[caled_list])
                for p in range(maxLabel):
                    if not caled[p]:
                        indices = dist_matrix[p].argsort()
                        if len(indices) > 1:
                            centers[p] = (centers[caled_list[indices[0]]] + centers[
                                caled_list[indices[1]]]) / 2 + np.random.normal(0, 0.05, 2)
                        else:
                            centers[p] = centers[caled_list[indices[0]]] + np.random.normal(0, 0.1, 2)
                init = centers
                init += np.random.normal(0, 0.001, (maxLabel, 2))
            else:
                init = None

    f_dict = {}
    for i in range(maxLabel):
        f_dict[i] = {}
        for j in range(maxLabel):
            f_dict[i][j] = f_dist[i][j]

    G = get_planar(f_dist, maxLabel)

    edge_matrix = np.zeros((maxLabel, maxLabel), dtype='bool')
    for e in G.edges():
        edge_matrix[e[0]][e[1]] = edge_matrix[e[1]][e[0]] = True

    if init is None:
        # import time
        # seed = int(time.time())
        # pos = nx.random_layout(G, seed=seed)
        pos = None
        pos = nx.kamada_kawai_layout(G, pos=pos)
    else:
        result = get_FD_layout_centers_stability(f_dict, init - init.mean(axis=0), caled, planer_G=G)

        result -= result.min(axis=0)
        result /= result.max(axis=0)

        return result, edge_matrix

    G_full = nx.complete_graph(maxLabel)
    pos = nx.kamada_kawai_layout(G_full, pos=pos, dist=f_dict)
    result = np.zeros((maxLabel, 2))
    for i in range(maxLabel):
        result[i] = np.array(pos[i])

    if info_before is None:
        best_result = None
        best_a = None
        for rid in range(16):
            r = rid * 2 * math.pi / 16
            tmp_result = np.zeros((maxLabel, 2))
            for lb in range(maxLabel):
                tmp_x = result[lb][0]
                tmp_y = result[lb][1]
                tmp_result[lb][0] = tmp_x * math.cos(r) - tmp_y * math.sin(r)
                tmp_result[lb][1] = tmp_x * math.sin(r) + tmp_y * math.cos(r)
            bound = tmp_result.max(axis=0) - tmp_result.min(axis=0)
            if best_a is None or bound[0] * bound[1] < best_a:
                best_a = bound[0] * bound[1]
                best_result = tmp_result
        result = best_result

    # random_rotate = True
    # if random_rotate:
    #     import random
    #     import time
    #     random.seed(time.time())
    #     rid = random.randint(0, 15)
    #     r = rid * 2 * math.pi / 16
    #     tmp_result = np.zeros((maxLabel, 2))
    #     for lb in range(maxLabel):
    #         tmp_x = result[lb][0]
    #         tmp_y = result[lb][1]
    #         tmp_result[lb][0] = tmp_x * math.cos(r) - tmp_y * math.sin(r)
    #         tmp_result[lb][1] = tmp_x * math.sin(r) + tmp_y * math.cos(r)
    #     result = tmp_result

    result -= result.min(axis=0)
    result /= result.max(axis=0)

    return result, edge_matrix