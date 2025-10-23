import numpy as np
import shapely
from scipy.optimize import linear_sum_assignment
import time


def getSubType(obj):
    obj.sub_type = "group"
    area = (obj.box[2] - obj.box[0]) * (obj.box[3] - obj.box[1])
    ratio = 0.9
    for sub_obj in obj.children:
        sub_type = sub_obj.type
        if sub_type == "group":
            sub_type = sub_obj.sub_type
        if sub_type == "data" or sub_type == "non-data":
            sub_area = (sub_obj.box[2] - sub_obj.box[0]) * (sub_obj.box[3] - sub_obj.box[1])
            if sub_area > area * ratio:
                ratio = sub_area / area
                obj.sub_type = sub_type


def iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou_value = inter_area / (box1_area + box2_area - inter_area + 0.000001)
    return iou_value


class Group:
    def __init__(self):
        self.box = [0, 0, 0, 0]
        self.children = []
        self.type = None


def if_cover(obj1, obj2, type='hard'):
    box1 = obj1.box
    box2 = obj2.box

    [x1_A, y1_A, x2_A, y2_A] = box1
    [x1_B, y1_B, x2_B, y2_B] = box2

    x_left = max(x1_A, x1_B)
    y_top = max(y1_A, y1_B)
    x_right = min(x2_A, x2_B)
    y_bottom = min(y2_A, y2_B)

    if x_right < x_left or y_bottom < y_top:
        intersection_area = 0
    else:
        intersection_width = x_right - x_left
        intersection_height = y_bottom - y_top
        intersection_area = intersection_width * intersection_height

    A_area = (x2_A - x1_A) * (y2_A - y1_A)
    B_area = (x2_B - x1_B) * (y2_B - y1_B)

    # print('intersection', intersection_area, A_area, B_area)

    hard = 0
    soft = 0
    very_hard = 0
    if intersection_area > 0.8 * B_area and B_area < 0.8 * A_area and B_area-intersection_area < 0.75*(A_area-intersection_area):
        hard = 1
    if intersection_area > 0.95 * B_area and B_area < 0.95 * A_area:
        hard = 1
    if intersection_area > 0.8 * B_area and B_area < A_area and B_area-intersection_area < 0.75*(A_area-intersection_area):
        soft = 1
    if intersection_area > 0.95 * B_area:
        soft = 1
    if intersection_area > 0.95 * B_area and B_area < 0.8 * A_area and B_area-intersection_area < 0.75*(A_area-intersection_area):
        very_hard = 1

    if type == 'hard':
        return hard
    elif type == "soft":
        return soft
    elif type == "both":
        return hard, soft
    elif type == "very_hard":
        return very_hard

    return 0


def getShape(obj, recalc=True, shape_store=None):
    if not recalc:
        if hasattr(obj, 'shape'):
            return obj.shape

    if shape_store is not None:
        sub_obj_list = getBasicObj(obj)
        tp = getIds(sub_obj_list)
        if not recalc and tp in shape_store:
            obj.shape = shape_store[tp]
            return obj.shape

    if obj.type != "group":
        if not hasattr(obj, 'shape'):
            if obj.type in ["mark", "area-under-line_mark", "pie_mark", "treemap_mark"]:
                obj.shape = obj.mask_shape
            else:
                obj.shape = shapely.geometry.box(obj.box[0], obj.box[1], obj.box[2], obj.box[3])
        if shape_store is not None:
            shape_store[tp] = obj.shape
        return obj.shape

    obj.shape = shapely.Polygon()

    if shape_store is not None and tp in shape_store:
        for sub_obj in obj.children:
            getShape(sub_obj, recalc, shape_store=shape_store)
        obj.shape = shape_store[tp]
    else:
        for sub_obj in obj.children:
            obj.shape = obj.shape.union(getShape(sub_obj, recalc, shape_store=shape_store))

    if shape_store is not None:
        shape_store[tp] = obj.shape

    return obj.shape


