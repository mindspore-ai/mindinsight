<!--
Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.

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
  <div class="mi-contour-map">
    <div class="map-content"
         ref="contour"></div>
    <div class="map-animation" v-if="showAnimation">
      <span class="animation-button"
            @click="playPathAnimation">
        <span class="el-icon-video-play"></span>
        {{$t('lossAnalysis.playTrackAnimation')}}
      </span>
    </div>
    <div v-if="showLegend"
         class="map-legend"
         :style="{
           'grid-template-rows': `repeat(${legendColors.length + 1}, 1fr)`,
         }">
      <div v-for="(color, index) in legendColors"
           :key="color[1]"
           class="legend-item">
        <div :class="[
               'legend-color',
               isArea ? 'topographic-color' : 'contour-color',
             ]">
          <div :style="{backgroundColor: color[1]}"
               class="color"></div>
        </div>
        <div class="text">{{ ((index + 1) % ~~(legendColors.length / 5) === 0) ? color[0] : '' }}</div>
      </div>
      <div class="legend-title">{{ $t('lossAnalysis.lossValue') }}</div>
    </div>
  </div>
</template>

<script>
/**
 * Class of echarts custom text item
 */
class ContourLabel {
  type = 'text';
  x;
  y;
  z2 = chartZIndexMap[CONTOUR_LABEL];
  rotation;
  transition = [];
  style = {
    x: null,
    y: null,
    text: null,
    fill: null,
  };
  /**
   * @param {string} value
   * @param {string} color
   * @param {Array} prev [x, y]
   * @param {Array} next [x, y]
   */
  constructor(value, color, prev, next) {
    this.style.text = value;
    this.style.fill = color;
    this.x = (prev[0] + next[0]) / 2;
    this.y = (prev[1] + next[1]) / 2;
    const {rotation, x, y} = calLabelTransform(prev, next);
    if (rotation) this.rotation = rotation;
    if (x) this.style.x = x;
    if (y) this.style.y = y;
  }
}

/**
 * Calculate label transform
 * @param {number} x1
 * @param {number} y1
 * @param {number} x2
 * @param {number} y2
 * @return {Object} {rotation, x, y}
 */
function calLabelTransform([x1, y1], [x2, y2]) {
  const x1Large = x1 >= x2;
  const y1Large = y1 >= y2;
  let rotation;
  let x;
  const y = -5;
  if (x1Large === y1Large) {
    /**
     * x1Large && y1Large      !x1Large && !y1Large
     *         2                        1
     *          \                        \
     *         label                    label
     *            \                        \
     *             1                        2
     */
    rotation = Math.atan((x1 - x2) / (y1 - y2)) - (Math.PI / 2);
  } else {
    /**
     * x1Large && !y1Large      !x1Large && y1Large
     *         1                        2
     *        /                        /
     *     label                    label
     *      /                        /
     *     2                        1
     */
    rotation = Math.atan((y2 - y1) / (x1 - x2));
  }
  return {rotation, x, y};
}

/**
 * Generate path lines series of contour map chart
 * @param {Array} data
 * @param {Array} lines
 * @param {number} width
 * @param {string} color
 * @param {boolean} transition
 * @return {Object} path lines series
 */
function usePathLines(data, lines, width, color, transition = false) {
  return {
    name: PATH_LINES,
    zlevel: 1,
    type: 'custom',
    silent: true,
    z: chartZIndexMap[PATH_LINES],
    renderItem: (_params, api) => {
      return {
        type: 'group',
        children: lines.map((line) => {
          return {
            type: 'polyline',
            shape: {
              points: [
                api.coord([line[0], line[1]]),
                api.coord([line[2], line[3]]),
              ],
            },
            transition: transition ? ['shape'] : [],
            style: {
              stroke: color,
              lineWidth: width,
            },
          };
        }),
      };
    },
    clip: true,
    data: [data],
  };
}

/**
 * Generate path points series of contour map chart
 * @param {Array} markPoints
 * @param {Array} points
 * @param {number} size
 * @return {Object} path points series
 */
function usePathPoints(markPoints, points, size) {
  return {
    type: 'scatter',
    zlevel: 1,
    name: PATH_POINTS,
    symbol: 'circle',
    symbolSize: size,
    markPoint: {
      data: markPoints,
    },
    itemStyle: {
      opacity: 1,
      color: '#FF8C00',
    },
    animation: false,
    z: chartZIndexMap[PATH_POINTS],
    showSymbol: true,
    data: points,
    tooltip: {
      formatter: (params) => {
        const [x, y, z, epoch] = params.data;
        return `
          epoch: ${epoch}<br>
          x: ${x}<br>
          y: ${y}<br>
          z: ${z}<br>
        `;
      },
    },
  };
}

/**
 * Generate path series of contour map chart
 * @param {Object} path
 * @param {Array} data
 * @param {number} width
 * @param {string} color
 * @return {Object} path series
 */
function usePathSeries(path, data, width, color) {
  const {intervals, x, y, z} = path;
  const lines = [];
  const lastIndex = intervals.length - 1;
  const markPoints = [];
  const points = [];
  intervals.forEach((epoch, index) => {
    if (index === 0) {
      markPoints.push({value: start, xAxis: x[index], yAxis: y[index]});
    }
    if (index === lastIndex) {
      markPoints.push({value: end, xAxis: x[index], yAxis: y[index]});
    }
    points.push([x[index], y[index], z[index], epoch]);
    if (index < lastIndex) {
      lines.push([x[index], y[index], x[index + 1], y[index + 1]]);
    }
  });
  return [
    usePathPoints(markPoints, points, width * 3),
    usePathLines(data, lines, width, color),
  ];
}

/**
 * Calculate tooltip position
 * @param {number} rowIndex
 * @param {number} columnIndex
 * @param {number} lastIndex
 * @return {string}
 */
function calTooltipPosition(rowIndex, columnIndex, lastIndex) {
  if (columnIndex === 0) {
    return 'right';
  }
  if (columnIndex === lastIndex) {
    return 'left';
  }
  if (rowIndex === 0) {
    return 'bottom';
  }
  if (rowIndex === lastIndex) {
    return 'top';
  }
  return 'top';
}
/**
 * Generate points series of contour map chart
 * @param {Array} pointMatrix
 * @param {Object} chartInstance
 * @param {Array} convergencePoint
 * @return {Object} points series
 */
