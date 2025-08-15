#ifndef _TREEMAP_H
#define _TREEMAP_H

#include <iostream>
#include <vector>
#include <utility>
#include <ctime>
#include <algorithm>
#include <math.h>
#include <map>

#define MAXSTATE 100000000
#define MAXGRID 200

//double time0 = 0;
//double time1 = 0;
//double time2 = 0;
//double time3 = 0;
//double time4 = 0;
//double time5 = 0;
//double time_dp = 0;

//int CalcCount = 0;

void AxisRank(int order[], int n, std::vector<int> &rank, int SetRank[]) {
    if(SetRank[0]!=-1) {
        memcpy(order, SetRank, n*sizeof(int));
        return;
    }
    for(int i=0;i<n-1;i++)
    for(int j=i+1;j<n;j++)
    if(rank[order[j]]<rank[order[i]]) {
        int tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }
    memcpy(SetRank, order, n*sizeof(int));
}

int getSetId(long long now_set, 
std::unordered_map<long long, int> &SetHash, int &SetCount,
std::vector<std::unordered_map<int, int>> &StateHash, int &StateCount) {
    if(SetHash.count(now_set)==0){
        SetHash[now_set] = SetCount;
        std::unordered_map<int, int> newSizeHash;
		StateHash.push_back(newSizeHash);
//        StateHash[SetCount] = newSizeHash;
        SetCount += 1;
    }
    int SetId = SetHash[now_set];
    
    return SetId;
}

int getStateId(long long now_set, int grid_x, int grid_y,
std::unordered_map<long long, int> &SetHash, int &SetCount,
std::vector<std::unordered_map<int, int>> &StateHash, int &StateCount,
int CutAxis[]) {
    int SetId = getSetId(now_set, SetHash, SetCount, StateHash, StateCount);
    
    int now_size = grid_x * MAXGRID + grid_y;
    if(StateHash[SetId].count(now_size)==0){
        StateHash[SetId][now_size] = StateCount;
        CutAxis[StateCount] = -1;
        StateCount += 1;
    }
    int StateId = StateHash[SetId][now_size];
    
    return StateId;
}