def getInnerShape(obj, recalc=True, shape_store=None):
    if not recalc and hasattr(obj, 'inner_shape'):
        return obj.inner_shape, obj.inner_flag

    full_shape = shapely.Polygon()
    min_x, min_y, max_x, max_y = 10000000, 10000000, -10000000, -10000000

    obj_list = obj.children

    area_list = []
    for tmp_obj in obj_list:
        # area_list.append(tmp_obj.shape.area)
        area_list.append((tmp_obj.box[2]-tmp_obj.box[0])*(tmp_obj.box[3]-tmp_obj.box[1]))
        if tmp_obj.type == "group":
            area_list[-1] *= 0
        min_x = min(min_x, tmp_obj.box[0])
        min_y = min(min_y, tmp_obj.box[1])
        max_x = max(max_x, tmp_obj.box[2])
        max_y = max(max_y, tmp_obj.box[3])

    width = max(0, max_x - min_x)
    height = max(0, max_y - min_y)
    box_area = width * height

    ls = [i for i in range(len(obj_list))]
    for i in range(len(obj_list) - 1):
        for j in range(i + 1, len(obj_list)):
            if area_list[ls[i]] < area_list[ls[j]]:
                ls[i], ls[j] = ls[j], ls[i]

    flag = False
    flag_list = []
    outer_list = []
    inner_list = []

    for i in range(len(ls)):
        tmp_obj = obj_list[ls[i]]
        # tmp_shape = tmp_obj.shape
        tmp_shape = shapely.geometry.box(tmp_obj.box[0], tmp_obj.box[1], tmp_obj.box[2], tmp_obj.box[3])
        if i < min(1, len(ls) - 1) and tmp_shape.area > 0.95 * box_area and tmp_obj.type != 'group':
            flag = True
            outer_list.append(tmp_obj)
            flag_list.append(True)
        else:
            inner_list.append(tmp_obj)
            flag_list.append(False)
    
    # if flag:
    #     flag = False
    #     basic_obj = getBasicObj(obj)
    #     for tmp_obj in basic_obj:
    #         if tmp_obj not in outer_list and tmp_obj.type == "image":
    #             flag = True
    #     # print("new flag", flag)

    # if False:
    if not flag:
        full_shape = obj.shape
    else:
        if shape_store is not None:
            basic_obj_list = getListBasicObj(inner_list)
            tp = getIds(basic_obj_list)
            if tp in shape_store:
                full_shape = shape_store[tp]
        if full_shape.is_empty:
            for i in range(len(ls)):
                tmp_obj = obj_list[ls[i]]
                tmp_shape = tmp_obj.shape
                # tmp_shape = shapely.geometry.box(tmp_obj.box[0], tmp_obj.box[1], tmp_obj.box[2], tmp_obj.box[3])
                if flag_list[i]:
                    continue
                if full_shape is None:
                    full_shape = tmp_shape
                else:
                    full_shape = full_shape.union(tmp_shape)
            if shape_store is not None:
                shape_store[tp] = full_shape

    obj.inner_shape = full_shape
    obj.inner_flag = flag
    obj.outer_obj = outer_list
    return full_shape, flag


def coverRatio(father_obj, full_area=None, inner_flag=False):
    obj_list = father_obj.children
    if full_area is not None:
        if not inner_flag:
            return 0, 0
    full_shape = None

    box_area = father_obj.shape.area

    if full_area is None:
        for obj in obj_list:
            tmp_shape = shapely.geometry.box(obj.box[0], obj.box[1], obj.box[2], obj.box[3])
            if full_shape is None:
                full_shape = tmp_shape
            else:
                full_shape = full_shape.union(tmp_shape)

        if full_shape is None or full_shape.is_empty or full_shape.area == 0:
            return 0, 0

        full_area = full_shape.area
    # elif inner_flag:
    #     full_area += 0.5 * (box_area - full_area)

    # print("cover", father_obj.box, father_obj.outer_obj[0].id)

    return full_area / (box_area + 0.000001), box_area + 0.000001


