<template>
  <el-select v-model="selectedLabels"
             :placeholder="$t('public.select')"
             :multiple="typeof multiple !== 'undefined' ? multiple : false"
             :collapse-tags="typeof collapseTags !== 'undefined' ? collapseTags : false"
             class="cl-search-select">
    <div class="cl-search-select-action">
      <el-input v-model="filter"
                :placeholder="$t('public.enter')"
                id="search-select-valid"
                class="action-gap"
                clearable></el-input>
      <span class="action-gap"
            :class="{'able': functionAble, 'disable': !functionAble}"
            @click="selectAll"
            v-if="multiple">{{$t('public.selectAll')}}</span>
      <span @click="clearAll"
            :class="{'able': functionAble, 'disable': !functionAble}"
            v-if="multiple">
        {{$t('public.clear')}}</span>
    </div>
    <slot v-if="!ifReady" name="oriData"></slot>
    <!-- Option -->
    <template v-if="type === 'option'">
      <el-option v-for="option of options"
                 :key="option.label"
                 :label="option.label"
                 :value="option.value"
                 :disabled="typeof option.disabled !== 'undefined' ? option.disabled : false">
      </el-option>
    </template>
    <!-- Group -->
    <template v-else>
      <el-option-group v-for="group in groups"
                       :key="group.label"
                       :label="group.label"
                       :disabled="typeof group.disabled !== 'undefined' ? group.disabled : false">
        <el-option v-for="option in group.options"
                   :key="option.value"
                   :label="option.label"
                   :value="option.value"
                   :disabled="typeof option.disabled !== 'undefined' ? option.disabled : false">
        </el-option>
      </el-option-group>
    </template>
    <div slot="empty">
      <div class="cl-search-select-action cl-search-select-empty">
        <el-input v-model="filter"
                  :placeholder="$t('public.enter')"
                  id="search-select-empty"
                  class="action-gap"
                  clearable></el-input>
        <span class="action-gap"
              :class="{'able': functionAble, 'disable': !functionAble}"
              @click="selectAll"
              v-if="multiple">{{$t('public.selectAll')}}</span>
        <span @click="clearAll"
              :class="{'able': functionAble, 'disable': !functionAble}"
              v-if="multiple">
          {{$t('public.clear')}}</span>
      </div>
      <div class="cl-search-select-nodata">{{$t('public.emptyData')}}</div>
    </div>
  </el-select>
</template>

