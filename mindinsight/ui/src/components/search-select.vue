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
  <div class="cl-search-select"
       ref="selector"
       @click="mouseClick($event)"
       tabindex="0"
       @keyup.enter="enter">
    <div class="cl-search-select-inner"
         :class="{'is-focus': ifFocus}"
         @click="click">
      <!-- Multiple Choice -->
      <template v-if="multiple">
        <div class="mul-tag"
             v-if="indexes.length > 0">
          <div class="mul-tag-content"
               :title="options[indexes[0]].label"
               :style="{'text-overflow': overflow}">
            {{options[indexes[0]].label}}
          </div>
          <div class="mul-tag-del"
               @click="cancelLabel($event, indexes[0])"
               v-if="cancel && !options[indexes[0]].disabled">
            <i class="el-icon-close"></i>
          </div>
        </div>
        <div v-else>
          {{sPlaceholder}}
        </div>
        <div v-if="indexes.length > 1"
             class="mul-tag">
          <div class="mul-tag-content">
            +{{indexes.length - 1}}
          </div>
        </div>
      </template>
      <!-- Single choice -->
      <template v-else>
        <div class="single-tag"
             :style="{'text-overflow': overflow}">
          {{indexes.length > 0 ? options[indexes[0]].label : sPlaceholder}}
        </div>
      </template>
    </div>
    <div class="select-container"
         :style="{
           'top': containerTop,
           'left': containerLeft,
           'min-width': containerWidth,
         }"
         v-show="ifActive">
      <!-- Filter Line -->
      <div class="filter-container">
        <el-input v-model="filter"
                  clearable
                  class="has-gap">
        </el-input>
        <span class="has-gap"
              :class="{'able': functionAble, 'disable': !functionAble}"
              @click="selectAll"
              v-if="multiple">{{$t('public.selectAll')}}</span>
        <span @click="clearAll"
              :class="{'able': functionAble, 'disable': !functionAble}"
              v-if="multiple">
          {{$t('public.clear')}}</span>
      </div>
      <div class="option-container"
           ref="options">
        <div v-for="(option, index) in options"
             :key="option.label"
             :value="option.value"
             v-show="option.show"
             class="select-option"
             :class="{
                'is-selected': option.selected,
                'is-disabled': option.disabled,
              }"
             @click="optionClick(option, index)">
          <div class="label-container"
               :title="option.label">{{option.label}}</div>
          <div class="icon-container">
            <i class="el-icon-check"
               :class="{'icon-no-selected': !option.selected}"></i>
          </div>
        </div>
      </div>
      <div class="option-empty"
           v-show="ifEmpty">
        {{$t('public.emptyData')}}
      </div>
    </div>
  </div>
</template>

<script>
/**
 * The publicStore holds the key of focused selector
 * When there is more than two component in same page, help selector to keep correct display
 */
