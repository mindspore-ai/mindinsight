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
<script>
export default {
  data() {
    return {
      autoUpdateTimer: null, // Automatic refresh timer
      isReloading: false, // Refreshing
    };
  },
  computed: {
    /**
     * Global refresh
     * @return {Boolen}
     */

    isReload() {
      return this.$store.state.isReload;
    },
    /**
     * Auto refresh
     * @return {Boolen}
     */

    isTimeReload() {
      return this.$store.state.isTimeReload;
    },

    timeReloadValue() {
      return this.$store.state.timeReloadValue;
    },
  },
  watch: {
    /**
     * Listener global refresh
     * @param {Boolen} newVal New value
     * @param {Boolen} oldVal Old value
     */

    isReload(newVal, oldVal) {
      if (newVal) {
        this.isReloading = true;
        // Retiming
        if (this.isTimeReload) {
          this.autoUpdateSamples();
        }
        this.updateAllData(false);
      }
    },
    /**
     * Listener auto refresh
     * @param {Boolen} newVal New value
     * @param {Boolen} oldVal Old value
     */

    isTimeReload(newVal, oldVal) {
      if (newVal) {
        this.autoUpdateSamples();
      } else {
        this.stopUpdateSamples();
      }
    },
    /**
     * The refresh time is changed
     */

    timeReloadValue() {
      this.autoUpdateSamples();
    },
  },
  methods: {
    /**
     * Enable automatic refresh
     */

    autoUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
      this.autoUpdateTimer = setInterval(() => {
        this.$store.commit('clearToken');
        this.updateAllData(true);
      }, this.timeReloadValue * 1000);
    },

    /**
     * Disable automatic refresh
     */

    stopUpdateSamples() {
      if (this.autoUpdateTimer) {
        clearInterval(this.autoUpdateTimer);
        this.autoUpdateTimer = null;
      }
    },
  },
  destroyed() {
    // Disable the automatic refresh timer
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
      this.autoUpdateTimer = null;
    }
  },
};
</script>