function usePointSeries(pointMatrix, chartInstance, convergencePoint, pointColor) {
  const points = [];
  const lastIndex = pointMatrix.length - 1;
  pointMatrix.forEach((row, r) => {
    points.push(...(row.map((item, c) => {
      return {
        name: `point,${r},${c}`,
        value: [item.x, item.y, item.z],
        position: calTooltipPosition(r, c, lastIndex),
      };
    })));
  });
  return {
    name: POINTS,
    type: 'scatter',
    symbol: 'rect',
    z: chartZIndexMap[POINTS],
    symbolSize: (_value, _params) => {
      if (!chartInstance) return 50;
      const {top, left, bottom, right} = chartInstance._model.option.grid[0];
      const width = (chartInstance.getWidth() - +left - +right) / lastIndex;
      const height = (chartInstance.getHeight() - +top - +bottom) / lastIndex;
      return [width, height];
    },
    data: points,
    itemStyle: {
      opacity: 0,
    },
    animation: false,
    markPoint: convergencePoint ? {
      symbol: 'circle',
      symbolSize: 12,
      itemStyle: {
        color: pointColor,
      },
      data: [
        {
          name: conPoint,
          xAxis: convergencePoint[0],
          yAxis: convergencePoint[1],
        },
      ],
    } : {},
    tooltip: {
      formatter: () => '',
    },
  };
}

/**
 * Generate points tooltip series of contour map chart
 * @param {Array} pointMatrix
 * @param {Object} chartInstance
 * @param {Array} convergencePoint
 * @return {Object} points series
 */
function usePointTooltip(pointMatrix) {
  const points = [];
  pointMatrix.forEach((row) => {
    row.forEach((point) => {
      points.push([point.x, point.y, point.z]);
    });
  });
  return {
    name: 'pointsTooltip',
    type: 'scatter',
    z: chartZIndexMap[POINTS],
    zlevel: 2,
    data: points,
    symbol: 'circle',
    symbolSize: 0,
    silent: true,
    tooltip: {
      padding: [2, 8],
      textStyle: {
        fontSize: 8,
      },
      formatter: (params) => {
        const [x, y, z] = params.data;
        return `
        x: ${x}<br>
        y: ${y}<br>
        z: ${z}<br>
        `;
      },
    },
  };
}

/**
 * Generate labels on contour line of contour map chart
 * @param {number} z
 * @param {Array} line
 * @return {Array} Array of labels
 */
function useLineLabels(z, line) {
  const labels = [];
  const pointCount = line.length;
  const maxLabelCount = ~~Math.sqrt(pointCount);
  if (maxLabelCount === 1) {
    line.forEach((point, index) => {
      const [x, y] = point;
      if (index === 0) {
        const [x2, y2] = line[1];
        const label = new ContourLabel(z, 'gray', [x, y], [x2, y2]);
        labels.push(label);
      }
    });
  } else {
    const labelIndexFactor = ~~(pointCount / maxLabelCount);
    line.forEach((point, index) => {
      const [x, y] = point;
      if (index !== 0 && index !== (pointCount - 1) && index % labelIndexFactor === 0) {
        const nextIndex = index + 1;
        const [x2, y2] =line[nextIndex];
        labels.push(new ContourLabel(z, 'gray', [x, y], [x2, y2]));
      }
    });
  }
  return labels;
}

/**
 * Generate contour area enclosed by no line segments
 * @param {number} index
 * @param {Map} contourColorMap
 * @param {Object} area
 * @return {Object}
 */
function useNoLineArea(index, contourColorMap, area) {
  const {z, points} = area;
  const keys = contourColorMap.entries();
  let color;
  while (!color) {
    const key = keys.next().value[0];
    if (key === z) {
      color = keys.next().value[1];
    }
  }
  return {
    type: 'group',
    children: [
      {
        type: 'polygon',
        shape: {
          points,
          smooth: 0,
        },
        z2: index,
        style: {
          fill: color,
          stroke: 'gray',
          lineWidth: 1,
        },
      },
    ],
  };
}

/**
 * Generate contour area series of contour map chart
 * @param {number} z
 * @param {number} index
 * @param {Array} lines
 * @param {Map} contourColorMap
 * @param {Object} border
 * @param {Object} zOnBorderInOrder
 * @param {Array} noPointArea
 * @return {Object}
 */
function useContourArea(z, index, lines, contourColorMap, border, zOnBorderInOrder, noPointArea) {
  const labels = [];
  const color = contourColorMap.get(z);
  lines.forEach((line) => {
    labels.push(...useLineLabels(z, line.points));
  });
  const polygon = {
    type: 'polygon',
    shape: {
      points: completeTopoArea(z, lines, border, zOnBorderInOrder, noPointArea),
      smooth: 0.1,
    },
    z2: index,
    style: {
      fill: color,
      stroke: 'gray',
      lineWidth: 1,
    },
  };
  return {
    type: 'group',
    children: [
      polygon,
      ...labels,
    ],
  };
}

/**
 * Generate contour line series of contour map chart
 * @param {number} z
 * @param {Array} line
 * @param {Map} contourColorMap
 * @return {Object}
 */
function useContourLine(z, line, contourColorMap) {
  const labels = useLineLabels(z, line);
  const color = contourColorMap.get(z);
  // Contour
  const polyline = {
    type: 'polyline',
    shape: {
      points: line,
      smooth: 0.1,
    },
    style: {
      fill: 'none',
      stroke: color,
      lineWidth: 1.2,
    },
  };
  return {
    type: 'group',
    children: [
      polyline,
      ...labels,
    ],
  };
}

/**
 * Complete single line points
 * @param {number} z
 * @param {Array} line
 * @param {Object} border
 * @param {Object} zOnBorderInOrder
 * @param {Array} noPointArea
 * @return {Array}
 */
function completeSingleLine(z, line, border, zOnBorderInOrder, noPointArea) {
  const {startIndex, startBorder} = line;
  const startBorderInOrder = zOnBorderInOrder[startBorder];
  const startIncreasing = startBorderInOrder[startIndex - 1] < z || z < startBorderInOrder[startIndex + 1];
  switch (startBorder) {
    case 'top':
    case 'right':
      return completeByClockwise(z, line, border, startIncreasing, zOnBorderInOrder, noPointArea);
    case 'bottom':
    case 'left':
      return completeByClockwise(z, line, border, !startIncreasing, zOnBorderInOrder, noPointArea);
  }
}

/**
 * Complete single line points with specified order
 * @param {number} z
 * @param {Array} line
 * @param {Object} border
 * @param {boolean} clockwise
 * @param {Object} zOnBorderInOrder
 * @param {Array} noPointArea
 * @return {Array}
 */