double SearchForTreeDP(std::vector<std::vector<double>> &xy, std::vector<std::vector<double>> &sxy,
std::vector<int> &rank_x, std::vector<int> &rank_y, std::vector<double> &weight,
long long now_set, int n, int grid_x, int grid_y,
std::unordered_map<long long, int> &SetHash, int &SetCount,
std::vector<std::unordered_map<int, int>> &StateHash, int &StateCount,
int CutAxis[], int CutPlace[], double CutCost[],
int SetRankX[], int SetRankY[],
int ori_grid_x, int ori_grid_y, bool use_area_bias=false, double area_ratio=0.05) {
//    CalcCount += 1;

//    double full_start = clock();
//    double start = clock();

    if(SetHash.count(now_set)==0){
        SetHash[now_set] = SetCount;
        std::unordered_map<int, int> newSizeHash;
        newSizeHash.reserve(5*(grid_x+grid_y+1));
        StateHash.push_back(newSizeHash);
//        StateHash[SetCount] = newSizeHash;
        SetCount += 1;
    }
    int SetId = SetHash[now_set];
    
//    time0 += (clock()-start)/CLOCKS_PER_SEC;
    
    int now_size = grid_x * MAXGRID + grid_y;
    std::unordered_map<int, int>* tmp_map = &(StateHash[SetId]);
    
//    time0 += (clock()-start)/CLOCKS_PER_SEC;
    
    if((*tmp_map).count(now_size)==0){
        (*tmp_map)[now_size] = StateCount;
        CutAxis[StateCount] = -1;
        StateCount += 1;
    }
    int StateId = (*tmp_map)[now_size];

//    time0 += (clock()-start)/CLOCKS_PER_SEC;

//    start = clock();

    double tot = 0;
    for(int i=0;i<n;i++)
    if(now_set&(1ll<<i)) {
        tot += weight[i];
    }

    if(CutAxis[StateId]>=0) {
        
//        time1 += (clock()-start)/CLOCKS_PER_SEC;
//        time_dp += (clock()-full_start)/CLOCKS_PER_SEC;
        
        return CutCost[StateId];
    }
    
    int now_n = 0;
    int tmp_i = -1;
    for(int i=0;i<n;i++)
    if(now_set&(1ll<<i)) {
        now_n += 1;
        tmp_i = i;
    }
    
    if(now_n == 1) {

//        grid_x = std::max(1, grid_x);
//        grid_y = std::max(1, grid_y);
//        double size_x = 1.0*grid_x/(grid_x+grid_y);
//        double size_y = 1.0*grid_y/(grid_x+grid_y);
//        double cost = tot*tot*(size_x*size_x+size_y*size_y)/(size_x*size_y);
        
        double cost = 1.0*(grid_x*grid_x+grid_y*grid_y) * grid_x*grid_y / 12 /(ori_grid_x*ori_grid_y*ori_grid_x*ori_grid_y);
        if(use_area_bias) {
            double diff = std::abs(weight[tmp_i]/weight[weight.size()-1]-1.0*grid_x*grid_y/(ori_grid_x*ori_grid_y));
//            double cons = std::max(area_ratio/5, area_ratio*weight[tmp_i]/weight[weight.size()-1]);
            double cons = area_ratio*weight[tmp_i]/weight[weight.size()-1];
            if(diff>cons)cost += 0.1*(diff-cons);
        }

        CutAxis[StateId] = 0;
        CutPlace[StateId] = 0;
        CutCost[StateId] = cost;

//        time1 += (clock()-start)/CLOCKS_PER_SEC;
//        time_dp += (clock()-full_start)/CLOCKS_PER_SEC;
        
        return cost;
    }
    
    int *order_x = new int[n];
    int *order_y = new int[n];
    now_n = 0;
    for(int i=0;i<n;i++)
    if(now_set&(1ll<<i)) {
        order_x[now_n] = order_y[now_n] = i;
        now_n += 1;
    }

    AxisRank(order_x, now_n, rank_x, SetRankX+(SetId*n));
    AxisRank(order_y, now_n, rank_y, SetRankY+(SetId*n));
    
//    bool flag = false;
//    if((grid_x == 6)&&(grid_y == 10)&&(now_n==3)) {
//        for(int i=0;i<now_n;i++) printf("(%.2lf, %.2lf) ", xy[order_y[i]][0], xy[order_y[i]][1]);
//        printf("\n");
//        for(int i=0;i<now_n;i++) printf("(%.2f) ", weight[order_y[i]]);
//        printf("\n");
//        if((weight[order_y[0]]==312)&&(weight[order_y[1]]==12)&&(weight[order_y[2]]==66))
//            flag = true;
//    }
    
//    time1 += (clock()-start)/CLOCKS_PER_SEC;

//    start = clock();

    double *left = new double[now_n];
    double *right = new double[now_n];
    double *top = new double[now_n];
    double *bottom = new double[now_n];

    std::vector<double> cross;
    for(int axis=0;axis<2;axis++) {
        int *order;
        if(axis==0)order = order_x;
        else order = order_y;

        double *small, *big;
        if(axis==0) {
            small = left;
            big = right;
        }else {
            small = top;
            big = bottom;
        }

        double tmp = -1;
        for(int i=0;i<now_n;i++){
            tmp = std::max(tmp, xy[order[i]][axis]+sxy[order[i]][axis]);
            small[i] = tmp;
        }
        tmp = 10000000;
        for(int i=now_n-1;i>=0;i--){
            tmp = std::min(tmp, xy[order[i]][axis]-sxy[order[i]][axis]);
            big[i] = tmp;
        }
        for(int i=0;i<now_n-1;i++)cross.push_back(small[i]-big[i+1]);
    }

    std::sort(cross.begin(), cross.end());

//    time2 += (clock()-start)/CLOCKS_PER_SEC;

    long long now_set1, now_set2;
    for(int axis=0;axis<2;axis++) {

//        double start = clock();

        int *order;
        if(axis==0)order = order_x;
        else order = order_y;

        double *small, *big;
        if(axis==0) {
            small = left;
            big = right;
        }else {
            small = top;
            big = bottom;
        }

        now_set1 = now_set2 = 0;
        double tmp_count = 0;

        double thres = cross[cross.size()/4]+1e-3;
//        thres = std::min(thres, (cross[0]+cross[cross.size()/2])/2+1e-3);
        if(cross[0]<=-0.005) {
            thres = -0.005;
        }else {
            thres = 100000;
        }

//        time3 += (clock()-start)/CLOCKS_PER_SEC;

        for(int i=0;i<now_n-1;i++) {
            now_set1 += (1ll)<<order[i];
            now_set2 = now_set-now_set1;
            tmp_count += weight[order[i]];
            if(small[i]-big[i+1]<=thres) {
                
//                double start = clock();

                int new_grid_x1 = grid_x;
                int new_grid_y1 = grid_y;
                int new_grid_x2 = grid_x;
                int new_grid_y2 = grid_y;
                if(axis==0){
                    new_grid_x1 = grid_x*tmp_count/tot+0.5;
                    new_grid_x2 = grid_x-new_grid_x1;
                    if(grid_x>0) {
                        if(new_grid_x1 == 0) {
                            new_grid_x1 += 1;
                            new_grid_x2 -= 1;
                        }
                        if(new_grid_x2 == 0) {
                            new_grid_x2 += 1;
                            new_grid_x1 -= 1;
                        }
                    }
                }else{
                    new_grid_y1 = grid_y*tmp_count/tot+0.5;
                    new_grid_y2 = grid_y-new_grid_y1;
                    if(grid_y>0) {
                        if(new_grid_y1 == 0) {
                            new_grid_y1 += 1;
                            new_grid_y2 -= 1;
                        }
                        if(new_grid_y2 == 0) {
                            new_grid_y2 += 1;
                            new_grid_y1 -= 1;
                        }
                    }
                }

//                time4 += (clock()-start)/CLOCKS_PER_SEC;
                
//                start = clock();
                
                double cost1 = SearchForTreeDP(xy, sxy, rank_x, rank_y, weight, now_set1, n, new_grid_x1, new_grid_y1, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ori_grid_x, ori_grid_y, use_area_bias, area_ratio);
                double cost2 = SearchForTreeDP(xy, sxy, rank_x, rank_y, weight, now_set2, n, new_grid_x2, new_grid_y2, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ori_grid_x, ori_grid_y, use_area_bias, area_ratio);

//                time_dp -= (clock()-start)/CLOCKS_PER_SEC;
                
//                start = clock();

                double cost = cost1 + cost2;
                if((CutAxis[StateId]<0)||(CutCost[StateId]>cost)) {
                    CutAxis[StateId] = axis;
                    CutPlace[StateId] = i;
                    CutCost[StateId] = cost;
                }

//                time5 += (clock()-start)/CLOCKS_PER_SEC;
            }
        }
    }
    
//    time_dp += (clock()-full_start)/CLOCKS_PER_SEC;

    delete[] order_x;
    delete[] order_y;

    delete[] left;
    delete[] right;
    delete[] top;
    delete[] bottom;

//    time_dp += (clock()-full_start)/CLOCKS_PER_SEC;
        
    return CutCost[StateId];
}


