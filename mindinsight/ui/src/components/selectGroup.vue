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
  <div class="cl-checkboxes-container">
    <!-- Title -->
    <div class="checkboxes-title left"
         v-if="typeof title !== 'undefined'">
      {{title}}
    </div>
    <!-- Group -->
    <div class="right">
      <el-tooltip v-for="checkbox in checkboxes"
                  :key="checkbox.label"
                  effect="dark"
                  :content="checkbox.label"
                  placement="top">
        <div class="checkboxes-item item"
             @click="checkedChange(checkbox)">
          <div class="checkbox"
               :class="{'is-checked': checkbox.checked, 'is-unchecked': !checkbox.checked}">
          </div>
          <div class="label">
            {{checkbox.label}}
          </div>
        </div>
      </el-tooltip>
      <!-- Slot -->
      <div class="checkboxes-last item">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    // Array<Checkbox>
    // Class Checkbox {checked: boolean, label: string}
    checkboxes: Array,
    title: String, // The title of group
  },
  data() {
    return {
      checkedList: [],
    };
  },
  watch: {
    checkboxes() {
      this.initCheckedList(this.checkboxes);
    },
  },
  methods: {
    /**
     * The logic when checkbox click
     * @param {Object} checkbox Checkbox object
     */
    checkedChange(checkbox) {
      checkbox.checked = !checkbox.checked;
      this.updateCheckedList(this.checkboxes);
      this.$emit('updateCheckedList', this.checkedList);
    },
    /**
     * The logic of init checked checkbox list
     * @param {Object} checkboxes Checkbox list
     */
    initCheckedList(checkboxes) {
      if (typeof checkboxes !== 'undefined' && Array.isArray(checkboxes)) {
        this.updateCheckedList(checkboxes);
      }
      this.$emit('updateCheckedList', this.checkedList);
    },
    /**
     * The logic of update checked checkbox list
     * @param {Object} checkboxes Checkbox list
     */
    updateCheckedList(checkboxes) {
      this.checkedList = [];
      for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
          this.checkedList.push(checkboxes[i].label ? checkboxes[i].label : '');
        }
      }
    },
  },
};
</script>
<style lang="scss" scoped>
.cl-checkboxes-container {
  display: flex;
  .left {
    width: 100px;
    min-width: 100px;
    .checkboxes-title {
      line-height: 22px;
      font-size: 14px;
      color: #333333;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }
  .right {
    flex-shrink: 1;
    display: flex;
    flex-wrap: wrap;
    .checkboxes-item {
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      .checkbox {
        height: 16px;
        width: 16px;
        margin-right: 16px;
      }
      .label {
        width: 100px;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
        font-size: 14px;
        color: #333333;
      }
      .is-checked {
        background-image: url('../assets/images/mult-select.png');
      }
      .is-unchecked {
        background-image: url('../assets/images/mult-unselect.png');
      }
    }
  }
  .item {
    padding-bottom: 10px;
    margin-right: 20px;
    height: 32px;
  }
}
</style>
