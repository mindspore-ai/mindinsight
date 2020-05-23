<!--
Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <div class="cl-checklist-container">
    <!-- Select tag -->
    <div class="select-content">
      <div class="title mr24">{{componentsLabel.title || $t("components.tagSelectTitle")}}</div>
      <!-- Select all -->
      <div class="select-all mr24"
           @click="listSelectAll">
        <span class="multiCheckBox-border multi-check-border"
              :class="operateSelectAll ? 'checkbox-checked':'checkbox-unchecked'"></span>
        <span class="label-item select-disable">{{$t("components.selectAll")}}</span>
      </div>
      <!-- Tag search box -->
      <el-input class="search-input-item"
                v-model="searchInput"
                @input="listFilter"
                v-if="listFullScreen"
                :placeholder="componentsLabel.placeholder || $t('components.tagFilterPlaceHolder')"></el-input>
      <!-- Tag list -->
      <div class="select-item-content"
           v-if="!listFullScreen"
           :ref="itemId">
        <div class="select-item"
             v-for="(item, itemIndex) in checkListArr"
             :key="itemIndex"
             @click="listItemClick(item)"
             v-show="item.show"
             :class="(isLimit && selectedNumber >= limitNum && !item.checked)?'item-disable':'item-able'">
          <span class="multiCheckBox-border multi-check-border"
                :class="item.checked ? 'checkbox-checked':'checkbox-unchecked'"></span>
          <span class="label-item">
            <el-tooltip effect="dark"
                        popper-class="tooltip-show-content"
                        :content="item.label"
                        placement="top">
              <span class="select-disable"><i title="CACHING" v-if="item.loading"
                   class="el-icon-loading"></i>{{item.label}}</span>
            </el-tooltip>
          </span>
        </div>
      </div>
      <!-- Tag expansion/collapse button -->
      <div class="select-content-open select-disable"
           @click="toggleListFullScreen"
           v-if="overRowFlag || searchInput"
           v-show="!listFullScreen">{{$t("components.open")}}</div>
      <div class="select-content-open select-disable"
           @click="toggleListFullScreen"
           v-if="overRowFlag || listFullScreen"
           v-show="listFullScreen">{{$t("components.close")}}</div>
    </div>
    <div class="select-content-all"
         v-if="listFullScreen">
      <div class="select-item"
           v-for="(item, itemIndex) in checkListArr"
           :key="itemIndex"
           @click="listItemClick(item)"
           v-show="item.show"
           :class="(isLimit && selectedNumber >= limitNum && !item.checked)?'item-disable':'item-able'">
        <span class="multiCheckBox-border multi-check-border"
              :class="item.checked ? 'checkbox-checked' : 'checkbox-unchecked'"></span>
        <span class="label-item">
          <el-tooltip effect="dark"
                      popper-class="tooltip-show-content"
                      :content="item.label"
                      placement="top">
            <span class="select-disable"><i title="CACHING" v-if="item.loading"
                 class="el-icon-loading"></i>{{item.label}}</span>
          </el-tooltip>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    checkListArr: Array,
    isLimit: {
      type: Boolean,
      default: false,
    },
    limitNum: {
      type: Number,
      default: 0,
    },
    componentsLabel: {
      type: Object,
      default() {
        return {
          title: '',
          placeholder: '',
        };
      },
    },
  },
  data() {
    return {
      listFullScreen: false, // Indicates whether to expand the selection list.
      overRowFlag: false, // Check whether the list contains more than one line.
      searchInputTimer: null, // Timer for filtering.
      searchInput: '', // Regular input value of the search.
      valiableSearchInput: '', // Last valid input for tag retrieval.
      multiSelectedItemNames: {}, // Dictionary for storing the name of the selected tags.
      operateSelectAll: true, // Indicates whether to select all tags.
      perSelectItemMarginBottom: 1, // Outer margin of the bottom of each selection box.
      selectedNumber: 0, // Number of Selected items
      itemId: '', // component Id
      searching: false,
    };
  },
  computed: {},
  watch: {},
  mounted() {
    this.init();
  },
  methods: {
    /**
     * Initialize
     */
    init() {
      this.itemId =
        `${new Date().getTime()}` +
        `${this.$store.state.multiSelectedGroupCount}`;
      this.$store.commit('multiSelectedGroupComponentNum');
      this.$nextTick(() => {
        this.resizeCallback();
      });
      window.addEventListener('resize', this.resizeCallback, false);
    },
    /**
     * The callback of window size changes listener
     */
    resizeCallback() {
      // Calculating the display of the Expand Folding Button
      const selectItemContent = this.$refs[this.itemId];
      if (selectItemContent) {
        this.overRowFlag =
          selectItemContent.clientHeight <
          selectItemContent.scrollHeight - this.perSelectItemMarginBottom;
      }
    },
    /**
     * Click select all
     */
    listSelectAll() {
      this.operateSelectAll = !this.operateSelectAll;
      this.multiSelectedItemNames = {};
      // Setting the status of list items
      if (this.operateSelectAll) {
        if (this.isLimit) {
          const loopCount = this.checkListArr.length;
          for (let i = 0; i < loopCount; i++) {
            if (this.selectedNumber >= this.limitNum) {
              break;
            }
            const listItem = this.checkListArr[i];
            if (listItem.show) {
              listItem.checked = true;
              this.multiSelectedItemNames[listItem.label] = true;
              this.selectedNumber++;
            }
          }
        } else {
          this.checkListArr.forEach((listItem) => {
            if (listItem.show) {
              listItem.checked = true;
              this.multiSelectedItemNames[listItem.label] = true;
            }
          });
        }
      } else {
        this.checkListArr.forEach((listItem) => {
          if (listItem.show && listItem.checked) {
            this.selectedNumber--;
            listItem.checked = false;
          }
        });
      }
      // Returns a dictionary containing selected items.
      this.$emit('selectedChange', this.multiSelectedItemNames);
    },
    /**
     * Tag Filter
     */
    listFilter() {
      this.searching = true;
      if (this.searchInputTimer) {
        clearTimeout(this.searchInputTimer);
        this.searchInputTimer = null;
      }
      this.searchInputTimer = setTimeout(() => {
        this.searching = false;
        let reg;
        try {
          reg = new RegExp(this.searchInput);
        } catch (e) {
          this.$message.warning(this.$t('public.regIllegal'));
          return;
        }
        this.valiableSearchInput = this.searchInput;
        this.multiSelectedItemNames = {};
        let itemSelectAll = true;
        // Filter the tags that do not meet the conditions in the operation bar and hide them
        this.checkListArr.forEach((listItem) => {
          if (reg.test(listItem.label)) {
            listItem.show = true;
            if (listItem.checked) {
              this.multiSelectedItemNames[listItem.label] = true;
            } else {
              itemSelectAll = false;
            }
          } else {
            listItem.show = false;
          }
        });
        // Update the selected status of the Select All button
        if (this.isLimit && !itemSelectAll) {
          itemSelectAll = this.selectedNumber >= this.limitNum;
        }
        this.operateSelectAll = itemSelectAll;
        this.$emit('selectedChange', this.multiSelectedItemNames);
      }, 200);
    },
    /**
     * Item click event
     * @param {Object} listItem Current item object
     */
    listItemClick(listItem) {
      if (
        !listItem ||
        (this.isLimit &&
          this.selectedNumber >= this.limitNum &&
          !listItem.checked)
      ) {
        return;
      }
      listItem.checked = !listItem.checked;
      // Refreshes the selected status of the current label option
      if (listItem.checked) {
        this.multiSelectedItemNames[listItem.label] = true;
        this.selectedNumber++;
      } else {
        if (this.multiSelectedItemNames[listItem.label]) {
          delete this.multiSelectedItemNames[listItem.label];
          this.selectedNumber--;
        }
      }
      // Update the selected status of the Select All button
      let itemSelectAll = true;
      this.checkListArr.some((curListItem) => {
        if (curListItem.show && !curListItem.checked) {
          itemSelectAll = false;
          return true;
        }
      });
      if (this.isLimit && !itemSelectAll) {
        itemSelectAll = this.selectedNumber >= this.limitNum;
      }
      this.operateSelectAll = itemSelectAll;
      // Return a dictionary containing selected items.
      this.$emit('selectedChange', this.multiSelectedItemNames);
    },
    /**
     * Expand or collapse the list of items.
     */
    toggleListFullScreen() {
      this.listFullScreen = !this.listFullScreen;
      if (!this.listFullScreen) {
        this.$nextTick(() => {
          this.resizeCallback();
        });
      }
    },
    /**
     * Updates the dictionary of selected tags.
     * @return {Object} Dictionary containing selected tags
     */
    updateSelectedDic() {
      if (this.searching) {
        return this.multiSelectedItemNames;
      }
      let reg;
      try {
        reg = new RegExp(this.searchInput);
      } catch (e) {
        reg = new RegExp(this.valiableSearchInput);
      }
      this.multiSelectedItemNames = {};
      let itemSelectAll = true;
      if (this.isLimit) {
        this.selectedNumber = 0;
        const loopCount = this.checkListArr.length;
        for (let i = 0; i < loopCount; i++) {
          const listItem = this.checkListArr[i];
          if (reg.test(listItem.label)) {
            listItem.show = true;
            if (this.selectedNumber >= this.limitNum) {
              listItem.checked = false;
              itemSelectAll = false;
            } else if (listItem.checked) {
              this.multiSelectedItemNames[listItem.label] = true;
              this.selectedNumber++;
            } else {
              itemSelectAll = false;
            }
          } else {
            listItem.show = false;
          }
        }
        if (!itemSelectAll && this.selectedNumber >= this.limitNum) {
          itemSelectAll = true;
        }
      } else {
        this.checkListArr.forEach((listItem) => {
          if (reg.test(listItem.label)) {
            listItem.show = true;
            if (listItem.checked) {
              this.multiSelectedItemNames[listItem.label] = true;
            } else {
              itemSelectAll = false;
            }
          } else {
            listItem.show = false;
          }
        });
      }
      this.operateSelectAll = itemSelectAll;
      this.resizeCallback();
      return this.multiSelectedItemNames;
    },
  },
  destroyed() {
    // Remove the listener of window size change
    window.removeEventListener('resize', this.resizeCallback);
    // Remove filter timer
    if (this.searchInputTimer) {
      clearTimeout(this.searchInputTimer);
      this.searchInputTimer = null;
    }
  },
};
</script>
<style lang="scss">
.cl-checklist-container {
  width: 100%;
  height: 100%;
  .select-content {
    display: flex;
    align-items: center;
    .title {
      font-size: 14px;
      vertical-align: middle;
      flex-shrink: 0;
    }
    .select-all {
      cursor: pointer;
      flex-shrink: 0;
    }
    .select-item-content {
      display: flex;
      height: 16px;
      flex-wrap: wrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .select-content-open {
      flex: 1;
      text-align: right;
      font-size: 14px;
      color: #00a5a7;
      cursor: pointer;
      min-width: 60px;
    }
  }
  .select-content-all {
    max-height: 150px;
    padding-left: 72px;
    overflow-x: hidden;
    display: flex;
    flex-wrap: wrap;
    .label-item {
      line-height: 14px;
    }
    .select-item {
      height: 25px;
      margin-top: 25px;
    }
  }
  .select-item {
    margin-right: 20px;
    flex-shrink: 0;
    margin-bottom: 1px;
    .label-item {
      width: 100px;
      display: block;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      text-align: left;
      position: relative;
      .loading-icon {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        text-align: center;
        background: rgba(255, 255, 255, 0.5);
        i {
          font-weight: bold;
        }
      }
    }
  }
  .item-disable {
    cursor: not-allowed;
    opacity: 0.5;
  }
  .item-able {
    cursor: pointer;
  }
  .multiCheckBox-border {
    width: 16px;
    height: 16px;
    display: block;
    margin-right: 20px;
    float: left;
  }
  .checkbox-checked {
    background-image: url('../assets/images/mult-select.png');
  }
  .checkbox-unchecked {
    background-image: url('../assets/images/mult-unselect.png');
  }
  .label-item {
    font-size: 14px;
    line-height: 14px;
    vertical-align: middle;
    .el-tooltip {
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      text-align: left;
      height: 16px;
    }
    span {
      font-size: 14px;
      line-height: 14px;
      display: block;
    }
  }
  .mr24 {
    margin-right: 24px;
  }
  .select-disable {
    -moz-user-select: none; /*Firefox*/
    -webkit-user-select: none; /*webkitbrowser*/
    -ms-user-select: none; /*IE10*/
    -khtml-user-select: none; /*Early browser*/
    user-select: none;
  }
  .search-input-item {
    width: 261px;
  }
}
.tooltip-show-content {
  max-width: 50%;
}
</style>
