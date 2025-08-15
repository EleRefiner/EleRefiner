<template>
    <div class="tool-title" id="sample-title" @click="clickTitle">
        <p class="arrow" id="sample-arrow">></p>
        <p>Sample Information</p>
    </div>
    <div class="sub-control">
        <v-row style="height: 100%; margin: 0" justify="center" align="center">
            <v-col cols="12" style="height: 100%; padding-top: 0; padding-bottom: 0; font-size: 12px;">
                <div class="meta-info">
                    <label style="font-weight: bold;">Image Source: </label>
                    <label class="meta-label" id="meta_imgsc" style="display: block;" :title="item.image+'('+selectedItemIndex+')'">{{item.image?item.image:"none"}}</label>
                </div>
                <div class="meta-info">
                    <label style="font-weight: bold;">Number of Boxes: </label>
                    <label class="meta-label" id="meta_boxn" style="display: block;">{{item.boxes?item.boxes.length:"none"}}</label>
                </div>
                <div class="meta-info selector">
                    <label id="category-label" style="font-weight: bold;" for="category" >Choose Category:</label>
                    <select id="category" v-model="selectedCategory" @change="updateCategory" style="display: block; border-style: solid; border-radius: 2px;">
                        <option value="good">优</option>
                        <option value="normal">良</option>
                        <option value="normal-only-image">良-仅缺少视觉元素</option>
                        <option value="normal-only-small-image">良-仅缺少小图标</option>
                        <option value="bad">差</option>
                        <option value=""></option>
                    </select>
                </div>
            </v-col>
        </v-row>
    </div>
</template>

<script>
import { VContainer, VRow, VCol } from 'vuetify/components'; 
import * as d3 from 'd3';
import * as Global from '../plugins/global';
import { mapState, mapActions } from 'vuex';
window.d3 = d3;

