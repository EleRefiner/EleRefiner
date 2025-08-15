#ifndef _SCENE_TREE_H
#define _SCENE_TREE_H

#include <iostream>
#include <vector>
#include <utility>
#include <ctime>
#include <algorithm>
#include <math.h>
#include <map>
#include <string>
#include <cmath>


void GetAns(std::vector<std::vector<int>> &ans, int id, std::vector<std::vector<int>> children) {
    std::vector<int> tmp;
    tmp.push_back(id); tmp.push_back(children[id].size());
    ans.push_back(tmp);
    for(int i=0;i<children[id].size();i++) {
        GetAns(ans, children[id][i], children);
    }
}


std::string getSubType(int now_id, std::vector<int> &children, double bounds[][4], std::vector<std::string> &categories, std::vector<std::string> &sub_categories) {
    std::string sub_type = "group";
    double area = (bounds[now_id][2] - bounds[now_id][0]) * (bounds[now_id][3] - bounds[now_id][1]);
    double ratio = 0.9;
    for(int i=0;i<children.size();i++) {
        int id1 = children[i];
        std::string tmp_type = categories[id1];
        if(tmp_type == "group")
            tmp_type = sub_categories[id1];
        if((tmp_type == "data")||(tmp_type == "non-data")) {
            double sub_area = (bounds[id1][2] - bounds[id1][0]) * (bounds[id1][3] - bounds[id1][1]);
            if(sub_area > area * ratio) {
                ratio = sub_area / area;
                sub_type = tmp_type;
            }
        }
    }
    return sub_type;
}


double get_dist(double bound1[], double bound2[], std::string &category1, std::string &category2, std::string &sub_category1, std::string &sub_category2) {

    double x1_A = bound1[0], y1_A = bound1[1], x2_A = bound1[2], y2_A = bound1[3];
    double x1_B = bound2[0], y1_B = bound2[1], x2_B = bound2[2], y2_B = bound2[3];

    double horizontal_distance = std::max(std::max(0.0, x1_A - x2_B), x1_B - x2_A);
    double vertical_distance = std::max(std::max(0.0, y1_A - y2_B), y1_B - y2_A);

    double dist = std::max(horizontal_distance, vertical_distance);

    double horizontal_align = std::abs(x1_A - x1_B) + std::abs(x2_A - x2_B) + std::abs((x1_A + x2_A) / 2 - (x1_B + x2_B) / 2);
    double vertical_align = std::abs(y1_A - y1_B) + std::abs(y2_A - y2_B) + std::abs((y1_A + y2_A) / 2 - (y1_B + y2_B) / 2);
    double align = 0.9 * std::min(horizontal_align, vertical_align) + 0.1 * std::max(horizontal_align, vertical_align);

    double horizontal_similar = std::abs((x2_A - x1_A) - (x2_B - x1_B));
    double vertical_similar = std::abs((y2_A - y1_A) - (y2_B - y1_B));
    double similar = 0.9 * std::min(horizontal_similar, vertical_similar) + 0.1 * std::max(horizontal_similar, vertical_similar);

    double tot_dist = dist + 0.3 * align + 0.2 * similar;

    if((category1!=category2)&&((category1!="group")&&(category1!="non-data")&&(category1!="data"))&&((category2!="group")&&(category2!="non-data")&&(category2!="data"))) {
        tot_dist *= 0.75;
    } else if(((category1=="data")||((category1=="group")&&(sub_category1=="data")))&&((category2=="data")||((category2=="group")&&(sub_category2=="data")))) {
        tot_dist *= 0.75;
    } else if(((category1=="non-data")||((category1=="group")&&(sub_category1=="non-data")))&&((category2=="non-data")||((category2=="group")&&(sub_category2=="non-data")))) {
        tot_dist *= 0.75;
    } else if((category1=="group")&&(category2=="group")) {
        tot_dist *= 0.9;
    } else if((((category1=="data")||(category1=="non-data"))||((category1=="group")&&((sub_category1=="data")||(sub_category1=="non-data"))))&&((category2=="text")||(category2=="image"))) {
        tot_dist *= 1.2;
    } else if((((category2=="data")||(category2=="non-data"))||((category2=="group")&&((sub_category2=="data")||(sub_category2=="non-data"))))&&((category1=="text")||(category1=="image"))) {
        tot_dist *= 1.2;
    }
    return tot_dist;
}