function completeByClockwise(z, line, border, clockwise, zOnBorderInOrder, noPointArea) {
  const {startBorder, endBorder, points} = line;
  const lastIndex = points.length - 1;
  const startInversionPoint = calInversionPoint(points[0], points[1]);
  const endInversionPoint = calInversionPoint(points[lastIndex], points[lastIndex - 1]);
  switch (startBorder + endBorder) {
    case 'topleft':
    case 'leftbottom':
    case 'bottomright':
    case 'righttop':
      if (!clockwise) {
        const addPoints = checkNoPointAreaInConnecting(line, zOnBorderInOrder, border);
        if (addPoints) {
          // NoPointArea exist
          noPointArea.push({
            points: [
              ...addPoints,
              startInversionPoint,
              ...points,
              endInversionPoint,
            ],
            z,
          });
        }
      }
      break;
    case 'lefttop':
    case 'bottomleft':
    case 'rightbottom':
    case 'topright':
      if (clockwise) {
        const addPoints = checkNoPointAreaInConnecting(line, zOnBorderInOrder, border);
        if (addPoints) {
          // NoPointArea exist
          noPointArea.push({
            points: [
              ...addPoints,
              startInversionPoint,
              ...points,
              endInversionPoint,
            ],
            z,
          });
        }
      }
      break;
  }
  let startPoint = ['top', 'bottom'].includes(endBorder) ? ['middle', endBorder] : [endBorder, 'middle'];

  const addPointsPosition = [];
  do {
    startPoint = useNextCornerByClockwise(startPoint, clockwise);
    addPointsPosition.push(startPoint);
  } while (startPoint.every((b) => b !== startBorder));

  const addPoints = addPointsPosition.map(([x, y]) => {
    return [border[x], border[y]];
  });
  return [
    ...addPoints,
    startInversionPoint,
    ...points,
    endInversionPoint,
  ];
}

/**
 * Get next corner point with specified order
 * @param {Array} startPoint
 * @param {boolean} clockwise
 * @return {Array}
 */
function useNextCornerByClockwise(startPoint, clockwise) {
  switch (startPoint.join('')) {
    case 'middletop':
      return clockwise ? ['right', 'top'] : ['left', 'top'];
    case 'rightmiddle':
      return clockwise ? ['right', 'bottom'] : ['right', 'top'];
    case 'middlebottom':
      return clockwise ? ['left', 'bottom'] : ['left', 'bottom'];
    case 'leftmiddle':
      return clockwise ? ['left', 'top'] : ['left', 'bottom'];
    case 'lefttop':
      return clockwise ? ['right', 'top'] : ['left', 'bottom'];
    case 'righttop':
      return clockwise ? ['right', 'bottom'] : ['left', 'top'];
    case 'rightbottom':
      return clockwise ? ['left', 'bottom'] : ['right', 'top'];
    case 'leftbottom':
      return clockwise ? ['left', 'top'] : ['right', 'bottom'];
  }
}

/**
 * Calculate the inversion point of target point relative to origin point
 * @param {Array} origin
 * @param {Array} target
 * @return {Array}
 */
function calInversionPoint(origin, target) {
  const shrinkFactor = 20; // Used to reduce contour area out of border
  return [
    origin[0] - (target[0] - origin[0]) / shrinkFactor,
    origin[1] - (target[1] - origin[1]) / shrinkFactor,
  ];
}

/**
 * Complete area points
 * @param {number} z
 * @param {Array} lines
 * @param {Object} border
 * @param {Object} zOnBorderInOrder
 * @param {Array} noPointArea
 * @return {Array}
 */
function completeTopoArea(z, lines, border, zOnBorderInOrder, noPointArea) {
  if (lines.length === 1) {
    const line = lines[0];
    const {points, startBorder, endBorder} = line;
    if (!startBorder) {
      // Circle
      return points;
    }
    if (startBorder === endBorder) {
      // Start and end on same border
      const lastIndex = points.length - 1;
      return [
        calInversionPoint(points[0], points[1]),
        ...points,
        calInversionPoint(points[lastIndex], points[lastIndex - 1]),
      ];
    }
    // Start and end on different border
    return completeSingleLine(z, line, border, zOnBorderInOrder, noPointArea);
  } else {
    // Multiple lines, and start and end on different border
    return connectLines(z, lines, border, zOnBorderInOrder, noPointArea);
  }
}

/**
 * Transform x, y position to value of point in right order
 * @param {string} border1
 * @param {string} border2
 * @param {Object} border
 * @return {Array}
 */
function useCornerPoint(border1, border2, border) {
  const expandFactor = 5; // Used to enlarge contour area out of border
  const expandBorder = {
    left: border.left - expandFactor,
    top: border.top - expandFactor,
    right: border.right + expandFactor,
    bottom: border.bottom + expandFactor,
  };
  const point = ['left', 'right'].includes(border1)
                  ? [expandBorder[border1], expandBorder[border2]]
                  : [expandBorder[border2], expandBorder[border1]];
  return point;
}

/**
 * Transform x, y position to value of points in right order
 * @param {string} startBorder
 * @param {string} endBorder
 * @param {Object} border
 * @param {string} direction
 * @return {Array}
 */
function useTwoCornerPoints(startBorder, endBorder, border, direction) {
  if (['top', 'bottom'].includes(direction)) {
    return [[border[direction], border[endBorder]], [border[direction], border[startBorder]]];
  } else {
    // 'left' and 'right'
    return [[border[endBorder], border[direction]], [border[startBorder], border[direction]]];
  }
}

/**
 * Check no point area whether exist, if exist, return points used to supplement
 * @param {Object} line
 * @param {Object} zOnBorderInOrder
 * @param {Object} border
 * @return {Array}
 */
function checkNoPointAreaInConnecting(line, zOnBorderInOrder, border) {
  const {startBorder, endBorder, startIndex, endIndex} = line;
  const startBorderLastPointIndex = zOnBorderInOrder[startBorder].length - 1;
  const endBorderLastPointIndex = zOnBorderInOrder[endBorder].length - 1;
  switch (startBorder + endBorder) {
    case 'topleft':
    case 'lefttop':
      if (startIndex === 0 && endIndex === 0) {
        return [useCornerPoint(startBorder, endBorder, border)];
      }
      break;
    case 'topright':
    case 'leftbottom':
      if (startIndex === startBorderLastPointIndex && endIndex === 0) {
        return [useCornerPoint(startBorder, endBorder, border)];
      }
      break;
    case 'bottomleft':
    case 'righttop':
      if (startIndex === 0 && endIndex === endBorderLastPointIndex) {
        return [useCornerPoint(startBorder, endBorder, border)];
      }
      break;
    case 'bottomright':
    case 'rightbottom':
      if (startIndex === startBorderLastPointIndex && endIndex === endBorderLastPointIndex) {
        return [useCornerPoint(startBorder, endBorder, border)];
      }
      break;
    case 'topbottom':
    case 'bottomtop':
    case 'rightleft':
    case 'leftright':
      if (startIndex === 0 && endIndex === 0) {
        const direction = ['top', 'bottom'].includes(startBorder) ? 'left' : 'top';
        return useTwoCornerPoints(startBorder, endBorder, border, direction);
      } else if (startIndex === startBorderLastPointIndex && endIndex === endBorderLastPointIndex) {
        const direction = ['top', 'bottom'].includes(startBorder) ? 'right' : 'bottom';
        return useTwoCornerPoints(startBorder, endBorder, border, direction);
      }
      break;
    default:
      // Never happen under the right calculation
      return;
  }
}