def overlapRatio(obj_list):
    full_shape = None
    min_x, min_y, max_x, max_y = 10000000, 10000000, -10000000, -10000000
    for i in range(len(obj_list)):
        obj1 = obj_list[i]
        shape1 = shapely.geometry.box(obj1.box[0], obj1.box[1], obj1.box[2], obj1.box[3])
        shape1_2 = obj1.shape
        min_x = min(min_x, obj1.box[0])
        min_y = min(min_y, obj1.box[1])
        max_x = max(max_x, obj1.box[2])
        max_y = max(max_y, obj1.box[3])
        for j in range(i + 1, len(obj_list)):
            obj2 = obj_list[j]
            shape2 = shapely.geometry.box(obj2.box[0], obj2.box[1], obj2.box[2], obj2.box[3])
            shape2_2 = obj2.shape
            hard_cover1, soft_cover1 = if_cover(obj1, obj2, type='both')
            hard_cover2, soft_cover2 = if_cover(obj2, obj1, type='both')
            true_cover1 = (hard_cover1 == 1 and obj1.type != "group" and obj1.type != "text") or (
                    soft_cover1 == 1 and obj1.type != "group" and obj1.type != "text" and obj2.type == "group")
            true_cover2 = (hard_cover2 == 1 and obj2.type != "group" and obj2.type != "text") or (
                    soft_cover2 == 1 and obj2.type != "group" and obj2.type != "text" and obj1.type == "group")
            # print(obj1.shape, obj1.box)
            # print(obj2.shape, obj2.box)
            # print(hard_cover1, soft_cover1, hard_cover2, soft_cover2)

            if not true_cover1 and not true_cover2:
                # tmp_shape = shape1.intersection(shape2)
                tmp_shape = shape1_2.intersection(shape2_2)
                if full_shape is None:
                    full_shape = tmp_shape
                else:
                    full_shape = full_shape.union(tmp_shape)

    width = max(0, max_x - min_x)
    height = max(0, max_y - min_y)
    box_area = width * height

    if full_shape is None or full_shape.is_empty or full_shape.area == 0:
        return 0, box_area

    return full_shape.area / box_area, box_area


def getBasicObj(obj):
    if obj.type != "group":
        if not hasattr(obj, 'hide') or not obj.hide:
            return [obj]
        else:
            return []
    if hasattr(obj, 'basic_obj') and obj.basic_obj is not None:
        return obj.basic_obj[:]
    obj_list = []
    for sub_obj in obj.children:
        obj_list.extend(getBasicObj(sub_obj))
    obj.basic_obj = obj_list[:]
    return obj_list


def getListBasicObj(obj_list):
    basic_obj_list = []
    for obj in obj_list:
        basic_obj_list.extend(getBasicObj(obj))
    return basic_obj_list

def getBasicWeight(obj_list):
    weight_list = np.ones(len(obj_list))

    for i in range(len(obj_list) - 1):
        obj1 = obj_list[i]
        for j in range(i + 1, len(obj_list)):
            obj2 = obj_list[j]
            cover1 = if_cover(obj1, obj2, type='very_hard')
            cover2 = if_cover(obj2, obj1, type='very_hard')

            if not (cover1 and obj1.type!='text') and not (cover2 and obj2.type!='text'):
                tmp_shape = obj1.shape.intersection(obj2.shape)
                if tmp_shape.area / obj1.shape.area > 0.25 or tmp_shape.area / obj2.shape.area > 0.25:
                    weight_list[i] = max(0, weight_list[i] - tmp_shape.area / obj1.shape.area / 2)
                    weight_list[j] = max(0, weight_list[j] - tmp_shape.area / obj2.shape.area / 2)

    return weight_list


