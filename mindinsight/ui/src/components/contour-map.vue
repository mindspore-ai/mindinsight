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
 * @param {number} unit
 * @return {Object} path points series
 */
function usePathPoints(markPoints, points, size, unit) {
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
        const [x, y, z, order] = params.data;
        return `
          ${unit}: ${order}<br>
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
 * @param {string} unit
 * @return {Object} path series
 */
function usePathSeries(path, data, width, color, unit) {
  const {intervals, x, y, z} = path;
  const lines = [];
  const lastIndex = intervals.length - 1;
  const markPoints = [];
  const points = [];
  intervals.forEach((order, index) => {
    if (index === 0) {
      markPoints.push({value: start, xAxis: x[index], yAxis: y[index]});
    }
    if (index === lastIndex) {
      markPoints.push({value: end, xAxis: x[index], yAxis: y[index]});
    }
    points.push([x[index], y[index], z[index], order]);
    if (index < lastIndex) {
      lines.push([x[index], y[index], x[index + 1], y[index + 1]]);
    }
  });
  return [
    usePathPoints(markPoints, points, width * 3, unit),
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
 * @return {Object} points series
 */
function usePointSeries(pointMatrix, chartInstance) {
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
    tooltip: {
      formatter: () => '',
    },
  };
}

/**
 * Generate convergence point series of contour map chart
 * @param {Array} convergencePoint
 * @param {string} pointColor
 * @return {Object}
 */
function useConvergencePoint(convergencePoint, pointColor) {
  return {
    name: CONVERGENCE_POINT,
    type: 'scatter',
    symbol: 'circle',
    symbolSize: 10,
    z: chartZIndexMap[CONVERGENCE_POINT],
    data: [convergencePoint],
    itemStyle: {
      color: pointColor,
    },
    tooltip: {
      padding: [2, 8],
      textStyle: {
        fontSize: 8,
      },
      formatter: (params) => {
        const [x, y] = params.data;
        return `
        ${conPoint}<br>
        x: ${x}<br>
        y: ${y}<br>
        `;
      },
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
    zlevel: 1,
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
 * Generate contour line series of contour map chart
 * @param {Array} points
 * @param {string} color
 * @return {Object}
 */
function useContourLine(points, color) {
  // Contour
  return {
    type: 'polyline',
    shape: {
      points: points,
      smooth: 0.2,
    },
    style: {
      fill: 'none',
      stroke: color,
      lineWidth: 1.2,
    },
  };
}

/**
 * @param {number} index
 * @param {Array} shape
 * @param {string} color
 * @return {Object}
 */
function useSimplePolygon(index, shape, color) {
  return {
    type: 'polygon',
    z2: index,
    shape: {
      points: shape,
      smooth: 0.2,
    },
    style: {
      fill: color,
      stroke: '#666',
      lineWidth: 1,
    },
  };
}
// Border Sample
// class Border {
//   top: number;
//   bottom: number;
//   left: number;
//   right: number;
// }

const SECTION_SPLIT = '|';

/**
 * Complete polygon area by lines that start and end on border
 * @param {Border} border
 * @param {Array<Shape>} borderLines
 * @param {Map<number, string>} contourColorMap
 * @param {Array<number>} contours
 * @return {Array<Object>}
 */
function completeAreaByBorderLines(border, borderLines, contourColorMap, contours) {
  const borderPointMap = generateBorderPointMap(border, borderLines);
  const children = [];
  borderLines.forEach((line) => {
    // Complete area
    const shape = trackNextLine(line, border, borderPointMap);
    children.push({
      z: shape.z,
      index: -1,
      points: shape.points,
      color: contourColorMap.get(shape.z),
    });
  });
  const sections = ['top', 'bottom', 'left', 'right'].map((border) => getSection(border));
  sections.forEach((section) => {
    if (borderPointMap[section].size) {
      borderPointMap[section].forEach((s) => {
        if (!borderPointMap[section].has(s)) {
          return;
        }
        const [start, end] = s.split(SECTION_SPLIT);
        const b = getBorderBySection(section);
        const coord = borderPointMap[b].has(+start) ? +start : +end;
        const shape = trackNextLine(borderPointMap[b].get(coord), border, borderPointMap, true);
        const index = contours.indexOf(shape.z);
        const contour = contours[index + 1] ?? Infinity;
        children.push({
          z: contour,
          index: -1,
          points: shape.points,
          color: contourColorMap.get(contour),
        });
      });
    }
  });
  return children;
}

/**
 * @param {string} section
 * @return {string}
 */
function getBorderBySection(section) {
  return section.replace('Section', '');
}

/**
 * @param {number} start
 * @param {number} end
 * @return {string}
 */
function generateSection(start, end) {
  return start > end ? `${end}${SECTION_SPLIT}${start}` : `${start}${SECTION_SPLIT}${end}`;
}

/**
 * Start track from end to next point to complete area
 * @param {Shape} line
 * @param {Border} border
 * @param {Object} borderPointMap
 * @param {boolean} reverse
 * @return {Object}
 */
function trackNextLine(line, border, borderPointMap, reverse = false) {
  const {z, borders, config} = line;
  let points = JSON.parse(JSON.stringify(line.points));
  let [startBorder, endBorder] = borders;
  // Start coord
  const startCoord = getEffectiveCoord(startBorder, points[0]);
  // End about
  let endCoord = getEffectiveCoord(endBorder, points[points.length - 1]);
  const mainClockwise = reverse ? !config.clockwise[1] : config.clockwise[1];
  extendLine(points);
  let [nextPointBorder, nextPointCoord] = trackNextPoint(endCoord, endBorder, mainClockwise, borderPointMap, border);
  if (startBorder === nextPointBorder && startCoord === nextPointCoord) {
    // Simple area, next point is start point
    if (startBorder === endBorder) {
      borderPointMap[getSection(startBorder)].delete(generateSection(startCoord, endCoord));
    } else {
      const addPoints = addCornerPoints(endBorder, startBorder, border, mainClockwise);
      const startCornerPoint = addPoints[0];
      const startCornerCoord = getEffectiveCoord(startBorder, startCornerPoint);
      borderPointMap[getSection(startBorder)].delete(generateSection(startCoord, startCornerCoord));
      const endCornerPoint = addPoints[addPoints.length - 1];
      const endCornerCoord = getEffectiveCoord(endBorder, endCornerPoint);
      borderPointMap[getSection(endBorder)].delete(generateSection(endCoord, endCornerCoord));
      // points = points.concat(addPoints);
      points = points.concat(extendCornerPoints(addPoints));
    }
    return {
      points,
      z,
    };
  } else {
    while (startBorder !== nextPointBorder || startCoord !== nextPointCoord) {
      // Not finish track
      if (endBorder !== nextPointBorder) {
        // Cross border, need add corner
        const addPoints = addCornerPoints(endBorder, nextPointBorder, border, mainClockwise);
        const startCornerPoint = addPoints[0];
        const startCornerCoord = getEffectiveCoord(endBorder, startCornerPoint);
        borderPointMap[getSection(endBorder)].delete(generateSection(startCoord, startCornerCoord));
        const endCornerPoint = addPoints[addPoints.length - 1];
        const endCornerCoord = getEffectiveCoord(nextPointBorder, endCornerPoint);
        borderPointMap[getSection(nextPointBorder)].delete(generateSection(nextPointCoord, endCornerCoord));
        // points = points.concat(addPoints);
        points = points.concat(extendCornerPoints(addPoints));
      } else {
        borderPointMap[getSection(nextPointBorder)].delete(generateSection(endCoord, nextPointCoord));
      }
      const nextLine = borderPointMap[nextPointBorder].get(nextPointCoord);
      const nextBorders = nextLine.borders;
      const nextPoints = JSON.parse(JSON.stringify(nextLine.points));
      if (nextPointBorder === nextBorders[0] && nextPointCoord === getEffectiveCoord(nextBorders[0], nextPoints[0])) {
        // Next point is start of next line
        endBorder = nextBorders[1];
        endCoord = getEffectiveCoord(endBorder, nextPoints[nextPoints.length - 1]);
      } else {
        // Next point is end of next line
        endBorder = nextBorders[0];
        endCoord = getEffectiveCoord(endBorder, nextPoints[0]);
        nextPoints.reverse();
      }
      extendLine(nextPoints);
      points = points.concat(nextPoints);
      [nextPointBorder, nextPointCoord] = trackNextPoint(endCoord, endBorder, mainClockwise, borderPointMap, border);
    }
    if (endBorder !== nextPointBorder) {
      // Cross border, need add corner
      const addPoints = addCornerPoints(endBorder, nextPointBorder, border, mainClockwise);
      const startCornerPoint = addPoints[0];
      const startCornerCoord = getEffectiveCoord(endBorder, startCornerPoint);
      borderPointMap[getSection(endBorder)].delete(generateSection(startCoord, startCornerCoord));
      const endCornerPoint = addPoints[addPoints.length - 1];
      const endCornerCoord = getEffectiveCoord(nextPointBorder, endCornerPoint);
      borderPointMap[getSection(nextPointBorder)].delete(generateSection(nextPointCoord, endCornerCoord));
      // points = points.concat(addPoints);
      points = points.concat(extendCornerPoints(addPoints));
    } else {
      borderPointMap[getSection(nextPointBorder)].delete(generateSection(endCoord, nextPointCoord));
    }
    return {
      points,
      z,
    };
  }
}

/**
 * Extend line to avoid smooth side effect
 * @param {Array} line
 */
function extendLine(line) {
  const startOrigin = line[0];
  const startNext = line[1];
  line.unshift(calcInversivePoint(startOrigin, startNext));
  const endOrigin = line[line.length - 1];
  const endNext = line[line.length - 2];
  line.push(calcInversivePoint(endOrigin, endNext));
}

/**
 * Extend corner point to avoid smooth side effect
 * @param {Array} cornerPoints
 * @return {Array}
 */
function extendCornerPoints(cornerPoints) {
  return cornerPoints.map((point) => {
    return point.map((v) => v * 1.1); // Extend 10%
  });
}

/**
 * Calc inversive point
 * @param {Array} origin
 * @param {Array} target
 * @return {Array}
 */
function calcInversivePoint(origin, target) {
  return [
    origin[0] - (target[0] - origin[0]),
    origin[1] - (target[1] - origin[1]),
  ];
}

// type PointInPosition = [string, string];

/**
 * @param {PointInPosition} startPoint
 * @param {boolean} clockwise
 * @return {PointInPosition}
 */
function useNextCornerByClockwise(startPoint, clockwise) {
  switch (startPoint.join('')) {
    case 'middletop':
      return clockwise ? ['right', 'top'] : ['left', 'top'];
    case 'rightmiddle':
      return clockwise ? ['right', 'bottom'] : ['right', 'top'];
    case 'middlebottom':
      return clockwise ? ['left', 'bottom'] : ['right', 'bottom'];
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
 * Set start and end border, calc corner points
 * @param {string} startBorder
 * @param {string} endBorder
 * @param {Border} border
 * @param {boolean} clockwise
 * @return {Array}
 */
function addCornerPoints(startBorder, endBorder, border, clockwise) {
  let startPoint = ['top', 'bottom'].includes(startBorder) ? ['middle', startBorder] : [startBorder, 'middle'];
  const addPointsPosition = [];
  do {
    startPoint = useNextCornerByClockwise(startPoint, clockwise);
    addPointsPosition.push(startPoint);
  } while (startPoint.every((b) => b !== endBorder));
  const addPoints = addPointsPosition.map(([x, y]) => {
    return [border[x], border[y]];
  });
  return addPoints;
}

/**
 * @param {number} effectiveCoord
 * @param {string} border
 * @param {boolean} clockwise
 * @param {Map} borderPointMap
 * @return {Array} [border, effectiveCoord]
 */
function trackNextPoint(effectiveCoord, border, clockwise, borderPointMap) {
  const order = borderPointMap[getOrder(border)];
  const index = order.indexOf(effectiveCoord);
  const nextIndex = ['top', 'left'].includes(border)
    ? index + (clockwise ? 1 : -1)
    : index + (clockwise ? -1 : 1);
  if (0 <= nextIndex && nextIndex < order.length) {
    // In range
    return [border, order[nextIndex]];
  } else {
    // Out of range
    let nextBorder = getNextBorderByClockwise(border, clockwise);
    let nextIndex;
    while (!borderPointMap[nextBorder].size) {
      nextBorder = getNextBorderByClockwise(nextBorder, clockwise);
    }
    switch (nextBorder) {
      case 'top':
      case 'left':
        nextIndex = clockwise ? 0 : borderPointMap[nextBorder].size - 1;
        break;
      case 'bottom':
      case 'right':
        nextIndex = clockwise ? borderPointMap[nextBorder].size - 1 : 0;
        break;
    }
    return [nextBorder, borderPointMap[getOrder(nextBorder)][nextIndex]];
  }
}

/**
 * @param {string} border
 * @param {boolean} clockwise
 * @return {string}
 */
function getNextBorderByClockwise(border, clockwise) {
  switch (border) {
    case 'top':
      return clockwise ? 'right' : 'left';
    case 'bottom':
      return clockwise ? 'left' : 'right';
    case 'left':
      return clockwise ? 'top' : 'bottom';
    case 'right':
      return clockwise ? 'bottom' : 'top';
  }
}

/**
 * @param {string} order
 * @return {string}
 */
function getBorderByOrder(order) {
  return order.replace('Order', '');
}

/**
 * @param {string} border
 * @return {string}
 */
function getOrder(border) {
  return `${border}Order`;
}

/**
 * @param {string} border
 * @return {string}
 */
function getSection(border) {
  return `${border}Section`;
}

/**
 * Generate borderPointMap, includes the information of all points on the border
 * @param {Border} borderObject
 * @param {Array} borderLines
 * @return {Object}
 */
function generateBorderPointMap(borderObject, borderLines) {
  const orders = ['top', 'bottom', 'left', 'right'].map((border) => getOrder(border));
  const sections = ['top', 'bottom', 'left', 'right'].map((border) => getSection(border));
  const borderPointMap = {
    top: new Map(),
    [orders[0]]: [],
    [sections[0]]: new Set(),
    bottom: new Map(),
    [orders[1]]: [],
    [sections[1]]: new Set(),
    left: new Map(),
    [orders[2]]: [],
    [sections[2]]: new Set(),
    right: new Map(),
    [orders[3]]: [],
    [sections[3]]: new Set(),
  };
  borderLines.forEach((line) => {
    const {borders, points} = line;
    const [startBorder, endBorder] = borders;
    // Start
    const startEffectiveCoord = getEffectiveCoord(startBorder, points[0]);
    borderPointMap[startBorder].set(startEffectiveCoord, line);
    borderPointMap[getOrder(startBorder)].push(startEffectiveCoord);
    // End
    const endEffectiveCoord = getEffectiveCoord(endBorder, points[points.length - 1]);
    borderPointMap[endBorder].set(endEffectiveCoord, line);
    borderPointMap[getOrder(endBorder)].push(endEffectiveCoord);
  });
  // Generate border composition
  orders.forEach((order) => {
    const border = getBorderByOrder(order);
    const pointsOrder = borderPointMap[order].concat(getStartAndEndCorner(border, borderObject));
    pointsOrder.sort((a, b) => a - b);
    pointsOrder.forEach((coord, index) => {
      if (pointsOrder[index + 1]) {
        borderPointMap[getSection(border)].add(`${coord}${SECTION_SPLIT}${pointsOrder[index + 1]}`);
      }
    });
    pointsOrder.pop();
    pointsOrder.shift();
    borderPointMap[order] = pointsOrder;
  });
  return borderPointMap;
}

/**
 * Get corner effective coord by border
 * @param {string} border
 * @param {Object} borderObject
 * @return {Array}
 */
function getStartAndEndCorner(border, borderObject) {
  switch (border) {
    case 'top':
    case 'bottom':
      return [borderObject.right, borderObject.left];
    case 'left':
    case 'right':
      return [borderObject.top, borderObject.bottom];
  }
}

/**
 * Get effective coord of point by the border of the point
 * @param {string} border
 * @param {Array} point
 * @return {number}
 */
function getEffectiveCoord(border, point) {
  return ['top', 'bottom'].includes(border) ? point[0] : point[1];
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
  const children = [];
  contourMap.forEach((lines) => {
    lines.forEach((shape) => {
      shape.points = shape.points.map((point) => {
        return Array.isArray(point) ? point : [point.x, point.y];
      });
    });
  });
  if (isArea) {
    const [left, bottom] = minPoint;
    const [right, top] = maxPoint;
    const border = {left, bottom, right, top};
    const borderLines = [];
    contourMap.forEach((lines, z) => {
      const index = contours.indexOf(z);
      const color = contourColorMap.get(z);
      lines.forEach((shape) => {
        const {points, config} = shape;
        if (config.circle) {
          if (config.updateContour) {
            children.push({
              z,
              index: index + 1,
              points,
              color: contourColorMap.get(contours[index + 1]),
            });
          } else {
            children.push({
              z,
              index,
              points,
              color,
            });
          }
          return;
        }
        borderLines.push(shape);
      });
    });
    if (borderLines.length) {
      children.push(...completeAreaByBorderLines(border, borderLines, contourColorMap, contours));
    }
  } else {
    contourMap.forEach((lines, z) => {
      const index = contours.indexOf(z);
      const color = contourColorMap.get(z);
      lines.forEach((shape) => {
        const {points} = shape;
        children.push({
          z,
          index,
          points,
          color,
        });
      });
    });
  }
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
      const newChildren = children.map((shape) => {
        let {index, points, color} = shape;
        points = points.map((point) => {
          return api.coord(point);
        });
        return isArea ? useSimplePolygon(index, points, color) : useContourLine(points, color);
      });
      return {
        type: 'group',
        children: newChildren,
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
    ? parseInt(number * factor) / factor
    : (parseInt(number * factor) + 1) / factor;
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
    ? (parseInt(number * factor) - 1) / factor
    : parseInt(number * factor) / factor;
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
  const min = zList[0];
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

let globalContour;
let globalPointMatrix;

/**
 * Calculate Map<z, [line as points, line as points]> with contours and matrix of point
 * @param {Array<number>} contours Array<z>
 * @param {Array} pointMatrix
 * @return {Map<number, Array<Lines>>}
 */
function calContoursPoints(contours, pointMatrix) {
  globalPointMatrix = pointMatrix;
  const cellsNumber = pointMatrix.length - 1;
  const contourPointMap = new Map();
  contours.forEach((value) => {
    globalContour = value;
    const shapes = [];
    contourPointMap.set(value, shapes);
    const cellMatrix = [];
    for (let row = 0; row < cellsNumber; row++) {
      cellMatrix.push([]);
      for (let column = 0; column < cellsNumber; column++) {
        const index = generateCellIndex(value, row, column);
        cellMatrix[row].push({
          index,
          direction: getDirectionByIndex(index),
        });
      }
    }
    generateShapesByCellMatrix(cellMatrix, shapes);
  });
  return contourPointMap;
}

/**
 * @param {string} index
 * @return {string | Array<string>}
 */
function getDirectionByIndex(index) {
  switch (index) {
    case '0000':
    case '1111':
      return null;
    case '0001':
    case '1110':
      return 'left->bottom';
    case '0010':
    case '1101':
      return 'right->bottom';
    case '0011':
    case '1100':
      return 'left->right';
    case '0100':
    case '1011':
      return 'top->right';
    case '0111':
    case '1000':
      return 'top->left';
    case '0110':
    case '1001':
      return 'top->bottom';
    case '01010':
    case '10101':
      return ['top->right', 'left->bottom'];
    case '01011':
    case '10100':
      return ['top->left', 'right->bottom'];
  }
}

/**
 * Generate index of cell contour type
 * @param {number} value
 * @param {number} r
 * @param {number} c
 * @return {string}
 */
function generateCellIndex(value, r, c) {
  const [
    tl,
    tr,
    br,
    bl,
  ] = [
    globalPointMatrix[r][c],
    globalPointMatrix[r][c + 1],
    globalPointMatrix[r + 1][c + 1],
    globalPointMatrix[r + 1][c],
  ];
  let index =
    `${calcValueIndex(tl.z, value)}${calcValueIndex(tr.z, value)}${
      calcValueIndex(br.z, value)}${calcValueIndex(bl.z, value)}`;
  if (['0101', '1010'].includes(index)) {
    const avg = (tl.z + tr.z + br.z + bl.z) / 4;
    index += calcValueIndex(avg, value);
  }
  return index;
}

/**
 * @param {number} pointValue
 * @param {number} value
 * @return {number}
 */
function calcValueIndex(pointValue, value) {
  return pointValue > value ? 1 : 0;
}

const getFlag = (r, c) => `${r},${c}`;

const optimizationSet = new Set();
const existSet = new Set();
let brokenLines;

/**
 * Generate shapes of contour by matrix of cell index
 * @param {Array} cellMatrix
 * @param {Array} shapes
 */
function generateShapesByCellMatrix(cellMatrix, shapes) {
  optimizationSet.clear();
  existSet.clear();
  brokenLines = [];
  for (let i = 0; i < cellMatrix.length; i++) {
    existSet.add(i);
  }
  for (let r = 0; r < cellMatrix.length; r++) {
    for (let c = 0; c < cellMatrix.length; c++) {
      if (optimizationSet.has(getFlag(r, c))) {
        continue;
      }
      const shape = generateShapeByCellIndex(r, c, cellMatrix);
      if (shape && shape.config.complete) {
        shapes.push(shape);
      }
    }
  }
  while (brokenLines.length) {
    const line = brokenLines.shift();
    const newLine = completeLine(line, brokenLines);
    if (newLine) {
      shapes.push(newLine);
    }
  }
}

/**
 * Connect lines
 * @param {Shape} line
 * @param {Array<Shape>} brokenLines
 * @return {Shape}
 */
function completeLine(line, brokenLines) {
  for (let i = 0; i < brokenLines.length; i++) {
    const newLine = verifyConnection(line, brokenLines[i]);
    if (newLine) {
      brokenLines.splice(i, 1);
      const shape = new Shape(newLine);
      const {borders, config} = shape;
      if (borders.length === 2) {
        config.clockwise = [calcClockwise(shape, true), calcClockwise(shape, false)];
        config.complete = true;
        return shape;
      } else {
        return completeLine(newLine, brokenLines);
      }
    }
  }
}

/**
 * @param {Shape} shape1
 * @param {Shape} shape2
 * @return {Shape}
 */
function verifyConnection(shape1, shape2) {
  const points1 = shape1.points;
  const points2 = shape2.points;
  const start1 = points1[0];
  const end1 = points1[points1.length - 1];
  const start2 = points2[0];
  const end2 = points2[points2.length - 1];
  const border1 = shape1.borders;
  const border2 = shape2.borders;
  const indexes1 = shape1.indexes;
  const indexes2 = shape2.indexes;
  let points;
  let borders;
  let indexes;
  if (start1.x === start2.x && start1.y === start2.y) {
    points2.shift();
    indexes2.shift();
    points = points1.reverse().concat(points2);
    borders = border1.concat(border2);
    indexes = indexes1.reverse().concat(indexes2);
  }
  if (start1.x === end2.x && start1.y === end2.y) {
    points1.shift();
    indexes1.shift();
    points = points2.concat(points1);
    borders = border2.concat(border1);
    indexes = indexes2.concat(indexes1);
  }
  if (end1.x === start2.x && end1.y === start2.y) {
    points2.shift();
    indexes2.shift();
    points = points1.concat(points2);
    borders = border1.concat(border2);
    indexes = indexes1.concat(indexes2);
  }
  if (end1.x === end2.x && end1.y === end2.y) {
    points1.pop();
    indexes1.pop();
    points = points1.concat(points2.reverse());
    borders = border1.concat(border2);
    indexes = indexes1.concat(indexes2.reverse());
  }
  if (points) {
    return {
      z: globalContour,
      points,
      borders,
      indexes,
    };
  }
}

/**
 * @param {number} r
 * @param {number} c
 * @param {string} position
 * @return {Object}
 */
function calcPointCoord(r, c, position) {
  const [
    topLeft,
    topRight,
    bottomRight,
    bottomLeft,
  ] = [
    globalPointMatrix[r][c],
    globalPointMatrix[r][c + 1],
    globalPointMatrix[r + 1][c + 1],
    globalPointMatrix[r + 1][c],
  ];
  switch (position) {
    case 'top':
      return calHorizontalContourPoint(topLeft, topRight, globalContour);
    case 'bottom':
      return calHorizontalContourPoint(bottomLeft, bottomRight, globalContour);
    case 'left':
      return calVerticalContourPoint(topLeft, bottomLeft, globalContour);
    case 'right':
      return calVerticalContourPoint(topRight, bottomRight, globalContour);
  }
}

/**
 * Continue track
 * @param {number} r
 * @param {number} c
 * @param {string} end
 * @param {Array} cellMatrix
 * @param {Shape} shape
 */
function getNextTrack(r, c, end, cellMatrix, shape) {
  switch (end) {
    case 'top':
      continueTrack(r - 1, c, 'bottom', cellMatrix, shape);
      break;
    case 'bottom':
      continueTrack(r + 1, c, 'top', cellMatrix, shape);
      break;
    case 'left':
      continueTrack(r, c - 1, 'right', cellMatrix, shape);
      break;
    case 'right':
      continueTrack(r, c + 1, 'left', cellMatrix, shape);
      break;
  }
}

/**
 * Get end from direction with given start
 * @param {string} start
 * @param {string} direction
 * @return {string}
 */
function getEndByDirection(start, direction) {
  const dirs = direction.split('->');
  const index = dirs.indexOf(start);
  dirs.splice(index, 1);
  const end = dirs[0];
  return end;
}

/**
 * Finish circle track
 * @param {number} r
 * @param {number} c
 * @param {string} start
 * @param {Object} cell
 * @param {Shape} shape
 */
function finishCircleTrack(r, c, start, cell, shape) {
  const {direction} = cell;
  const end = getEndByDirection(start, direction);
  const {points, config} = shape;
  config.updateContour = calcUpdateContour(shape);
  config.circle = true;
  points.push(calcPointCoord(r, c, end));
}

/**
 * Calc whether to raise the contour
 * @param {Shape} shape
 * @return {boolean}
 */
function calcUpdateContour(shape) {
  const indexTotal = shape.indexes.join('');
  return findTargetNumber(indexTotal, '1') < findTargetNumber(indexTotal, '0');
}

/**
 * @param {string} source
 * @param {string} target
 * @return {number}
 */
function findTargetNumber(source, target) {
  let result = 0;
  for (let i = 0; i < source.length; i++) {
    if (source[i] === target) {
      result++;
    }
  }
  return result;
}

/**
 * Calc whether the path on the border
 * @param {number} r
 * @param {number} c
 * @param {string} position
 * @return {string | undefined}
 */
function calcPathBorder(r, c, position) {
  const size = existSet.size - 1;
  if (r === 0 && position === 'top') {
    return 'top';
  }
  if (r === size && position === 'bottom') {
    return 'bottom';
  }
  if (c === 0 && position === 'left') {
    return 'left';
  }
  if (c === size && position === 'right') {
    return 'right';
  }
}

/**
 * @param {Shape} shape
 * @param {boolean} isStart
 * @return {boolean}
 */
function calcClockwise(shape, isStart) {
  const {indexes, borders} = shape;
  const border = isStart ? borders[0] : borders[1];
  const index = isStart ? indexes[0] : indexes[indexes.length - 1];
  switch (border) {
    case 'top':
      return ['1000', '1011', '10100', '1001', '10101'].includes(index);
    case 'bottom':
      return ['0010', '1110', '0110', '10100', '10101'].includes(index);
    case 'left':
      return ['0001', '0111', '0011', '01010', '01011'].includes(index);
    case 'right':
      return ['0100', '1110', '01010', '1100', '01011'].includes(index);
  }
}

/**
 * Continue track
 * @param {number} r
 * @param {number} c
 * @param {string} start
 * @param {Array} cellMatrix
 * @param {Shape} shape
 */
function continueTrack(r, c, start, cellMatrix, shape) {
  const {indexes, points, borders, config} = shape;
  if (!existSet.has(r) || !existSet.has(c)) {
    // End on border
    if (borders.length === 2) {
      // Complete line
      config.clockwise = [calcClockwise(shape, true), calcClockwise(shape, false)];
      config.complete = true;
    } else {
      // borders.length < 2
      brokenLines.push(shape);
    }
    return;
  }
  const flag = getFlag(r, c);
  if (optimizationSet.has(flag)) {
    if (!borders.length) {
      // Circle
      finishCircleTrack(r, c, start, cellMatrix[r][c], shape);
      config.complete = true;
    } else {
      // Broken lines
      brokenLines.push(shape);
    }
    return;
  }
  let direction = cellMatrix[r][c].direction;
  if (Array.isArray(direction)) {
    for (let i = 0; i < direction.length; i++) {
      if (direction[i].includes(start)) {
        cellMatrix[r][c].direction = direction[i === 0 ? 1 : 0];
        direction = direction[i];
        break;
      }
    }
  } else {
    optimizationSet.add(flag);
  }
  // Indexes
  indexes.push(cellMatrix[r][c].index);
  // Points
  const end = getEndByDirection(start, direction);
  const point = calcPointCoord(r, c, end);
  points.push(point);
  // Border
  const endBorder = calcPathBorder(r, c, end);
  endBorder && borders.push(endBorder);
  // Continue
  getNextTrack(r, c, end, cellMatrix, shape);
}

/**
 * Class of shape
 */
class Shape {
  z;
  indexes;
  points;
  borders;
  config = {
    complete: null,
    circle: null,
    updateContour: null,
    clockwise: null,
  }
  /**
   * @param {Object} object
   */
  constructor({z, indexes, points, borders}) {
    this.z = z;
    this.indexes = indexes ?? [];
    this.points = points ?? [];
    this.borders = borders ?? [];
  }
}

/**
 * Start track
 * @param {number} r
 * @param {number} c
 * @param {string} direction
 * @param {Array} cellMatrix
 * @return {Shape}
 */
function startTrack(r, c, direction, cellMatrix) {
  if (!existSet.has(r) || !existSet.has(c)) {
    return;
  }
  const shape = new Shape({z: globalContour});
  const [start, end] = direction.split('->');
  const {indexes, points, borders} = shape;
  // Index
  indexes.push(cellMatrix[r][c].index);
  // Points
  points.push(calcPointCoord(r, c, start), calcPointCoord(r, c, end));
  // Border
  const startBorder = calcPathBorder(r, c, start);
  const endBorder = calcPathBorder(r, c, end);
  startBorder && borders.push(startBorder);
  endBorder && borders.push(endBorder);
  // Continue
  getNextTrack(r, c, end, cellMatrix, shape);
  return shape;
}

/**
 * Preparation for start track
 * @param {number} r
 * @param {number} c
 * @param {Array} cellMatrix
 * @return {Shape}
 */
function generateShapeByCellIndex(r, c, cellMatrix) {
  const flag = getFlag(r, c);
  let direction = cellMatrix[r][c].direction;
  if (!direction) {
    return;
  }
  if (Array.isArray(direction)) {
    direction = direction[0];
    cellMatrix[r][c].direction = direction[1];
  } else {
    optimizationSet.add(flag);
  }
  return startTrack(r, c, direction, cellMatrix);
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

/**
 * Get decimal places of number
 * @param {number} value
 * @return {number}
 */
function getDecimalPlaces(value) {
  return Number.isInteger(value) ? 0 : (value + '').split('.')[1].length;
}

import {getGradientColor} from '@/js/utils';

import echarts, {echartsThemeName} from '@/js/echarts';

import CommonProperty from '@/common/common-property';

const convergencePointColor = CommonProperty.convergencePointColor;

// Chart type
const CONTOUR = 'contour';
const TOPOGRAPHIC = 'topographic';

// Chart series name
const CONVERGENCE_POINT = 'convergencePoint';
const PATH_POINTS = 'pathPoints';
const PATH_LINES = 'pathLines';
const POINTS = 'points';
const TOOLTIP = 'tooltip';

// Chart series z index
const chartZIndexMap = {
  [CONVERGENCE_POINT]: 999,
  [PATH_POINTS]: 998,
  [PATH_LINES]: 997,
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
      if (this.tooltipTimer) {
        clearTimeout(this.tooltipTimer);
      }
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
        this.tooltipTimer = null;
      }, 500); // Use to reduce tooltip consumption
    },
    /**
     * Hide tooltip
     */
    hideTooltip() {
      if (this.tooltipTimer) {
        clearTimeout(this.tooltipTimer);
        this.tooltipTimer = null;
      }
      this.chartInstance.dispatchAction({
        type: 'hideTip',
      });
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
      let index = 0;
      const playNextAnimation = () => {
        setTimeout(() => {
          if (!this.chartInstance) return;
          if (index === intervals.length - 1) {
            // Close path animation
            this.chartInstance.setOption({
              series: [usePathLines(rightTop, clearLines, pathWidth, pathColor, false)],
            });
            this.chartInstance.off('finished');
            return;
          }
          clearLines[index] = [x[index], y[index], x[index + 1], y[index + 1]];
          index++;
          this.chartInstance.setOption({
            series: [usePathLines(rightTop, clearLines, pathWidth, pathColor, true)],
          });
        }, 100); // Buffer time
      };
      if (!this.chartInstance) return;
      this.chartInstance.on('finished', playNextAnimation);
      this.chartInstance.setOption({
        series: [
          usePathLines(rightTop, clearLines, pathWidth, pathColor),
        ],
      });
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
      const {pathWidth, pathColor, unit} = setting;
      // Update path chart
      if (!this.chartInstance) {
        if (!this.initContourMap()) return;
      }
      this.chartInstance.setOption({
        series: [
          ...usePathSeries(path, rightTop, pathWidth, pathColor, unit),
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
      const {contourColors, contoursNumber, pathWidth, pathColor, unit} = setting;
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
        series.push(...usePathSeries(path, rightTop, pathWidth, pathColor, unit));
      }
      // Make sure push order: other -> point series -> point tooltip series -> other
      series.push(usePointSeries(
          pointMatrix,
          this.chartInstance,
      ));
      series.push(usePointTooltip(pointMatrix));
      if (showConvergencePoint && convergencePoint) {
        series.push(useConvergencePoint(convergencePoint, convergencePointColor[this.$store.state.themeIndex]));
      }
      series.push(
          useContourGroup(contours, contourPointMap, leftBottom, rightTop, contourColorMap, isArea),
      );
      this.chartInstance.setOption({
        legend,
        series,
      });
      this.chartInstance.on('mousemove', this.showTooltip);
      this.chartInstance.on('mouseout', this.hideTooltip);
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
      const calcAxisMin = (value) => {
        const min = value.min;
        if (typeof min !== 'number' || Number.isNaN(min)) return;
        const decimalPlaces = getDecimalPlaces(min);
        return decimalPlaces ? min : floorDecimalPlaces(min, decimalPlaces - 1);
      };
      const calcAxisMax = (value) => {
        const max = value.max;
        if (typeof max !== 'number' || Number.isNaN(max)) return;
        const decimalPlaces = getDecimalPlaces(max);
        return decimalPlaces ? max : floorDecimalPlaces(max, decimalPlaces - 1);
      };
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
            let minVal = calcAxisMin(value)
            return minVal ? String(minVal).length > 5
              ? minVal.toFixed(5)
              : minVal : minVal;
          },
          max: (value) => {
            let maxVal = calcAxisMax(value)
            return maxVal ? String(maxVal).length > 5
              ? maxVal.toFixed(5)
              : maxVal : maxVal;
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
            let minVal = calcAxisMin(value)
            return minVal ? String(minVal).length > 5
              ? minVal.toFixed(5)
              : minVal : minVal;
          },
          max: (value) => {
            let maxVal = calcAxisMax(value)
            return maxVal ? String(maxVal).length > 5
              ? maxVal.toFixed(5)
              : maxVal : maxVal;
          },
        },
      });
      return true;
    },
    resize() {
      this.chartInstance && this.chartInstance.resize();
    },
    beforeDestroy() {
      if (this.tooltipTimer) {
        clearTimeout(this.tooltipTimer);
      }
      if (this.chartInstance) {
        this.chartInstance.off('mousemove');
        this.chartInstance.off('mouseout');
      }
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