export default {
    name: 'SampleView',
    components: {
        VContainer,
        VRow,
        VCol
    },
    props: ['item', 'selectedItemIndex'],
    emits: ['categroy-selected', 'click-node'],
    data: function() {
        return {
            selectedCategory: '',
            svg: null,
            svg_g: null,
            svgsize: null,
            svg_width: 100,
            svg_height: 100,
            color_list: ['rgb(255, 23, 23)', 'rgb(255, 139, 23)', 'rgb(255, 238, 23)', 'rgb(180, 255, 23)', 'rgb(23, 255, 35)', 'rgb(23, 255, 255)', 'rgb(23, 64, 255)', 'rgb(168, 23, 255)', 'rgb(255, 83, 247)'],
            max_deep: 0,
            root: null,
            click_id: -1,
            click_ids: [],
            scale: 1,
            xshift: 0,
            yshift: 0,
            isShowHierarchy: false,
            is_zoom: 0,
            only_drag: false,
        };
    },
    methods: {
        clickTitle: function() {
            let card = document.querySelector('.sub-control');
            card.classList.toggle('expanded');
            let arrow = document.querySelector('#sample-arrow');
            arrow.classList.toggle('expanded');
        },
        // buttonZoomIn: function() {
        //     let tmp = document.getElementById('meta-svg');
        //     if(this.is_zoom == 1) {
        //         tmp.classList.remove('magnifier-cursor');
        //         if(this.only_drag)
        //             tmp.classList.add('drag-cursor');
        //         this.is_zoom = 0;
        //     }else {
        //         if(this.is_zoom == -1) {
        //             tmp.classList.remove('shrink-cursor');
        //             if(this.only_drag)
        //                 tmp.classList.add('drag-cursor');
        //             this.is_zoom = 0;
        //         }
        //         if(this.only_drag)
        //             tmp.classList.remove('drag-cursor');
        //         tmp.classList.add('magnifier-cursor');
        //         this.is_zoom = 1;
        //     }
        // },
        // buttonZoomOut: function() {
        //     let tmp = document.getElementById('meta-svg');
        //     if(this.is_zoom == -1) {
        //         tmp.classList.remove('shrink-cursor');
        //         if(this.only_drag)
        //             tmp.classList.add('drag-cursor');
        //         this.is_zoom = 0;
        //     }else {
        //         if(this.is_zoom == 1) {
        //             tmp.classList.remove('magnifier-cursor');
        //             if(this.only_drag)
        //                 tmp.classList.add('drag-cursor');
        //             this.is_zoom = 0;
        //         }
        //         if(this.only_drag)
        //             tmp.classList.remove('drag-cursor');
        //         tmp.classList.add('shrink-cursor');
        //         this.is_zoom = -1;
        //     }
        // },
        updateCategory: function() {
            if (this.item !== null) {
                this.item.category = this.selectedCategory;
                this.$emit('categroy-selected');
            }
        },
        setClick: function(id) {
            // this.click_id = id;
            // this.updateTree();
        },
        setShowHierarchy: function(show) {
            // this.isShowHierarchy = show;
            // this.updateTree();
        },
        // updateTree: function() {
        //     let that = this;
        //     if(that.svg == null)return;
            
        //     this.svg_g.attr("transform", "translate("+this.xshift+","+this.yshift+")");

        //     that.click_ids = [];
        //     that.svg_g.selectAll(".node")
        //         .filter((d) => that.click_id == d.data.name)
        //         .each(function(d){
        //             if((d.data.children!=null)&&(d.data.children.length>0))
        //                 that.click_ids = d.data.child_names;
        //         })

        //     let lineGenerator = d3.line().curve(d3.curveBasis);

        //     that.svg_g.selectAll(".link")
        //         .attr("d", d => {
        //             const source = [d.source.x*that.scale, d.source.y*that.scale];
        //             const target = [d.target.x*that.scale, d.target.y*that.scale];
        //             return lineGenerator([source, [source[0], (source[1]*2+target[1])/3], [target[0], (source[1]+target[1]*2)/3], target]);
        //         })
        //         .attr("stroke", "#ccc")
        //         .attr("fill", "none")
        //         .transition()
        //         .duration(200)
        //         .style('opacity', function(d) {
        //             if(that.click_ids.length>0){
        //                 if((that.click_ids.includes(d.source.data.name))&&(that.click_ids.includes(d.target.data.name)))
        //                     return 1;
        //                 else return 0.25;
        //             }
        //             return 1;
        //         });

        //     const node = that.svg_g.selectAll(".node")
        //         .attr("transform", d => `translate(${d.x*that.scale},${d.y*that.scale})`)
            
        //     node.transition()
        //         .duration(200)
        //         .style('opacity', function(d) {
        //             if(that.click_ids.length>0){
        //                 if(that.click_ids.includes(d.data.name))
        //                     return 1;
        //                 else return 0.25;
        //             }
        //             return 1;
        //         });

        //     node.selectAll("circle")
        //         .attr("r", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return 4.5*Math.sqrt(that.scale);
        //             return 3*Math.sqrt(that.scale);
        //         })
        //         .attr("fill",  (d) => {
        //             if((that.isShowHierarchy)&&('deep' in d.data)) 
        //                 return that.color_list[(that.max_deep-d.data.deep)%that.color_list.length];
        //             if(d.data.class == "non-data_element") 
        //                 return 'red';
        //             else if(d.data.class == "data_element")
        //                 return 'rgb(34, 177, 76)';
        //             else if(d.data.class == "visual_element")
        //                 return 'rgb(255, 255, 0)';
        //             else if(d.data.class == "group")
        //                 return 'transparent';
        //             else return 'blue';
        //         })
        //         .attr("stroke", "black")
        //         .attr("stroke-width", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return 1.5*Math.sqrt(that.scale);
        //             return 0.5*Math.sqrt(that.scale);
        //         })
        //         .attr("stroke-dasharray", function(d) {
        //             // if(d.data.class == "group")
        //             //     return "2,1";
        //             return null;
        //         });
        //     // console.log(that.click_id, node.filter((d) => that.click_id == d.data.name));
        //     node.filter((d) => that.click_id == d.data.name).raise();

        //     node.selectAll("rect")
        //         .attr("width", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return 4.5*Math.sqrt(that.scale)*2;
        //             return 3*Math.sqrt(that.scale)*2;
        //         })
        //         .attr("height", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return 4.5*Math.sqrt(that.scale)*2;
        //             return 3*Math.sqrt(that.scale)*2;
        //         })
        //         .attr("x", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return -4.5*Math.sqrt(that.scale);
        //             return -3*Math.sqrt(that.scale);
        //         })
        //         .attr("y", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return -4.5*Math.sqrt(that.scale);
        //             return -3*Math.sqrt(that.scale);
        //         })
        //         .attr("fill",  (d) => {
        //             if((that.isShowHierarchy)&&('deep' in d.data)) 
        //                 return that.color_list[(that.max_deep-d.data.deep)%that.color_list.length];
        //             if(d.data.class == "non-data_element") 
        //                 return 'red';
        //             else if(d.data.class == "data_element")
        //                 return 'rgb(34, 177, 76)';
        //             else if(d.data.class == "visual_element")
        //                 return 'rgb(255, 255, 0)';
        //             else if(d.data.class == "group")
        //                 return 'transparent';
        //             else return 'blue';
        //         })
        //         .attr("stroke", "black")
        //         .attr("stroke-width", function(d) {
        //             if(that.click_id == d.data.name)
        //                 return 1.5*Math.sqrt(that.scale);
        //             return 0.5*Math.sqrt(that.scale);
        //         })
        //         .attr("stroke-dasharray", function(d) {
        //             // if(d.data.class == "group")
        //             //     return "2,1";
        //             return null;
        //         });
        //     // console.log(that.click_id, node.filter((d) => that.click_id == d.data.name));
        //     node.filter((d) => that.click_id == d.data.name).raise();
        // },
    },
    computed: {
    },
    watch: {
        item: function(item) {
            let that = this;
            that.selectedCategory = item.category;

        //     if(that.svg == null)return;

        //     that.scale = 1;
        //     that.xshift = 0.125*that.svg_width;
        //     that.yshift = 0.025*that.svg_height;
        //     this.svg_g.attr("transform", "translate("+this.xshift+","+this.yshift+")");

        //     const ImageZoom = function(x, y, zoom) {
        //         const scaleBefore = that.scale;
        //         const zoomFactor = 0.2;
        //         that.scale *= 1+zoom*zoomFactor;
        //         that.scale = Math.max(1, that.scale);

        //         that.xshift = x + (that.xshift - x)*that.scale/scaleBefore;
        //         that.yshift = y + (that.yshift - y)*that.scale/scaleBefore; 

        //         that.updateTree();
        //     }

        //     that.svg.on("wheel", (event) => {
        //         const rect = that.svg.node().getBoundingClientRect();
        //         const x = event.clientX - rect.left;
        //         const y = event.clientY - rect.top;
        //         ImageZoom(x, y, event.deltaY<0 ? 1 : -1);
        //     });

        //     let drag_offsetX = 0;
        //     let drag_offsetY = 0;

        //     const ImageMoveStartEnd = function(e, d) {
        //         if(e.type=='start') {
        //             drag_offsetX = e.x - that.xshift;
        //             drag_offsetY = e.y - that.yshift;
        //         }
        //     };

        //     const ImageMoving = function(e, d) {
        //         that.xshift = e.x - drag_offsetX;
        //         that.yshift = e.y - drag_offsetY;
        //         that.updateTree();
        //     };

        //     that.svg.call(d3.drag()
        //         .container(that.svg.node())
        //         .on('start end', ImageMoveStartEnd)
        //         .on('drag', ImageMoving),
        //     );

        //     // console.log("item", item);

        //     let id_cnt = 0;
        //     let boxes = item.boxes.map(function(d) {
        //         id_cnt += 1;
        //         return {
        //             id: id_cnt-1,
        //             bbox: [d.x, d.y, d.width, d.height],
        //             type: 'pred',
        //             class: d.class,
        //             score: d.score,
        //             iscrowd: 0,
        //         };
        //     });
        //     that.max_deep = 0;

        //     let h_data = null;
        //     id_cnt = 10000;
        //     function dfs(hierarchy, deep) {
        //         if(typeof hierarchy === 'number') {
        //             boxes[hierarchy].deep = deep;
        //             return {"name": boxes[hierarchy].id, "deep": deep, "class": boxes[hierarchy].class, "child_names": [boxes[hierarchy].id]};
        //         }
        //         id_cnt += 1;
        //         let tmp = {
        //             name: id_cnt-1,
        //             deep: hierarchy.deep,
        //             class: 'group',
        //             children: [],
        //             child_names: [id_cnt-1],
        //         }
        //         that.max_deep = Math.max(that.max_deep, hierarchy.deep);
        //         for(let child of hierarchy.children) {
        //             let tmp_child = dfs(child, hierarchy.deep-1);
        //             tmp.children.push(tmp_child);
        //             tmp.child_names = tmp.child_names.concat(tmp_child.child_names);
        //         }
        //         return tmp;
        //     }
        //     if(item.hierarchy != null) {
        //         h_data = dfs(item.hierarchy, item.hierarchy.deep);
        //     }else if(boxes.length >= 1) {
        //         h_data = {"name": boxes[0].id, "deep": 0, "class": boxes[0].class}
        //     }
        //     // console.log("hierarchy", h_data);

        //     that.svg_g.selectAll(".link").remove();
        //     that.svg_g.selectAll(".node").remove();

        //     if(h_data != null) {
        //         const root = d3.hierarchy(h_data);
        //         const treeLayout = d3.tree().size([0.85*that.svg_width, 0.95*that.svg_height]);
        //         treeLayout(root);
                
        //         that.root = root;

        //         let lineGenerator = d3.line().curve(d3.curveBasis);

        //         that.svg_g.selectAll(".link")
        //             .data(root.links())
        //             .enter()
        //             .append("path")
        //             .attr("class", "link");

        //         // console.log('root', root.descendants());
        //         const node = that.svg_g.selectAll(".node")
        //             .data(root.descendants())
        //             .enter()
        //             .append("g")
        //             .attr("class", "node")
        //             .on('click', function(e, d) {
        //                 if(that.click_id != d.data.name) {
        //                     // console.log(d);
        //                     that.click_id = d.data.name;
        //                     that.$emit('click-node', d.data.name);
        //                     that.updateTree();
        //                 }else {
        //                     that.click_id = -1;
        //                     that.$emit('click-node', -1);
        //                     that.updateTree();
        //                 }
        //             });

        //         node.filter(d => d.data.children != null)
        //             .append("circle");

        //         node.filter(d => d.data.children == null)
        //             .append("rect");

        //         that.svg.on("click", function(event) {
        //             const rect = that.svg.node().getBoundingClientRect();
        //             const x = event.clientX - rect.left;
        //             const y = event.clientY - rect.top;
        //             if(that.is_zoom!=0) {
        //                 ImageZoom(x, y, 2*that.is_zoom);
        //                 return;
        //             }
        //             if (event.target.tagName === "svg") {
        //                 that.click_id = -1;
        //                 that.$emit('click-node', -1);
        //                 that.updateTree();
        //             }
        //         });
        //     }
        //     that.updateTree();
        }
    },
    mounted() {
        // this.svg = d3.select("#meta-svg");
        // this.svgsize = this.svg.node().getBoundingClientRect();
        // this.svg_width = this.svgsize.width;
        // this.svg_height = this.svgsize.height;

        // this.scale = 1;
        // this.xshift = 0.125*this.svg_width;
        // this.yshift = 0.025*this.svg_height;
        // this.svg_g = this.svg.select("g")
        //     .attr("transform", "translate("+this.xshift+","+this.yshift+")");
        
    },
};
</script>

