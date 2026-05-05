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
  AxisPointerComponent
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
      // ECharts candlestick data format: [open, close, low, high]
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

      // Build MA series
      const maSeries = [
        { key: 'ma5', name: 'MA5', data: ma5Data, period: 5 },
        { key: 'ma10', name: 'MA10', data: ma10Data, period: 10 },
        { key: 'ma20', name: 'MA20', data: ma20Data, period: 20 },
        { key: 'ma60', name: 'MA60', data: ma60Data, period: 60 }
      ].map(({ key, name, data: maData, period }) => ({
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

      return {
        animation: false,
        backgroundColor: BG_COLOR,
        // Axis pointer link for synchronized crosshair
        axisPointer: {
          link: [{ xAxisIndex: [0, 1] }]
        },
        // Legend for MA lines (top-left per D-11)
        legend: {
          data: ['MA5', 'MA10', 'MA20', 'MA60'],
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
        // Grid layout: 75/25 split (per D-08)
        grid: [
          {
            left: 60,
            right: 60,
            top: 40,
            bottom: '28%'
          },
          {
            left: 60,
            right: 60,
            top: '76%',
            bottom: 50
          }
        ],
        // X-axis (two, one per grid)
        xAxis: [
          {
            type: 'category',
            data: dates,
            gridIndex: 0,
            axisLine: { lineStyle: { color: BORDER_COLOR } },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            axisTick: { show: false },
            boundaryGap: true,
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLine: { lineStyle: { color: BORDER_COLOR } },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            axisTick: { show: false },
            boundaryGap: true,
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        // Y-axis (two, one per grid)
        yAxis: [
          {
            type: 'value',
            gridIndex: 0,
            position: 'right',
            scale: true,
            axisLine: { show: false },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            splitLine: { lineStyle: { color: BORDER_COLOR, opacity: 0.3 } }
          },
          {
            type: 'value',
            gridIndex: 1,
            position: 'right',
            scale: false,
            axisLine: { show: false },
            axisLabel: { color: TEXT_MUTED, fontSize: 11 },
            splitLine: { show: false }
          }
        ],
        // Data zoom (per D-03, D-09)
        dataZoom: [
          {
            type: 'slider',
            xAxisIndex: [0, 1],
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
            xAxisIndex: [0, 1],
            zoomOnMouseWheel: true,
            moveOnMouseMove: true,
            moveOnMouseWheel: false
          }
        ],
        // Tooltip with OHLCV display (per CHART-02)
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
            const volumeParam = params.find((p) => p.seriesType === 'bar')
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
            const maParams = params.filter((p) => p.seriesType === 'line')
            const maLines = maParams.map((p) => {
              const val = p.data !== null && p.data !== undefined ? p.data : '-'
              return `<span style="color:${p.color}">${p.seriesName}: ${val}</span>`
            }).join('<br/>')

            const changeColor = isUp ? UP_COLOR : DOWN_COLOR
            const arrow = isUp ? '▲' : '▼'

            return `<div style="font-size:12px;line-height:1.6">
              <div style="margin-bottom:4px;font-weight:600">${date}</div>
              <div>开盘: ${open}  收盘: <span style="color:${changeColor}">${close}</span></div>
              <div>最高: ${high}  最低: ${low}</div>
              <div>涨跌: <span style="color:${changeColor}">${arrow} ${change.toFixed(2)} (${changePct}%)</span></div>
              <div>成交量: ${typeof vol === 'object' ? vol.value : vol}</div>
              <div style="margin-top:4px;border-top:1px solid ${BORDER_COLOR};padding-top:4px">${maLines}</div>
            </div>`
          }
        },
        // Series
        series: [
          // Candlestick (K-line)
          {
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
          },
          // Volume bars
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumeData,
            barMaxWidth: 8
          },
          // MA lines
          ...maSeries
        ]
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
