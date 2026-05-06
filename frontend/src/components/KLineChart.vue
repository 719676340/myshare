<template>
  <div class="kline-chart" ref="chartContainer">
    <v-chart
      :option="chartOption"
      :autoresize="true"
      :loading="stockStore.isLoading"
      class="chart-instance"
    />
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { use } from 'echarts/core'
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  AxisPointerComponent,
  MarkLineComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useStockStore } from '@/stores/stock'
import { useChartStore } from '@/stores/chart'

// Register ECharts components
use([
  CandlestickChart,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  AxisPointerComponent,
  MarkLineComponent,
  CanvasRenderer
])

// Colors per D-10
const MA_COLORS = {
  ma5: '#ffffff',  // white
  ma10: '#ffeb3b', // yellow
  ma20: '#e040fb', // purple
  ma60: '#26a69a'  // green
}

const UP_COLOR = '#ef5350'    // A-share red for up
const DOWN_COLOR = '#26a69a'  // A-share green for down
const BG_COLOR = '#131722'
const BORDER_COLOR = '#363a45'
const TEXT_MUTED = '#787b86'
const TEXT_PRIMARY = '#d1d4dc'

/**
 * Calculate Simple Moving Average
 */
function calculateMA(closeData, period) {
  const result = []
  for (let i = 0; i < closeData.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += closeData[i - j]
      }
      result.push(+(sum / period).toFixed(2))
    }
  }
  return result
}

/**
 * Align indicator data with K-line dates using a lookup map
 * @param {string[]} dates - K-line date array
 * @param {Array} indicatorData - indicator data from backend [{trade_date, ...values}]
 * @param {string} valueKey - key to extract from indicator data point
 * @returns {Array} - values aligned with dates (null where no match)
 */
function alignIndicatorData(dates, indicatorData, valueKey) {
  if (!indicatorData || indicatorData.length === 0) {
    return dates.map(() => null)
  }
  const map = new Map(indicatorData.map((d) => [d.trade_date, d]))
  return dates.map((date) => {
    const point = map.get(date)
    return point != null && point[valueKey] != null ? point[valueKey] : null
  })
}

