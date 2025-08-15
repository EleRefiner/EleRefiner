import random
from .grouping import eval_hierarchy
from .eval2 import calcOneScore, iou
import numpy as np
import copy
import time
import math
import os


def non_max_suppression(items, scores, iou_threshold):
    idxs = np.argsort(np.array(scores))[::-1]

    selected_items = []

    while len(idxs) > 0:
        current_idx = idxs[0]
        current_item = items[current_idx]
        selected_items.append(current_item)

        remaining_items = [items[idxs[i]] for i in range(1, len(idxs))]
        remaining_idxs = [idxs[i] for i in range(1, len(idxs))]

        remaining_idx_list = []
        for i, item in enumerate(remaining_items):
            # TODO check the nms strategy here
            if current_item["type"] != item["type"] or iou(current_item["box"], item["box"]) < iou_threshold:
                remaining_idx_list.append(remaining_idxs[i])

        idxs = np.array(remaining_idx_list)

    return selected_items


def eval(subset, full_dict_list, full_conf_list, image=None, nms_update=False, scale=1, line=3, padding=10, show=False,
         adjust=True, store=None, award_list=None, show_text=False, shape_dict=None, img_shape=None, tot_time=None, ori=False):
    if len(subset) == 0:
        return 0, 0, 0, 0, None

    dict_list = [full_dict_list[i] for i in subset]
    scores = [full_conf_list[i] for i in subset]

    # if not ori:
    #     dict_list = non_max_suppression(dict_list, scores, 0.65)
    #     # dict_list = non_max_suppression(dict_list, scores, 0.8)
    #     if nms_update:
    #         subset_to_remove = []
    #         for i in subset:
    #             if full_dict_list[i] not in dict_list:
    #                 subset_to_remove.append(i)
    #         for i in subset_to_remove:
    #             subset.remove(i)

    score_cover, score_overlap, score_similar, hierarchy = eval_hierarchy(dict_list, image, scale=scale, line=line, padding=padding, show=show, adjust=adjust, store=store, show_text=show_text, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)
    score = calcOneScore(score_cover, score_overlap, score_similar)
    
    # if show:
    #     print("one score before", score)
    #     print("subset", subset)

    if award_list is not None:
        for i in subset:
            score += award_list[i]
    
    # if show:
    #     print("one score", score)
    
    return score, score_cover, score_overlap, score_similar, hierarchy


def generate_neighbors(subset, full_set, ori_select, forbid_list=None):
    neighbors = []
    for i, elem in enumerate(full_set):
        if elem in ori_select:
            continue
        if forbid_list is not None and elem in forbid_list:
            continue
        if elem in subset:
            neighbor = subset.copy()
            neighbor.remove(elem)
            neighbors.append((neighbor, i))
        else:
            neighbor = subset.copy()
            neighbor.append(elem)
            neighbors.append((neighbor, i))
    return neighbors


def original(ori_select, full_dict_list, full_conf_list, init_subset=None, image=None,
                  scale=1, line=3, padding=30, store=None, award_list=None, full_conf_list2=None, save_root='result/images/', shape_dict=None, img_shape=None, tot_time=None):
    start = time.time()

    if award_list is None:
        if full_conf_list2 is not None:
            award_list = []
            for i in range(len(full_dict_list)):
                if i in ori_select:
                    # award_list.append(full_conf_list2[i]/20)
                    award_list.append(full_conf_list2[i]/5)
                else:
                    # award_list.append(0)
                    award_list.append(full_conf_list2[i]/5)

    if store is None:
        store = {"weight": {}, "match": {}, "shape": {}, "overlap": {}}
    full_set = [i for i in range(len(full_dict_list))]
    if init_subset is None:
        current_subset = ori_select.copy()
    else:
        current_subset = init_subset.copy()
    current_score, _, _, _, current_hierarchy = eval(current_subset, full_dict_list, full_conf_list, image, nms_update=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time, ori=True)

    print(current_subset)
    if image is not None:
        if isinstance(image, str):
            tmp = save_root+os.path.basename(image)
        else:
            tmp = True
        eval(current_subset, full_dict_list, full_conf_list, image, nms_update=True, scale=scale, line=line,
            padding=padding, show=tmp, adjust=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time, ori=True)

    print('original time', time.time() - start)
    return current_subset, current_score, current_hierarchy


