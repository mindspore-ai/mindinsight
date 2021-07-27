/**
 * Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import CommonProperty from '../common/common-property';

export const useEChartsTheme = (themeIndex) => {
  const chartTheme = CommonProperty.commonChartTheme[themeIndex];

  const axisTheme = {
    nameTextStyle: {
      color: chartTheme.axisLabelColor,
    },
    axisLabel: {
      color: chartTheme.axisLabelColor,
    },
    axisLine: {
      lineStyle: {
        color: chartTheme.axisLineColor,
        width: 2,
      },
    },
    splitLine: {
      lineStyle: {
        color: chartTheme.splitLineColor,
      },
    },
  };

  return {
    legend: {
      textStyle: {
        color: chartTheme.legendTextColor,
      },
    },
    tooltip: {
      backgroundColor: chartTheme.tooltipBgColor,
      borderWidth: 0,
      textStyle: {
        color: chartTheme.tooltipFontColor,
      },
    },
    dataZoom: {
      fillerColor: chartTheme.dataZoomFillerColor,
      borderColor: chartTheme.dataZoomBorderColor,
      backgroundColor: chartTheme.dataZoomBgColor,
    },
    timeAxis: axisTheme,
    logAxis: axisTheme,
    valueAxis: axisTheme,
    categoryAxis: axisTheme,
  };
};