def searchWeight(sub_obj_list, tp, weight_store=None):
    tmp_list = None
    if weight_store is not None:
        if tp not in weight_store:
            tmp_list = getBasicWeight(sub_obj_list)
            weight_store[tp] = tmp_list
        else:
            tmp_list = weight_store[tp]
    else:
        tmp_list = getBasicWeight(sub_obj_list)
    return tmp_list


def getObjSimilarity(obj1, obj2):
    if obj1.type != obj2.type:
        return 0

    if iou(obj1.box, obj2.box) > 0.2:
        return 0

    score = 1
    cover1 = if_cover(obj1, obj2, type='very_hard')
    cover2 = if_cover(obj2, obj1, type='very_hard')
    if not cover1 and not cover2:
        tmp_shape = obj1.shape.intersection(obj2.shape)
        if tmp_shape.area / obj1.shape.area > 0.25 or tmp_shape.area / obj2.shape.area > 0.25:
            score *= (1 - tmp_shape.area / obj1.shape.area / 2) * (1 - tmp_shape.area / obj2.shape.area / 2)

    width1 = obj1.box[2] - obj1.box[0]
    height1 = obj1.box[3] - obj1.box[1]
    width2 = obj2.box[2] - obj2.box[0]
    height2 = obj2.box[3] - obj2.box[1]
    area1 = width1 * height1
    area2 = width2 * height2

    similarity_min = 1 - max(abs(width1 - width2) / (max(width1, width2) + 0.00001),
                             abs(height1 - height2) / (max(height1, height2) + 0.00001))
    similarity_max = 1 - min(abs(width1 - width2) / (max(width1, width2) + 0.00001),
                             abs(height1 - height2) / (max(height1, height2) + 0.00001))
    similarity_area = 1 - abs(area1 - area2) / (max(area1, area2) + 0.00001)
    similarity_length = 1 - abs(width1 - width2 + height1 - height2) / (max(width1 + height1, width2 + height2) + 0.00001)

    # if obj1.id in [91] or obj2.id in [91]:
    #     print('similar', similarity_min, similarity_max, similarity_area)
    #     if (similarity_min > 1 / 2 and similarity_max > 2 / 3) or (similarity_min > 1 / 2 and similarity_area > 2 / 3):
    #         print('yes', obj1.id, obj2.id)

    if (similarity_length > 3 / 4 and similarity_max > 0.9) or (similarity_min > 1 / 2 and similarity_max > 2 / 3) or (similarity_min > 1 / 2 and similarity_area > 2 / 3):
        return score
    
    if obj1.small and obj2.small and similarity_length > 0.4:
        return score
    
    if obj1.tiny and obj2.tiny:
        return score

    # elif similarity > 1/2:
    #     return score*0.25
    # elif similarity > 1/3:
    #     return score*0.125

    return 0
    # return score*0.25