def hill_climbing(ori_select, full_dict_list, full_conf_list, forbid_list=None, step=1, max_it_cnt=10000, best_cnt=3, init_subset=None, image=None,
                  scale=1, line=3, padding=30, store=None, award_list=None, full_conf_list2=None, save_root='result/images/', shape_dict=None, img_shape=None, tot_time=None):
    start = time.time()

    if award_list is None:
        if full_conf_list2 is not None:
            award_list = []
            if img_shape is None:
                for i in range(len(full_dict_list)):
                    if i in ori_select:
                        # award_list.append(full_conf_list2[i]/20)
                        award_list.append(full_conf_list2[i]/5)
                    else:
                        # award_list.append(0)
                        award_list.append(full_conf_list2[i]/5)
            else:
                for i in range(len(full_dict_list)):
                    ratio = (full_dict_list[i]["box"][2]-full_dict_list[i]["box"][0])*(full_dict_list[i]["box"][3]-full_dict_list[i]["box"][1])/(img_shape[0]*img_shape[1])
                    ratio = min(ratio, 1/5)
                    award_list.append(full_conf_list2[i]*ratio)
                    # award_list.append(full_conf_list2[i]/5)


    if store is None:
        store = {"weight": {}, "match": {}, "shape": {}, "overlap": {}}
    full_set = [i for i in range(len(full_dict_list))]
    if init_subset is None:
        current_subset = ori_select.copy()
    else:
        current_subset = init_subset.copy()
    current_score, _, _, _, current_hierarchy = eval(current_subset, full_dict_list, full_conf_list, image, nms_update=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)

    old_ori_select = ori_select
    # new_ori_select = [i for i in ori_select if (full_conf_list2[i]>0.2)or((full_conf_list2[i]>0.1)and(full_dict_list[i]['type']!='text'))]
    new_ori_select = []

    # ori_select = new_ori_select

    it_cnt = 0

    random.seed(20)
    order = [i for i in range(len(full_dict_list)) if (forbid_list is None or full_set[i] not in forbid_list)]
    random.shuffle(order)
    ori_best_cnt = best_cnt
    add_cnt = 0
    max_add_cnt = 2
    while it_cnt < max_it_cnt:
        it_cnt += 1
        # print('it_cnt', it_cnt, len(current_subset))
        # neighbors = generate_neighbors(current_subset, full_set, ori_select)
        # random.shuffle(neighbors)
        neighbors = generate_neighbors(current_subset, [full_set[i] for i in order], ori_select, forbid_list=forbid_list)

        best_neighbor = None
        best_score = current_score
        best_hierarchy = None
        now_best_cnt = 0

        for neighbor in neighbors:
            neighbor_score, score_cover, score_overlap, score_similar, neighbor_hierarchy = eval(neighbor[0], full_dict_list, full_conf_list, image, nms_update=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)
            if neighbor_score > best_score:
                best_score = neighbor_score
                best_neighbor = neighbor
                best_hierarchy = neighbor_hierarchy

            if neighbor_score > current_score:
                now_best_cnt += 1
                if now_best_cnt >= best_cnt:
                    break

        if best_neighbor is None:
            if step == 1:
                ori_select = new_ori_select
                step = 2
                continue
            break

        current_subset = best_neighbor[0]
        current_score = best_score
        current_hierarchy = best_hierarchy

        order = order[best_neighbor[1] + 1:] + order[:best_neighbor[1] + 1]

        if now_best_cnt < best_cnt:
            best_cnt = now_best_cnt
            add_cnt = 0
        else:
            add_cnt += 1
            if add_cnt >= max_add_cnt:
                best_cnt = min(best_cnt + 1, ori_best_cnt)
                add_cnt = 0

    print("ori_select", old_ori_select, new_ori_select)
    print(current_subset, it_cnt)

    # if image is not None:
    #     if isinstance(image, str):
    #         tmp = save_root+os.path.basename(image)
    #     else:
    #         tmp = True
    #     eval(current_subset, full_dict_list, full_conf_list, image, nms_update=True, scale=scale, line=line,
    #         padding=padding, show=tmp, adjust=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)

    # print('hill climbing time', time.time() - start)
    return current_subset, current_score, current_hierarchy