function calIntersectionPoint(line1point1, line1point2, line2point1, line2point2) {
  const line1DiffX = line1point2[0] - line1point1[0];
  const line2DiffX = line2point2[0] - line2point1[0];
  const line1DiffY = line1point2[1] - line1point1[1];
  const line2DiffY = line2point2[1] - line2point1[1];
  let k1;
  let k2;
  let e1;
  let e2;
  if (line1DiffX === 0 && line2DiffX === 0) {
    // Vertical parallel, such as | |
    return [];
  } else if (line1DiffX === 0) {
    k2 = line2DiffY / line2DiffX;
    e2 = (line2point2[1] - k2 * line2point2[0]);
    const x = line1point1[0];
    return [x, k2 * x + e2];
  } else if (line2DiffX === 0) {
    const k1 = line1DiffY / line1DiffX;
    const e1 = (line1point2[1] - k1 * line1point2[0]);
    const x = line2point1[0];
    return [x, k1 * x + e1];
  }
  if (line1DiffY === 0 && line2DiffY === 0) {
    // Horizontal parallel, such as 二
    return [];
  } else if (line1DiffY === 0) {
    k2 = line2DiffY / line2DiffX;
    e2 = (line2point2[1] - k2 * line2point2[0]);
    const y = line1point1[1];
    return [(y - e2) / k2, y];
  } else if (line2DiffY === 0) {
    k1 = line1DiffY / line1DiffX;
    e1 = (line1point2[1] - k1 * line1point2[0]);
    const y = line2point1[1];
    return [(y - e1) / k1, y];
  }
  k1 = line1DiffY / line1DiffX;
  e1 = (line1point2[1] - k1 * line1point2[0]);
  k2 = line2DiffY / line2DiffX;
  e2 = (line2point2[1] - k2 * line2point2[0]);

  if (k1 === k2) {
    // Slope parallel, such as \ \ or / /
    return [];
  }

  const x = (e2 - e1) / (k1 - k2);
  const y = k1 * x + e1;

  return [x, y];
}

/**
 * Calculate two line relation, if two line can connect on same border, return connected line
 * @param {Object} line1
 * @param {Object} line2
 * @return {Object}
 */
function calTwoLineRelation(line1, line2) {
  const points1 = line1.points;
  const points2 = line2.points;
  const lastIndex1 = points1.length - 1;
  const lastIndex2 = points2.length - 1;
  if (line1.startBorder === line2.startBorder) {
    const controlPoint = calIntersectionPoint(points1[0], points1[1], points2[0], points2[1]);
    points1.reverse();
    return {
      points: [...points1, controlPoint, ...points2],
      startBorder: line1.endBorder,
      endBorder: line2.endBorder,
      passBorder: line2.startBorder,
    };
  } else if (line1.startBorder === line2.endBorder) {
    const controlPoint = calIntersectionPoint(points1[0], points1[1], points2[lastIndex2], points2[lastIndex2 - 1]);
    return {
      points: [...points2, controlPoint, ...points1],
      startBorder: line2.startBorder,
      endBorder: line1.endBorder,
      passBorder: line1.startBorder,
    };
  } else if (line1.endBorder === line2.startBorder) {
    const controlPoint = calIntersectionPoint(points1[lastIndex1], points1[lastIndex1 - 1], points2[0], points2[1]);
    return {
      points: [...points1, controlPoint, ...points2],
      startBorder: line1.startBorder,
      endBorder: line2.endBorder,
      passBorder: line1.endBorder,
    };
  } else if (line1.endBorder === line2.endBorder) {
    const controlPoint = calIntersectionPoint(
        points1[lastIndex1 - 1],
        points1[lastIndex1],
        points2[lastIndex2 - 1],
        points2[lastIndex2],
    );
    points2.reverse();
    return {
      points: [...points1, controlPoint, ...points2],
      startBorder: line1.startBorder,
      endBorder: line2.startBorder,
      passBorder: line1.endBorder,
    };
  } else {
    return;
  }
}

/**
 * Connect lines
 * @param {number} z
 * @param {Array} lines
 * @param {Object} border
 * @param {Object} zOnBorderInOrder
 * @param {Array} noPointArea
 * @return {Array} newLine
 */
function connectLines(z, lines, border, zOnBorderInOrder, noPointArea) {
  let startLine = lines.splice(0, 1)[0];
  const addPoints = checkNoPointAreaInConnecting(startLine, zOnBorderInOrder, border);
  if (addPoints) {
    // NoPointArea exist
    noPointArea.push({
      points: addPoints.concat(startLine.points),
      z,
    });
  }
  while (lines.length > 0) {
    for (let i = 0; i < lines.length; i++) {
      const otherLine = lines[i];
      const addPoints = checkNoPointAreaInConnecting(otherLine, zOnBorderInOrder, border);
      const otherPoints = otherLine.points;
      if (addPoints) {
        // NoPointArea exist
        noPointArea.push({
          points: addPoints.concat(otherPoints),
          z,
        });
      }
      const connection = calTwoLineRelation(startLine, otherLine);
      if (connection) {
        startLine = connection;
        lines.splice(i, 1);
        if (lines.length === 0) {
          const {points, startBorder, endBorder, passBorder} = startLine;
          const lastIndex = points.length - 1;
          switch (startBorder + endBorder) {
            case 'bottomleft':
            case 'leftbottom':
            case 'bottomright':
            case 'rightbottom':
            case 'topright':
            case 'righttop':
            case 'topleft':
            case 'lefttop':
              return [
                useCornerPoint(startBorder, endBorder, border),
                calInversionPoint(points[0], points[1]),
                ...points,
                calInversionPoint(points[lastIndex], points[lastIndex - 1]),
              ];
            case 'rightleft':
            case 'leftright':
            case 'topbottom':
            case 'bottomtop':
              const addPointBorder = useOppositeBorder(passBorder);
              return [
                useCornerPoint(startBorder, addPointBorder, border),
                calInversionPoint(points[0], points[1]),
                ...points,
                calInversionPoint(points[lastIndex], points[lastIndex - 1]),
                useCornerPoint(endBorder, addPointBorder, border),
              ];
          }
        }
      } else {
        // No connection
        if (lines.length === 1) {
          /**
           *     \    /
           *       or
           *  \          /
           */
          return connectDiagonalLines(startLine, otherLine, border);
        }
      }
    }
  }
  return startLine.points;
}

/**
 * Connect diagonal lines
 * @param {Object} line1
 * @param {Object} line2
 * @param {Object} border
 * @return {Array}
 */
