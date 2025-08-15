import copy
from collections import Counter
import numpy as np
from scipy.spatial.distance import cdist

def getLabelMap(labels, top_labels=None):
    label_map = {}
    label_map_back = []
    new_labels = labels.copy()
    top_part = []

    for i in range(len(labels)):
        if labels[i] not in label_map:
            label_map[labels[i]] = len(label_map_back)
            if top_labels is not None:
                top_part.append(top_labels[i])
            label_map_back.append(labels[i])
        new_labels[i] = label_map[labels[i]]

    if top_labels is not None:
        top_part = np.array(top_part).astype('int')
    else:
        top_part = np.array([0]*len(label_map_back)).astype('int')

    return label_map, label_map_back, new_labels, top_part

def get_label_partition_feature(X_feature, labels, top_labels, filter_labels, cluster_ratio=0.2, original_top_labels=None):
    unique_labels = np.unique(labels)
    assert np.array_equal(unique_labels, np.arange(unique_labels.shape[0])) # labels should be normalized

    label_embeds = {}
    label_lists = {}
    filtered_labels = []

    map2top = {}

    for i in range(X_feature.shape[0]):
        if labels[i] not in label_embeds:
            label_embeds[labels[i]] = []
        label_embeds[labels[i]].append(X_feature[i])
        if top_labels[i] not in label_lists:
            label_lists[top_labels[i]] = []

        map2top[labels[i]] = top_labels[i]

        if labels[i] in filter_labels[1]:
            if labels[i] not in filtered_labels:
                filtered_labels.append(labels[i])
        else:
            if labels[i] not in label_lists[top_labels[i]]:
                label_lists[top_labels[i]].append(labels[i])

    # print("time label partition 0", time.time()-start)

    # print(filter_labels)
    # print(label_lists)
    # print(filtered_labels)

    top_partition = []
    partitions = {}
    cur_partition = 0
    cluster_size = int(X_feature.shape[0] * cluster_ratio)
    tcnt = 0
    for tlabel in label_lists:
        if tlabel in filter_labels[0]:
            continue
        tcnt += 1
    for tlabel in label_lists:
        if tlabel in filter_labels[0]:
            filtered_labels.extend(label_lists[tlabel])
            continue
        if len(label_lists[tlabel])==0:
            continue

        for i in range(len(label_lists[tlabel])):
            partitions[label_lists[tlabel][i]] = i + cur_partition

        cur_partition += len(label_lists[tlabel])

        for i in range(len(label_lists[tlabel])):
            top_partition.append(tlabel)

    top_partition = np.array(top_partition)

    from collections import Counter
    # print(top_partition)
    # print(Counter(labels))

    # print("time label partition 1", time.time()-start)
    # print(filtered_labels)

    for label in filtered_labels:
        partitions[label] = -1
    label_partition = np.zeros((unique_labels.shape[0], ))
    for i in range(unique_labels.shape[0]):
        label_partition[i] = partitions[i]
    label_partition = label_partition.astype(np.int32)
    partition_num = cur_partition
    partition_centers = np.zeros((partition_num, X_feature.shape[1]))

    # print(Counter(label_partition[labels]))

    for i in range(partition_num):
        partition_centers[i] = (X_feature[(label_partition[labels] == i)]).sum(axis=0)/(X_feature[(label_partition[labels] == i)]).shape[0]

    # print(partition_num)

    if original_top_labels is not None:
        original_label_lists = {}
        original_map2top = {}
        for i in range(X_feature.shape[0]):
            if original_top_labels[i] not in original_label_lists:
                original_label_lists[original_top_labels[i]] = []
            original_map2top[labels[i]] = original_top_labels[i]

            if labels[i] not in filtered_labels:
                if labels[i] not in original_label_lists[original_top_labels[i]]:
                    original_label_lists[original_top_labels[i]].append(labels[i])

    if len(filtered_labels) > 0:

        filtered_center = []
        for label in filtered_labels:
            label_center = np.mean(np.array(label_embeds[label]), axis=0)
            filtered_center.append(label_center)
        filtered_center = np.array(filtered_center)
        dist_matrix = cdist(filtered_center, partition_centers)

        order = 0
        for label in filtered_labels:
            # label_center = np.mean(np.array(label_embeds[label]), axis=0)
            tlabel = map2top[label]
            if original_top_labels is not None and (len(original_label_lists[original_map2top[label]]) > 0):
                tmp_list = original_label_lists[original_map2top[label]]
                nn = label_partition[tmp_list][dist_matrix[order][label_partition[tmp_list]].argsort()[0]]
                label_partition[label] = nn
            elif tlabel not in filter_labels[0] and (len(label_lists[tlabel]) > 0):
                nn = label_partition[label_lists[tlabel]][dist_matrix[order][label_partition[label_lists[tlabel]]].argsort()[0]]
                label_partition[label] = nn
            else:
                nn = dist_matrix[order].argsort()[0]
                label_partition[label] = nn
            order += 1

    for i in range(partition_num):
        partition_centers[i] = (X_feature[(label_partition[labels] == i)]).sum(axis=0)/(X_feature[(label_partition[labels] == i)]).shape[0]
    partition_labels = np.array(list(map(lambda x: label_partition[x], labels)))

    # print("time label partition 2", time.time()-start)

    # from IPython import embed; embed()
    return label_partition, partition_labels, top_partition