def generate_neighbor(subset, full_set, ori_select, tried=[]):
    if len(full_set) - len(ori_select) <= len(tried):
        tried.clear()

    subset = [item for item in subset if item not in tried]
    full_set = [item for item in full_set if item not in tried]
    ori_select = [item for item in ori_select if item not in tried]

    new_subset = subset.copy()
    tmp_subset = [item for item in new_subset if item not in ori_select]
    if random.random() > 0.5 and len(tmp_subset) > 0:
        choice = random.choice(tmp_subset)
        new_subset.remove(choice)
    else:
        tmp_subset = [item for item in full_set if item not in ori_select]
        tmp_subset2 = [x for x in tmp_subset if x not in new_subset]
        if len(tmp_subset2) == 0: 
            return new_subset, None
        choice = random.choice(tmp_subset2)
        new_subset.append(choice)
    return new_subset, choice


def simulated_annealing(ori_select, full_dict_list, full_conf_list, initial_temp=1000, min_temp=1, cooling_rate='auto', show_step_score=False,
                        max_it_cnt=500, max_stop_cnt=300, max_update_cnt=20, init_subset=None, image=None, scale=1,
                        line=3, padding=30, store=None, award_list=None, full_conf_list2=None, save_root='result/images/', shape_dict=None, max_hc_cnt=30, img_shape=None, tot_time=None):
    start = time.time()

    if award_list is None:
        if full_conf_list2 is None:
            award_list = []
            for i in range(len(full_dict_list)):
                if i in ori_select:
                    award_list.append(0.005)
                else:
                    award_list.append(0)
        else:
            award_list = []
            for i in range(len(full_dict_list)):
                if i in ori_select:
                    # award_list.append(full_conf_list2[i]/20)
                    award_list.append(full_conf_list2[i]/5)
                else:
                    # award_list.append(0)
                    award_list.append(full_conf_list2[i]/5)
                    # award_list.append(full_conf_list2[i]/40)
        # print('award list', award_list)
        # print('ori select', len(ori_select), len([i for i in ori_select if award_list[i]>0.0065]))
        # print('new ori select', [i for i in ori_select if award_list[i]>0.0065])

    if store is None:
        store = {"weight": {}, "match": {}, "shape": {}, "overlap": {}}
    full_set = [i for i in range(len(full_dict_list))]
    if init_subset is None:
        current_subset = ori_select.copy()
    else:
        current_subset = init_subset.copy()
    current_score, _, _, _, current_hierarchy = eval(current_subset, full_dict_list, full_conf_list, image, nms_update=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)
    temperature = initial_temp

    best_subset = current_subset
    best_score = current_score
    best_hierarchy = current_hierarchy

    old_ori_select = ori_select
    # new_ori_select = []
    # new_ori_select = [i for i in ori_select if award_list[i]>0.005]
    # new_ori_select = [i for i in ori_select if (award_list[i]>0.01)or((award_list[i]>0.005)and(full_dict_list[i]['type']!='text'))]
    new_ori_select = [i for i in ori_select if (full_conf_list2[i]>0.2)or((full_conf_list2[i]>0.1)and(full_dict_list[i]['type']!='text'))]
    # ori_select = new_ori_select
    
    it_cnt = 0
    stop_cnt = 0
    update_cnt = 0
    random.seed(20)

    if cooling_rate == 'auto':
        cooling_rate = math.exp(math.log(min_temp / initial_temp) / max_it_cnt)

    step = 1
    tried = []
    while (temperature > min_temp or update_cnt < max_update_cnt) and stop_cnt < max_stop_cnt and it_cnt < max_it_cnt * 2:
        if it_cnt > max_it_cnt/2 or stop_cnt > max_stop_cnt/2:
            if step == 1:
                ori_select = new_ori_select
                stop_cnt = 0
                step = 2

        it_cnt += 1
        stop_cnt += 1

        new_subset, choice = generate_neighbor(current_subset, full_set, ori_select, tried)
        if choice is None:
            break
        new_score, _, _, _, new_hierarchy = eval(new_subset, full_dict_list, full_conf_list, image, nms_update=True, store=store, award_list=award_list, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)
        # tried.append(choice)

        score_diff = new_score - current_score

        if score_diff > 0 or math.exp(4000 * score_diff / temperature) > random.random():
            # tried = []
            current_subset = new_subset
            current_score = new_score
            current_hierarchy = new_hierarchy

            if new_score > best_score:
                update_cnt += 1
                if new_score > best_score + 0.002:
                    stop_cnt = 0
                else:
                    stop_cnt /= 2
                best_subset = new_subset
                best_score = new_score
                best_hierarchy = new_hierarchy

        temperature = max(min_temp, temperature * cooling_rate)
        # print('it cnt', it_cnt, stop_cnt, update_cnt)

    step1_score = (best_score, best_subset)

    print('ori_selected', len(old_ori_select), len(new_ori_select))
    best_subset, best_score, best_hierarchy = hill_climbing(new_ori_select, full_dict_list, full_conf_list, step=2, max_it_cnt=max_hc_cnt, best_cnt=1, full_conf_list2=full_conf_list2, 
                                            init_subset=best_subset, store=store, award_list=award_list, save_root=save_root, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)

    # print(best_subset)
    # if image is not None:
    #     if isinstance(image, str):
    #         tmp = save_root+os.path.basename(image)
    #     else:
    #         tmp = True
    #     eval(best_subset, full_dict_list, full_conf_list, image, nms_update=True, scale=scale, line=line,
    #         padding=padding, show=tmp, adjust=True, store=store, award_list=award_list, show_text=True, shape_dict=shape_dict, img_shape=img_shape, tot_time=tot_time)

    # best_subset.append(38)
    # eval(best_subset, full_dict_list, full_conf_list, image, nms_update=True, scale=scale, line=line, padding=padding, show=True, adjust=True, award_list=award_list, shape_dict=shape_dict)
    # print(best_subset)

    print('simulated annealing time', time.time() - start)

    if show_step_score:
        return best_subset, best_score, best_hierarchy, step1_score
    return best_subset, best_score, best_hierarchy