<style scoped>

.tool-title {
    pointer-events: auto;
    /* color: rgb(204, 204, 204); */
    background-color: rgb(204, 204, 204);
    font-weight: bold;
    font-size: 12px;
    border-bottom: 1px solid #ddd;
    text-align: left;
    border-radius: 4px;
    display: flex;
    text-align: center;
    align-items: center;
}

.arrow {
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    font-size: 16px;
    padding-left: 6px;
    padding-right: 6px;
    transition: transform 0.5s ease;
}

.arrow.expanded {
    transform: rotate(90deg);
}

.sub-control-outter {
    position: relative;
    width: 100%;
    height: 25%;
}

.sub-control {
    pointer-events: auto;
    background-color: transparent;
    text-align: left;
    position: relative;
    width: 100%;
    /* height: 40%; */
    transition: max-height 0.5s ease, border 0.5s ease, background-color 0.5s ease;
    max-height: 0%;
    overflow: hidden;
    /* min-height: 30px; */
    line-height: 30px;
    border: 2px solid transparent;
    padding-bottom: 8px;
}

.sub-control.expanded {
    background-color: rgba(255, 255, 255, 0.75);
    max-height: 40%;
    border: 2px solid #aaa;
}

.meta-info {
    width: 100%;
}

.image-info {
  height: 100%;
  width: 100%;
}

.datainfo-image {
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
}

.svg-info {
    position: relative;
    height: 100%;
    width: 100%;
}

.tree-box {
    position: relative;
    border: 1px solid #ddd;
    width: 100%;
    height: 100%;
    flex-shrink: 100;
}

.datainfo-svg {
    width: 100%;
    height: 100%;
}

.datainfo-bar {
    height: 10%;
    width: 90%;
}

.meta-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.V-centered {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.H-centered {
    align-items: center;
    text-align: center;
}

</style>