def mergeSmallLabels(labels, top_labels, filter_labels):
    for i in range(len(labels)):
        if top_labels[i] in filter_labels[0]:
            if labels[i] not in filter_labels[1]:
                filter_labels[1].append(labels[i])
    filter_labels[0] = []

    label_cnt = labels.max() + 1000000
    unique_top_labels = np.unique(top_labels)
    merge_labels = labels.copy()

    for tlabel in unique_top_labels:
        ids = np.arange(len(top_labels), dtype='int')[(top_labels == tlabel)]
        tmp_labels = labels[ids]
        for label in filter_labels[1]:
            merge_labels[ids[tmp_labels == label]] = label_cnt
        label_cnt += 1
    return merge_labels

def solveTopLabels(X_feature, labels, top_labels, filter_labels, info_before):
    original_top_labels = top_labels.copy()
    original_labels = labels.copy()
    original_filter = copy.deepcopy(filter_labels)

    #----------------------------------将top_label更改为上层分块----------------------------------------

    if info_before is not None:
        for i in range(len(labels)):
            if top_labels[i] in filter_labels[0]:
                if labels[i] not in filter_labels[1]:
                    filter_labels[1].append(labels[i])
        filter_labels[0] = []

        selected_bf = info_before['selected_bf']
        selected_now = info_before['selected']
        partition_info_bf = info_before['partition_info_bf']
        partition_labels_bf = partition_info_bf['partition_labels']

        cnt = 0
        partition_bf_id = {}
        partition_bf_list = []
        map_bf = {}
        for i in range(len(selected_now)):
            if partition_labels_bf[selected_bf[i]] not in partition_bf_id:
                partition_bf_id[partition_labels_bf[selected_bf[i]]] = cnt
                partition_bf_list.append(partition_labels_bf[selected_bf[i]])
                cnt += 1
            map_bf[top_labels[selected_now[i]]] = partition_bf_id[partition_labels_bf[selected_bf[i]]]

        top_list = []
        for i in range(cnt):
            top_list.append([])
        cnt2 = 0
        top_list2 = []
        top_id2 = []
        map_bf2 = {}

        counter = Counter(top_labels)

        for t_lb in counter:
            if t_lb in map_bf:
                top_list[map_bf[t_lb]] = X_feature[top_labels == t_lb].mean(axis=0)
            else:
                map_bf2[t_lb] = cnt2
                cnt2 += 1
                top_list2.append(X_feature[top_labels == t_lb].mean(axis=0))
                top_id2.append(t_lb)

        if cnt2 > 0:
            top_dist = cdist(top_list2, top_list, "eu")
            for i in range(cnt2):
                map_bf[top_id2[i]] = top_dist[i].argsort()[0]

        top_labels = np.array(list(map(lambda x: map_bf[x], top_labels)))

    return top_labels

    # #----------------------------------START LABEL PARTITION----------------------------------------
    #
    # import time
    # start = time.time()
    #
    # # label normalization
    # def norm_labels(labels):
    #     labelmap = {}
    #     cur_idx = 0
    #     for label in labels:
    #         label = int(label)
    #         if label not in labelmap:
    #             labelmap[label] = cur_idx
    #             cur_idx += 1
    #     return labelmap
    #
    # labelmap = norm_labels(labels)
    # labels = np.array(list(map(lambda x: labelmap[x], labels)))
    # filter_labels[1] = np.array(list(map(lambda x: labelmap[x], filter_labels[1]))).astype(np.int32)
    # label_partition, partition_labels, top_partition = get_label_partition_feature(X_feature, labels, top_labels, filter_labels, original_top_labels=original_top_labels)
    #
    # tlabelmap = norm_labels(top_partition)
    # top_partition = np.array(list(map(lambda x: tlabelmap[x], top_partition))).astype(np.int32)