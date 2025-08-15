import random

from scipy.optimize import quadratic_assignment
import numpy as np
import time
import math
from multiprocessing import dummy
from multiprocessing.pool import ThreadPool
from sklearn.manifold._t_sne import _joint_probabilities
from sklearn.manifold._t_sne import _joint_probabilities_nn
from sklearn.manifold import TSNE
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
from .qap import quadratic_assignment_faq
# from lapjv import lapjv as lsa
from lsa import linear_sum_assignment as lsa

import pickle

def save_pickle(data, file):
    with open(file, 'wb') as f:
        pickle.dump(data, f)

def load_pickle(file):
    with open(file, 'rb') as f:
        return pickle.load(f)

from scipy.sparse import csr_matrix
from scipy.spatial.distance import squareform
from collections import Counter
from sklearn_extra.cluster import KMedoids
from sklearn.cluster import KMeans
import networkx as nx

def get_init_kmedoids_with_pos(feature, grids, init_pos=None):
    from .utils import kamada_kawai_layout
    n = len(feature)
    m = max(min(20, len(feature)), int(len(feature)/30))

    dist = cdist(feature, feature, "eu") + ((1 - np.eye(n)) * 1e-5)
    kmedoids = KMedoids(n_clusters=m, random_state=42, metric='precomputed')
    father = kmedoids.fit_predict(dist)

    cost_matrix = np.zeros((n, n))

    if init_pos is not None:
        g_dist = cdist(init_pos, grids, "eu")
        for i in range(m):
            tmp_idx = (father == i)
            cost_matrix[tmp_idx] = g_dist[tmp_idx].mean(axis=0)

    sol = lsa(cost_matrix)[0]
    centers = np.zeros((m, 2))
    grids = grids - grids.min(axis=0)
    grids = grids / (grids.max(axis=0)+1e-8)
    for i in range(m):
        tmp_idx = (father == i)
        centers[i] = grids[sol[tmp_idx]].mean(axis=0)
    # centers = centers + np.random.normal(0, 0.001, (m, 2))

    feature_mean = []
    for i in range(m):
        tmp_idx = (father == i)
        feature_mean.append(feature[tmp_idx].mean(axis=0))
    f_dist = cdist(feature_mean, feature_mean, 'eu')
    if m > 1:
        f_dist = squareform(f_dist) + 1e-6
        if f_dist.max() > f_dist.min() + 1e-6:
            f_dist = f_dist - f_dist.min()
        f_dist = squareform(f_dist)
        f_dist /= f_dist.max()
        tmp_min = 1 / np.sqrt(2) / (np.sqrt(m) - 0.999)
        tmp_delta = 1 - tmp_min
        f_dist = squareform(squareform(f_dist) * tmp_delta + tmp_min)
    f_dist = squareform(squareform(f_dist) + 1e-3)
    f_dict = {}
    for i in range(m):
        f_dict[i] = {}
        for j in range(m):
            f_dict[i][j] = f_dist[i][j]

    pos = {}
    for i in range(m):
        pos[i] = centers[i] - 0.5
    G_full = nx.complete_graph(m)
    # pos = nx.random_layout(G_full, seed=0)
    pos = kamada_kawai_layout(G_full, pos=pos, dist=f_dict, tol=1e-3)
    result = np.zeros((m, 2))
    for i in range(m):
        result[i] = np.array(pos[i])

    return result, father