function connectDiagonalLines(line1, line2, border) {
  const points1 = line1.points;
  const points2 = line2.points;
  if (line2.startBorder !== useOppositeBorder(line1.startBorder)) {
    points2.reverse();
  }
  const point1Border = ['top', 'bottom'].includes(line1.startBorder)
                   ? [line1.endBorder, useOppositeBorder(line1.startBorder)]
                   : [useOppositeBorder(line1.startBorder), line1.endBorder];
  const point2Border = useOppositeCorner(point1Border);
  const point1 = point1Border.map((b) => border[b]);
  const point2 = point2Border.map((b) => border[b]);
  const lastIndex1 = points1.length - 1;
  const lastIndex2 = points2.length - 1;
  return [
    calInversionPoint(points1[0], points1[1]),
    ...points1,
    calInversionPoint(points1[lastIndex1], points1[lastIndex1 - 1]),
    point1,
    calInversionPoint(points2[0], points2[1]),
    ...points2,
    calInversionPoint(points2[lastIndex2], points2[lastIndex2 - 1]),
    point2,
  ];
}

/**
 * Generate opposite border
 * @param {string} border
 * @return {string}
 */
function useOppositeBorder(border) {
  if (border === 'left') return 'right';
  if (border === 'right') return 'left';
  if (border === 'top') return 'bottom';
  if (border === 'bottom') return 'top';
}

/**
 * Generate opposite corner point
 * @param {Array} border
 * @return {Array}
 */
function useOppositeCorner(border) {
  return border.map((b) => useOppositeBorder(b));
}

/**
 * Calculate is the point on the border
 * @param {Array} point
 * @param {Object} border
 * @return {string | null} result
 */
function calPointBorder(point, border) {
  const {top, left, bottom, right} = border;
  if (left === point[0]) {
    return 'left';
  } else if (right === point[0]) {
    return 'right';
  } else if (top === point[1]) {
    return 'top';
  } else if (bottom === point[1]) {
    return 'bottom';
  } else {
    return null;
  }
}

/**
 * Generate data required for calculation
 * @param {Map} contourMap
 * @param {Object} border
 * @return {Object}
 */
function createDataRequiredForCalculation(contourMap, border) {
  const pointsOnBorder = {
    top: [],
    left: [],
    right: [],
    bottom: [],
  };
  contourMap.forEach((lines, z) => {
    lines.forEach((line, index) => {
      const start = line[0];
      const startBorder = calPointBorder(start, border);
      if (startBorder) {
        const end = line[line.length - 1];
        const endBorder = calPointBorder(end, border);
        const lineObject = {
          points: line,
          startBorder,
          startIndex: null,
          endBorder,
          endIndex: null,
        };
        pointsOnBorder[startBorder].push({
          point: [...start, z],
          start: true,
          line: lineObject,
        });
        pointsOnBorder[endBorder].push({
          point: [...end, z],
          end: true,
          line: lineObject,
        });
        lines[index] = lineObject;
      } else {
        // Circle
        lines[index] = {
          points: line,
          startBorder: null,
          endBorder: null,
        };
      }
    });
  });
  Object.keys(pointsOnBorder).forEach((border) => {
    // 'top' and 'bottom': 'x' is the value to be compared, means index === 0
    // 'left' and 'right': 'y' is the value to be compared, means index === 1
    const compareIndex = ['top', 'bottom'].includes(border) ? 0 : 1;
    pointsOnBorder[border].sort((a, b) => {
      return a.point[compareIndex] - b.point[compareIndex];
    });
    pointsOnBorder[border] = pointsOnBorder[border].map((item, index) => {
      if (item.start) {
        item.line.startIndex = index;
      }
      if (item.end) {
        item.line.endIndex = index;
      }
      return item.point[2];
    });
  });
  return pointsOnBorder;
}

/**
 * Generate contour map chart series
 * @param {Array<number>} contours
 * @param {Map<number, Array>} contourMap
 * @param {Array} minPoint
 * @param {Array} maxPoint
 * @param {Map} contourColorMap
 * @param {boolean} isArea
 * @return {Object} echarts custom series
 */
function useContourGroup(contours, contourMap, minPoint, maxPoint, contourColorMap, isArea) {
  return {
    type: 'custom',
    clip: true,
    zlevel: -1,
    name: 'contour',
    data: [
      minPoint,
      maxPoint,
    ],
    renderItem: (_params, api) => {
      const newContourMap = new Map();
      const children = [];
      contourMap.forEach((lines, z) => {
        newContourMap.set(z, []);
        lines.forEach((line) => {
          const newLine = line.map((point) => {
            return api.coord([point.x, point.y]);
          });
          newContourMap.get(z).push(newLine);
        });
      });
      if (isArea) {
        const [left, bottom] = api.coord(minPoint);
        const [right, top] = api.coord(maxPoint);
        const border = {top, right, bottom, left};
        const zOnBorderInOrder = createDataRequiredForCalculation(newContourMap, border);
        const noPointArea = [];
        newContourMap.forEach((lines, z) => {
          if (!lines.length) return;
          const index = contours.length - contours.indexOf(z);
          children.push(useContourArea(z, index, lines, contourColorMap, border, zOnBorderInOrder, noPointArea));
        });
        noPointArea.forEach((area) => {
          const index = contours.length - contours.indexOf(area.z);
          children.push(useNoLineArea(index, contourColorMap, area));
        });
      } else {
        newContourMap.forEach((lines, z) => {
          lines.forEach((line) => {
            children.push(useContourLine(z, line, contourColorMap));
          });
        });
      }
      return {
        type: 'group',
        children,
        silent: true,
      };
    },
  };
}

/**
 * Keep decimal places to largest
 * @param {number} number
 * @param {number} decimalPlaces
 * @return {number}
 */
function ceilDecimalPlaces(number, decimalPlaces) {
  const factor = Math.pow(10, decimalPlaces);
  return number < 0
    ? ~~(number * factor) / factor
    : (~~(number * factor) + 1) / factor;
}

/**
 * Keep decimal places to smallest
 * @param {number} number
 * @param {number} decimalPlaces
 * @return {number}
 */
function floorDecimalPlaces(number, decimalPlaces) {
  const factor = Math.pow(10, decimalPlaces);
  return number < 0
    ? (~~(number * factor) - 1) / factor
    : ~~(number * factor) / factor;
}

/**
 * Calculate contour color
 * @param {Array} colors
 * @param {Array} contours
 * @param {boolean} isTopographic
 * @return {Object}
 */
function updateContourColor(colors, contours, isTopographic) {
  const step = contours.length / 5; // 5: color change times of colors
  const contourColors = [];
  for (let i = 0; i < 5; i++) {
    contourColors.push(...getGradientColor(colors[i], colors[i + 1], step));
  }
  contourColors.push(colors.slice(-1)[0]);
  const contourColorMap = new Map();
  contours.forEach((val, index) => {
    contourColorMap.set(val, contourColors[index]);
  });
  if (isTopographic) {
    contourColorMap.set(Infinity, colors[colors.length - 1]);
  }
  return {
    contourColorMap,
    legendColors: Array.from(contourColorMap).reverse(),
  };
}