const publicStore = {
  activeKey: {
    key: '',
  },
};
export default {
  props: {
    multiple: {
      type: Boolean,
      default: false,
    }, // If open multiple choice
    sPlaceholder: {
      type: String,
      default: '',
    }, // The placeholder of selector
    iPlaceholder: {
      type: String,
      default: '',
    }, // The placeholder of filter input
    overflow: {
      type: String,
      default: 'none',
    }, // The display way of overflow selected label('none' or 'ellipsis')
    cancel: {
      type: Boolean,
      default: true,
    }, // If the tag can be cancel by icon, only effective when multiple is true
    plain: {
      type: Boolean,
      default: false,
    }, // Represents whether the type of the incoming array, 'true' stands for 'String', 'false' stands for 'Object'
    source: {
      type: Array,
      default: () => {
        return [];
      },
    }, // The total data source of component
    labelName: {
      type: String,
      default: 'label',
    }, // The name of the property representing label in the object
    valueName: {
      type: String,
      default: 'value',
    }, // The name of the property representing value in the object
    disabledName: {
      type: String,
      default: 'disabled',
    }, // The name of the property representing disabled in the object
    selectedName: {
      type: String,
      default: 'selected',
    }, // The name of the property representing selected in the object
  },
  data() {
    return {
      ifFocus: false, // When the selector is focused, the options area may not display
      ifActive: false, // When the selector is active, the options area must display
      options: [], // The option list after processing original data
      containerTop: 0, // The top to set container position
      containerLeft: 0, // The left to set container position
      containerWidth: 0, // The min-width of container
      containerToSelector: 12, // The gap between options-container and selector
      functionAble: true, // The effective of button after input
      // The key of component to make sure it can be distinguished from publicStore
      key: new Date().getTime().toString(),
      filter: '', // The value to filter the option
      ifEmpty: true, // If no option match the filter
      activeKey: undefined, // In order to add wacter to the publicStore.activeKey.key
      latestIndex: undefined, // The index of the last click option, only effective when multiple is false
      indexes: [], // The list of index of selected options
      filterDebounce: 150, // The filter watcher debounce time in ms
    };
  },
  methods: {
    /**
     * The logic of calculate values or value
     * @return {Array | String | Number}
     */
    calValues() {
      if (this.multiple) {
        const values = [];
        for (let i = 0; i < this.indexes.length; i++) {
          values.push(this.options[this.indexes[i]].value);
        }
        return values;
      } else {
        return this.options[this.indexes[0]].value;
      }
    },
    /**
     * The logic of enter down
     */
    enter() {
      this.ifFocus = false;
      this.ifActive = false;
      this.$emit('selectEnter');
    },
    /**
     * The logic of click the display area of selector, excluding the options area
     */
    click() {
      this.ifActive = !this.ifActive;
      this.ifFocus = true;
    },
    /**
     * The logic of click event that add to window, which can make response to defocus
     */
    clickHandler() {
      if (this.ifFocus) {
        this.ifFocus = false;
        this.ifActive = false;
        this.$emit('selectBlur');
      }
    },
    /**
     * The logic of click the selector, including everywhere
     * @param {Object} event
     */
    mouseClick(event) {
      publicStore.activeKey.key = this.key;
      event.stopPropagation();
      event.preventDefault();
    },
    /**
     * The logic of click selectAll button
     */
    selectAll() {
      if (!this.functionAble) {
        return;
      }
      this.indexes = [];
      for (let i = 0; i < this.options.length; i++) {
        if (this.options[i].disabled) {
          if (this.options[i].selected) {
            this.indexes.push(i);
          }
        } else {
          this.mulSelectOption(this.options[i], i);
        }
      }
    },
    /**
     * The logic of click clearAll button
     */
    clearAll() {
      if (!this.functionAble) {
        return;
      }
      const indexes = [];
      for (let i = 0; i < this.indexes.length; i++) {
        const option = this.options[this.indexes[i]];
        if (option.disabled) {
          indexes.push(i);
        } else {
          option.selected = false;
        }
      }
      this.indexes = indexes;
    },
    /**
     * The logic of process original data when group is false
     * @param {Array} data
     * @return {Array}
     */
    processDefault(data) {
      const options = [];
      if (!this.plain) {
        for (let i = 0; i < data.length; i++) {
          options.push({
            label: data[i][this.labelName],
            value: data[i][this.valueName],
            disabled: data[i][this.disabledName] === true ? true : false,
            selected: data[i][this.selectedName] === true ? true : false,
            show: true,
          });
          if (options[i].selected) {
            this.indexes.push(i);
          }
        }
      } else {
        for (let i = 0; i < data.length; i++) {
          options.push({
            label: data[i],
            value: data[i],
            disabled: false,
            selected: false,
            show: true,
          });
        }
      }
      return options;
    },
    /**
     * The logic of process original data
     * @param {Array} data
     * @return {Array}
     */
    processData(data) {
      return this.processDefault(data);
    },
    /**
     * The logic of deselect option when multiple is true
     * @param {Object} option
     * @param {Number} index
     */
    mulDeselectOption(option, index) {
      return new Promise((resolve) => {
        const indexTemp = this.indexes.indexOf(index);
        this.indexes.splice(indexTemp, 1);
        option.selected = false;
        this.$nextTick(() => {
          resolve(true);
        });
      });
    },
    /**
     * The logic of select option when multiple is true
     * @param {Object} option
     * @param {Number} index
     */
    mulSelectOption(option, index) {
      this.indexes.push(index);
      option.selected = true;
    },
    /**
     * The logic of click option
     * @param {Object} option
     * @param {Number} index
     */
    optionClick(option, index) {
      if (option.disabled) {
        return;
      }
      if (option.selected) {
        if (this.multiple) {
          this.mulDeselectOption(option, index);
        } else {
          // Single choice not allowed to deselect directly, do this by selecting other options
          return;
        }
      } else {
        if (this.multiple) {
          this.mulSelectOption(option, index);
        } else {
          this.indexes[0] = index;
          // When multiple is false, there is at most one option can have 'selected' true
          if (typeof this.latestIndex === 'number') {
            this.options[this.latestIndex].selected = false;
          }
          this.latestIndex = index;
          return;
        }
      }
    },
    /**
     * The logic of click cancel icon
     * @param {Object} event
     * @param {Number} index
     */
    cancelLabel(event, index) {
      event.stopPropagation();
      event.preventDefault();
      this.mulDeselectOption(this.options[index], index).then(() => {
        if (!this.ifActive) {
          this.$emit('cancelLabel');
        }
      });
    },
  },
  created() {
    if (this.source.length > 0) {
      this.options = this.processData(this.source);
      this.ifEmpty = false;
    }
    this.activeKey = publicStore.activeKey;
    window.addEventListener('click', this.clickHandler);
  },
  mounted() {
    // Calculate position and width of options container
    if (this.$refs.selector) {
      const styleList = getComputedStyle(this.$refs.selector);
      const height = styleList['height'].replace('px', '');
      const minWidth = styleList['width'];
      this.containerTop = `${parseInt(height) + this.containerToSelector}px`;
      this.containerWidth = minWidth;
    }
  },
  watch: {
    // The watcher of filter,to filter options and control ifEmpty after filtered
    filter(newVal) {
      if (newVal !== '') {
        this.functionAble = false;
      } else {
        this.functionAble = true;
      }
      clearTimeout(this.filterTimer);
      this.filterTimer = setTimeout(() => {
        for (let i = 0; i < this.options.length; i++) {
          if (this.options[i].label.indexOf(newVal) < 0) {
            this.options[i].show = false;
          } else {
            this.options[i].show = true;
          }
        }
        this.$nextTick(() => {
          if (this.$refs.options) {
            if (getComputedStyle(this.$refs.options)['height'] === '0px') {
              this.ifEmpty = true;
            } else {
              this.ifEmpty = false;
            }
          }
        });
      }, this.filterDebounce);
    },
    // The watcher of source can process asynchronous data input, or make response when original data changed
    'source': {
      handler(newVal) {
        this.indexes = [];
        this.options = this.processData(newVal);
        this.ifEmpty = false;
      },
    },
    // The watcher of activeKey to keep the selector in right state
    'activeKey.key': {
      handler(newVal) {
        if (newVal !== this.key) {
          this.ifFocus = false;
          this.ifActive = false;
        }
      },
    },
    'indexes': {
      handler() {
        this.$nextTick(() => {
          this.$emit('selectedUpdate', this.calValues());
        });
      },
    },
  },
  beforeDestroy() {
    window.removeEventListener('click', this.clickHandler);
  },
};
</script>
<style>
.cl-search-select .filter-container .el-input {
  width: 0;
  flex-grow: 1;
}
.cl-search-select .filter-container .el-input .el-input__inner {
  padding: 0 9px;
}
</style>
<style scoped>
.cl-search-select {
  height: 100%;
  width: 100%;
  position: relative;
}
.cl-search-select .cl-search-select-inner {
  height: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 1px;
  background-color: #fff;
  color: #606266;
  padding: 0 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.cl-search-select .is-focus {
  border-color: #00a5a7;
}
.cl-search-select .mul-tag {
  height: 24px;
  padding: 0 4px 0 8px;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  background-color: #f4f4f5;
  border-color: #e9e9eb;
  margin-right: 6px;
  max-width: 70%;
  display: flex;
  align-items: center;
}
.cl-search-select .mul-tag .mul-tag-content {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  color: #909399;
  margin-right: 4px;
}
.cl-search-select .mul-tag .mul-tag-del {
  font-size: 12px;
  background-color: #c0c4cc;
  min-height: 12.8px;
  min-width: 12.8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.cl-search-select .mul-tag .mul-tag-del:hover {
  background-color: #909399;
}
.cl-search-select .mul-tag .mul-tag-del .el-icon-close {
  color: #909399;
}
.cl-search-select .mul-tag .mul-tag-del .el-icon-close:hover {
  color: #fff;
}
.cl-search-select .single-tag {
  flex-wrap: nowrap;
  overflow: hidden;
}
.cl-search-select .select-container {
  position: absolute;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  margin: 5px 0;
  display: flex;
  flex-direction: column;
  max-height: 244px;
  z-index: 9998;
}
.cl-search-select .select-container .filter-container {
  margin-top: 4px;
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 10px;
}
.cl-search-select .select-container .filter-container .has-gap {
  margin-right: 6px;
}
.cl-search-select .select-container .filter-container .able {
  color: #00a5a7;
  cursor: pointer;
}
.cl-search-select .select-container .filter-container .disable {
  color: #c3c3c3;
  cursor: not-allowed;
}
.cl-search-select .select-container .option-container {
  overflow-x: hidden;
  overflow-y: scroll;
}
.cl-search-select .select-container .option-container .select-option {
  padding: 0 20px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}
.cl-search-select .select-container .option-container .select-option:hover {
  background-color: #f5f7fa;
}
.cl-search-select
  .select-container
  .option-container
  .select-option
  .label-container {
  white-space: nowrap;
  max-width: 320px;
  text-overflow: ellipsis;
  overflow: hidden;
}
.cl-search-select
  .select-container
  .option-container
  .select-option
  .icon-container {
  width: 14px;
}
.cl-search-select
  .select-container
  .option-container
  .select-option
  .icon-container
  .icon-no-selected {
  display: none;
}
.cl-search-select .select-container .option-container .is-selected {
  color: #00a5a7;
}
.cl-search-select .select-container .option-container .is-disabled {
  color: #c0c4cc;
  cursor: not-allowed !important;
}
.cl-search-select .select-container .option-container::-webkit-scrollbar {
  cursor: pointer;
  width: 6px;
}
.cl-search-select .select-container .option-container::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px #fff;
  background-color: #fff;
  border-radius: 3px;
}
.cl-search-select .select-container .option-container::-webkit-scrollbar-thumb {
  border-radius: 7px;
  -webkit-box-shadow: inset 0 0 6px rgba(144, 147, 153, 0.3);
  background-color: #e8e8e8;
}
.cl-search-select
  .select-container
  .option-container::-webkit-scrollbar-thumb:hover {
  -webkit-box-shadow: inset 0 0 6px rgba(144, 147, 153, 0.3);
  background-color: #cacaca;
  border-radius: 3px;
}
.cl-search-select .select-container .option-empty {
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