def getHardSimilar(obj1, obj2, weight_store=None, match_store=None):
    if obj1.type != 'group' or obj1.type != obj2.type:
        return False

    if iou(obj1.box, obj2.box) > 0.2:
        return False

    box1 = obj1.box
    box2 = obj2.box

    [x1_A, y1_A, x2_A, y2_A] = box1
    [x1_B, y1_B, x2_B, y2_B] = box2

    width1 = obj1.box[2] - obj1.box[0]
    height1 = obj1.box[3] - obj1.box[1]
    width2 = obj2.box[2] - obj2.box[0]
    height2 = obj2.box[3] - obj2.box[1]
    area1 = width1 * height1
    area2 = width2 * height2

    similarity = 1 - max(abs(width1 - width2) / ((width1 + width2) / 2 + 0.00001),
                         abs(height1 - height2) / ((height1 + height2) / 2 + 0.00001))

    horizontal_distance = max(0, x1_A - x2_B, x1_B - x2_A) / min((height1 + height2), (width1 + width2) * 2)
    vertical_distance = max(0, y1_A - y2_B, y1_B - y2_A) / min((height1 + height2) * 2, (width1 + width2))

    horizontal_align = (abs(x1_A - x1_B) + abs(x2_A - x2_B) + abs((x1_A + x2_A) / 2 - (x1_B + x2_B) / 2)) / (
            width1 + width2)
    vertical_align = (abs(y1_A - y1_B) + abs(y2_A - y2_B) + abs((y1_A + y2_A) / 2 - (y1_B + y2_B) / 2)) / (
            height1 + height2)

    if similarity > 0.85 and max(horizontal_distance, vertical_distance) < 0.05 and min(horizontal_align,
                                                                                        vertical_align) < 0.05:
        sub_obj_list1 = getBasicObj(obj1)
        sub_obj_list2 = getBasicObj(obj2)
        tp1 = getIds(sub_obj_list1)
        tp2 = getIds(sub_obj_list2)
        weight_list1 = searchWeight(sub_obj_list1, tp1, weight_store)
        weight_list2 = searchWeight(sub_obj_list2, tp2, weight_store)

        if getGroupSimilarity(sub_obj_list1, sub_obj_list2, weight_list1, weight_list1, tp1, tp2, match_store) > 0.85:
            return 1
        # return 1

    return 0


def getGroupSimilarity(basic_obj1, basic_obj2, weight_list1, weight_list2, tuple1=None, tuple2=None, match_store=None):
    if match_store is not None:
        ans = match_store.get((tuple1, tuple2))
        if ans is not None:
            return ans

    ll = max(len(basic_obj1), len(basic_obj2))
    mtx = np.zeros((ll, ll))
    for i in range(len(basic_obj1)):
        for j in range(len(basic_obj2)):
            mtx[i][j] = getObjSimilarity(basic_obj1[i], basic_obj2[j]) * weight_list1[i] * weight_list2[j]

    row_ind, col_ind = linear_sum_assignment(-mtx)
    match = mtx[row_ind, col_ind].sum()
    ans = match / max(0.000001, len(basic_obj1) + len(basic_obj2) - match)

    if match_store is not None:
        match_store[(tuple1, tuple2)] = ans
        match_store[(tuple2, tuple1)] = ans

    return ans


def getIds(obj_list):
    ls = []
    for item in obj_list:
        ls.append(item.id)
    ls.sort()
    return tuple(ls)


def get_showed_children(obj):
    cnt = 0
    for sub_obj in obj.children:
        if len(getBasicObj(sub_obj)) > 0:
            cnt += 1
    return cnt


def getFullSame(obj, basic_obj):
    if hasattr(obj, "full_same"):
        return obj.full_same
    obj.full_same = True
    for i in range(len(basic_obj)):
        for j in range(i+1, len(basic_obj)):
            if getObjSimilarity(basic_obj[i], basic_obj[j])<0.95:
                obj.full_same = False
                break
        if not obj.full_same:
            break
    return obj.full_same


