<!--
Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
      {{ title }}
    </div>
    <!-- Group -->
    <div class="right">
      <el-tooltip v-for="checkbox in checkboxes"
                  :key="checkbox.label"
                  effect="dark"
                  :content="
          checkbox.label + (typeof checkbox.title === 'string' && checkbox.title !== ''
            ? ($t('symbols.comma') + checkbox.title)
            : '')
        "
                  placement="top">
        <template v-if="typeof checkbox.disabled === 'boolean' && checkbox.disabled">
          <div class="checkboxes-item item item-disabled">
            <div class="checkbox is-disabled"></div>
            <div class="label label-disabled">
              {{ checkbox.label }}
            </div>
          </div>
        </template>
        <template v-else>
          <div class="checkboxes-item item"
               @click="checkedChange(checkbox)">
            <div class="checkbox"
                 :class="{
                'is-checked': checkbox.checked,
                'is-unchecked': !checkbox.checked,
              }"></div>
            <div class="label"
                 :title="typeof checkbox.title === 'string' ? checkbox.title : ''">
              {{ checkbox.label }}
            </div>
          </div>
        </template>
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
    /** The structure of checkboxes should be Array<Checkbox>
    *   The structure of Checkbox should as follow
    *   Class Checkbox {
    *     checked: boolean,
    *     label: string,
    *     title?: string,
    *     disabled?: Boolean,
    *   }
    */
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
<style scoped>
.cl-checkboxes-container {
  display: flex;
}
.cl-checkboxes-container .left {
  width: 100px;
  min-width: 100px;
}
.cl-checkboxes-container .left .checkboxes-title {
  line-height: 22px;
  font-size: 14px;
  color: #333333;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.cl-checkboxes-container .right {
  flex-shrink: 1;
  display: flex;
  flex-wrap: wrap;
}
.cl-checkboxes-container .right .checkboxes-item {
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}
.cl-checkboxes-container .right .checkboxes-item .checkbox {
  height: 16px;
  width: 16px;
  margin-right: 16px;
}
.cl-checkboxes-container .right .checkboxes-item .label {
  width: 100px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  font-size: 14px;
  color: #333333;
}
.cl-checkboxes-container .right .checkboxes-item .label-disabled {
  color: #c0c4cc;
}
.cl-checkboxes-container .right .checkboxes-item .is-checked {
  background-image: url("../assets/images/mult-select.png");
}
.cl-checkboxes-container .right .checkboxes-item .is-unchecked {
  background-image: url("../assets/images/mult-unselect.png");
}
.cl-checkboxes-container .right .checkboxes-item .is-disabled {
  border: 1px solid #dbdbdb;
  background-color: #e7e7e7;
}
.cl-checkboxes-container .item {
  padding-bottom: 10px;
  margin-right: 20px;
  height: 32px;
}
.cl-checkboxes-container .item-disabled {
  cursor: not-allowed !important;
}
.cl-checkboxes-container .checkboxes-last {
  display: flex;
  align-items: center;
}
</style>
