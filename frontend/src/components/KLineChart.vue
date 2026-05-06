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
import { CandlestickChart, BarChart, LineChart, ScatterChart } from 'echarts/charts'
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
  ScatterChart,
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

      // Build signal and pattern lookup maps
      const signalMap = new Map(
        (stockStore.vpaData.signals || []).map(s => [s.trade_date, s])
      )
      const patternMap = new Map(
        (stockStore.vpaData.patterns || []).map(p => [p.trade_date, p])
      )

      // Determine anomaly signal types (visually distinct from confirmation)
      const anomalyTypes = ['long_candle_low_volume', 'short_candle_high_volume', 'rising_volume_decline']

      // Confirmation signal markers (triangles) per D-06
      if (chartStore.showSignals) {
        // Build confirmation signal data (up and down separately for different symbols)
        const confirmUpData = []
        const confirmDownData = []

        for (let i = 0; i < dates.length; i++) {
          const signal = signalMap.get(dates[i])
          if (!signal || anomalyTypes.includes(signal.signal_type)) continue
          const high = data[i].high
          const low = data[i].low
          const offset = (high - low) * 0.3 || high * 0.01
          if (signal.direction === 'up') {
            confirmUpData.push({
              value: [i, high + offset],
              itemStyle: { color: '#26a69a' }
            })
          } else {
            confirmDownData.push({
              value: [i, low - offset],
              itemStyle: { color: '#ef5350' }
            })
          }
        }

        // Up confirmation signals (triangle pointing up, green)
        series.push({
          name: '确认信号(涨)',
          type: 'scatter',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: confirmUpData,
          symbol: 'triangle',
          symbolSize: 8,
          z: 20
        })

        // Down confirmation signals (triangle pointing down, red)
        series.push({
          name: '确认信号(跌)',
          type: 'scatter',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: confirmDownData,
          symbol: 'triangle',
          symbolSize: 8,
          symbolRotate: 180,
          z: 20
        })

        // Anomaly signal markers (diamonds, yellow) per D-07
        const anomalyData = []
        for (let i = 0; i < dates.length; i++) {
          const signal = signalMap.get(dates[i])
          if (!signal || !anomalyTypes.includes(signal.signal_type)) continue
          const high = data[i].high
          const low = data[i].low
          const offset = (high - low) * 0.3 || high * 0.01
          anomalyData.push({
            value: [i, high + offset],
            itemStyle: { color: '#ffeb3b' }
          })
        }

        series.push({
          name: '异常信号',
          type: 'scatter',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: anomalyData,
          symbol: 'diamond',
          symbolSize: 10,
          z: 20
        })
      } else {
        // Hidden: add empty scatter series so indices stay consistent
        series.push(
          { name: '确认信号(涨)', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0, data: [], symbol: 'triangle', symbolSize: 8, z: 20 },
          { name: '确认信号(跌)', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0, data: [], symbol: 'triangle', symbolSize: 8, symbolRotate: 180, z: 20 },
          { name: '异常信号', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0, data: [], symbol: 'diamond', symbolSize: 10, z: 20 }
        )
      }

      // K-line pattern markers (dots above bars) per D-08
      if (chartStore.showPatterns) {
        const patternDotData = []
        for (let i = 0; i < dates.length; i++) {
          const pattern = patternMap.get(dates[i])
          if (!pattern) continue
          const high = data[i].high
          const low = data[i].low
          const offset = (high - low) * 0.4 || high * 0.015
          patternDotData.push({
            value: [i, high + offset],
            itemStyle: { color: '#d1d4dc' }
          })
        }

        series.push({
          name: 'K线形态',
          type: 'scatter',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: patternDotData,
          symbol: 'circle',
          symbolSize: 6,
          z: 20
        })
      } else {
        series.push({
          name: 'K线形态',
          type: 'scatter',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: [],
          symbol: 'circle',
          symbolSize: 6,
          z: 20
        })
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

            // Signal and pattern info in tooltip
            const dateStr = candleParam.axisValue
            const signal = signalMap.get(dateStr)
            const pattern = patternMap.get(dateStr)
            let vpaInfo = ''
            if (signal || pattern) {
              vpaInfo = '<div style="margin-top:4px;border-top:1px solid #363a45;padding-top:4px">'
              if (signal) {
                const isAnomaly = anomalyTypes.includes(signal.signal_type)
                const signalColor = isAnomaly ? '#ffeb3b' : (signal.direction === 'up' ? '#26a69a' : '#ef5350')
                vpaInfo += `<div style="color:${signalColor}">信号: ${signal.description}</div>`
              }
              if (pattern) {
                vpaInfo += `<div style="color:#d1d4dc">形态: ${pattern.name} - ${pattern.description}</div>`
              }
              vpaInfo += '</div>'
            }

            return `<div style="font-size:12px;line-height:1.6">
              <div style="margin-bottom:4px;font-weight:600">${date}</div>
              <div>开盘: ${open}  收盘: <span style="color:${changeColor}">${close}</span></div>
              <div>最高: ${high}  最低: ${low}</div>
              <div>涨跌: <span style="color:${changeColor}">${arrow} ${change.toFixed(2)} (${changePct}%)</span></div>
              <div>成交量: ${typeof vol === 'object' ? vol.value : vol}</div>
              <div style="margin-top:4px;border-top:1px solid ${BORDER_COLOR};padding-top:4px">${maLines}</div>
              ${indicatorLines.join('')}
              ${vpaInfo}
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
