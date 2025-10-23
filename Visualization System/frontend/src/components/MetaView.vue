<template>
    <div class="MetaView">
        <div class="meta-content">
<!--            <v-row style="margin: 0; padding-top: 0; padding-bottom: 0; font-size: 16px; height: calc(50% - 1px); text-align: left;">-->
<!--                <v-col cols="3" class="V-centered" style="height: 100%; font-weight: bold; padding: 0px;">-->
<!--                    <span class="label-text">Dataset:</span>-->
<!--                </v-col>-->
<!--                <v-col cols="9" style="height: 100%; padding: 0px;">-->
<!--                    <v-select-->
<!--                        density="compact"-->
<!--                        v-model="selectedOption"-->
<!--                        :items="options"-->
<!--                        @change="updateOptions2"-->
<!--                        style="font-size: 16px;">-->
<!--                    </v-select>-->
<!--                </v-col>-->
<!--                &lt;!&ndash; <v-col cols="4" class="V-centered" style="height: 100%;">-->
<!--                </v-col> &ndash;&gt;-->
<!--            </v-row>-->
<!--            <v-row style="margin: 0; margin-top: 2px; padding-top: 0; padding-bottom: 0; font-size: 16px; height: calc(50% - 1px); text-align: left;">-->
<!--                <v-col cols="3" class="V-centered" style="height: 100%; font-weight: bold; padding: 0px;">-->
<!--                    <span class="label-text">Description:</span>-->
<!--                </v-col>-->
<!--                <v-col cols="9" class="V-centered" style="height: 100%; padding: 0px; text-align: justify;">-->
<!--                    <span class="label-text">{{items?items.length:"none"}} different infographic charts and their layout templates. </span>-->
<!--                </v-col>-->
<!--            </v-row>-->
            <div class="meta-dataset">
                <div class="meta-inner">
                    <div class="meta-title">
                        <p> Dataset </p>
                    </div>
                    <div class="meta-info">
                          <div class="dropdown-container">
                              <select class="custom-dropdown" v-model="selectedOption" @change="updateOptions2">
                                  <option v-for="option in options" :key="option" :value="option">
                                      {{ option }}
                                  </option>
                              </select>
                          </div>
                    </div>
                </div>
            </div>
            <div class="meta-description">
                <div class="meta-inner">
                    <div class="meta-title">
                        <p> Description </p>
                    </div>
                    <div class="meta-info">
                        <div class="big-number">
                            <p> {{items_len?items_len:"none"}} </p>
                        </div>
                        <div class="description-text">
                            <p> infographic charts and their clusters </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { VContainer, VRow, VCol, VSelect } from 'vuetify/components'; 

export default {
    name: 'MetaView',
    components: {
        VContainer,
        VRow,
        VCol,
        VSelect
    },
    props: ['items_len'],
    data: function() {
        return {
            selectedOption: 'Infographic',
            options: ['Infographic', "?"],
        };
    },
    methods: {
        updateOptions2: function(e) {
            console.log("change", this.selectedOption);
        },
    },
    computed: {

    },
    watch: {

    },
    mounted() {

    },
};
</script>

<style>

.v-field {
    font-size: 16px;
}

</style>

<style scoped>
.meta-content {
    width: calc(100% - 20px);
    height: calc(95% - 12px);
    margin-left: 10px;
    margin-right: 10px;
    margin-bottom: 12px;
    top: 2.5%;
    position: relative;
    display: flex;
}

.meta-dataset {
    height: 100%;
    width: calc(42%);
    background: white;
    border-radius: 5px;
}
.meta-description {
    height: 100%;
    width: calc(58% - 15px);
    margin-left: 13px;
    background: white;
    border-radius: 5px;
}

.meta-inner {
    height: calc(100% - 30px);
    width: calc(100% - 30px);
    margin: 15px;
}

.meta-title {
    font-size: 16px;
    height: 30%;
    width: 100%;
    font-weight: bold;
    text-align: left;
}

.meta-info {
    height: 70%;
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: center;
    align-items: center;
}

.dropdown-container {
    width: 100%;
}

.custom-dropdown {
    font-size: 13px;
    width: 100%;
    padding: 10px;
    border-radius: 5px;
    background-color: #E9EFFB;
    /* appearance: none; */
    cursor: pointer;
    position: relative;
    -webkit-appearance: auto;
}

/* .custom-dropdown::after {
    content: '\25BC';
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    color: #666;
} */

/* 选中时的样式 */
.custom-dropdown:focus {
    outline: none;
    border-color: rgb(120, 159, 226);
    box-shadow: 0 0 5px rgba(120, 159, 226, 0.5);
}

.big-number {
    height: 100%;
    width: 42.5%;
    font-size: 35px;
    font-weight: bold;
    display: flex;
    align-items: center;
}
.description-text {
    height: 100%;
    width: 57.5%;
    font-size: 13px;
    font-weight: bold;
    color: #697283;
    display: flex;
    align-items: center;
}

.V-centered {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

</style>
