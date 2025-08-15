
function distance(p1, p2) {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
}

function angle(p1, p2) {
    return Math.atan2(p2.y - p1.y, p2.x - p1.x);
}

function mean(points) {
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    return {
        x: sumX / points.length,
        y: sumY / points.length
    };
}

function angleDifference(angle1, angle2) {
    let diff = angle1 - angle2;
    while (diff > Math.PI) diff -= 2 * Math.PI;
    while (diff < -Math.PI) diff += 2 * Math.PI;
    return Math.abs(diff);
}

function angleClockDifference(angle1, angle2) {
    let diff = angle2 - angle1;
    while (diff > 2*Math.PI) diff -= 2 * Math.PI;
    while (diff < 0) diff += 2 * Math.PI;
    return diff;
}

const minSplitDistance = 10;

function findMidpoint(source, targetMean, targets, alpha, max_length) {
    const direction = {
        x: targetMean.x - source.x,
        y: targetMean.y - source.y
    };
    const length = Math.max(0.0001, Math.sqrt(direction.x * direction.x + direction.y * direction.y));
    direction.x /= length;
    direction.y /= length;

    let left = 0;
    let right = max_length - minSplitDistance;
    let iterations = 20;
    // console.log("find mid", left, right);

    while (iterations-- > 0 && right - left > 0.01) {
        const mid = (left + right) / 2;
        const midpoint = {
            x: source.x + direction.x * mid,
            y: source.y + direction.y * mid
        };

        let maxAngle = 0;
        let tooClose = false;
        const angle3 = angle(midpoint, source);
        for (let i = 0; i < targets.length; i++) {
            const angle1 = angle(midpoint, targets[i]);
            for (let j = i + 1; j < targets.length; j++) {
                const angle2 = angle(midpoint, targets[j]);
                const angleDiff = angleDifference(angle1, angle2);
                maxAngle = Math.max(maxAngle, angleDiff);
            }
            const angleFrom = angleDifference(angle3, angle1);
            if (angleFrom < Math.PI * 0.5) {
                tooClose = true;
                break;
            }
            const dist = distance(midpoint, targets[i]);
            if (dist < minSplitDistance * 0.9) {
                tooClose = true;
                break;
            }
        }

        if (!tooClose && maxAngle <= alpha) {
            left = mid;
        } else {
            right = mid;
        }
    }
    // console.log("find mid result", left);

    return {
        x: source.x + direction.x * left,
        y: source.y + direction.y * left
    };
}


