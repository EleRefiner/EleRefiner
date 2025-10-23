/* eslint-disable */
import * as d3 from "d3";
import { findMidpoint, mergeAll, angle, angleClockDifference, angleDifference } from "./flowMap_new";

const MapRender = function(parent) {
    let that = this;
    that.parent = parent;
    that.init = true;
    that.line_width = 1;

    that.update_info_from_parent = function() {
        that.svg = that.parent.svg;
        that.grid_group = that.parent.grid_group;
        that.grid_group2 = that.parent.grid_group2;
        that.boundary_group = that.parent.boundary_group;
        that.highlight_group = that.parent.highlight_group;
        that.map_group = that.parent.map_group;
        that.render_image = that.parent.use_image;

        that.create_ani = that.parent.create_ani/3;
        that.update_ani = that.parent.update_ani/3;
        that.remove_ani = that.parent.remove_ani/3;
        that.fast_ani = 400;
        that.colorinter = d3.interpolateHcl;
        that.svg_width = that.parent.svg_width;
        that.svg_height = that.parent.svg_height;
        that.gridstack = that.parent.gridstack;
        that.detection_items = that.parent.items;
    };

    that.update_info_from_parent();
    
    that.link_g = that.map_group.append("g")
        .attr("class", "link_g");
    that.box_g = that.map_group.append("g")
        .attr("class", "box_g");
    
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
        if(map_info == null) {
            map_info = {
                "source": { "x": 0, "y": 0, "width": 0, "height": 0},
                "pairs": []
            }
        }
        // map_info["pairs"] = map_info["pairs"].slice(0, 6)

        console.log("map_info", map_info);
        that.update_info_from_parent();

        let source = {"x": map_info.source.x+map_info.source.width/2, "y": map_info.source.y+map_info.source.width/2};
        let targets = [];
        
        let scale = 10;
        let tmp_max = 0;
        let tmp_mean = 0;
        for(let pair of map_info.pairs) {
            tmp_max = max(tmp_max, pair.flow);
            tmp_mean += pair.flow;
        }
        tmp_mean /= map_info.pairs.length;
        scale = tmp_mean/2;

        for(let pair of map_info.pairs) {
            // targets.push({"x": pair.target.x+map_info.source.width/2, "y": pair.target.y+map_info.source.width/2, "flow": 1+Math.random()*3.5});
            // targets.push({"x": pair.target.x+map_info.source.width/2, "y": pair.target.y+map_info.source.width/2, "flow": Math.min(5, pair.scores.length/3)});
            targets.push({"x": pair.target.x+map_info.source.width/2, "y": pair.target.y+map_info.source.width/2, "flow": 1*Math.max(1, Math.min(5, pair.flow/scale))});
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
                .transition()
                .duration(that.create_ani)
                .delay(that.remove_ani+that.update_ani)
                .attr("opacity", 1);
        }

        function pointsToPath(points) {
            // const [firstPoint, ...otherPoints] = points;
            // const path = `M ${firstPoint.x+firstPoint.bias[0]} ${firstPoint.y+firstPoint.bias[1]} ` + 
            //              otherPoints.map((d) => `L ${d.x+d.bias[0]} ${d.y+d.bias[1]}`).join(" ");
            
            const lineGenerator = d3.line()
                .x(d => d[0])
                .y(d => d[1])
                .curve(d3.curveCardinal.tension(0.8));
                // .curve(d3.curveCatmullRom.alpha(0.5));
            const [firstPoint, ...otherPoints] = points;
            let new_points = [[firstPoint.x+firstPoint.bias[0], firstPoint.y+firstPoint.bias[1]]];
            for(let point of otherPoints){
                // new_points.push([(new_points[new_points.length-1][0]+point.x+point.bias[0])/2, (new_points[new_points.length-1][1]+point.y+point.bias[1])/2])
                new_points.push([point.x+point.bias[0], point.y+point.bias[1]])
            }
            // console.log("path", new_points);
            const path = lineGenerator(new_points);

            return path.trim();
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
            // .data(map_info.pairs, d => { return String(d.source.sample_id)+"&"+String(d.target.sample_id); });
            .data(map_info.pairs, d => { return String(d.source.sample_id)+"&"+String(d.target.sample_id)+"-"+String(Math.random()); });
        let new_link_groups = link_groups.enter()
            .append("g")
            .attr("class", "link-group")
            .attr("opacity", 0);

        new_link_groups.transition()
            .duration(that.create_ani)
            .delay(that.remove_ani+that.update_ani)
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
                if(isEntering&&(d2.target.sample_id == d.target.sample_id))
                    el.raise();
                el.select(".link-back")
                    .attr("opacity", (isEntering&&(d2.target.sample_id == d.target.sample_id)) ? 1 : 0)
            });
            const boxes = that.box_g.selectAll("g.box-plot");
            boxes.each(function(d2) {
                let el = d3.select(this);
                if(isEntering&&(d2.target.sample_id == d.target.sample_id))
                    el.raise();
                el.select("rect.back")
                    .attr("opacity", (isEntering&&(d2.target.sample_id == d.target.sample_id)) ? 1 : 0)
            });
        };

        new_link_groups
            .on('mouseenter mouseleave', linkHover);

        link_groups.exit()
            .transition()
            .duration(that.remove_ani)
            .attr("opacity", 0)
            .remove();
        
        // link_groups.select(".link")
        //     .transition()
        //     .duration(that.update_ani)
        //     .delay(that.remove_ani)
        //     .attr("d", function(d) {
        //         // console.log("d");
        //         // return `M ${d.source.x+d.source.width/2} ${d.source.y+d.source.width/2} L ${d.target.x+d.source.width/2} ${d.target.y+d.source.width/2}`;
        //         return pointsToPath2(d.path);
        //     })
        //     .attr("marker-end", "url(#arrowhead)");


        let box_plots = that.box_g.selectAll(".box-plot")
            .data(map_info.pairs, d => { return String(d.source.sample_id)+"&"+String(d.target.sample_id)+"-"+String(Math.random()); });

        let box_width = 30*1;
        let box_height = 30*1;

        box_plots.exit()
            .transition()
            .duration(that.remove_ani)
            .attr("opacity", 0)
            .remove();

        map_info.pairs.forEach((d) => {
            let tmp_x = d.target.x+d.source.width/2-box_width/2;
            let tmp_y = d.target.y+d.source.height/2-box_height/2;
            let di_list = [[0, 0, 1], [-1, -1, Math.sqrt(2)], [-1, 0, 1], [0, -1, 1], [1, -1, Math.sqrt(2)], [1, 0, 1], [1, 1, Math.sqrt(2)], [-1, 1, Math.sqrt(2)], [0, 1, 1]];
            for(let i=0;i<di_list.length-1;i++)
            for(let j=i+1;j<di_list.length;j++) {
                let di1 = di_list[i];
                let di2 = di_list[j];
                if((di1[0]*(d.target.x-d.source.x)+di1[1]*(d.target.y-d.source.y))/di1[2]<(di2[0]*(d.target.x-d.source.x)+di2[1]*(d.target.y-d.source.y))/di2[2]) {
                    let tmp = di_list[i];
                    di_list[i] = di_list[j];
                    di_list[j] = tmp;
                }
            }
            d.box = [tmp_x, tmp_y, box_width+4, box_height+4];
            for(let di of di_list){
                let new_tmp_x = tmp_x+di[0]*box_width*2/3;
                let new_tmp_y = tmp_y+di[1]*box_height*2/3;
                if((new_tmp_x>0)&&(new_tmp_x+box_width<that.parent.gridlayout_size[0])
                    &&(new_tmp_y>0)&&(new_tmp_y+box_height<that.parent.gridlayout_size[1])) {
                    d.box = [new_tmp_x, new_tmp_y, box_width+4, box_height+4];
                    break;
                }
            }
        });

        let nodes = that.calcPos(map_info.pairs);
        if(!change)
            that.parent.grid_render.click_render_images(nodes);

        let new_boxes = box_plots.enter()
            .append("g")
            .attr("class", "box-plot")
            .attr("opacity", 0)
            .attr("transform", d => {
                return `translate(${d.box[0]}, ${d.box[1]})`;
            });

        new_boxes
            .transition()
            .duration(that.create_ani)
            .delay(that.remove_ani+that.update_ani)
            .attr("opacity", 1);

        new_boxes
            .on('mouseenter mouseleave', linkHover);

        new_boxes.each(function(d) {
            let now = d3.select(this);

            now.append("rect")
                .attr("class", "back")
                .attr("x", -2)
                .attr("y", -2)
                .attr("width", box_width+4)
                .attr("height", box_height+4)
                .attr("fill", "white")
                .attr("opacity", 0);
                // .attr("fill", `rgb(255, ${(165+255*5)/6}, ${255*5/6})`)
                // .attr("fill", `rgb(255, ${(165*(min_score*4+2)+255*(4-min_score*4))/6}, ${255*(4-min_score*4)/6})`)
                // .attr("opacity", 1);
                // .attr("stroke", "black")
                // .attr("stroke-width", 1);

            now.append("rect")
                .attr("class", "back2")
                .attr("x", -0.5)
                .attr("y", -0.5)
                .attr("width", box_width+1)
                .attr("height", box_height+1)
                .attr("stroke", "black")
                .attr("stroke-width", 1)
                .attr("fill", "white");

            now.append("image")
                .attr("x", 0)
                .attr("y", 0)
                .attr("width", box_width)
                .attr("height", box_height)
                .attr("xlink:href", d => d.image);
        });




        // let box_plots = that.box_g.selectAll(".box-plot")
        //     // .data(map_info.pairs, d => { return String(d.source.sample_id)+"&"+String(d.target.sample_id); });
        //     .data(map_info.pairs, d => { return String(d.source.sample_id)+"&"+String(d.target.sample_id)+"-"+String(Math.random()); });

        // let box_width = 15;
        // let box_height = 30;
        
        // box_plots.exit()
        //     .transition()
        //     .duration(that.remove_ani)
        //     .attr("opacity", 0)
        //     .remove();
        
        // map_info.pairs.forEach((d) => {
        //     let tmp_x = d.target.x+d.source.width/2-box_width/2;
        //     let tmp_y = d.target.y+d.source.height/2-box_height/2;
        //     let di_list = [[0, 0, 1], [-1, -1, Math.sqrt(2)], [-1, 0, 1], [0, -1, 1], [1, -1, Math.sqrt(2)], [1, 0, 1], [1, 1, Math.sqrt(2)], [-1, 1, Math.sqrt(2)], [0, 1, 1]];
        //     for(let i=0;i<di_list.length-1;i++)
        //     for(let j=i+1;j<di_list.length;j++) {
        //         let di1 = di_list[i];
        //         let di2 = di_list[j];
        //         if((di1[0]*(d.target.x-d.source.x)+di1[1]*(d.target.y-d.source.y))/di1[2]<(di2[0]*(d.target.x-d.source.x)+di2[1]*(d.target.y-d.source.y))/di2[2]) {
        //             let tmp = di_list[i];
        //             di_list[i] = di_list[j];
        //             di_list[j] = tmp;
        //         }
        //     }
        //     d.box = [tmp_x, tmp_y, box_width+4, box_height+4];
        //     for(let di of di_list){
        //         let new_tmp_x = tmp_x+di[0]*box_width*2/3;
        //         let new_tmp_y = tmp_y+di[1]*box_height*2/3;
        //         if((new_tmp_x>0)&&(new_tmp_x+box_width<that.parent.gridlayout_size[0])
        //             &&(new_tmp_y>0)&&(new_tmp_y+box_height<that.parent.gridlayout_size[1])) {
        //             d.box = [new_tmp_x, new_tmp_y, box_width+4, box_height+4];
        //             break;
        //         }
        //     }
        // });

        // let nodes = that.calcPos(map_info.pairs);
        // if(!change)
        //     that.parent.grid_render.click_render_images(nodes);

        // let new_boxes = box_plots.enter()
        //     .append("g")
        //     .attr("class", "box-plot")
        //     .attr("opacity", 0)
        //     .attr("transform", d => {
        //         return `translate(${d.box[0]}, ${d.box[1]})`;
        //     });
        //     // .attr("x", d => `${d.target.x+d.source.width/2-box_width}`)
        //     // .attr("y", d => `${d.target.y+d.source.width/2-box_height}`)
        
        // new_boxes
        //     .transition()
        //     .duration(that.create_ani)
        //     .delay(that.remove_ani+that.update_ani)
        //     .attr("opacity", 1);

        // new_boxes
        //     .on('mouseenter mouseleave', linkHover);

        // new_boxes.each(function(d) {
        //     let now = d3.select(this);

        //     let min_score = Math.min(...d.scores);
        //     now.append("rect")
        //         .attr("class", "back2")
        //         .attr("x", -0.5)
        //         .attr("y", -0.5)
        //         .attr("width", box_width+1)
        //         .attr("height", box_height+1)
        //         .attr("fill", "transparent")
        //         // .attr("fill", `rgb(255, ${(165+255*5)/6}, ${255*5/6})`)
        //         // .attr("fill", `rgb(255, ${(165*(min_score*4+2)+255*(4-min_score*4))/6}, ${255*(4-min_score*4)/6})`)
        //         .attr("opacity", 1);
        //         // .attr("stroke", "black")
        //         // .attr("stroke-width", 1);

        //     let mean_height = 0.01;
        //     now.append("rect")
        //         .attr("class", "mean-bar")
        //         .attr("x", 0-0.25)
        //         .attr("y", box_height*(1-mean_height))
        //         .attr("width", box_width+0.5)
        //         .attr("height", box_height*mean_height+0.25)
        //         .attr("fill", `rgb(255, ${(165*(min_score*4+2)+255*(4-min_score*4))/6}, ${255*(4-min_score*4)/6})`)
        //         .attr("opacity", 1)
        //         .attr("stroke", "black")
        //         .attr("stroke-width", 0.5);
            
        //     let highlight_stroke = 1;
        //     now.append("rect")
        //         .attr("class", "back")
        //         .attr("x", -highlight_stroke/2)
        //         .attr("y", -highlight_stroke/2)
        //         .attr("width", box_width+highlight_stroke)
        //         .attr("height", box_height+highlight_stroke)
        //         .attr("fill", "none")
        //         .attr("opacity", 0)
        //         .attr("stroke", "black")
        //         .attr("stroke-width", highlight_stroke);
            
        //     for(let i=0;i<5;i++) {
        //         now.append("rect")
        //             .attr("class", `${i}-bar`)
        //             .attr("x", box_width*0.2*i)
        //             .attr("y", ((1-mean_height)*(1-d.bin[i]))*box_height)
        //             .attr("width", box_width*0.2)
        //             .attr("height", (1-mean_height)*d.bin[i]*box_height)
        //             .attr("fill", `rgb(255, ${(165*(i+2)+255*(4-i))/6}, ${255*(4-i)/6})`)
        //             .attr("stroke", "black")
        //             .attr("stroke-width", 0.5);
        //     }
        // });



        // function calculateBoxPlotProperties(data) {
        //     const sortedData = data.slice().sort((a, b) => a - b);
        //     const length = sortedData.length;
        //     const median = calculatePercentile(sortedData, 0.5);
        //     const q1 = calculatePercentile(sortedData, 0.25);
        //     const q3 = calculatePercentile(sortedData, 0.75);
        //     const min = sortedData[0];
        //     const max = sortedData[length - 1];
        //     return {
        //         "min": min,
        //         "q1": q1,
        //         "median": median,
        //         "q3": q3,
        //         "max": max,
        //         "outliers": []
        //     };
        // }
        // function calculatePercentile(sortedData, percentile) {
        //     const length = sortedData.length;
        //     const index = percentile * (length - 1);
        //     const lowerIndex = Math.floor(index);
        //     const upperIndex = Math.ceil(index);
        
        //     if (lowerIndex === upperIndex) {
        //         return sortedData[lowerIndex];
        //     }
        
        //     const lowerValue = sortedData[lowerIndex];
        //     const upperValue = sortedData[upperIndex];
        //     const weight = index - lowerIndex;
        //     return lowerValue + (upperValue - lowerValue) * weight;
        // }
        // for(let d of map_info.pairs) {
        //     d.confidence = calculateBoxPlotProperties(d.scores);
        // }

        // console.log("new boxes", new_boxes);

        // new_boxes.each(function(d) {
        //     let now = d3.select(this);
        //     now.append("rect")
        //         .attr("class", "back")
        //         .attr("x", -2)
        //         .attr("y", -2)
        //         .attr("width", box_width+4)
        //         .attr("height", box_height+4)
        //         .attr("fill", `rgb(255, ${(165+255*5)/6}, ${255*5/6})`)
        //         .attr("opacity", 0);
        //         // .attr("stroke", "black")
        //         // .attr("stroke-width", 1);
            
        //     let dark_scale = 0.85;
        //     now.append("line")
        //         .attr("class", "border")
        //         .attr("x1", -2)
        //         .attr("x2", box_width+2)
        //         .attr("y1", -2)
        //         .attr("y2", -2)
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 2);

        //     now.append("line")
        //         .attr("class", "border")
        //         .attr("x1", -2)
        //         .attr("x2", box_width+2)
        //         .attr("y1", box_height+2)
        //         .attr("y2", box_height+2)
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 2);   

        //     now.append("rect")
        //         .attr("class", "box")
        //         .attr("y", box_height*(1-d.confidence.q3))
        //         .attr("width", box_width)
        //         .attr("height", box_height*(1-d.confidence.q1) - box_height*(1-d.confidence.q3))
        //         // .attr("fill", "none")
        //         .attr("fill", `rgb(255, ${(165+255*3)/4}, ${255*3/4})`)
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);

        //     now.append("line")
        //         .attr("class", "median")
        //         .attr("x1", 0)
        //         .attr("x2", box_width)
        //         .attr("y1", box_height*(1-d.confidence.median))
        //         .attr("y2", box_height*(1-d.confidence.median))
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);
        
        //     now.append("line")
        //         .attr("class", "whisker")
        //         .attr("x1", box_width/2)
        //         .attr("x2", box_width/2)
        //         .attr("y1", box_height*(1-d.confidence.min))
        //         .attr("y2", box_height*(1-d.confidence.q1))
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);
        
        //     now.append("line")
        //         .attr("class", "whisker")
        //         .attr("x1", box_width/2)
        //         .attr("x2", box_width/2)
        //         .attr("y1", box_height*(1-d.confidence.q3))
        //         .attr("y2", box_height*(1-d.confidence.max))
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);
        
        //     now.append("line")
        //         .attr("class", "whisker")
        //         .attr("x1", box_width/4)
        //         .attr("x2", box_width*3/4)
        //         .attr("y1", box_height*(1-d.confidence.min))
        //         .attr("y2", box_height*(1-d.confidence.min))
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);
        
        //     now.append("line")
        //         .attr("class", "whisker")
        //         .attr("x1", box_width/4)
        //         .attr("x2", box_width*3/4)
        //         .attr("y1", box_height*(1-d.confidence.max))
        //         .attr("y2", box_height*(1-d.confidence.max))
        //         // .attr("stroke", "orange")
        //         .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //         .attr("stroke-width", 1);
        
        //     d.confidence.outliers.forEach(outlier => {
        //         now.append("circle")
        //             .attr("class", "outlier")
        //             .attr("cx", box_width/2)
        //             .attr("cy", box_height*(1-outlier))
        //             .attr("r", 1)
        //             .attr("fill", "none")
        //             // .attr("stroke", "orange")
        //             .attr("stroke", `rgb(${255*dark_scale}, ${165*dark_scale}, 0)`)
        //             .attr("stroke-width", 1);
        //     });
        // });
    };
};

export default MapRender;
