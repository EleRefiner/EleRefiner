/* eslint-disable */
import * as d3 from "d3";

const GridLayout = function(parent) {
  let that = this;
  that.parent = parent;

  that.stroke_width = 1; // 0.4;
  that.extra_width = 1.5; // 1.2
  that.partition_width = 3.0; // 3.0

  that.update_info_from_parent = function() {
    that.grid_margin = that.parent.grid_margin;
    that.top_margin = that.parent.top_margin;

    that.create_ani = that.parent.create_ani;
    that.update_ani = that.parent.update_ani;
    that.remove_ani = that.parent.remove_ani;
    that.layout_width = that.parent.svg_width - that.grid_margin * 2;
    that.layout_height = that.parent.svg_height - that.top_margin - that.partition_width;
    that.gridstack = that.parent.gridstack;
    that.mode = that.parent.mode;
    that.detection_items = that.parent.detection_items;
  };

  that.update_color = function(grids, color_set) {
    let colors = color_set["colormap"];
    let pcolors = color_set["partitionmap"];
    that.colors = colors;
    that.pcolors = pcolors;
    grids.forEach(grid => {
      grid.color = colors[grid.label];
      grid.pcolor = pcolors[grid.label];
    });
    return grids;
  };

  that.update_layout = function(grid_info, color_set = null) {
    that.update_info_from_parent();

    // total position
    that.size = grid_info.size;
    that.cell = Math.min(
      that.layout_width / that.size[1],
      // (that.layout_height-(1/2*that.parent.min_image_size2)) / that.size[0]
      that.layout_height / that.size[0]
    );
    that.grid_width = that.cell * that.size[1];
    that.grid_height = that.cell * that.size[0];
    that.parent.parent.gridlayout_size = [that.grid_width, that.grid_height];
    
    that.grid_margin_x =
      (that.layout_width - that.grid_width) / 2 + that.grid_margin;
    that.grid_margin_y =
      (that.layout_height - that.grid_height) / 2 + that.top_margin + that.partition_width/2;
    // console.log("margin", that.grid_margin_y, that.layout_height, that.grid_height, that.top_margin)
    
    let meta = {
      delta_x: that.grid_margin_x,
      delta_y: that.grid_margin_y,
      grid_width: that.grid_width,
      grid_height: that.grid_height
    };

    // cell position and color
    let grids = [];
    // console.assert(grid_info.grid.length === that.size[0] * that.size[1]);
    let x = 0;
    let y = 0;

    // let colors = color_set ? color_set["colormap"] : {...grid_info.colors};
    // let pcolors = color_set ? color_set["partitionmap"] : {...grid_info.pcolors};
    let colors = {};
    let pcolors = {};
    for(let label of grid_info.labels) {
      if(!(label in colors))
        colors[label] = [255, 255, 255, 0];
        pcolors[label] = [255, 255, 255, 0];
    }

    that.colors = colors;
    that.pcolors = pcolors;
    // console.log('color_set', color_set, colors, pcolors);
    if (color_set === null) {
      Object.keys(colors).forEach(key => {
        let raw = colors[key];
        // colors[key] = [255 * raw[0], 255 * raw[1], 255 * raw[2]];
        colors[key] = [255, 255, 255, 0];   //set color to white
      });
      Object.keys(pcolors).forEach(key => {
        let raw = pcolors[key];
        // pcolors[key] = [255 * raw[0], 255 * raw[1], 255 * raw[2]];
        pcolors[key] = [255, 255, 255, 0];   //set color to white
      });
    }
    let pclasses = {};
    let pid = 0;
    let cclasses = {};
    let cid = 0;
    // console.log(color_set, grid_info.colors);
    class Matrix {
      constructor() {
        this.values = {};
      }
      set = function(x, y, value) {
        this.values[`${x},${y}`] = value;
      };
      get = function(x, y) {
        return this.values[`${x},${y}`];
      };
    }
    let matrix_t = new Matrix();

    let pos_bias_list = [[-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1]];
    let poses = [];
    let image_bias = [];
    let use_bias = false;
    let grid_width = that.cell - 2*that.stroke_width;
    let image_border = Math.max(4, 0.1*grid_width);
    if((that.parent.min_image_size > grid_width-2*image_border)
      && (that.parent.min_image_size2 > that.cell*1.2))
      use_bias = true;
    for(let i=0;i<grid_info.grid.length;i++) {
      poses.push([0, 0]);
      image_bias.push([1, 1]);
    }
    console.log("grid info", grid_info)

    let grid_map = {}
    for(let i=0;i<grid_info.grid.length;i++) {
      grid_map[`${grid_info.grid[i][0]}-${grid_info.grid[i][1]}`] = i;
    }
    for(let i=0;i<grid_info.grid.length;i++){
      let id = i;
      if(id>=grid_info.labels.length)continue;
      let lb1 = grid_info.labels[id];
      poses[id][0] = grid_info.grid[id][0];
      poses[id][1] = grid_info.grid[id][1];
      if(use_bias) {
        let best_same = 0;
        let best_bias = 0;
        for(let j=0;j<8;j++){
          let same_cnt = 0;
          let kk = (j+8) % 8;
          let range = [[0, 0], [0, 0]];
          for(let l=0;l<=1;l++){
            if(pos_bias_list[kk][l]==0)range[l] = [-Math.ceil(that.parent.min_image_size2/2/that.cell), Math.ceil(that.parent.min_image_size2/2/that.cell)];
            if(pos_bias_list[kk][l]==-1)range[l] = [-Math.ceil(that.parent.min_image_size2/that.cell), 0];
            if(pos_bias_list[kk][l]==1)range[l] = [0, Math.ceil(that.parent.min_image_size2/that.cell)];
          }
          // if((poses[id][0]==0)&&(poses[id][1]==29))
          //   console.log("range", range)
          for(let k=range[0][0];k<=range[0][1];k++)
          for(let l=range[1][0];l<=range[1][1];l++){
            let tmp_x = poses[id][0] + k;
            let tmp_y = poses[id][1] + l;
            // if((poses[id][0]==0)&&(poses[id][1]==29))
            //   console.log("tmp x y", tmp_x, tmp_y);
            if(tmp_x>=0 && tmp_x<that.size[0] && tmp_y>=0 && tmp_y<that.size[1]){
              let lb2 = grid_info.labels[grid_map[`${tmp_x}-${tmp_y}`]];
              // if((poses[id][0]==0)&&(poses[id][1]==29))
              //   console.log("lb2", grid_map[`${tmp_x}-${tmp_y}`], grid_info.grid[grid_map[`${tmp_x}-${tmp_y}`]]);
              if(lb1==lb2)same_cnt += 1;
            }else same_cnt -= 5;
          }
          // if((poses[id][0]==0)&&(poses[id][1]==29))
          //   console.log("bias", same_cnt, j);
          if(same_cnt>best_same){
            best_same = same_cnt;
            best_bias = j;
          }
        }
        // if((poses[id][0]==0)&&(poses[id][1]==29))
        //   console.log("best", best_same, best_bias);
        image_bias[id][0] = pos_bias_list[best_bias][0] * (that.parent.min_image_size2*grid_info["image_ratio"][id][1]/2 - grid_width/4);
        image_bias[id][1] = pos_bias_list[best_bias][1] * (that.parent.min_image_size2*grid_info["image_ratio"][id][0]/2 - grid_width/4);
        // console.log(image_bias[id], (that.parent.min_image_size2*grid_info["image_ratio"][id][0]/2 - grid_width/4), (that.parent.min_image_size2*grid_info["image_ratio"][id][1]/2 - grid_width/4))
      }
    }
    let image_width = 0;
    if(grid_width - 2*image_border >= that.parent.min_image_size)image_width = grid_width - 2*image_border;
    else image_width = that.parent.min_image_size2;
    let show_images = [];
    let if_show_images = [];

    let argsort = [];
    for(let i=0;i<grid_info.grid.length;i++)argsort.push(i);
    // argsort.sort(() => Math.random() - 0.5);
    argsort.reverse();

    for(let i=argsort.length-1;i>=0;i--){
      // // if((grid_info.sample_ids[argsort[i]] == 1674)||(grid_info.sample_ids[argsort[i]] == 1241)||(grid_info.sample_ids[argsort[i]] == 1395)||(grid_info.sample_ids[argsort[i]] == 1088)||(grid_info.sample_ids[argsort[i]] == 1255)||(grid_info.sample_ids[argsort[i]] == 1243)||(grid_info.sample_ids[argsort[i]] == 103))
      // if((grid_info.sample_ids[argsort[i]] == 1674)||(grid_info.sample_ids[argsort[i]] == 1241))
      //   continue;
      let id1 = argsort[i];
      let x1 = poses[id1][0]*that.cell;
      let y1 = poses[id1][1]*that.cell;
      let b_x1 = image_bias[id1][0];
      let b_y1 = image_bias[id1][1];
      let flag = true;
      for(let j=0;j<show_images.length;j++){
        let id2 = show_images[j];
        let x2 = poses[id2][0]*that.cell;
        let y2 = poses[id2][1]*that.cell;
        let b_x2 = image_bias[id2][0];
        let b_y2 = image_bias[id2][1];
        if(Math.max(Math.abs(x1+b_x1-x2-b_x2), Math.abs(y1+b_y1-y2-b_y2))*0.85<that.parent.min_image_size2){
          flag = false;
          break;
        }
      }
      if(flag){
        show_images.push(id1);
      };
      // if(show_images.length*that.parent.min_image_size2*that.parent.min_image_size2>argsort.length*that.cell*that.cell*0.33)break;
    }
//    console.log("show images num", show_images.length)
//    console.log("show images", show_images);
    for(let i=0;i<argsort.length;i++)if_show_images.push(that.parent.min_image_size <= grid_width-2*image_border);
    for(let i=0;i<show_images.length;i++)if_show_images[show_images[i]] = true;

    that.id_map = [];
    let id_cnt = 0;
    grid_info.grid.forEach((d, i) => {
      let grid = {};
      grid.order = i;
      grid.pos = [d[0], d[1]];
      grid.pos_t = [d[1], d[0]];
      x = d[0];
      y = d[1];
      // grid.x = y * that.cell + that.stroke_width;
      // grid.y = x * that.cell + that.stroke_width;
      // grid.width = that.cell - 2 * that.stroke_width;
      // grid.height = that.cell - 2 * that.stroke_width;
      grid.x = y * that.cell;
      grid.y = x * that.cell;
      grid.width = that.cell;
      grid.height = that.cell;
//      grid.show_image = ((that.parent.render_image && grid_info.grid.length <= 400 && (x%3===0) && (y%3===0)) ? true : false);
      grid.show_image = if_show_images[i];
      grid.o_show_image = if_show_images[i];
      grid.image_bias = [image_bias[i][1], image_bias[i][0]];
      grid.image_ratio = grid_info["image_ratio"][i];
      // console.log(grid.image_bias, grid.image_ratio)
      grid.use_image_bias = use_bias;
      grid.name = i;
      grid.index = i;
      grid.label = grid_info.labels[i];
      grid.part_label = grid_info.part_labels[i];
      grid.color_id = String(grid_info.top_labels[i]);

      that.id_map.push(id_cnt);
      id_cnt += 1;
      grid.label_name = grid_info.label_names[grid.label];
      grid.color = colors[grid.label];
      grid.pcolor = pcolors[grid.label];
      grid.gt_label = grid_info.gt_labels[i];
      grid.gt_label_name = grid_info.label_names[grid.gt_label];
      grid.bottom_label = grid_info.bottom_labels.labels[i];
      grid.bottom_label_name = grid_info.label_names[grid.bottom_label];
      grid.bottom_gt_label = grid_info.bottom_labels.gt_labels[i];
      grid.bottom_gt_label_name = grid_info.label_names[grid.bottom_gt_label];
      grid.is_confused = false;
      grid.confuse_values = [1];

      grid.pstr =
        grid.color_id.indexOf("-") === -1
          ? grid.color_id
          : grid.color_id.substring(0, grid.color_id.lastIndexOf("-"));
      if (!(grid.pstr in pclasses)) {
        pclasses[grid.pstr] = [pid, grid.pcolor];
        pid++;
      }
      grid.pclass = pclasses[grid.pstr][0];
      if (!(grid.part_label in cclasses)) {
        cclasses[grid.part_label] = [cid, grid.color];
        cid++;
      }
      grid.cclass = cclasses[grid.part_label][0];
      grid.sample_id = grid_info.sample_ids[i];
      if(that.detection_items != undefined) {
        // console.log("?", grid.sample_id, that.detection_items);
        grid.detection_category = that.detection_items[grid.sample_id].category;
        grid.detection_boxes = that.detection_items[grid.sample_id].boxes;
      }
      grid.stroke_width = that.stroke_width;
      grid.img = "";
      grids.push(grid);
      matrix_t.set(y, x, grid);
    });

    for(let i=0;i<grids.length;i++)
      for(let j=i+1;j<grids.length;j++){
        if((grids[i].x>grids[j].x)||((grids[i].x == grids[j].x)&&(grids[i].y>grids[j].y))){
          let tmp = grids[i];
          grids[i] = grids[j];
          grids[j] = tmp;
        }
      }

    let index_dict = {};
    for(let i=0;i<grids.length;i++){
      grids[i].index = i;
      grids[i].order = i;
      index_dict[grids[i].sample_id] = grids[i];
    }
    meta.index_dict = index_dict;

    //calculate accuracy
    let acc_dict = {}
    grids.forEach(grid => {
      if(!(grid.label in acc_dict)){
        acc_dict[grid.label] = [0, 0];
      }
      acc_dict[grid.label][1] += 1;
      if(grid.detection_category == "good")acc_dict[grid.label][0] += 1;
    })
    grids.forEach(grid => {
      grid.acc = acc_dict[grid.label][0]/acc_dict[grid.label][1];
    })

//    console.log(">>>", pclasses);
    grids.forEach(grid => {
      let pos_t = grid.pos_t;
      grid.left = matrix_t.get(pos_t[0] - 1, pos_t[1]);
      grid.right = matrix_t.get(pos_t[0] + 1, pos_t[1]);
      grid.top = matrix_t.get(pos_t[0], pos_t[1] - 1);
      grid.bottom = matrix_t.get(pos_t[0], pos_t[1] + 1);

      grid.px = [];
      grid.py = [];
      grid.pwidth = [];
      grid.pheight = [];

      // caculate extra width for label
      if (that.mode.indexOf("isolate_label") !== -1) {
        d3.range(pid).forEach(i => {
          let px = grid.x;
          let py = grid.y;
          let pwidth = grid.width;
          let pheight = grid.height;

          grid.px.push(px);
          grid.py.push(py);
          grid.pwidth.push(pwidth);
          grid.pheight.push(pheight);
        });
      }
    });

    let ppaths = [];
    let cur_node_index = that.gridstack[that.gridstack.length - 1];
    Object.keys(pclasses).forEach(pstr => {
      let pclass = pclasses[pstr][0];
      let boundaries = that.caculate_boundary(grids, pclass);
      let paths = that.caculate_path(boundaries, that.cell);
      paths.forEach((path, i) => {
        ppaths.push({
          pclass: pclass,
          path: path,
          name: `p-${cur_node_index}-${pclass}-${i}`,
          pcolor: pclasses[pstr][1]
        });
      });
    });
    meta.paths = ppaths;

    let cpaths = [];
    Object.keys(cclasses).forEach(label => {
      let cclass = cclasses[label][0];
      let boundaries = that.caculate_boundary(grids, cclass, "c");
      let paths = that.caculate_path(boundaries, that.cell);
      paths.forEach((path, i) => {
        cpaths.push({
          cclass: cclass,
          path: path,
          name: `c-${cur_node_index}-${cclass}-${i}`,
          color: colors[cclass]
        });
      });
    });
    meta.cpaths = cpaths;

    let minx, miny, maxx, maxy;
    grids.forEach((d, i) => {
      if (i === 0) {
        minx = d.x;
        miny = d.y;
        maxx = d.x + d.width;
        maxy = d.y + d.width;
      } else {
        minx = Math.min(minx, d.x);
        miny = Math.min(miny, d.y);
        maxx = Math.max(maxx, d.x + d.width);
        maxy = Math.max(maxy, d.y + d.width);
      }
    });
    meta.minx = minx;
    meta.miny = miny;
    meta.maxx = maxx;
    meta.maxy = maxy;
    meta.max_pid = pid;
    meta.matrix_t = matrix_t;

    return [meta, grids];
  };

  that._get_set_first_value = function(set) {
    let [first] = set;
    return first;
  };

  that._get_edge_name = function(start_node, end_node) {
    let [x1, y1] = start_node.split(",");
    let [x2, y2] = end_node.split(",");
    if (x1 === x2) {
      if (parseInt(y1) < parseInt(y2)) return `td-${x1}-${y1}`;
      else return `td-${x2}-${y2}`;
    } else {
      if (parseInt(x1) < parseInt(x2)) return `lr-${x1}-${y1}`;
      else return `lr-${x2}-${y2}`;
    }
  };

  that.caculate_boundary = function(grids, pclass, mode="p") {
    let pgrids = grids.filter(d => d.pclass === pclass);
    if(mode == "c")
      pgrids = grids.filter(d => d.cclass === pclass);
    let edge_sets = new Set();
    // console.log(pgrids);
    pgrids.forEach(d => {
      let [y, x] = d.pos;
      let edges = [
        `td-${x}-${y}`,
        `td-${x + 1}-${y}`,
        `lr-${x}-${y}`,
        `lr-${x}-${y + 1}`
      ];
      edges.forEach(edge => {
        if (edge_sets.has(edge)) edge_sets.delete(edge);
        else edge_sets.add(edge);
      });
    });
    let edge_nodes = {};
    let node_links = {};
    edge_sets.forEach(edge => {
      // get edge start node and end node
      let [type, x, y] = edge.split("-");
      x = parseInt(x);
      y = parseInt(y);
      let start_node = `${x},${y}`;
      let end_node;
      if (type === "td") end_node = `${x},${y + 1}`;
      else end_node = `${x + 1},${y}`;
      edge_nodes[edge] = [start_node, end_node];
      // get node links
      if (!(start_node in node_links)) node_links[start_node] = new Set();
      if (!(end_node in node_links)) node_links[end_node] = new Set();
      node_links[start_node].add(end_node);
      node_links[end_node].add(start_node);
    });
    let boundaries = [];
    while (edge_sets.size > 0) {
      let cur_edge = that._get_set_first_value(edge_sets);
      edge_sets.delete(cur_edge);
      let boundary = [];
      let [start_node, end_node] = edge_nodes[cur_edge];
      boundary.push(start_node);
      boundary.push(end_node);
      let bf_node = start_node;
      let cur_node = end_node;
      while (cur_node !== start_node) {
        let cur_node_link = node_links[cur_node];
        cur_node_link.delete(bf_node);
        let next_node = that._get_set_first_value(cur_node_link);
        if (next_node === undefined) next_node = start_node;
        else cur_node_link.delete(next_node);
        cur_edge = that._get_edge_name(cur_node, next_node);
        edge_sets.delete(cur_edge);
        bf_node = cur_node;
        cur_node = next_node;
        boundary.push(cur_node);
      }
      boundaries.push(boundary);
    }
    // console.log('boundary', boundaries);
    return boundaries;
  };

  that.caculate_path = function(boundaries, cell) {
    let paths = boundaries.map(boundary => {
      let path = "";
      boundary.forEach((node, i) => {
        let [x, y] = node.split(",");
        x = parseInt(x);
        y = parseInt(y);
        if (i === 0) path += `M${x * cell},${y * cell}`;
        else path += `L${x * cell},${y * cell}`;
      });
      return path + "Z";
    });
    return paths;
  };
};

export { GridLayout };