def AssignQAP(grid_solve_dict, scale=1/2, best_w=None, _maxit=20):
    random.seed(42)
    np.random.seed(42)

    start0 = time.time()
    time1 = 0
    time2 = 0
    time3 = 0
    time4 = 0
    FD_dict = {}

    for lb in grid_solve_dict:
        item = grid_solve_dict[lb]
        grids = np.array(item["grids"])
        features = np.array(item["features"])

        if item["info_before"] is not None:
            item["if_selected"] = np.ones(len(item["sample_ids"]), dtype='int') * -1
            select_map = {}
            for i in range(len(item["info_before"]["selected"])):
                id = item["info_before"]["selected"][i]
                select_map[id] = i
            for i in range(len(item["sample_ids"])):
                id = item["sample_ids"][i]
                if id in select_map:
                    item["if_selected"][i] = select_map[id]

        start1 = time.time()

        n = len(grids)

        if n == 1:
            F = np.array([[0]])
        else:
            perplexity = 30
            n_neighbors = min(n - 1, int(3.0 * perplexity + 1))

            now_dist = cdist(features, features, 'eu')
            knn_matrix = np.argsort(now_dist, axis=1)[:, 1:n_neighbors + 1]
            knn_distances = np.take_along_axis(now_dist, knn_matrix, axis=1)
            rows = np.repeat(np.arange(n), n_neighbors)
            cols = knn_matrix.flatten()
            data = knn_distances.flatten()
            cost_matrix_nn = csr_matrix((data, (rows, cols)), shape=(n, n))

            cost_matrix_nn.data **= 2
            P = _joint_probabilities_nn(cost_matrix_nn, perplexity, False)
            F = P.toarray()

        D = cdist(grids, grids, "euclidean")
        D = np.power(D, 2) * scale * scale
        D = np.log(1 + D)

        time1 += time.time() - start1
        sta_grids = None
        selected_list = None
        father = None

        if item["info_before"] is not None:

            start2 = time.time()

            sta_grids = []
            selected_list = []

            Fx = np.zeros((n, n))
            Dx = np.zeros((n, n))
            Fy = np.zeros((n, n))
            Dy = np.zeros((n, n))

            time2 += time.time() - start2

            grids_bf = item["info_before"]["grids"]
            selected_bf = item["info_before"]["selected_bf"]
            selected_index = np.ones(len(selected_bf), dtype='int') * -1
            for i in range(n):
                if item["if_selected"][i] >= 0:
                    selected_index[item["if_selected"][i]] = i
                    sta_grids.append(grids_bf[selected_bf[item["if_selected"][i]]])
                    selected_list.append(i)
            sta_grids = np.array(sta_grids)
            selected_list = np.array(selected_list)

            if len(selected_list) > 0:

                start3 = time.time()

                for i in range(len(selected_bf)):
                    if selected_index[i] >= 0:
                        id1 = selected_index[i]
                    else:
                        continue
                    for j in range(len(selected_bf)):
                        if selected_index[j] >= 0:
                            id2 = selected_index[j]
                        else:
                            continue
                        if grids_bf[selected_bf[i]][0] < grids_bf[selected_bf[j]][0]:
                            Fx[id1][id2] = 1
                        if grids_bf[selected_bf[i]][1] < grids_bf[selected_bf[j]][1]:
                            Fy[id1][id2] = 1

                time3 += time.time() - start3

                start4 = time.time()

                for i in range(n):
                    td_x = grids[:, 0] <= grids[i][0]
                    Dx[i][td_x] = scale * scale
                    td_y = grids[:, 1] <= grids[i][1]
                    Dy[i][td_y] = scale * scale

                addition_AB = [(Fx, Dx), (Fy, Dy)]
                # addition_AB = []

                father_dist = F[:, selected_list]
                father_dist[selected_list, np.arange(len(selected_list), dtype='int')] = 1
                father = np.argmax(father_dist, axis=1)

                time4 += time.time() - start4

            else:
                sta_grids = None
                selected_list = None
                father = None
                addition_AB = []
        else:
            addition_AB = []

        matrix0 = np.zeros((n, n))
        C = matrix0

        confuse_id = None

        solution0 = np.arange(n, dtype='int')
        np.random.seed(100)
        np.random.shuffle(solution0)
        P0 = np.eye(n)[solution0]

        init_pos = None
        if "init_pos" in item:
            init_pos = item["init_pos"]

        FD_dict[lb] = {"F": F, "D": D, "addition_AB": addition_AB, "C": C, "P0": P0, "solution0": solution0, "n": n,
                          "grids": grids, "sta_grids": sta_grids,
                          "selected_list": selected_list, "father": father,
                          "feature": features, "confuse_id": confuse_id, "init_pos": init_pos}

    def solve_Assign(lb, info):
        start = time.time()

        F = info["F"]
        D = info["D"]
        addition_AB = info["addition_AB"]
        C = info["C"]
        P0 = info["P0"]
        solution0 = info["solution0"]
        n = info["n"]
        grids = info["grids"]
        sta_grids = info["sta_grids"]
        selected_list = info["selected_list"]
        father = info["father"]
        feature_now = info["feature"]
        confuse_id = info["confuse_id"]
        init_pos = info["init_pos"]
        alpha = info["alpha"]

        if "P_pre" not in info:
            if sta_grids is not None:
                sta_grids = sta_grids.astype("float")
                delta = (sta_grids.max(axis=0) - sta_grids.min(axis=0))
                if delta[0] > 1e-8:
                    sta_grids[0] /= delta[0]
                if delta[1] > 1e-8:
                    sta_grids[1] /= delta[1]
                sta_grids *= (grids.max(axis=0) - grids.min(axis=0))
                sta_grids += grids.mean(axis=0) - sta_grids.mean(axis=0)
                # cost_matrix = np.zeros((n, n))
                # cost_matrix[selected_list, :] = np.power(cdist(sta_grids, grids, "euclidean"), 2)
                cost_matrix = np.power(cdist(sta_grids[father], grids, "euclidean"), 2)
                # cost_matrix += C[father] + C
                shuffle_col = np.arange(n, dtype='int')
                # np.random.shuffle(shuffle_col)
                solution2 = shuffle_col[lsa(cost_matrix[:, shuffle_col])[0]]
                P0 = np.eye(n)[solution2]
                solution0 = solution2
            else:
                sta_grids, father = get_init_kmedoids_with_pos(feature_now, grids, init_pos)
                # print("achor time", time.time()-start)
                sta_grids /= (sta_grids.max(axis=0) - sta_grids.min(axis=0) + 1e-12)
                sta_grids *= (grids.max(axis=0) - grids.min(axis=0))
                sta_grids += grids.mean(axis=0) - sta_grids.mean(axis=0)
                # cost_matrix = np.zeros((n, n))
                # cost_matrix[selected_list, :] = np.power(cdist(sta_grids, grids, "euclidean"), 2)
                cost_matrix = np.power(cdist(sta_grids[father], grids, "euclidean"), 2)
                # cost_matrix += C[father] + C
                shuffle_col = np.arange(n, dtype='int')
                # np.random.shuffle(shuffle_col)
                solution1 = shuffle_col[lsa(cost_matrix[:, shuffle_col])[0]]
                P0 = np.eye(n)[solution1]
                solution0 = solution1

            info["P_pre"] = P0
            info["solution_pre"] = solution0

            c_norm = 0
            if confuse_id is not None:
                tmp = (F @ P0 @ D.T + F.T @ P0 @ D)
                mean1 = (tmp[confuse_id].max(axis=1) - tmp[confuse_id].min(axis=1)).mean()
                mean2 = (C[confuse_id].max(axis=1) - C[confuse_id].min(axis=1)).mean()
                # print(mean1)
                # print(mean2)

                if mean2 > 0:
                    c_norm = mean1 / mean2
                else:
                    c_norm = 0

            C = C * c_norm
            info["c_norm"] = c_norm
        else:
            P0 = info["P_pre"]
            solution0 = info["solution_pre"]
            C = C * info["c_norm"]

        old_C, old_D = C, D

        # print("pre time 1", lb, n, time.time() - start)

        D = D * alpha
        C = C * (1 - alpha)

        # print("pre time 2", lb, n, time.time() - start)

        sparse = False
        if (len(addition_AB) > 0) and (addition_AB[0][0].sum() + addition_AB[1][0].sum() < 4 * (n / 20) ** 2):
            sparse = True

        maxit = _maxit
        ans2 = quadratic_assignment_faq(F, D, addition_AB, C, P0=P0, addition_sparse=sparse, maxiter=maxit, tol=0)
        solution2 = ans2["col_ind"]
        # print(ans2)
        # if len(addition_AB)>0:
        #     tmp = addition_AB[0][0] * addition_AB[0][1][solution2][:, solution2] + addition_AB[1][0] * addition_AB[1][1][solution2][:, solution2]
        #     print("xy", tmp.sum())
        # solution2 = solution0

        info["score"] = np.sum(F * old_D[solution2][:, solution2])
        info["cscore"] = np.sum(old_C[np.arange(n), solution2])

        # print("qap time", lb, n, time.time() - start)

        # print(ans2)
        return {lb: solution2}


    def getQAP(alpha=0.5):
        for label in FD_dict:
            FD_dict[label]["alpha"] = alpha

        maxLabel = len(FD_dict.keys())
        pool = ThreadPool(min(32, maxLabel))
        work_list = []
        for label in FD_dict:
            work_list.append((label, FD_dict[label]))
        result = pool.starmap_async(solve_Assign, work_list)
        pool.close()
        pool.join()
        result = result.get()
        ans = {}
        for item in result:
            ans.update(item)

        avg_score, avg_cscore = 0, 0
        for label in FD_dict:
            avg_score += FD_dict[label]["score"]
            avg_cscore += FD_dict[label]["cscore"]
        avg_score /= maxLabel
        avg_cscore /= maxLabel
        return ans, avg_score, avg_cscore

    # ---------------use fixed weight parameter for faster layout------------------
    if best_w is None:
        best_w = 0.15
    # print("best w", best_w)
    result, result_score, result_cscore = getQAP(best_w)
    # ---------------------------------------------------------------

    # # -------------use multi-task weight parameter------------------
    # goal = 2
    # pro_result, best_score, worst_cscore = getQAP(1)
    # conf_result, worst_score, best_cscore = getQAP(0.001)
    # left, right = 0, 1
    # best_solution = None
    # best_d = 0
    # for i in range(3):
    #     mid = (left + right) / 2
    #     new_result, new_score, new_cscore = getQAP(mid)
    #     d1 = (new_score - worst_score) / (best_score - worst_score)
    #     d2 = (new_cscore - worst_cscore) / (best_cscore - worst_cscore)
    #     if goal*d1 <= d2:
    #         left = mid
    #     else:
    #         right = mid
    #
    #     if best_solution is None or abs(goal * d1 - d2) / (d1 + d2) < best_d:
    #         best_d = abs(goal * d1 - d2) / (d1 + d2)
    #         best_solution = new_result.copy()
    #         result_score, result_cscore = new_score, new_cscore
    #
    # #     print("multitask", mid, d1, d2)
    #
    # result = best_solution
    # # -----------------------------------------------------------

    for label in FD_dict:
        solution2 = result[label]
        grids = np.array(grid_solve_dict[label]["grids"])
        grids = grids[solution2]
        grid_solve_dict[label]["grids"] = grids.tolist()

    return