void getAns(std::vector<std::vector<double>> &xy, std::vector<std::vector<double>> &sxy,
std::vector<int> &rank_x, std::vector<int> &rank_y, std::vector<double> &weight,
long long now_set, int n, int grid_x, int grid_y,
std::unordered_map<long long, int> &SetHash, int &SetCount,
std::vector<std::unordered_map<int, int>> &StateHash, int &StateCount,
int CutAxis[], int CutPlace[], double CutCost[],
int SetRankX[], int SetRankY[], 
std::vector<std::vector<int>> &ans) {

//    printf("size: %d %d\n", grid_x, grid_y);
    
    if(SetHash.count(now_set)==0){
        SetHash[now_set] = SetCount;
        std::unordered_map<int, int> newSizeHash;
        newSizeHash.reserve(5*(grid_x+grid_y+1));
        StateHash.push_back(newSizeHash);
//        StateHash[SetCount] = newSizeHash;
        SetCount += 1;
    }
    int SetId = SetHash[now_set];
    
    int now_size = grid_x * MAXGRID + grid_y;
    if(StateHash[SetId].count(now_size)==0){
        StateHash[SetId][now_size] = StateCount;
        CutAxis[StateCount] = -1;
        StateCount += 1;
    }
    int StateId = StateHash[SetId][now_size];

    int *order = new int[n];
    int now_n = 0;
    for(int i=0;i<n;i++)
    if(now_set&(1ll<<i)) {
        order[now_n] = i;
        now_n += 1;
    }

    double tot = 0;
    for(int i=0;i<now_n;i++)tot += weight[order[i]];

    if(now_n == 1) {
        delete[] order;
        return;
    }

    std::vector<int> cut;
    cut.push_back(CutAxis[StateId]);
    cut.push_back(CutPlace[StateId]);
    ans.push_back(cut);
    
//    printf("cut: %d %d\n", cut[0], cut[1]);

    long long now_set1, now_set2;
    int axis = CutAxis[StateId];
    int place = CutPlace[StateId];
    if(axis==0)AxisRank(order, now_n, rank_x, SetRankX+(SetId*n));
    else AxisRank(order, now_n, rank_y, SetRankY+(SetId*n));
    
    now_set1 = now_set2 = 0;
    double tmp_count = 0;
    for(int i=0;i<=place;i++) {
        now_set1 += (1ll)<<order[i];
        tmp_count += weight[order[i]];
    }
    now_set2 = now_set-now_set1;
    
    int new_grid_x1 = grid_x;
    int new_grid_y1 = grid_y;
    int new_grid_x2 = grid_x;
    int new_grid_y2 = grid_y;
    if(axis==0){
        new_grid_x1 = grid_x*tmp_count/tot+0.5;
        new_grid_x2 = grid_x-new_grid_x1;
        if(grid_x>0) {
            if(new_grid_x1 == 0) {
                new_grid_x1 += 1;
                new_grid_x2 -= 1;
            }
            if(new_grid_x2 == 0) {
                new_grid_x2 += 1;
                new_grid_x1 -= 1;
            }
        }
    }else{
        new_grid_y1 = grid_y*tmp_count/tot+0.5;
        new_grid_y2 = grid_y-new_grid_y1;
        if(grid_y>0) {
            if(new_grid_y1 == 0) {
                new_grid_y1 += 1;
                new_grid_y2 -= 1;
            }
            if(new_grid_y2 == 0) {
                new_grid_y2 += 1;
                new_grid_y1 -= 1;
            }
        }
    }
    
    getAns(xy, sxy, rank_x, rank_y, weight, now_set1, n, new_grid_x1, new_grid_y1, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ans);
    getAns(xy, sxy, rank_x, rank_y, weight, now_set2, n, new_grid_x2, new_grid_y2, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ans);

    delete[] order;
    return;
}