def similarRatio(obj, top=False, weight_store=None, match_store=None):
    obj_list = obj.children
    basic_obj_list = []
    basic_weight_list = []
    basic_tuple_list = []
    for tmp_obj in obj_list:
        sub_obj_list = getBasicObj(tmp_obj)
        tp = getIds(sub_obj_list)
        # if weight_store is not None:
        #     if tp not in weight_store:
        #         weight_list = getBasicWeight(sub_obj_list)
        #         weight_store[tp] = weight_list
        #     else:
        #         weight_list = weight_store[tp]
        # else:
        #     weight_list = getBasicWeight(sub_obj_list)
        weight_list = searchWeight(sub_obj_list, tp, weight_store)

        basic_obj_list.append(sub_obj_list)
        basic_weight_list.append(weight_list)
        basic_tuple_list.append(tp)

    full_similar = 0
    cnt_similar = 0
    full_match = True
    # len_ls = []
    # for basic_obj in basic_obj_list:
    #     len_ls.append(len(basic_obj))
    # print(len_ls, basic_weight_list)
    for i in range(len(obj_list) - 1):
        obj1 = obj_list[i]
        for j in range(i + 1, len(obj_list)):
            obj2 = obj_list[j]

            if not top and len(basic_obj_list[i]) == 1 and len(basic_obj_list[j]) == 1:
                if basic_obj_list[i][0].type != basic_obj_list[j][0].type:
                    full_match = False
                    continue

            if match_store is None or (basic_tuple_list[i], basic_tuple_list[j]) not in match_store:
                hard_cover1, soft_cover1 = if_cover(obj1, obj2, type='both')
                hard_cover2, soft_cover2 = if_cover(obj2, obj1, type='both')
                true_cover1 = (hard_cover1 == 1 and obj1.type != "group") or (
                        soft_cover1 == 1 and obj1.type != "group" and obj2.type == "group")
                true_cover2 = (hard_cover2 == 1 and obj2.type != "group") or (
                        soft_cover2 == 1 and obj2.type != "group" and obj1.type == "group")
                if true_cover1 or true_cover2:
                    full_match = False
                    continue

            similarity = getGroupSimilarity(basic_obj_list[i], basic_obj_list[j], basic_weight_list[i],
                                            basic_weight_list[j], basic_tuple_list[i],
                                            basic_tuple_list[j], match_store)

            pair_weight = 1

            # dist = abs(obj1.box[0]+obj1.box[2]-obj2.box[0]-obj2.box[2])/2 + abs(obj1.box[1]+obj1.box[3]-obj2.box[1]-obj2.box[3])/2
            dist = max(0, obj1.box[0] - obj2.box[2], obj2.box[0] - obj1.box[2]) + max(0, obj1.box[1] - obj2.box[3], obj2.box[1] - obj1.box[3])
            size = min(abs(obj1.box[0]-obj1.box[2]), abs(obj2.box[0]-obj2.box[2])) + min(abs(obj1.box[1]-obj1.box[3]), abs(obj2.box[1]-obj2.box[3]))

            # pair_weight = len(basic_obj_list[i])+len(basic_obj_list[j])
            # pair_weight = min(len(basic_obj_list[i]), len(basic_obj_list[j]))
            len1, len2 = len(basic_obj_list[i]), len(basic_obj_list[j])
            if (len1 == 1 or hasattr(obj_list[i], 'full_match')) and (len2 == 1 or hasattr(obj_list[j], 'full_match')):
                if similarity > 0.95 * min(len1, len2) / max(len1, len2):
                    # print('aaa before', similarity, pair_weight, len1, len2)

                    # if False:
                    if getFullSame(obj_list[i], basic_obj_list[i]) and getFullSame(obj_list[j], basic_obj_list[j]):
                        clen1, clen2 = len1, len2
                    else:
                        # clen1, clen2 = max(1, len(obj_list[i].children)), max(1, len(obj_list[j].children))
                        clen1, clen2 = max(1, get_showed_children(obj_list[i])), max(1, get_showed_children(obj_list[j]))

                    pair_weight = clen1 * clen2
                    similarity = similarity / max(min(clen1, clen2) / max(clen1, clen2), min(len1, len2) / max(len1, len2))
            # print('aaa', similarity, pair_weight)
            full_similar += pair_weight * similarity
            cnt_similar += pair_weight

    if cnt_similar == 0:
        return 0, 0

    if full_similar / cnt_similar > 0.95 and full_match:
        obj.full_match = True
    
    # print(full_similar / cnt_similar, cnt_similar)

    return full_similar / cnt_similar, cnt_similar