int if_cover(double bound1[], double bound2[], std::string &category1, std::string &category2, std::string &sub_category1, std::string &sub_category2) {

    double x1_A = bound1[0], y1_A = bound1[1], x2_A = bound1[2], y2_A = bound1[3];
    double x1_B = bound2[0], y1_B = bound2[1], x2_B = bound2[2], y2_B = bound2[3];

    double x_left = std::max(x1_A, x1_B);
    double y_top = std::max(y1_A, y1_B);
    double x_right = std::min(x2_A, x2_B);
    double y_bottom = std::min(y2_A, y2_B);

    double intersection_area = 0;
    if((x_right < x_left) || (y_bottom < y_top)){
        intersection_area = 0;
    } else {
        double intersection_width = x_right - x_left;
        double intersection_height = y_bottom - y_top;
        intersection_area = intersection_width * intersection_height;
    }

    double A_area = (x2_A - x1_A) * (y2_A - y1_A);
    double B_area = (x2_B - x1_B) * (y2_B - y1_B);

    int hard = 0;
    if((intersection_area > 0.8 * B_area) && (B_area < 0.8 * A_area) && (B_area-intersection_area < 0.75 * (A_area-intersection_area))) {
        hard = 1;
    }
    if((intersection_area > 0.95 * B_area) && (B_area < 0.95 * A_area)) {
        hard = 1;
    }

    return hard;
}


void get_adjust_dist(double a_dist_m[], double dist_m[], int can_merge_lm[], int cover_m[], int can_merge_m[], int obj_list[], int obj_list_len, double tmp_l[], int max_n) {

    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            a_dist_m[id1*max_n+id2] = dist_m[id1*max_n+id2];
        }
    }

    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        int flag = 0;
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            if(cover_m[id1*max_n+id2]>0) {
                flag += 1;
            }
        }
        if(flag > 1) {
            for(int j=0;j<obj_list_len;j++) {
                int id2 = obj_list[j];
                if(cover_m[id1*max_n+id2]>0) {
                    a_dist_m[id1*max_n+id2] *= 20;
                    a_dist_m[id2*max_n+id1] *= 20;
                }
            }
        }
    }

    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        tmp_l[id1] = 0;
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            tmp_l[id1] += cover_m[id2*max_n+id1];
        }
        tmp_l[id1] = std::max(1.0, tmp_l[id1]);
    }
    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        for(int j=i+1;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            if(can_merge_m[id1*max_n+id2]&&can_merge_m[id2*max_n+id1]) {
                double p = pow(30, std::min(tmp_l[id1], tmp_l[id2]));
                a_dist_m[id1*max_n+id2] /= p;
                a_dist_m[id2*max_n+id1] /= p;
			}
        }
    }

    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            if(!can_merge_lm[id1*max_n+id2]) a_dist_m[id1*max_n+id2] = 100000000;
        }
    }

    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        a_dist_m[id1*max_n+id1] = 100000000;
    }
}


double get_thres(double dist_m[], int obj_list[], int obj_list_len, int max_n, std::string type) {
    double ori_thres = -1;
    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            if(dist_m[id1*max_n+id2] == 0)continue;
            if((ori_thres < 0) || (dist_m[id1*max_n+id2] < ori_thres)) ori_thres = dist_m[id1*max_n+id2];
        }
    }
    double thres = ori_thres;
    for(int i=0;i<obj_list_len;i++) {
        int id1 = obj_list[i];
        for(int j=0;j<obj_list_len;j++) {
            int id2 = obj_list[j];
            if(dist_m[id1*max_n+id2] == 0)continue;
            if((dist_m[id1*max_n+id2] > thres) && (dist_m[id1*max_n+id2] < 1.05*ori_thres)) thres = dist_m[id1*max_n+id2];
        }
    }

    return thres;
}