/**
 * Calculate contours with list of z
 * @param {Array<number>} zList Should be arranged from small to large
 * @param {number} contoursNumber The number of contours
 * @return {Object} contours
 */
function calContours(zList, contoursNumber) {
  const min = 0;
  const max = zList[zList.length - 1];
  let stepTemp = (max - min) / (contoursNumber + 1);
  let step = stepTemp;
  let decimalPlaces = 0;
  while (stepTemp < 10) {
    stepTemp *= 10;
    decimalPlaces++;
  }
  step = floorDecimalPlaces(step, decimalPlaces);
  const contours = [];
  for (let i = 1; i <= contoursNumber; i++) {
    contours.push(+(min + step * i).toFixed(decimalPlaces));
  }
  return contours;
}

/**
 * Create point matrix with points data
 * @param {Object} points {x, y, z}
 * @return {Object}
 */
function createPointMatrix(points) {
  const {x, y, z} = points;
  const leftBottom = [x[0], y[0]];
  const rightTop = [x[x.length - 1], y[y.length - 1]];
  const zList = [];
  const pointMatrix = [];
  z.forEach((rowZ, rowIndex) => {
    pointMatrix.push([]);
    rowZ.forEach((itemZ, columnIndex) => {
      zList.push(itemZ);
      pointMatrix[rowIndex].push({
        x: x[columnIndex],
        y: y[rowIndex],
        z: itemZ,
      });
    });
  });
  pointMatrix.reverse();
  zList.sort((a, b) => a - b);
  return {
    pointMatrix: Object.freeze(pointMatrix),
    zList: Object.freeze(zList),
    leftBottom,
    rightTop,
  };
}

/**
 * Calculate Map<z, [line as points, line as points]> with contours and matrix of point
 * @param {Array<number>} contours Array<z>
 * @param {Array} pointMatrix
 * @return {Map<number, Array<Lines>>}
 */
function calContoursPoints(contours, pointMatrix) {
  const contourPointMap = new Map();
  contours.forEach((contour) => {
    contourPointMap.set(contour, []);
  });
  const startPointsNumber = pointMatrix.length - 1;
  const contoursAreaMap = new Map(); // <'row,column', Set<contours need to calculate>>
  for (let row = 0; row < startPointsNumber; row++) {
    for (let column = 0; column < startPointsNumber; column++) {
      contoursAreaMap.set(`${row},${column}`, new Set(contours));
    }
  }
  for (let row = 0; row < startPointsNumber; row++) {
    for (let column = 0; column < startPointsNumber; column++) {
      const contoursInArea = contoursAreaMap.get(`${row},${column}`);
      contoursInArea.forEach((contourNeedCalculate) => {
        const store = [];
        calContourPoints(contourNeedCalculate, row, column, store, pointMatrix, contoursAreaMap);
        if (store.length) {
          const lines = contourPointMap.get(contourNeedCalculate);
          let connected = false;
          for (let i = 0; i < lines.length; i++) {
            const result = verifyLinesConnected(lines[i], store);
            if (result) {
              lines[i] = result;
              connected = true;
              break;
            }
          }
          if (!connected) {
            lines.push(store);
          }
        }
      });
    }
  }
  return contourPointMap;
}


/**
 * Calculate contour points in point matrix
 * @param {number} contour points contour value
 * @param {number} row
 * @param {number} column
 * @param {Array} pointStore
 * @param {Array} pointMatrix
 * @param {Map} contoursAreaMap
 * @param {string} startPosition
 */
function calContourPoints(contour, row, column, pointStore, pointMatrix, contoursAreaMap, startPosition = null) {
  const contourNeedCalculate = contoursAreaMap.get(`${row},${column}`);
  if (!contourNeedCalculate || !contourNeedCalculate.has(contour)) return;
  // Delete this contour and start calculating
  contourNeedCalculate.delete(contour);
  const [
    topLeft,
    topRight,
    bottomLeft,
    bottomRight,
  ] = [
    pointMatrix[row][column],
    pointMatrix[row][column + 1],
    pointMatrix[row + 1][column],
    pointMatrix[row + 1][column + 1],
  ];
  let pointNumber = ['top', 'bottom', 'left', 'right'].includes(startPosition) ? 1 : 0;
  if (startPosition !== 'top') {
    const topPercent = (contour - topLeft.z) / (topRight.z - topLeft.z);
    if (0 < topPercent && topPercent < 1) {
      // Top exist
      pointStore.push(calHorizontalContourPoint(topLeft, topRight, contour));
      pointNumber++;
      if (pointNumber === 2) {
        calContourPoints(contour, row - 1, column, pointStore, pointMatrix, contoursAreaMap, 'bottom');
        return;
      }
    }
  }
  if (startPosition !== 'bottom') {
    const bottomPercent = (contour - bottomLeft.z) / (bottomRight.z - bottomLeft.z);
    if (0 < bottomPercent && bottomPercent < 1) {
      // Bottom exist
      pointStore.push(calHorizontalContourPoint(bottomLeft, bottomRight, contour));
      pointNumber++;
      if (pointNumber === 2) {
        calContourPoints(contour, row + 1, column, pointStore, pointMatrix, contoursAreaMap, 'top');
        return;
      }
    }
  }
  if (startPosition !== 'left') {
    const leftPercent = (contour - topLeft.z) / (bottomLeft.z - topLeft.z);
    if (0 < leftPercent && leftPercent < 1) {
      // Left exist
      pointStore.push(calVerticalContourPoint(topLeft, bottomLeft, contour));
      pointNumber++;
      if (pointNumber === 2) {
        calContourPoints(contour, row, column - 1, pointStore, pointMatrix, contoursAreaMap, 'right');
        return;
      }
    }
  }
  if (startPosition !== 'right') {
    const rightExist = (contour - topRight.z) / (bottomRight.z - topRight.z);
    if (0 < rightExist && rightExist < 1) {
      // Right exist
      pointStore.push(calVerticalContourPoint(topRight, bottomRight, contour));
      pointNumber++;
      if (pointNumber === 2) {
        calContourPoints(contour, row, column + 1, pointStore, pointMatrix, contoursAreaMap, 'left');
        return;
      }
    }
  }
  if (pointNumber !== 2) {
    return;
  }
}

/**
 * Verify whether the two lines are connected on same border
 * @param {Array} line1 {x, y, z}
 * @param {Array} line2 {x, y, z}
 * @return {Array} newLine
 */