function mergeAll(source, targets, alpha, log = false) {
    let stroke_width = 1*0.95;

    function setBias(paths, direction=null, split_bias=0) {
        // console.log("direction", direction);
        if(direction==null) {
            // for(let path of paths) {
            //     path[0]["bias"] = [0, 0];
            // }
            return;
        }
        let line_direction = [-direction.y, direction.x];
        let tot_flow = 0;
        for(let path of paths) {
            tot_flow += path[path.length-1].flow;
        }
        let bias = [line_direction[0]*(-tot_flow*stroke_width/2), line_direction[1]*(-tot_flow*stroke_width/2)];
        bias[0] -= split_bias*bias[0];
        bias[1] -= split_bias*bias[1];

        for(let path of paths) {
            path[0]["edge_points"] = [[bias[0], bias[1]]];
            bias[0] += line_direction[0]*path[path.length-1].flow*stroke_width/2;
            bias[1] += line_direction[1]*path[path.length-1].flow*stroke_width/2;
            path[0]["bias"] = [bias[0], bias[1]];
            bias[0] += line_direction[0]*path[path.length-1].flow*stroke_width/2;
            bias[1] += line_direction[1]*path[path.length-1].flow*stroke_width/2;
            path[0]["edge_points"].push([bias[0], bias[1]]);
        }
    }

    function merge(source, targets, alpha, direction=null, split=false, split_bias=0) {
        if (log) {
            console.log("source", source)
            console.log("targets", targets)
        }
        if (targets.length === 0) {
            return []
        }
        if (targets.length === 1) {
            let new_source = {"x": source.x, "y": source.y, "bias": [0, 0]};
            let new_target = {"x": targets[0].x, "y": targets[0].y, "bias": [0, 0], "flow": targets[0].flow};
            return [[new_source, new_target]];
        }
        targets = targets.slice(0).sort((a, b) => angle(source, a) - angle(source, b));

        let tmp_splitIndex = 0;
        let tmp_maxDelta = angleClockDifference(angle(source, targets[targets.length - 1]), angle(source, targets[0]));
        for (let i = 0; i < targets.length - 1; i++) {
            const angle1 = angle(source, targets[i]);
            const angle2 = angle(source, targets[i + 1]);
            const delta = angleClockDifference(angle1, angle2);
            if (delta > tmp_maxDelta) {
                tmp_maxDelta = delta;
                tmp_splitIndex = i + 1;
            }
        }
        if(tmp_splitIndex>0) {
            targets = targets.slice(tmp_splitIndex).concat(targets.slice(0, tmp_splitIndex));
        }
        const totalAngle = angleClockDifference(angle(source, targets[0]), angle(source, targets[targets.length - 1]))

        let hasNearbyTarget = false;

        for (let i = 0; i < targets.length; i++) {
            if (distance(source, targets[i]) <= minSplitDistance) {
                hasNearbyTarget = true;
                break;
            }
        }
        if (log) {
            console.log("hasNearbyTarget", hasNearbyTarget)
            console.log("totalAngle", totalAngle, alpha, split)
        }

        if (hasNearbyTarget) {
            const filteredTargets = [];
            for (let i = 0; i < targets.length; i++) {
                if (distance(source, targets[i]) > minSplitDistance) {
                    filteredTargets.push(targets[i])
                }
            }
            const paths = merge(source, filteredTargets, alpha, direction, false)
            const ret = []
            for (let i = 0, j = 0; i < targets.length; i++) {
                if (distance(source, targets[i]) > minSplitDistance) {
                    ret.push(paths[j++])
                } else {
                    let new_source = {"x": source.x, "y": source.y, "bias": [0, 0]};
                    let new_target = {"x": targets[i].x, "y": targets[i].y, "bias": [0, 0], "flow": targets[i].flow};
                    ret.push([new_source, new_target])
                }
            }
            setBias(ret, direction, split_bias);
            return ret;
        }

        if (totalAngle >= alpha || split) {
            let maxDelta = 0;
            let splitIndex = 1;
            for (let i = 0; i < targets.length - 1; i++) {
                const angle1 = angle(source, targets[i]);
                const angle2 = angle(source, targets[i + 1]);
                const delta = angleDifference(angle1, angle2);
                if (delta > maxDelta) {
                    maxDelta = delta;
                    splitIndex = i + 1;
                }
            }

            const targets1 = targets.slice(0, splitIndex);
            const targets2 = targets.slice(splitIndex);
            let ret = merge(source, targets1, alpha, direction, false, -1).concat(merge(source, targets2, alpha, direction, false, 1));
            setBias(ret, direction, split_bias);
            return ret;
        }

        const targetMean = mean(targets);
        let min_dist = 1000000;
        for (let i = 0; i < targets.length; i++) {
            min_dist = Math.min(min_dist, distance(source, targets[i]));
        }
        // const midpoint = findMidpoint(source, targetMean, targets, alpha, min_dist*0.8);
        const midpoint = findMidpoint(source, targetMean, targets, alpha, min_dist);
        if (isNaN(midpoint.x) || isNaN(midpoint.y)) {
            return []
        }
        // midpoint.id = `${source.id.split('-')[0]}-${Math.round(midpoint.x)}-${Math.round(midpoint.y)}`;

        const new_direction = {
            x: midpoint.x - source.x,
            y: midpoint.y - source.y
        };
        const length = Math.max(0.0001, Math.sqrt(new_direction.x * new_direction.x + new_direction.y * new_direction.y));
        new_direction.x /= length;
        new_direction.y /= length;

        const paths = merge(midpoint, targets, alpha, new_direction, true);

        let ret = paths.map(function(path) {
            let new_source = {"x": source.x, "y": source.y, "bias": [0, 0]};
            return [new_source].concat(path);
        });

        // if(direction == null)direction = new_direction;

        setBias(ret, direction, split_bias);
        return ret;
    }
    let paths = merge(source, targets, alpha);
    return targets.map(target => paths.find(path => distance(path[path.length - 1], target) < 0.0001));
}

export { findMidpoint, mergeAll, angle, angleClockDifference, angleDifference }