void merge(int id1, int id2, std::vector<std::vector<int>> &merge_list, int merge_cluster[], double max_thres[], double dist=0) {
    int cluster1 = merge_cluster[id1];
    int cluster2 = merge_cluster[id2];
    if(cluster1 == cluster2) return;
    for(int k=0;k<merge_list[cluster2].size();k++) {
        int id3 = merge_list[cluster2][k];
        merge_cluster[id3] = cluster1;
        merge_list[cluster1].push_back(id3);
    }
    std::vector<int> tmp;
    merge_list[cluster2] = tmp;
    max_thres[cluster1] = std::max(std::max(max_thres[cluster1], max_thres[cluster2]), dist);
}


std::vector<std::vector<int>> HierarchyMerge(std::vector<std::vector<double>> _bounds, std::vector<std::string> categories) {
    int n = _bounds.size();
    int now_n = n;

    if(n == 1) {
        std::vector<std::vector<int>> ans;
        std::vector<int> cut;
        cut.push_back(0);
        cut.push_back(0);
        ans.push_back(cut);
        return ans;
    }

    int max_n = n*2+5;

//	double (*bounds)[4];
    double (*bounds)[4] = new double[max_n][4];
    for(int i=0;i<n;i++) {
        for(int j=0;j<4;j++) {
            bounds[i][j] = _bounds[i][j];
        }
    }
    std::vector<std::string> sub_categories;
    for(int i=0;i<n;i++) sub_categories.push_back("");

    int full_flag = 1;
    int cnt = 100000;
    int cnt2 = 0;

    int *cover_m = new int[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) cover_m[i] = 0;
    int *can_merge_l = new int[max_n];
    for(int i=0;i<max_n;i++) can_merge_l[i] = 1;
    int *can_merge_m = new int[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) can_merge_m[i] = 0;
    int *can_merge_m2 = new int[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) can_merge_m2[i] = 0;
    int *can_merge_lm = new int[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) can_merge_lm[i] = 0;
    double *dist_m = new double[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) dist_m[i] = 0;
    double *a_dist_m = new double[max_n*max_n];
    for(int i=0;i<max_n*max_n;i++) a_dist_m[i] = 0;

    double *tmp_l = new double[max_n];
    for(int i=0;i<max_n;i++) tmp_l[i] = 0;

    int *obj_list = new int[max_n];
    for(int i=0;i<n;i++) obj_list[i] = i;
    int obj_list_len = n;

    int *new_obj_list = new int[max_n];
    int new_obj_list_len = 0;

    int one_list_len = 0;

    double thres = 0;
    double ori_thres = 0;

    int *merge_cluster = new int[max_n];
    double *max_thres = new double[max_n];
    std::vector<std::vector<int>> merge_list;
    for(int i=0;i<max_n;i++) {
        std::vector<int> tmp;
        merge_list.push_back(tmp);
    }
    std::vector<std::vector<int>> children;
    for(int i=0;i<max_n;i++) {
        std::vector<int> tmp;
        children.push_back(tmp);
    }
    while((obj_list_len > 1) && (cnt > 0)) {
        cnt -= 1;
        cnt2 += 1;

        if(full_flag > 0) {
            for(int i=0;i<one_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=one_list_len;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    cover_m[id1*max_n+id2] = if_cover(bounds[id1], bounds[id2], categories[id1], categories[id2], sub_categories[id1], sub_categories[id2]);
                    cover_m[id2*max_n+id1] = if_cover(bounds[id2], bounds[id1], categories[id2], categories[id1], sub_categories[id1], sub_categories[id2]);
                }
            }
            for(int i=one_list_len;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=i+1;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    cover_m[id1*max_n+id2] = if_cover(bounds[id1], bounds[id2], categories[id1], categories[id2], sub_categories[id1], sub_categories[id2]);
                    cover_m[id2*max_n+id1] = if_cover(bounds[id2], bounds[id1], categories[id2], categories[id1], sub_categories[id1], sub_categories[id2]);
                }
            }

            for(int i=0;i<obj_list_len;i++) can_merge_l[obj_list[i]] = 1;
            for(int i=0;i<obj_list_len;i++) {
                for(int j=0;j<obj_list_len;j++) can_merge_m[obj_list[i]*max_n+obj_list[j]] = 0;
            }
            for(int i=0;i<obj_list_len;i++) {
                for(int j=0;j<obj_list_len;j++) can_merge_m2[obj_list[i]*max_n+obj_list[j]] = 0;
            }
            for(int i=0;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                int father = -1;
                double father_area = -1;
                for(int j=0;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    if(cover_m[id2*max_n+id1] == 0) continue;
                    double new_area = (bounds[id2][2] - bounds[id2][0]) * (bounds[id2][3] - bounds[id2][1]);
                    if((father == -1) || (new_area < father_area)) {
                        father = id2;
                        father_area = new_area;
                    }
                }
                if(father != -1) {
                    can_merge_l[id1] = 0;
                    can_merge_l[father] = 0;
                    can_merge_m[id1*max_n+father] = can_merge_m2[father*max_n+id1] = 1;
                    for(int j=0;j<obj_list_len;j++) {
                        int id2 = obj_list[j];
                        if(cover_m[father*max_n+id2] == 0) continue;
                        can_merge_m[id1*max_n+id2] = can_merge_m2[father*max_n+id2] = 1;
                    }
                }
            }

            for(int i=0;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                int flag = 0;
                for(int j=0;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    if(can_merge_m2[id1*max_n+id2]>0) {
                        flag = 1;
                        break;
                    }
                }
                if(flag>0) {
                    for(int j=0;j<obj_list_len;j++) {
                        int id2 = obj_list[j];
                        can_merge_m[id1*max_n+id2] = can_merge_m2[id1*max_n+id2];
                    }
                }
            }

            for(int i=0;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=i+1;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    can_merge_lm[id1*max_n+id2] = can_merge_lm[id2*max_n+id1] = (can_merge_l[id1] > 0 || can_merge_m[id1*max_n+id2] > 0) && (can_merge_l[id2] > 0 or can_merge_m[id2*max_n+id1] > 0);
                }
            }

            for(int i=0;i<one_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=one_list_len;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    dist_m[id1*max_n+id2] = get_dist(bounds[id1], bounds[id2], categories[id1], categories[id2], sub_categories[id1], sub_categories[id2]);
                    dist_m[id2*max_n+id1] = get_dist(bounds[id2], bounds[id1], categories[id2], categories[id1], sub_categories[id1], sub_categories[id2]);
                }
            }
            for(int i=one_list_len;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=i+1;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    dist_m[id1*max_n+id2] = get_dist(bounds[id1], bounds[id2], categories[id1], categories[id2], sub_categories[id1], sub_categories[id2]);
                    dist_m[id2*max_n+id1] = get_dist(bounds[id2], bounds[id1], categories[id2], categories[id1], sub_categories[id1], sub_categories[id2]);
                }
            }

            get_adjust_dist(a_dist_m, dist_m, can_merge_lm, cover_m, can_merge_m, obj_list, obj_list_len, tmp_l, max_n);

            thres = get_thres(a_dist_m, obj_list, obj_list_len, max_n, "hard");
            ori_thres = thres;
        }

        for(int i=0;i<obj_list_len;i++) {
            int id1 = obj_list[i];
            std::vector<int> tmp;
            tmp.push_back(id1);
            merge_list[id1] = tmp;
        }
        for(int i=0;i<obj_list_len;i++) {
            int id1 = obj_list[i];
            merge_cluster[id1] = id1;
        }
        for(int i=0;i<obj_list_len;i++) {
            int id1 = obj_list[i];
            max_thres[id1] = 0;
        }

        double merge_scale1 = 2;
        double merge_scale2 = 1.5;

        int full_flag = 0;
        int flag = true;

        while(flag) {
            flag = false;
            for(int i=0;i<obj_list_len;i++) {
                int id1 = obj_list[i];
                for(int j=i+1;j<obj_list_len;j++) {
                    int id2 = obj_list[j];
                    if(a_dist_m[id1*max_n+id2] > thres * merge_scale1) continue;
                    if(merge_cluster[id1] == merge_cluster[id2]) continue;

                    if(!can_merge_lm[id1*max_n+id2]) continue;

                    // double tmp_thres = thres
                    // if(merge_list[merge_cluster[id1]].size() > 1) {
                    //     tmp_thres = std::min(thres * merge_scale1, std::max(std::max_thres[merge_cluster[id1]] * merge_scale2, tmp_thres))
                    // }
                    // if(merge_list[merge_cluster[id2]].size() > 1) {
                    //     tmp_thres = std::min(thres * merge_scale1, std::max(std::max_thres[merge_cluster[id2]] * merge_scale2, tmp_thres))
                    // }
                    double tmp_thres = thres * merge_scale2;

                    if(a_dist_m[id1*max_n+id2] > tmp_thres + 0.000001) continue;

                    full_flag += 1;
                    flag = true;
                    merge(id1, id2, merge_list, merge_cluster, max_thres, a_dist_m[id1*max_n+id2]);

                    if(cover_m[id1*max_n+id2]) {
                        for(int k=0;k<obj_list_len;k++) {
                            int id3 = obj_list[k];
                            if((cover_m[id1*max_n+id3]>0)&&(merge_cluster[id3] != merge_cluster[id1]))
                                merge(id1, id3, merge_list, merge_cluster, max_thres);
                        }
                    }
                    if(cover_m[id2*max_n+id1]) {
                        for(int k=0;k<obj_list_len;k++) {
                            int id3 = obj_list[k];
                            if((cover_m[id2*max_n+id3]>0)&&(merge_cluster[id3] != merge_cluster[id2]))
                                merge(id2, id3, merge_list, merge_cluster, max_thres);
                        }
                    }
                }
            }
        }

        new_obj_list_len = 0;
        one_list_len = 0;

        for(int i=0;i<obj_list_len;i++) {
            int id1 = obj_list[i];
            if(merge_list[id1].size() == 1) {
                new_obj_list[new_obj_list_len] = merge_list[id1][0];
                new_obj_list_len += 1;
                one_list_len += 1;
            }
        }

        for(int i=0;i<obj_list_len;i++) {
            int id1 = obj_list[i];
            if(merge_list[id1].size() <= 1) continue;

            double min_x = 10000000;
            double min_y = 10000000;
            double max_x = -10000000;
            double max_y = -10000000;
            for(int j=0;j<merge_list[id1].size();j++) {
                int id2 = merge_list[id1][j];
                children[now_n].push_back(id2);
                min_x = std::min(min_x, bounds[id2][0]);
                min_y = std::min(min_y, bounds[id2][1]);
                max_x = std::max(max_x, bounds[id2][2]);
                max_y = std::max(max_y, bounds[id2][3]);
            }
            bounds[now_n][0] = min_x; bounds[now_n][1] = min_y; bounds[now_n][2] = max_x; bounds[now_n][3] = max_y;
            categories.push_back("group");
            sub_categories.push_back(getSubType(now_n, children[now_n], bounds, categories, sub_categories));

            new_obj_list[new_obj_list_len] = now_n;
            new_obj_list_len += 1;
            now_n += 1;
        }

        if(full_flag == 0)
            thres += std::min(0.5 * thres, std::max(0.2 * thres, ori_thres));

        for(int i=0;i<new_obj_list_len;i++) obj_list[i] = new_obj_list[i];
        obj_list_len = new_obj_list_len;
    }

    std::vector<std::vector<int>> ans;
    GetAns(ans, obj_list[0], children);

    delete[] bounds;
    delete[] cover_m;
    delete[] can_merge_l;
    delete[] can_merge_m;
    delete[] can_merge_m2;
    delete[] can_merge_lm;
    delete[] dist_m;
    delete[] a_dist_m;
    delete[] tmp_l;
    delete[] obj_list;
    delete[] new_obj_list;
    delete[] merge_cluster;
    delete[] max_thres;
    return ans;
}

#endif