function verifyLinesConnected(line1, line2) {
  const line1Start = line1[0];
  const line1End = line1[line1.length - 1];
  const line2Start = line2[0];
  const line2End = line2[line2.length - 1];
  if (line1Start.x === line2Start.x && line1Start.y === line2Start.y) {
    line1.shift();
    return line1.reverse().concat(line2);
  }
  if (line1End.x === line2End.x && line1End.y === line2End.y) {
    line1.pop();
    return line1.concat(line2.reverse());
  }
  if (line1Start.x === line2End.x && line1Start.y === line2End.y) {
    line1.shift();
    return line2.concat(line1);
  }
  if (line1End.x === line2Start.x && line1End.y === line2Start.y) {
    line1.pop();
    return line1.concat(line2);
  }
}

/**
 * Calculate point position on horizontal direction between point1 and point2 by z value
 * @param {Object} point1 {x, y, z}
 * @param {Object} point2 {x, y, z}
 * @param {number} z
 * @return {Object} position {x, y}
 */
function calHorizontalContourPoint(point1, point2, z) {
  const [minZ, maxZ, xOfMinZ, xOfMaxZ] = point1.z > point2.z ?
    [point2.z, point1.z, point2.x, point1.x] :
    [point1.z, point2.z, point1.x, point2.x];
  const minPart = z - minZ;
  const maxPart = maxZ - z;
  const total = minPart + maxPart;
  const xUnit = xOfMaxZ - xOfMinZ;
  return {
    x: (minPart / total) * xUnit + xOfMinZ,
    y: point1.y,
  };
}

/**
 * Calculate point position on vertical direction between point1 and point2 by z value
 * @param {Object} point1 {x, y, z}
 * @param {Object} point2 {x, y, z}
 * @param {number} z
 * @return {Object} position {x, y}
 */
function calVerticalContourPoint(point1, point2, z) {
  const [minZ, maxZ, yOfMinZ, yOfMaxZ] = point1.z > point2.z ?
    [point2.z, point1.z, point2.y, point1.y] :
    [point1.z, point2.z, point1.y, point2.y];
  const minPart = z - minZ;
  const maxPart = maxZ - z;
  const total = minPart + maxPart;
  const yUnit = yOfMaxZ - yOfMinZ;
  return {
    x: point1.x,
    y: (minPart / total) * yUnit + yOfMinZ,
  };
}

import {getGradientColor} from '@/js/utils';

import echarts, {echartsThemeName} from '@/js/echarts';

import CommonProperty from '@/common/common-property';

// Chart type
const CONTOUR = 'contour';
const TOPOGRAPHIC = 'topographic';

// Chart series name
const PATH_POINTS = 'pathPoints';
const PATH_LINES = 'pathLines';
const CONTOUR_LABEL = 'pathLines';
const POINTS = 'points';
const TOOLTIP = 'tooltip';