export default {
  name: 'KLineChart',
  components: {
    VChart
  },
  setup() {
    const chartContainer = ref(null)
    const stockStore = useStockStore()
    const chartStore = useChartStore()

    const chartOption = computed(() => {
      const data = stockStore.dailyData
      if (!data || data.length === 0) {
        return {}
      }

      // Extract chart data arrays
      const dates = data.map((d) => d.trade_date)
      const ohlc = data.map((d) => [d.open, d.close, d.low, d.high])
      const volumes = data.map((d) => d.vol)
      const closes = data.map((d) => d.close)

      // Volume data with per-bar color based on up/down
      const volumeData = data.map((d) => ({
        value: d.vol,
        itemStyle: {
          color: d.close >= d.open ? UP_COLOR : DOWN_COLOR,
          opacity: 0.7
        }
      }))

      // Calculate MAs
      const ma5Data = calculateMA(closes, 5)
      const ma10Data = calculateMA(closes, 10)
      const ma20Data = calculateMA(closes, 20)
      const ma60Data = calculateMA(closes, 60)

      // Default show last 120 bars
      const totalBars = data.length
      const defaultShowBars = 120
      const startPercent = totalBars > defaultShowBars
        ? ((totalBars - defaultShowBars) / totalBars) * 100
        : 0

      // Determine active indicator sub-charts
      const activeIndicators = []
      if (chartStore.showMACD) activeIndicators.push('macd')
      if (chartStore.showRSI) activeIndicators.push('rsi')
      if (chartStore.showKDJ) activeIndicators.push('kdj')

      // Calculate grid layout
      // Base: K-line + volume. Each indicator adds a sub-chart.
      // Heights: K-line=35%, volume=12%, each indicator=15%
      const klineHeight = 35
      const volumeHeight = 12
      const indicatorHeight = 15
      const gap = 2 // gap between grids
      const totalHeight = klineHeight + gap + volumeHeight + gap + activeIndicators.length * (indicatorHeight + gap)

      // Scale factor to fit everything in 100%
      const scale = totalHeight > 100 ? 100 / totalHeight : 1
      const scaledKline = klineHeight * scale
      const scaledVolume = volumeHeight * scale
      const scaledIndicator = indicatorHeight * scale
      const scaledGap = gap * scale

      // Build grids dynamically
      const grids = []
      const xAxes = []
      const yAxes = []
      const series = []
      const legendData = ['MA5', 'MA10', 'MA20', 'MA60']

      // Track xAxisIndex for each grid
      let currentTop = scaledGap

      // Grid 0: K-line main chart
      grids.push({
        left: 60,
        right: 60,
        top: currentTop + '%',
        height: scaledKline + '%'
      })
      xAxes.push({
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: BORDER_COLOR } },
        axisLabel: { show: false },
        axisTick: { show: false },
        boundaryGap: true,
        min: 'dataMin',
        max: 'dataMax'
      })
      yAxes.push({
        type: 'value',
        gridIndex: 0,
        position: 'right',
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: TEXT_MUTED, fontSize: 11 },
        splitLine: { lineStyle: { color: BORDER_COLOR, opacity: 0.3 } }
      })

      currentTop += scaledKline + scaledGap

      // Grid 1: Volume (always present)
      grids.push({
        left: 60,
        right: 60,
        top: currentTop + '%',
        height: scaledVolume + '%'
      })
      xAxes.push({
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: BORDER_COLOR } },
        axisLabel: { show: false },
        axisTick: { show: false },
        boundaryGap: true,
        min: 'dataMin',
        max: 'dataMax'
      })
      yAxes.push({
        type: 'value',
        gridIndex: 1,
        position: 'right',
        scale: false,
        axisLine: { show: false },
        axisLabel: { color: TEXT_MUTED, fontSize: 11 },
        splitLine: { show: false }
      })

      currentTop += scaledVolume + scaledGap

      // Build MA series
      const maSeries = [
        { key: 'ma5', name: 'MA5', data: ma5Data, period: 5 },
        { key: 'ma10', name: 'MA10', data: ma10Data, period: 10 },
        { key: 'ma20', name: 'MA20', data: ma20Data, period: 20 },
        { key: 'ma60', name: 'MA60', data: ma60Data, period: 60 }
      ].map(({ key, name, data: maData }) => ({
        name,
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: maData,
        smooth: false,
        showSymbol: false,
        lineStyle: {
          color: MA_COLORS[key],
          width: 1
        },
        z: 5
      }))

      // Candlestick series
      series.push({
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: UP_COLOR,
          color0: DOWN_COLOR,
          borderColor: UP_COLOR,
          borderColor0: DOWN_COLOR
        }
      })

      // Volume series
      series.push({
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        barMaxWidth: 8
      })

      // MA lines
      series.push(...maSeries)

      // BOLL overlay on K-line main chart (grid 0)
      if (chartStore.showBOLL && stockStore.indicatorData.boll) {
        const bollData = stockStore.indicatorData.boll.data
        const upperData = alignIndicatorData(dates, bollData, 'upper')
        const middleData = alignIndicatorData(dates, bollData, 'middle')
        const lowerData = alignIndicatorData(dates, bollData, 'lower')

        series.push({
          name: 'BOLL上轨',
          type: 'line',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: upperData,
          smooth: false,
          showSymbol: false,
          lineStyle: { color: '#e040fb', width: 1, type: 'dashed' },
          z: 5
        })
        series.push({
          name: 'BOLL中轨',
          type: 'line',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: middleData,
          smooth: false,
          showSymbol: false,
          lineStyle: { color: '#e040fb', width: 1 },
          z: 5
        })
        series.push({
          name: 'BOLL下轨',
          type: 'line',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: lowerData,
          smooth: false,
          showSymbol: false,
          lineStyle: { color: '#e040fb', width: 1, type: 'dashed' },
          z: 5
        })
        legendData.push('BOLL上轨', 'BOLL中轨', 'BOLL下轨')
      }

      // Indicator sub-charts
      const allXAxisIndices = [0, 1]

      for (const indicator of activeIndicators) {
        const gridIndex = grids.length
        const xAxisIndex = xAxes.length
        const yAxisIndex = yAxes.length

        // Add grid
        grids.push({
          left: 60,
          right: 60,
          top: currentTop + '%',
          height: scaledIndicator + '%'
        })

        // Add x-axis (shared data)
        xAxes.push({
          type: 'category',
          data: dates,
          gridIndex: gridIndex,
          axisLine: { lineStyle: { color: BORDER_COLOR } },
          axisLabel: { show: false },
          axisTick: { show: false },
          boundaryGap: true,
          min: 'dataMin',
          max: 'dataMax'
        })

        allXAxisIndices.push(xAxisIndex)

        if (indicator === 'macd') {
          // MACD sub-chart
          yAxes.push({
            type: 'value',
            gridIndex: gridIndex,
            position: 'right',
            scale: true,
            axisLine: { show: false },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            splitLine: { lineStyle: { color: BORDER_COLOR, opacity: 0.3 } }
          })

          const macdData = stockStore.indicatorData.macd?.data
          const macdValues = alignIndicatorData(dates, macdData, 'macd')
          const signalValues = alignIndicatorData(dates, macdData, 'signal')
          const histogramValues = alignIndicatorData(dates, macdData, 'histogram')

          // MACD line
          series.push({
            name: 'MACD',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: macdValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#2962ff', width: 1 },
            z: 5
          })

          // Signal line
          series.push({
            name: 'Signal',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: signalValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#ff6d00', width: 1 },
            z: 5
          })

          // Histogram bars with positive/negative coloring
          const histogramBarData = histogramValues.map((v) => ({
            value: v,
            itemStyle: {
              color: v != null && v >= 0 ? '#ef5350' : '#26a69a'
            }
          }))

          series.push({
            name: 'Histogram',
            type: 'bar',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: histogramBarData,
            barMaxWidth: 4
          })

          legendData.push('MACD', 'Signal', 'Histogram')
        } else if (indicator === 'rsi') {
          // RSI sub-chart
          yAxes.push({
            type: 'value',
            gridIndex: gridIndex,
            position: 'right',
            scale: true,
            axisLine: { show: false },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            splitLine: { lineStyle: { color: BORDER_COLOR, opacity: 0.3 } },
            min: 0,
            max: 100
          })

          const rsiData = stockStore.indicatorData.rsi?.data
          const rsiValues = alignIndicatorData(dates, rsiData, 'rsi')

          series.push({
            name: 'RSI',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: rsiValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#e040fb', width: 1 },
            z: 5,
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { color: TEXT_MUTED, type: 'dashed', width: 1, opacity: 0.5 },
              data: [
                { yAxis: 30, label: { show: true, formatter: '30', color: TEXT_MUTED, fontSize: 10 } },
                { yAxis: 70, label: { show: true, formatter: '70', color: TEXT_MUTED, fontSize: 10 } }
              ]
            }
          })

          legendData.push('RSI')
        } else if (indicator === 'kdj') {
          // KDJ sub-chart
          yAxes.push({
            type: 'value',
            gridIndex: gridIndex,
            position: 'right',
            scale: true,
            axisLine: { show: false },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            splitLine: { lineStyle: { color: BORDER_COLOR, opacity: 0.3 } }
          })

          const kdjData = stockStore.indicatorData.kdj?.data
          const kValues = alignIndicatorData(dates, kdjData, 'k')
          const dValues = alignIndicatorData(dates, kdjData, 'd')
          const jValues = alignIndicatorData(dates, kdjData, 'j')

          series.push({
            name: 'K',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: kValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#ffffff', width: 1 },
            z: 5
          })
          series.push({
            name: 'D',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: dValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#ffeb3b', width: 1 },
            z: 5
          })
          series.push({
            name: 'J',
            type: 'line',
            xAxisIndex: xAxisIndex,
            yAxisIndex: yAxisIndex,
            data: jValues,
            smooth: false,
            showSymbol: false,
            lineStyle: { color: '#ef5350', width: 1 },
            z: 5
          })

          legendData.push('K', 'D', 'J')
        }

        currentTop += scaledIndicator + scaledGap
      }

      // Show axis labels on the bottom-most grid
      if (xAxes.length > 0) {
        xAxes[xAxes.length - 1].axisLabel = {
          color: TEXT_MUTED,
          fontSize: 11
        }
      }

      // Build dataZoom with all xAxis indices
      const dataZoomConfig = [
        {
          type: 'slider',
          xAxisIndex: allXAxisIndices,
          bottom: 10,
          height: 20,
          start: startPercent,
          end: 100,
          borderColor: BORDER_COLOR,
          fillerColor: 'rgba(41,98,255,0.15)',
          handleStyle: { color: '#2962ff', borderColor: '#2962ff' },
          textStyle: { color: TEXT_MUTED },
          dataBackground: {
            lineStyle: { color: BORDER_COLOR },
            areaStyle: { color: 'rgba(41,98,255,0.05)' }
          }
        },
        {
          type: 'inside',
          xAxisIndex: allXAxisIndices,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          moveOnMouseWheel: false
        }
      ]

      // Build axisPointer link for all grids
      const axisPointerLink = [{ xAxisIndex: allXAxisIndices }]

      return {
        animation: false,
        backgroundColor: BG_COLOR,
        axisPointer: {
          link: axisPointerLink
        },
        legend: {
          data: legendData,
          top: 10,
          left: 10,
          textStyle: {
            color: TEXT_PRIMARY,
            fontSize: 11
          },
          itemWidth: 14,
          itemHeight: 2,
          itemGap: 12
        },
        grid: grids,
        xAxis: xAxes,
        yAxis: yAxes,
        dataZoom: dataZoomConfig,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            crossStyle: { color: TEXT_MUTED },
            lineStyle: { color: TEXT_MUTED }
          },
          backgroundColor: '#1e222d',
          borderColor: BORDER_COLOR,
          borderWidth: 1,
          textStyle: {
            color: TEXT_PRIMARY,
            fontSize: 12
          },
          formatter: function (params) {
            if (!params || params.length === 0) return ''
            // Find the candlestick data
            const candleParam = params.find((p) => p.seriesType === 'candlestick')
            const volumeParam = params.find((p) => p.seriesName === '成交量')
            if (!candleParam) return ''

            const date = candleParam.axisValue
            const d = candleParam.data
            // d is [open, close, low, high]
            const open = d[0]
            const close = d[1]
            const low = d[2]
            const high = d[3]
            const change = close - open
            const changePct = ((change / open) * 100).toFixed(2)
            const isUp = close >= open
            const vol = volumeParam ? volumeParam.data : '-'

            // MA values
            const maParams = params.filter((p) => p.seriesType === 'line' && p.seriesName.startsWith('MA'))
            const maLines = maParams.map((p) => {
              const val = p.data !== null && p.data !== undefined ? p.data : '-'
              return `<span style="color:${p.color}">${p.seriesName}: ${val}</span>`
            }).join('<br/>')

            const changeColor = isUp ? UP_COLOR : DOWN_COLOR
            const arrow = isUp ? '▲' : '▼'

            // Indicator values in tooltip
            const indicatorLines = []
            const indicatorParams = params.filter((p) =>
              !p.seriesName.startsWith('MA') &&
              p.seriesName !== 'K线' &&
              p.seriesName !== '成交量' &&
              p.seriesType === 'line'
            )
            if (indicatorParams.length > 0) {
              indicatorLines.push('<div style="margin-top:4px;border-top:1px solid ' + BORDER_COLOR + ';padding-top:4px">')
              for (const p of indicatorParams) {
                const val = p.data !== null && p.data !== undefined ? p.data : '-'
                indicatorLines.push(`<span style="color:${p.color}">${p.seriesName}: ${val}</span>`)
              }
              indicatorLines.push('</div>')
            }

            return `<div style="font-size:12px;line-height:1.6">
              <div style="margin-bottom:4px;font-weight:600">${date}</div>
              <div>开盘: ${open}  收盘: <span style="color:${changeColor}">${close}</span></div>
              <div>最高: ${high}  最低: ${low}</div>
              <div>涨跌: <span style="color:${changeColor}">${arrow} ${change.toFixed(2)} (${changePct}%)</span></div>
              <div>成交量: ${typeof vol === 'object' ? vol.value : vol}</div>
              <div style="margin-top:4px;border-top:1px solid ${BORDER_COLOR};padding-top:4px">${maLines}</div>
              ${indicatorLines.join('')}
            </div>`
          }
        },
        series: series
      }
    })

    return {
      chartContainer,
      chartOption,
      stockStore
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.kline-chart {
  width: 100%;
  height: 100%;
}

.chart-instance {
  width: 100%;
  height: 100%;
}
</style>
