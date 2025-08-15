/* eslint-disable */
import * as d3 from "d3";
import { findMidpoint, mergeAll, angle, angleClockDifference, angleDifference } from "./flowMap_new";

const MapRender = function(parent) {
    let that = this;
    that.parent = parent;
    that.init = true;
    that.line_width = 1;

    that.update_info_from_parent = function() {
        that.map_group = that.parent.map_group;
    };

    that.update_info_from_parent();
    
    that.link_g = that.map_group.append("g")
        .attr("class", "link_g");
    
    let defs = that.map_group.append("defs");

    defs.append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 0 10 10")
        // .attr("refX", 5)
        .attr("refX", 9)
        .attr("refY", 5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 3)
        .attr("orient", "auto")
        .append("path")
        // .attr("d", "M 0 0 L 10 5 L 0 10 M 9 5 L 0 5") // 绘制直线
        .attr("d", "M 0 0 L 10 5 L 0 10") // 绘制直线
        .attr("fill", "none")
        .attr("stroke", "orange")
        .attr("stroke-width", 3);
    
    defs.append("marker")
        .attr("id", "arrowhead-back")
        .attr("viewBox", "0 0 10 10")
        // .attr("refX", 5)
        .attr("refX", 9)
        .attr("refY", 5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 3)
        .attr("orient", "auto")
        .append("path")
        // .attr("d", "M 0 0 L 10 5 L 0 10 M 9 5 L 0 5") // 绘制直线
        .attr("d", "M 0 0 L 10 5 L 0 10") // 绘制直线
        .attr("fill", "none")
        .attr("stroke", "white")
        .attr("stroke-width", 3);

    that.calcPos = function(pairs) {
        let nodes = [];
        for(let i=0;i<pairs.length;i++) {
            nodes.push({"x": pairs[i].box[0], "y": pairs[i].box[1], "width": pairs[i].box[2], "height": pairs[i].box[3]})
        }
        // console.log("node before", nodes);
        const simulation = d3.forceSimulation(nodes)
            .force("collide", d3.forceCollide().radius(d => Math.max(d.width, d.height) / 2).strength(1))
            .force("x", d3.forceX(d => d.x).strength(0.1))
            .force("y", d3.forceY(d => d.y).strength(0.1))
            .force("boundary", () => {
                nodes.forEach(node => {
                    node.x = Math.max(0, Math.min(that.parent.gridlayout_size[0] - node.width, node.x));
                    node.y = Math.max(0, Math.min(that.parent.gridlayout_size[1] - node.height, node.y));
                });
            })
            .stop(); 

        const alphaMin = simulation.alphaMin(); 
        // console.log("node alpha", simulation.alpha(), alphaMin);
        while (simulation.alpha() > alphaMin) {
            simulation.tick();
        }
        simulation.stop();
        // console.log("node after", nodes);
        for(let i=0;i<pairs.length;i++) {
            nodes[i].x = Math.max(0, Math.min(that.parent.gridlayout_size[0] - nodes[i].width, nodes[i].x));
            nodes[i].y = Math.max(0, Math.min(that.parent.gridlayout_size[1] - nodes[i].height, nodes[i].y));
            pairs[i].box[0] = nodes[i].x;
            pairs[i].box[1] = nodes[i].y;
            pairs[i].box[2] = nodes[i].width;
            pairs[i].box[3] = nodes[i].height;
        }
        return nodes;
    }
    
    that.render = function(map_info, change=false) {
        // console.log("map_info", map_info);

        if(map_info == null) {
            map_info = {
                "source": { "x": 0, "y": 0, "width": 0, "height": 0},
                "pairs": []
            }
        }

        // console.log("map_info", map_info);
        that.update_info_from_parent();

        let source = {"x": map_info.source.x+map_info.source.width/2, "y": map_info.source.y+map_info.source.height/2};
        let targets = [];
        for(let pair of map_info.pairs) {
            targets.push({"x": pair.target.x+pair.target.width/2, "y": pair.target.y+pair.target.height/2, "flow": 2});
        }
        let paths = mergeAll(source, targets, Math.PI/3);
        for(let i=0;i<map_info.pairs.length;i++){
            map_info.pairs[i].path = paths[i];
        }

        let points_list = [[source.x, source.y]];
        for(let i=0;i<map_info.pairs.length;i++) {
            if(paths[i][0].edge_points != null) {
                for(let j=0;j<paths[i][0].edge_points.length;j++) {
                    let tmp_point = paths[i][0].edge_points[j];
                    points_list.push([source.x+tmp_point[0], source.y+tmp_point[1]]);
                }
            }
        }
        const hull = d3.polygonHull(points_list);
        that.link_g.selectAll(".hull").remove();
        if(hull != null) {
            that.link_g.append("path")
                .attr("class", "hull")
                .attr("opacity", 0)
                .attr("d", `M${hull.join("L")}Z`)
                .attr("fill", "orange")
                // .transition()
                // .duration(that.create_ani)
                // .delay(that.remove_ani+that.update_ani)
                .attr("opacity", 1);
        }

        function pointsToPath2(points, r=30) {
            const [firstPoint, ...otherPoints] = points;
            // console.log("points", firstPoint, otherPoints, points);
            let path = `M ${firstPoint.x+firstPoint.bias[0]} ${firstPoint.y+firstPoint.bias[1]} `
            let last_point = [firstPoint.x+firstPoint.bias[0], firstPoint.y+firstPoint.bias[1]];
            for(let i=0;i<otherPoints.length;i++) {
                let now_point = [otherPoints[i].x+otherPoints[i].bias[0], otherPoints[i].y+otherPoints[i].bias[1]];
                // if(false) {
                if(i<otherPoints.length-1) {
                    let next_point = [otherPoints[i+1].x+otherPoints[i+1].bias[0], otherPoints[i+1].y+otherPoints[i+1].bias[1]];
                    function get_angle(p1, p2) {
                        return Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
                    }
                    const angle1 = get_angle(last_point, now_point);
                    const angle2 = get_angle(now_point, next_point);
                    const delta = angleClockDifference(angle1, angle2);
                    const delta2 = angleDifference(angle1, angle2);
                    let clc = 0;
                    if(delta<Math.PI) clc = 1;
                    let direction1 = [now_point[0]-last_point[0], now_point[1]-last_point[1]];
                    let direction2 = [next_point[0]-now_point[0], next_point[1]-now_point[1]];
                    let length1 = Math.max(0.0001, Math.sqrt(direction1[0]*direction1[0] + direction1[1]*direction1[1]));
                    direction1[0] /= length1;
                    direction1[1] /= length1;
                    let length2 = Math.max(0.0001, Math.sqrt(direction2[0]*direction2[0] + direction2[1]*direction2[1]));
                    direction2[0] /= length2;
                    direction2[1] /= length2;
                    // console.log("direction", direction1, direction2, length1, length2);
                    let tmp_r = Math.min(Math.min(r, length1/2), length2/2);
                    // let tmp_radius = tmp_r / Math.max(0.0001, Math.cos((Math.PI-delta2)/2));
                    let tmp_radius = tmp_r * Math.sin((Math.PI-delta2)/2) / Math.max(0.0001, Math.cos((Math.PI-delta2)/2));
                    // console.log("radius", angle1, angle2, delta2, tmp_r, Math.cos((Math.PI-delta2)/2), tmp_radius);
                    let mid_point1 = [now_point[0]-tmp_r*direction1[0], now_point[1]-tmp_r*direction1[1]];
                    let mid_point2 = [now_point[0]+tmp_r*direction2[0], now_point[1]+tmp_r*direction2[1]];
                    path += `L ${mid_point1[0]} ${mid_point1[1]} `
                    path += `A ${tmp_radius} ${tmp_radius} 0 0 ${clc} ${mid_point2[0]} ${mid_point2[1]} `;
                }else {
                    path += `L ${now_point[0]} ${now_point[1]} `
                }
                last_point = now_point;
            }
            return path.trim();
        }

        let link_groups = that.link_g.selectAll(".link-group")
            .data(map_info.pairs, d => { return String(d.source.id)+"&"+String(d.target.id)+"-"+String(Math.random()); });
        let new_link_groups = link_groups.enter()
            .append("g")
            .attr("class", "link-group")
            .attr("opacity", 0);

        new_link_groups
            // .transition()
            // .duration(that.create_ani)
            // .delay(that.remove_ani+that.update_ani)
            .attr("opacity", 1);

        new_link_groups
            .append("path")
            .attr("class", "link-back")
            .attr("fill", "none")
            .attr("stroke-width", d => d.path[d.path.length-1].flow*that.line_width)
            .attr("stroke", "white")
            // .attr("d", d => `M ${d.source.x+d.source.width/2} ${d.source.y+d.source.width/2} L ${d.target.x+d.source.width/2} ${d.target.y+d.source.width/2}`)
            .attr("d", d => pointsToPath2(d.path))
            .attr("marker-end", "url(#arrowhead)")
            .attr("stroke-linejoin", "round")
            .attr("opacity", 0)
            .attr("filter", "url(#strokeFilter)");

        new_link_groups
            .append("path")
            .attr("class", "link")
            .attr("fill", "none")
            .attr("stroke-width", d => d.path[d.path.length-1].flow*that.line_width)
            .attr("stroke", "orange")
            // .attr("d", d => `M ${d.source.x+d.source.width/2} ${d.source.y+d.source.width/2} L ${d.target.x+d.source.width/2} ${d.target.y+d.source.width/2}`)
            .attr("d", d => pointsToPath2(d.path))
            .attr("marker-end", "url(#arrowhead)")
            .attr("stroke-linejoin", "round");

        const linkHover = function(e, d) {
            const els = that.link_g.selectAll("g.link-group");
            const isEntering = e.type === 'mouseenter';
            // console.log("link hover", els, isEntering);
            els.each(function(d2) {
                let el = d3.select(this);
                if(isEntering&&(d2.target.id == d.target.id))
                    el.raise();
                el.select(".link-back")
                    .attr("opacity", (isEntering&&(d2.target.id == d.target.id)) ? 1 : 0)
            });
        };

        new_link_groups
            .on('mouseenter mouseleave', linkHover);

        link_groups.exit()
            // .transition()
            // .duration(that.remove_ani)
            .attr("opacity", 0)
            .remove();
        
        // console.log("link_groups", link_groups);
        link_groups.select(".link")
            // .transition()
            // .duration(that.update_ani)
            // .delay(that.remove_ani)
            .attr("d", function(d) {
                // console.log("d");
                // return `M ${d.source.x+d.source.width/2} ${d.source.y+d.source.width/2} L ${d.target.x+d.source.width/2} ${d.target.y+d.source.width/2}`;
                return pointsToPath2(d.path);
            })
            .attr("marker-end", "url(#arrowhead)");
    };
};

export default MapRender;
