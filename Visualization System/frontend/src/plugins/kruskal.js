function calculateDistance(p1, p2) {
    return Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2);
}
class UnionFind {
    constructor(n) {
        this.parent = Array.from({ length: n }, (_, i) => i);
        this.rank = Array(n).fill(0);
    }

    find(x) {
        if (this.parent[x] !== x) {
            this.parent[x] = this.find(this.parent[x]);
        }
        return this.parent[x];
    }

    union(x, y) {
        const rootX = this.find(x);
        const rootY = this.find(y);
        if (rootX !== rootY) {
            if (this.rank[rootX] > this.rank[rootY]) {
                this.parent[rootY] = rootX;
            } else if (this.rank[rootX] < this.rank[rootY]) {
                this.parent[rootX] = rootY;
            } else {
                this.parent[rootY] = rootX;
                this.rank[rootX]++;
            }
        }
    }
}

function kruskal(points) {
    const n = points.length;
    const edges = [];
    const uf = new UnionFind(n);

    // 计算所有边的权重并排序
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const weight = calculateDistance(points[i], points[j]);
            edges.push({ u: i, v: j, weight });
        }
    }

    edges.sort((a, b) => a.weight - b.weight);

    const mstEdges = [];
    for (const edge of edges) {
        if (uf.find(edge.u) !== uf.find(edge.v)) {
            uf.union(edge.u, edge.v);
            mstEdges.push(edge);
        }
    }

    return mstEdges;
}

function kruskal2(points) {
    const n = points.length;
    const edges = [];
    const uf = new UnionFind(n);

    // 计算所有边的权重并排序
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const weight = calculateDistance(points[i], points[j]);
            edges.push({ u: i, v: j, weight });
        }
    }

    edges.sort((a, b) => a.weight - b.weight);

    const mstEdges = [];
    let stop_list = [0];
    for (const edge of edges) {
        if (edge.u === 0) {
            if(!stop_list.includes(uf.find(edge.v))) {
                stop_list.push(uf.find(edge.v));
            }
        }
        if (edge.v === 0) {
            if(!stop_list.includes(uf.find(edge.u))) {
                stop_list.push(uf.find(edge.u));
            }
        }

        let flag = 0;
        if (stop_list.includes(uf.find(edge.u)) && !stop_list.includes(uf.find(edge.v))) {
            stop_list.push(uf.find(edge.v));
            continue;
            flag = 1;
        } else if (stop_list.includes(uf.find(edge.v)) && !stop_list.includes(uf.find(edge.u))) {
            stop_list.push(uf.find(edge.u));
            continue;
            flag = 1;
        } else if (stop_list.includes(uf.find(edge.u)) && stop_list.includes(uf.find(edge.v))) {
            continue;
        }
        if (uf.find(edge.u) !== uf.find(edge.v)) {
            uf.union(edge.u, edge.v);
            mstEdges.push(edge);
            if (flag === 1) {
                if(!stop_list.includes(uf.find(edge.u))) {
                    stop_list.push(uf.find(edge.u));
                }
            }
        }
    }

    return mstEdges;
}

function dividePoints(points) {
    const mstEdges = kruskal(points);

    // 找到权重最大的边并移除
    let maxEdge = mstEdges.reduce((max, edge) => (edge.weight > max.weight ? edge : max), mstEdges[0]);

    // 使用并查集重新划分集合
    const uf = new UnionFind(points.length);
    for (const edge of mstEdges) {
        if (edge !== maxEdge) {
            uf.union(edge.u, edge.v);
        }
    }

    const set1 = [];
    const set2 = [];
    const root1 = uf.find(maxEdge.u);
    const root2 = uf.find(maxEdge.v);

    for (let i = 0; i < points.length; i++) {
        if (uf.find(i) === root1) {
            set1.push(points[i]);
        } else {
            set2.push(points[i]);
        }
    }

    // console.log("set", set1, set2);
    return { set1, set2 };
}

function dividePoints2(points) {
    const mstEdges = kruskal2(points);

    // 找到权重最大的边并移除
    let maxEdge = mstEdges.reduce((max, edge) => (((edge.u !== 0)&&(edge.v !== 0)&&(edge.weight>max.weight)) ? edge : max), mstEdges[0]);

    // 使用并查集重新划分集合
    let uf = new UnionFind(points.length);
    for (const edge of mstEdges) {
        if ((edge.u !== 0)&&(edge.v !== 0)) {
            uf.union(edge.u, edge.v);
        }
    }

    let result = {};
    let cnt = 0;
    for (let i = 1; i < points.length; i++) {
        const root = uf.find(i);
        if(!(root in result)) {
            result[root] = [];
            cnt += 1;
        }
        result[root].push(points[i]);
    }
    if(cnt <= 1) {
        uf = new UnionFind(points.length);
        for (const edge of mstEdges) {
            if ((edge.u !== 0)&&(edge.v !== 0)&&(edge !== maxEdge)) {
                uf.union(edge.u, edge.v);
            }
        }
        result = {};
        for (let i = 1; i < points.length; i++) {
            const root = uf.find(i);
            if(!(root in result)) {
                result[root] = [];
                cnt += 1;
            }
            result[root].push(points[i]);
        }
    }

    return result;
}
export { dividePoints, dividePoints2 }