if __name__ == '__main__':
    scale = 3

    dict_list = [{'type': 'text', 'box': [0, 0, 100, 20]}, {'type': 'text', 'box': [0, 30, 10, 40]},
                 {'type': 'text', 'box': [0, 60, 10, 70]}, {'type': 'image', 'box': [15, 25, 40, 45]},
                 {'type': 'image', 'box': [15, 55, 40, 75]}]
    dict_list.extend([{'type': 'text', 'box': [50, 30, 60, 40]}, {'type': 'text', 'box': [50, 60, 60, 70]},
                      {'type': 'image', 'box': [65, 25, 90, 45]}, {'type': 'image', 'box': [65, 55, 90, 75]}])
    dict_list.extend([{'type': 'non-data', 'box': [0 - 1, 25 - 1, 40 + 1, 45 + 1]},
                      {'type': 'non-data', 'box': [0 - 1, 55 - 1, 40 + 1, 75 + 1]}])
    dict_list.extend([{'type': 'non-data', 'box': [50 - 1, 25 - 1, 90 + 1, 45 + 1]},
                      {'type': 'non-data', 'box': [50 - 1, 55 - 1, 90 + 1, 75 + 1]}])

    dict_list.extend([{'type': 'data', 'box': [0 - 2, 100 - 2, 100 + 2, 165 + 2]},
                      {'type': 'data', 'box': [0, 100, 30, 130]}, {'type': 'data', 'box': [0, 135, 30, 165]},
                      {'type': 'data', 'box': [35, 100, 65, 130]}, {'type': 'data', 'box': [35, 135, 65, 165]},
                      {'type': 'data', 'box': [70, 100, 100, 130]}, {'type': 'data', 'box': [70, 135, 100, 165]}])

    random.seed(70)
    np.random.seed(40)

    ori_dict_list = dict_list
    ori_select = [i for i in range(len(ori_dict_list))]

    num_to_remove = 8
    elements_to_remove = random.sample(ori_select, num_to_remove)
    # elements_to_remove = [3]
    for elem in elements_to_remove:
        ori_select.remove(elem)
    dict_list = [ori_dict_list[i] for i in ori_select]

    for i in range(len(ori_dict_list)):
        # for i in ori_select:
        dc = ori_dict_list[i]
        noise_std = 2
        noise = np.random.normal(0, noise_std, np.array(dc['box']).shape)
        bd1, bd2 = 0.2 * (dc['box'][2] - dc['box'][0]), 0.2 * (dc['box'][3] - dc['box'][1])
        noise[0], noise[2] = max(min(noise[0], bd1), -bd1), max(min(noise[2], bd1), -bd1)
        noise[1], noise[3] = max(min(noise[1], bd2), -bd2), max(min(noise[3], bd2), -bd2)
        dc['box'] = np.round(np.array(dc['box']) + noise).tolist()

    random.seed(80)
    np.random.seed(20)
    num_to_add = 8
    full_select = [i for i in range(len(ori_dict_list))]
    elements_to_add = random.sample(full_select, num_to_add)
    for elem in elements_to_add:
        ori_dict_list.append(copy.deepcopy(ori_dict_list[elem]))
        dc = ori_dict_list[-1]
        noise_std = 4
        noise = np.random.normal(0, noise_std, np.array(dc['box']).shape)
        bd1, bd2 = 0.5 * (dc['box'][2] - dc['box'][0]), 0.5 * (dc['box'][3] - dc['box'][1])
        noise[0], noise[2] = max(min(noise[0], bd1), -bd1), max(min(noise[2], bd1), -bd1)
        noise[1], noise[3] = max(min(noise[1], bd2), -bd2), max(min(noise[3], bd2), -bd2)
        dc['box'] = np.round(np.array(dc['box']) + noise).tolist()

    for i in range(len(ori_dict_list)):
        ori_dict_list[i]['id'] = i

    # dict_list = [{'type': 'text', 'box': [0, 0, 30, 30]}, {'type': 'text', 'box': [0, 30, 30, 60]},
    #              {'type': 'text', 'box': [30, 0, 60, 30]}, {'type': 'image', 'box': [0-1, 0-1, 30+1, 60+1]}]

    # tmp_select = [0, 6, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 14, 17, 9, 5, 27]
    # tmp_select = [i for i in range(20)]
    # tmp_select.remove(1)
    # eval_hierarchy([ori_dict_list[i] for i in tmp_select], (100, 180), scale=3, line=1, show=True, adjust=True)

    eval_hierarchy(dict_list, (100, 180), scale=3, line=1, show='select', adjust=True)
    eval_hierarchy(ori_dict_list, (100, 180), scale=3, line=1, show='full', adjust=True, show_text=True)

    conf = []
    for i in range(len(ori_dict_list)):
        if i in ori_select:
            conf.append(1)
        else:
            conf.append(0)
    
    award_list = []
    for i in range(len(ori_dict_list)):
        award_list.append(0)

    conf2 = []
    for i in range(len(ori_dict_list)):
        if i in ori_select:
            conf2.append(1)
        else:
            conf2.append(0)
    conf2[13] = 0

    # hill_climbing(ori_select, ori_dict_list, conf, image=(100, 180), scale=3, line=1, padding=10)
    simulated_annealing(ori_select, ori_dict_list, conf, image=(100, 180), scale=3, line=1, padding=10, full_conf_list2=conf2, award_list=award_list, save_root='', max_hc_cnt=30, img_shape=(100, 180))

    # tmp_select = [0, 6, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 14, 17, 9, 3, 5, 4, 1, 2]
    # eval_hierarchy([ori_dict_list[i] for i in tmp_select], (100, 180), scale=3, line=1, show='tmp', adjust=True)

    # dict_list = [{'type': 'data', 'box': (4, 292, 558, 542), 'conf': 0.555919349193573, 'id': 0}, {'type': 'image', 'box': (11, 365, 76, 432), 'conf': 0.33783864974975586, 'id': 28}, {'type': 'image', 'box': (93, 947, 120, 974), 'conf': 0.31990087032318115, 'id': 29}, {'type': 'image', 'box': (12, 631, 74, 692), 'conf': 0.3164196014404297, 'id': 30}, {'type': 'image', 'box': (491, 633, 553, 693), 'conf': 0.30149519443511963, 'id': 31}, {'type': 'image', 'box': (79, 365, 144, 432), 'conf': 0.28898152709007263, 'id': 32}, {'type': 'image', 'box': (81, 633, 143, 693), 'conf': 0.2777116298675537, 'id': 33}, {'type': 'image', 'box': (13, 826, 73, 887), 'conf': 0.2737579643726349, 'id': 34}, {'type': 'image', 'box': (149, 633, 212, 693), 'conf': 0.2298547476530075, 'id': 47}, {'type': 'image', 'box': (83, 827, 142, 887), 'conf': 0.23653890192508698, 'id': 42}, {'type': 'data', 'box': (12, 363, 555, 503), 'conf': 0.12360543012619019, 'id': 7}, {'type': 'image', 'box': (354, 633, 417, 692), 'conf': 0.22452887892723083, 'id': 50}, {'type': 'data', 'box': (11, 630, 555, 695), 'conf': 0.191262885928154, 'id': 2}, {'type': 'data', 'box': (3, 553, 559, 738), 'conf': 0.19089289009571075, 'id': 3}, {'type': 'image', 'box': (14, 759, 67, 819), 'conf': 0.06885575503110886, 'id': 74}, {'type': 'data', 'box': (8, 756, 556, 932), 'conf': 0.19004599750041962, 'id': 4}, {'type': 'image', 'box': (420, 364, 486, 431), 'conf': 0.20235565304756165, 'id': 59}, {'type': 'image', 'box': (492, 441, 553, 502), 'conf': 0.2530730068683624, 'id': 39}, {'type': 'image', 'box': (148, 365, 213, 432), 'conf': 0.22851119935512543, 'id': 48}, {'type': 'image', 'box': (355, 441, 416, 501), 'conf': 0.200442373752594, 'id': 62}, {'type': 'image', 'box': (423, 634, 485, 693), 'conf': 0.2615678310394287, 'id': 36}, {'type': 'non-data', 'box': (359, 826, 555, 929), 'conf': 0.07051698118448257, 'id': 24}, {'type': 'image', 'box': (217, 633, 279, 692), 'conf': 0.21197687089443207, 'id': 54}, {'type': 'image', 'box': (286, 633, 348, 692), 'conf': 0.20130735635757446, 'id': 60}, {'type': 'data', 'box': (5, 135, 551, 276), 'conf': 0.11923199146986008, 'id': 8}, {'type': 'image', 'box': (288, 827, 348, 887), 'conf': 0.20068250596523285, 'id': 61}, {'type': 'image', 'box': (151, 827, 211, 887), 'conf': 0.2271130084991455, 'id': 49}, {'type': 'image', 'box': (219, 827, 279, 887), 'conf': 0.19710032641887665, 'id': 63}, {'type': 'non-data', 'box': (211, 947, 376, 975), 'conf': 0.05635520815849304, 'id': 25}, {'type': 'image', 'box': (215, 365, 281, 432), 'conf': 0.2338688224554062, 'id': 45}, {'type': 'image', 'box': (423, 441, 485, 501), 'conf': 0.25285372138023376, 'id': 40}, {'type': 'image', 'box': (283, 365, 349, 432), 'conf': 0.23490335047245026, 'id': 44}, {'type': 'non-data', 'box': (11, 2, 559, 126), 'conf': 0.13395956158638, 'id': 13}, {'type': 'image', 'box': (287, 442, 348, 502), 'conf': 0.18626941740512848, 'id': 65}, {'type': 'image', 'box': (351, 365, 417, 432), 'conf': 0.2121666967868805, 'id': 53}, {'type': 'image', 'box': (489, 364, 554, 431), 'conf': 0.26581433415412903, 'id': 35}, {'type': 'image', 'box': (218, 442, 279, 502), 'conf': 0.21060402691364288, 'id': 56}, {'type': 'image', 'box': (150, 441, 211, 502), 'conf': 0.20603592693805695, 'id': 58}, {'type': 'image', 'box': (81, 441, 142, 501), 'conf': 0.22140781581401825, 'id': 51}, {'type': 'image', 'box': (14, 441, 75, 502), 'conf': 0.2571204900741577, 'id': 38}, {'type': 'non-data', 'box': (90, 946, 475, 977), 'conf': 0.09376806020736694, 'id': 19}, {'type': 'image', 'box': (382, 947, 472, 975), 'conf': 0.09256957471370697, 'id': 69}]
    # eval_hierarchy(dict_list, (563, 982), scale=1, line=3, padding=30, show="tmp", adjust=True)