<script>
export default {
  props: {
    type: String, // 'option' | 'group'
    collapseTags: Boolean, // If open the collapse tags
    multiple: Boolean, // If open the multiple
    slotReady: Boolean, // If the slot loading is asynchronous, should let the component know the state of slot
  },
  data() {
    return {
      includes: undefined, // If the String.prototype.includes() is useful
      ifReady: false, // If the option is ready
      selectedLabels: undefined, // The selected labels
      filter: '', // The value to filter the option
      functionAble: false, // If the selectAll and clearAll button accessible
      optionsTemp: [], // The options template includes all options
      groupsTemp: [], // The groups template includes all groups and options
      options: [], // The source of el-option that actually displayed
      groups: [], // The source of el-option-group that actually displayed
    };
  },
  watch: {
    /**
     * The logic to init the options when slot is ready
     * @param {Boolean} val
     */
    slotReady(val) {
      if (val) {
        this.$nextTick(() => {
          if (this.$slots.oriData) {
            this.init(this.type, this.$slots.oriData);
          } else {
            throw new Error('Wrong time');
          }
        });
      }
    },
    /**
     * The logic to filter options
     * @param {String} val The input word
     */
    filter(val) {
      if (val !== '') {
        this.functionAble = false;
      } else {
        this.functionAble = true;
      }
      if (this.type === 'option') {
        this.options = this.optionsTemp.filter((option) => {
          if (this.includes) {
            return option.label.includes(val);
          } else {
            return option.label.indexOf(val) >= 0;
          }
        });
      } else {
        for (let i = 0; i < this.groupsTemp.length; i++) {
          this.groups[i] = Object.assign({}, this.groupsTemp[i]);
          this.groups[i].options = this.groupsTemp[i].options.filter(
              (option) => {
                if (this.includes) {
                  return option.label.includes(val);
                } else {
                  return option.label.indexOf(val) >= 0;
                }
              },
          );
        }
        this.groups = this.groups.filter((val) => {
          return val.options.length !== 0;
        });
      }
      this.$nextTick(() => {
        if (this.type === 'option') {
          this.refocus(this.options.length);
        } else {
          this.refocus(this.groups.length);
        }
      });
    },
    /**
     * The logic executed when selected labels changed
     * @param {String} val The input word
     */
    selectedLabels(val) {
      this.$emit('selectedUpdate', val);
    },
  },
  methods: {
    /**
     * The logic of click selectAll
     */
    selectAll() {
      if (!this.functionAble) {
        return;
      }
      this.selectedLabels = [];
      if (this.type === 'option') {
        this.optionsTemp.forEach((element) => {
          this.selectedLabels.push(element.value);
        });
      } else {
        for (let i = 0; i < this.groupsTemp.length; i++) {
          this.groupsTemp[i].options.forEach((element) => {
            this.selectedLabels.push(element.value);
          });
        }
      }
    },
    /**
     * The logic of click clear
     */
    clearAll() {
      if (!this.functionAble) {
        return;
      }
      this.selectedLabels = [];
    },
    /**
     * The logic of init options by slot data when type is opitons
     * @param {Array<Object>} vnodes
     */
    initOptions(vnodes) {
      this.optionsTemp = [];
      for (let i = 0; i < vnodes.length; i++) {
        this.optionsTemp[i] = Object.assign(
            {},
            vnodes[i].componentOptions.propsData,
        );
      }
      this.options = Array.from(this.optionsTemp);
      this.functionAble = true;
      this.ifReady = true;
    },
    /**
     * The logic of init options by slot data when type is groups
     * @param {Array<Object>} vnodes
     */
    initGroups(vnodes) {
      this.groupsTemp = [];
      for (let i = 0; i < vnodes.length; i++) {
        this.groupsTemp[i] = Object.assign(
            {},
            vnodes[i].componentOptions.propsData,
        );
        this.groupsTemp[i].options = [];
        for (let j = 0; j < vnodes[i].componentOptions.children.length; j++) {
          this.groupsTemp[i].options[j] = Object.assign(
              {},
              vnodes[i].componentOptions.children[j].componentOptions.propsData,
          );
        }
      }
      this.groups = Array.from(this.groupsTemp);
      this.functionAble = true;
      this.ifReady = true;
    },
    /**
     * The logic of init options by slot data when type is groups
     * @param {number} length The filter word length
     */
    refocus(length) {
      if (length === 0) {
        const dom = document.getElementById('search-select-empty');
        if (dom) {
          dom.focus();
        }
      } else {
        const dom = document.getElementById('search-select-valid');
        if (dom) {
          dom.focus();
        }
      }
    },
    /**
     * The logic of init options by slot data
     * @param {String} type The type
     * @param {Array<Object>} slots
     */
    init(type, slots) {
      if (type === 'option') {
        this.initOptions(slots);
      } else if (type === 'group') {
        this.initGroups(slots);
      } else {
        throw new Error(
            `Wrong type. The value of type can only be one of 'option' or 'group'`,
        );
      }
    },
  },
  created() {
    if (this.multiple) {
      this.selectedLabels = '';
    } else {
      this.selectedLabels = [];
    }
    if (typeof String.prototype.includes !== 'function') {
      this.includes = false;
    } else {
      this.includes = true;
    }
  },
  mounted() {
    if (typeof this.slotReady === 'undefined') {
      if (this.$slots.oriData) {
        this.init(this.type, this.$slots.oriData);
      } else {
        throw new Error('Slot is not ready.');
      }
    }
  },
};
</script>

<style lang="scss">
.cl-search-select {
  width: 100%;
}
.cl-search-select-action {
  padding-right: 10px;
  padding-left: 10px;
  display: flex;
  align-items: center;
  .el-input {
    width: 0;
    flex-grow: 1;
    .el-input__inner {
      padding: 0 9px;
    }
  }
  .action-gap {
    margin-right: 6px;
  }
  .able {
    color: #00a5a7;
    cursor: pointer;
  }
  .disable {
    color: #c3c3c3;
    cursor: not-allowed;
  }
}
.cl-search-select-empty {
  padding-top: 6px;
}
.cl-search-select-nodata {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48px;
}
</style>