// Chart series z index
const chartZIndexMap = {
  [PATH_POINTS]: 999,
  [PATH_LINES]: 998,
  [CONTOUR_LABEL]: 997,
  [POINTS]: -1,
  [TOOLTIP]: 9999,
};
let start;
let end;
let conPoint;
export default {
  name: 'ContourMap',
  props: {
    showAnimation: Boolean,
    showConvergencePoint: Boolean,
    showLegend: Boolean,
    showFullScreen: Boolean,
    // Type of chart, cannot change after init
    type: {
      type: String,
      required: true,
      validator: (val) => {
        return [CONTOUR, TOPOGRAPHIC].includes(val);
      },
    },
  },
  data() {
    return {
      chartInstance: null,
      isArea: null,
      // Chart legend color list
      legendColors: [],
      // Chart style setting
      setting: {},
      CONTOUR,
      TOPOGRAPHIC,
    };
  },
  beforeCreate() {
    start = this.$t('components.startText');
    end = this.$t('components.endText');
    conPoint = this.$t('lossCompare.conpoint');
  },
  created() {
    this.isArea = this.type === TOPOGRAPHIC;
  },
  methods: {
    /**
     * The logic of show tooltip by params from echarts mousemove event
     * @param {Object} params
     */
    showTooltip(params) {
      if (this.tooltipTimer) clearTimeout(this.tooltipTimer);
      this.tooltipTimer = setTimeout(() => {
        if (params.seriesName !== POINTS) {
          return;
        }
        const {seriesIndex, dataIndex} = params;
        const position = params.data.position;
        this.chartInstance.dispatchAction({
          type: 'showTip',
          seriesIndex: seriesIndex + 1,
          dataIndex: dataIndex,
          position,
        });
      }, 500); // Use to reduce tooltip consumption
    },
    /**
     * The logic of play path animation
     */
    playPathAnimation() {
      const {path, rightTop, setting} = this;
      const {pathWidth, pathColor} = setting;
      // Clear path lines
      const {intervals, x, y} = path;
      const clearLines = [];
      x.forEach((_, index) => {
        if (index < x.length - 1) {
          clearLines.push([x[index], y[index], x[index], y[index]]);
        }
      });
      if (!this.chartInstance) {
        if (!this.initContourMap()) return;
      }
      this.chartInstance.setOption({
        series: [
          usePathLines(rightTop, clearLines, pathWidth, pathColor),
        ],
      });
      // Start animation
      let index = 0;
      const timer = setInterval(() => {
        if (index === intervals.length - 1) {
          this.chartInstance.setOption({
            series: [
              usePathLines(rightTop, clearLines, pathWidth, pathColor, false),
            ],
          });
          clearInterval(timer);
          return;
        }
        clearLines[index] = [x[index], y[index], x[index + 1], y[index + 1]];
        if (!this.chartInstance) {
          if (!this.initContourMap()) {
            clearInterval(timer);
            return;
          }
        }
        this.chartInstance.setOption({
          series: [
            usePathLines(rightTop, clearLines, pathWidth, pathColor, true),
          ],
        });
        index++;
      }, 600); // Animation time interval
    },
    /**
     * The logic of path style change
     * @param {Object} newSetting
     */
    handlePathStyleChange(newSetting) {
      const {setting, rightTop, path} = this;
      // Update setting
      setting.pathWidth = newSetting.pathWidth;
      setting.pathColor = newSetting.pathColor;
      const {pathWidth, pathColor} = setting;
      // Update path chart
      if (!this.chartInstance) {
        if (!this.initContourMap()) return;
      }
      this.chartInstance.setOption({
        series: [
          ...usePathSeries(path, rightTop, pathWidth, pathColor),
        ],
      });
    },
    /**
     * The logic of contour number change
     * @param {Object} newSetting
     */
    handleContoursNumberChange(newSetting) {
      const {pointMatrix, setting, zList, leftBottom, rightTop, isArea, type} = this;
      // Update setting
      setting.contoursNumber = newSetting.contoursNumber;
      const {contourColors, contoursNumber} = setting;
      // Update contours
      const contours = calContours(zList, contoursNumber);
      this.contours = contours;
      // Update contours color
      const {contourColorMap, legendColors} = updateContourColor(contourColors, contours, type === TOPOGRAPHIC);
      this.legendColors = legendColors;
      // Update contours points
      const contourPointMap = calContoursPoints(contours, pointMatrix);
      this.contourPointMap = contourPointMap;
      // Update contour chart
      if (!this.chartInstance) {
        if (!this.initContourMap()) return;
      }
      this.chartInstance.setOption({
        series: [
          useContourGroup(contours, contourPointMap, leftBottom, rightTop, contourColorMap, isArea),
        ],
      });
    },
    /**
     * The logic of contour color change
     * @param {Object} newSetting
     */
    handleContourColorsChange(newSetting) {
      const {contours, contourPointMap, leftBottom, rightTop, isArea, setting, type} = this;
      // Update setting
      setting.contourColors = newSetting.contourColors;
      const {contourColors} = setting;
      // Update contours color
      const {contourColorMap, legendColors} = updateContourColor(contourColors, contours, type === TOPOGRAPHIC);
      this.legendColors = legendColors;
      // Update contour chart
      if (!this.chartInstance) {
        if (!this.initContourMap()) return;
      }
      this.chartInstance.setOption({
        series: [
          useContourGroup(contours, contourPointMap, leftBottom, rightTop, contourColorMap, isArea),
        ],
      });
    },
    /**
     * Happen when points data changed
     * @param {Object} data
     * @param {Object} setting
     */
    handleDataChange(data, setting) {
      const {path, points} = data;
      const convergencePoint = data.convergence_point;
      const {contourColors, contoursNumber, pathWidth, pathColor} = setting;
      const {isArea, chartInstance, showConvergencePoint, type} = this;
      this.path = path;
      this.setting = setting;
      // Update point Matrix
      const {pointMatrix, zList, leftBottom, rightTop} = createPointMatrix(points);
      this.pointMatrix = pointMatrix;
      this.zList = zList;
      this.leftBottom = leftBottom;
      this.rightTop = rightTop;
      // Update contours
      const contours = calContours(zList, contoursNumber);
      this.contours = contours;
      // Update contours color
      const {contourColorMap, legendColors} = updateContourColor(contourColors, contours, type === TOPOGRAPHIC);
      this.legendColors = legendColors;
      // Update contours points
      const contourPointMap = calContoursPoints(contours, pointMatrix);
      this.contourPointMap = contourPointMap;
      // Update all chart
      if (chartInstance) {
        chartInstance.clear();
        this.initContourMap();
      } else {
        if (!this.initContourMap()) return;
      }
      const legend = {data: []};
      const series = [];
      if (path) {
        legend.data = path.intervals;
        series.push(...usePathSeries(path, rightTop, pathWidth, pathColor));
      }
      series.push(usePointSeries(
          pointMatrix,
          this.chartInstance,
          showConvergencePoint && convergencePoint,
          +this.$store.state.themeIndex === 0 ? '#000' : '#ddd',
      ));
      series.push(usePointTooltip(pointMatrix));
      series.push(
          useContourGroup(contours, contourPointMap, leftBottom, rightTop, contourColorMap, isArea),
      );
      // series.push({name: TOOLTIP, type: 'custom', z: chartZIndexMap[TOOLTIP], renderItem: () => {}});
      this.chartInstance.setOption({
        legend,
        series,
      });
      this.chartInstance.on('mousemove', this.showTooltip);
    },
    /**
     * The logic of init contour map chart
     * @return {boolean} Whether init successful
     */
    initContourMap() {
      if (!this.chartInstance) {
        if (!this.$refs.contour) return false;
        this.chartInstance = echarts.init(this.$refs.contour, echartsThemeName);
      }
      this.chartInstance.setOption({
        legend: {
          show: false,
        },
        tooltip: {
          trigger: 'item',
          axisPointer: {
            type: 'cross',
          },
          alwaysShowContent: true,
        },
        toolbox: {
          feature: {
            saveAsImage: {},
            dataZoom: {
              filterMode: 'none',
            },
            myFullScreen: this.showFullScreen ? {
              show: true,
              title: this.$t('scalar.fullScreen'),
              icon: CommonProperty.fullScreenIcon[this.$store.state.themeIndex],
              onclick: () => {
                this.$emit('fullScreen');
              },
            } : {},
          },
          right: 10,
        },
        grid: {
          left: 60,
          right: this.showLegend ? 120 : 10,
          top: 30,
          bottom: 20,
        },
        xAxis: {
          type: 'value',
          splitLine: {
            show: false,
          },
          axisLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          min: (value) => {
            return floorDecimalPlaces(value.min, 4);
          },
          max: (value) => {
            return ceilDecimalPlaces(value.max, 4);
          },
        },
        yAxis: {
          type: 'value',
          axisLine: {
            show: false,
          },
          splitLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          min: (value) => {
            return floorDecimalPlaces(value.min, 4);
          },
          max: (value) => {
            return ceilDecimalPlaces(value.max, 4);
          },
        },
      });
      return true;
    },
    resize() {
      this.chartInstance && this.chartInstance.resize();
    },
    beforeDestroy() {
      this.chartInstance.off('mousemove');
    },
  },
};
</script>

<style>
.mi-contour-map {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.mi-contour-map .map-content {
  flex-grow: 1;
}
.mi-contour-map .map-animation {
  height: 30px;
  padding-right: 20px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.mi-contour-map .map-animation .animation-button {
  cursor: pointer;
}
.mi-contour-map .map-legend {
  position: absolute;
  bottom: 48px;
  right: 0;
  display: grid;
  height: 240px;
  width: 100px;
}
.mi-contour-map .map-legend .legend-item {
  display: grid;
  grid-template-columns: 20px 1fr;
  align-items: center;
  gap: 10px;
  position: relative;
}
.mi-contour-map .map-legend .legend-item .legend-color {
  height: 100%;
  display: flex;
  align-items: center;
}

/* contour */
.mi-contour-map .map-legend .legend-item .contour-color {
  border-right: 1px solid gray;
  border-left: 1px solid gray;
}
.mi-contour-map .map-legend .legend-item:first-of-type .contour-color {
  border-top: 1px solid gray;
}
.mi-contour-map .map-legend .legend-item:last-of-type .contour-color {
  border-bottom: 1px solid gray;
}
.mi-contour-map .map-legend .legend-item .contour-color .color{
  height: 2px;
  width: 100%;
}

/* topographic */
.mi-contour-map .map-legend .legend-item .topographic-color {
  border: 1px solid gray;
  border-bottom: none;
}
.mi-contour-map .map-legend .legend-item:last-of-type .topographic-color {
  border-bottom: 1px solid gray;
}
.mi-contour-map .map-legend .legend-item .topographic-color .color{
  height: 100%;
  width: 100%;
}
.mi-contour-map .map-legend .legend-item .text {
  position: absolute;
  left: 24px;
}
.map-legend .legend-title {
  height: 30px;
  line-height: 30px;
}
</style>