std::vector<std::vector<int>> SearchForTree(std::vector<std::vector<double>> xy, std::vector<std::vector<double>> sxy,
std::vector<int> rank_x, std::vector<int> rank_y, int grid_x, int grid_y, std::vector<double> weight) {

//    double start = clock();

    int n = xy.size();

    double tot_weight = 0;
    for(int i=0;i<n;i++)tot_weight += weight[i];
    weight.push_back(tot_weight);

    std::unordered_map<long long, int> SetHash;
    std::vector<std::unordered_map<int, int>> StateHash;

    int m = 0;
    for(int i1=1;i1<=n;i1++)
    for(int i2=1;i2<=i1;i2++)
    for(int i3=1;i3<=i2;i3++)m += i3;
    
    SetHash.reserve(m*10);
    StateHash.reserve(m);

    int *CutAxis = new int[MAXSTATE];
    int *CutPlace = new int[MAXSTATE];
    double *CutCost = new double[MAXSTATE];

    //集合元素的x、y轴顺序，保存下来方便使用
    int *SetRankX = new int[m*n];
    int *SetRankY = new int[m*n];
    for(int i=0;i<m;i++) {
        SetRankX[i*n] = SetRankY[i*n] = -1;
    }

//    printf("%.4lf\n", (clock()-start)/CLOCKS_PER_SEC);

    int SetCount = 0;
    int StateCount = 0;

    double score = SearchForTreeDP(xy, sxy, rank_x, rank_y, weight, ((1ll)<<n)-1, n, grid_x, grid_y, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, grid_x, grid_y);

//    printf("score %.2lf\n", score);
//    printf("SetCount %d\n", SetCount);
//    printf("StateCount %d\n", StateCount);
//    printf("CalcCount %d\n", CalcCount);
//    printf("time %.2lf %.2lf %.2lf %2.lf %.2lf %.2lf\n", time0, time1, time2, time3, time4, time5);
//    printf("full time %.2lf\n", time_dp);
    
    std::vector<std::vector<int>> ans;
    getAns(xy, sxy, rank_x, rank_y, weight, ((1ll)<<n)-1, n, grid_x, grid_y, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ans);

    delete[] CutAxis;
    delete[] CutPlace;
    delete[] CutCost;

    delete[] SetRankX;
    delete[] SetRankY;

//    printf("%.4lf\n", (clock()-start)/CLOCKS_PER_SEC);

    return ans;
}