def getScore(obj, top=True, weight_store=None, match_store=None, shape_store=None, outer_list=None, img_shape=None):
    score_list = np.zeros(6)
    if top:
        score_list[0] += obj.shape.area
        if img_shape is None:
            score_list[1] += (obj.box[2]-obj.box[0])*(obj.box[3]-obj.box[1])
        else:
            score_list[1] += img_shape[0]*img_shape[1]
        # print("top", score_list)
    
    if len(obj.children) > 0:
        inner_shape, inner_flag = getInnerShape(obj, shape_store=shape_store)
        score_cover, cnt_cover = coverRatio(obj, inner_shape.area, inner_flag)
        score_list[0] += score_cover * cnt_cover
        score_list[1] += cnt_cover

        if outer_list is not None:
            for tmp_obj in obj.outer_obj:
                if tmp_obj not in outer_list:
                    outer_list.append(tmp_obj.id)
            
        # score_overlap, cnt_overlap = overlapRatio(obj.children)
        # # print('overlap', score_overlap, cnt_overlap)
        # score_list[2] += score_overlap * cnt_overlap
        # score_list[3] += cnt_overlap

        # score_similar, cnt_similar = similarRatio(obj, top=top, weight_store=weight_store,
        #                                           match_store=match_store)
        # score_list[4] += score_similar * cnt_similar
        # score_list[5] += cnt_similar
    else:
        if ((obj.type == "chart") or ("mark" in obj.type) or ("sub-element" == obj.type)) and (outer_list is not None and obj.id not in outer_list):
            # print(obj.type, "added", obj.id, outer_list)
            score_list[1] += obj.shape.area 

    obj.score_list = score_list
    return score_list


def getFullScore(obj, top=True, weight_store=None, match_store=None, shape_store=None, outer_list=None, img_shape=None):
    score_list = np.zeros(6)

    if outer_list is None:
        outer_list = []

    score_list += getScore(obj, top, weight_store=weight_store, match_store=match_store, shape_store=shape_store, outer_list=outer_list, img_shape=img_shape)

    for sub_obj in obj.children:
        score_list += getFullScore(sub_obj, top=False, weight_store=weight_store, match_store=match_store, shape_store=shape_store, outer_list=outer_list, img_shape=img_shape)

    if top:
        score_list[1] += 0.0000001
        score_list[3] += 0.0000001
        score_list[5] += 0.0000001
    return score_list


def calcOneScore(score_cover, score_overlap, score_similar):
    # return 0.2 * score_cover - 10 * score_overlap + score_similar / 3
    return 0.2 * score_cover - 10 * score_overlap + score_similar / 3


def calcOneScoreFull(full_score):
    return calcOneScore(full_score[0] / full_score[1], full_score[2] / full_score[3], full_score[4] / full_score[5])