std::vector<std::vector<int>> SearchForTree2(std::vector<std::vector<double>> xy, std::vector<std::vector<double>> sxy,
std::vector<int> rank_x, std::vector<int> rank_y, int grid_x, int grid_y, std::vector<double> weight, double area_ratio) {

//    double start = clock();

    int n = xy.size();

    double tot_weight = 0;
    for(int i=0;i<n;i++)tot_weight += weight[i];
    weight.push_back(tot_weight);

    std::unordered_map<long long, int> SetHash;
    std::vector<std::unordered_map<int, int>> StateHash;

    int m = 0;
    for(int i1=1;i1<=n;i1++)
    for(int i2=1;i2<=i1;i2++)
    for(int i3=1;i3<=i2;i3++)m += i3;

    SetHash.reserve(m*10);
    StateHash.reserve(m);

    int *CutAxis = new int[MAXSTATE];
    int *CutPlace = new int[MAXSTATE];
    double *CutCost = new double[MAXSTATE];

    //集合元素的x、y轴顺序，保存下来方便使用
    int *SetRankX = new int[m*n];
    int *SetRankY = new int[m*n];
    for(int i=0;i<m;i++) {
        SetRankX[i*n] = SetRankY[i*n] = -1;
    }

//    printf("%.4lf\n", (clock()-start)/CLOCKS_PER_SEC);

    int SetCount = 0;
    int StateCount = 0;

    double score = SearchForTreeDP(xy, sxy, rank_x, rank_y, weight, ((1ll)<<n)-1, n, grid_x, grid_y, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, grid_x, grid_y, true, area_ratio);

//    printf("score %.2lf\n", score);
//    printf("SetCount %d\n", SetCount);
//    printf("StateCount %d\n", StateCount);
//    printf("CalcCount %d\n", CalcCount);
//    printf("time %.2lf %.2lf %.2lf %2.lf %.2lf %.2lf\n", time0, time1, time2, time3, time4, time5);
//    printf("full time %.2lf\n", time_dp);

    std::vector<std::vector<int>> ans;
    getAns(xy, sxy, rank_x, rank_y, weight, ((1ll)<<n)-1, n, grid_x, grid_y, SetHash, SetCount, StateHash, StateCount, CutAxis, CutPlace, CutCost, SetRankX, SetRankY, ans);

    delete[] CutAxis;
    delete[] CutPlace;
    delete[] CutCost;

    delete[] SetRankX;
    delete[] SetRankY;

//    printf("%.4lf\n", (clock()-start)/CLOCKS_PER_SEC);

    return ans;
}

#endif