def adjust_hierarchy(obj, full_score, father=None, top=True, weight_store=None, match_store=None, shape_store=None):
    ch_list = []
    for ch in obj.children:
        ch_list.append(ch)

    flag = False
    for ch in ch_list:
        new_obj = adjust_hierarchy(ch, full_score, obj, False, weight_store=weight_store, match_store=match_store,
                                    shape_store=shape_store)
        if new_obj != ch:
            flag = True
    
    if flag:
        # print('children updated')
        new_score = full_score - obj.score_list
        getScore(obj, top, weight_store=weight_store, match_store=match_store, shape_store=shape_store)
        new_score = new_score + obj.score_list
        for i in range(len(full_score)):
            full_score[i] = new_score[i]

    if len(obj.children) == 2:
        start = time.time()
        cover = False
        obj1, obj2 = obj.children[0], obj.children[1]
        hard_cover1 = if_cover(obj1, obj2, type='hard')
        hard_cover2 = if_cover(obj2, obj1, type='hard')
        if hard_cover1 == 1 and obj1.type == "group":
            cover = True
        elif hard_cover2 == 1 and obj2.type == "group":
            cover = True
            obj1, obj2 = obj2, obj1

        hard_similar = getHardSimilar(obj1, obj2, weight_store=weight_store, match_store=match_store)

        if not cover and not (hard_similar and not obj1.inner_flag and not obj2.inner_flag):
            # print('bk', time.time() - start)
            return obj

        if obj1.type == "group":
            insert_obj = Group()
            min_x = 10000000
            min_y = 10000000
            max_x = -10000000
            max_y = -10000000
            for sub_obj in obj1.children:
                insert_obj.children.append(sub_obj)
                min_x = min(min_x, sub_obj.box[0])
                min_y = min(min_y, sub_obj.box[1])
                max_x = max(max_x, sub_obj.box[2])
                max_y = max(max_y, sub_obj.box[3])
            insert_obj.children.append(obj2)
            min_x = min(min_x, obj2.box[0])
            min_y = min(min_y, obj2.box[1])
            max_x = max(max_x, obj2.box[2])
            max_y = max(max_y, obj2.box[3])
            insert_obj.box = [min_x, min_y, max_x, max_y]
            insert_obj.type = 'group'
            getSubType(insert_obj)
            # print("shape1 before", time.time() - start)
            # getShape(insert_obj, False, shape_store=shape_store)
            insert_obj.shape = obj.shape
            # print("score1 before", time.time() - start)
            getScore(insert_obj, top, weight_store=weight_store, match_store=match_store, shape_store=shape_store)
            insert_score_list = full_score - obj.score_list - obj1.score_list + insert_obj.score_list
            insert_score = calcOneScoreFull(insert_score_list)
        else:
            insert_obj = Group()
            insert_score = -100000000
            insert_score_list = []
        # print("calc1 time", time.time() - start)

        if obj1.type == "group" and obj2.type == "group":
            merge_obj = Group()
            min_x = 10000000
            min_y = 10000000
            max_x = -10000000
            max_y = -10000000
            for sub_obj in obj1.children:
                merge_obj.children.append(sub_obj)
                min_x = min(min_x, sub_obj.box[0])
                min_y = min(min_y, sub_obj.box[1])
                max_x = max(max_x, sub_obj.box[2])
                max_y = max(max_y, sub_obj.box[3])
            for sub_obj in obj2.children:
                merge_obj.children.append(sub_obj)
                min_x = min(min_x, sub_obj.box[0])
                min_y = min(min_y, sub_obj.box[1])
                max_x = max(max_x, sub_obj.box[2])
                max_y = max(max_y, sub_obj.box[3])
            merge_obj.box = [min_x, min_y, max_x, max_y]
            merge_obj.type = 'group'
            getSubType(merge_obj)
            # print("shape2 before", time.time() - start)
            # getShape(merge_obj, False, shape_store=shape_store)
            merge_obj.shape = obj.shape
            # print("score2 before", time.time() - start)
            getScore(merge_obj, top, weight_store=weight_store, match_store=match_store, shape_store=shape_store)
            merge_score_list = full_score - obj.score_list - obj1.score_list - obj2.score_list + merge_obj.score_list
            merge_score = calcOneScoreFull(merge_score_list)
        else:
            merge_obj = Group()
            merge_score = -100000000
            merge_score_list = []
        # print("calc2 time", time.time() - start)

        ori_score = calcOneScoreFull(full_score)

        if merge_score+0.00005 >= insert_score and merge_score >= ori_score:
            new_score = full_score - obj.score_list - obj1.score_list - obj2.score_list + merge_obj.score_list
            for i in range(len(full_score)):
                full_score[i] = new_score[i]
            if father is not None:
                father.children.remove(obj)
                father.children.append(merge_obj)
                # print("ad time", time.time() - start)
                return merge_obj
        elif insert_score > merge_score+0.00005 and insert_score >= ori_score:
            # print('score', insert_score, merge_score, ori_score)
            new_score = full_score - obj.score_list - obj1.score_list + insert_obj.score_list
            for i in range(len(full_score)):
                full_score[i] = new_score[i]
            if father is not None:
                father.children.remove(obj)
                father.children.append(insert_obj)
                # print("ad time", time.time() - start)
                return insert_obj

        # print("bk time", time.time() - start)
    return obj
