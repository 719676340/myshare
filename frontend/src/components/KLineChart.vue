<template>
  <div class="kline-chart" ref="chartContainer">
    <v-chart
      ref="chartRef"
      :option="chartOption"
      :autoresize="true"
      :loading="stockStore.isLoading"
      class="chart-instance"
      @datazoom="handleDataZoom"
    />
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { use } from 'echarts/core'
import { CandlestickChart, BarChart, LineChart, ScatterChart, CustomChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  AxisPointerComponent,
  MarkLineComponent,
  MarkAreaComponent
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
  CustomChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  AxisPointerComponent,
  MarkLineComponent,
  MarkAreaComponent,
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
  props: {
    // Optional: fixed data array to use instead of stockStore.dailyData (practice mode)
    fixedData: {
      type: Array,
      default: null
    },
    // Optional: buy/sell markers [{ date: string, type: 'buy'|'sell', price: number }]
    buySellMarkers: {
      type: Array,
      default: null
    }
  },
  setup(props) {
    const chartContainer = ref(null)
    const chartRef = ref(null)
    const stockStore = useStockStore()
    const chartStore = useChartStore()

    // Debounced VAP dataZoom handler
    let vapDebounceTimer = null

    function handleDataZoom() {
      if (!chartStore.showVAP || !stockStore.currentStock) return
      clearTimeout(vapDebounceTimer)
      vapDebounceTimer = setTimeout(() => {
        const chart = chartRef.value?.chart
        if (!chart) return
        const option = chart.getOption()
        if (!option.dataZoom || !option.dataZoom[0]) return
        const startValue = option.dataZoom[0].startValue
        const endValue = option.dataZoom[0].endValue
        const dateData = option.xAxis[0].data
        if (!dateData || dateData.length === 0) return
        const startDate = dateData[Math.floor(startValue)] || dateData[0]
        const endDate = dateData[Math.ceil(endValue)] || dateData[dateData.length - 1]
        if (startDate && endDate) {
          stockStore.fetchVAPData(startDate, endDate)
        }
      }, 500)
    }

    // Market cycle phase colors
    const CYCLE_COLORS = {
      accumulation: '#2196f3',
      markup: '#4caf50',
      distribution: '#ff9800',
      markdown: '#f44336'
    }

    const chartOption = computed(() => {
      // Multi-timeframe support
      const isMultiTimeframe = chartStore.timeframe !== 'daily'
      // Practice mode: props.fixedData overrides store data
      const ohlcData = props.fixedData || stockStore.dailyData
      const rawData = isMultiTimeframe ? (stockStore.timeframeData || []) : ohlcData
      if (!rawData || rawData.length === 0) {
        return {}
      }

      // Extract chart data arrays
      const dates = rawData.map((d) => d.trade_date)
      const ohlc = rawData.map((d) => [d.open, d.close, d.low, d.high])
      const volumes = rawData.map((d) => d.vol)
      const closes = rawData.map((d) => d.close)

      // Volume data with per-bar color based on up/down
      const volumeData = rawData.map((d) => ({
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
      const totalBars = rawData.length
      const defaultShowBars = 120
      const startPercent = totalBars > defaultShowBars
        ? ((totalBars - defaultShowBars) / totalBars) * 100
        : 0

      // Determine active indicator sub-charts (skip in multi-timeframe mode)
      const activeIndicators = []
      if (!isMultiTimeframe) {
        if (chartStore.showMACD) activeIndicators.push('macd')
        if (chartStore.showRSI) activeIndicators.push('rsi')
        if (chartStore.showKDJ) activeIndicators.push('kdj')
      }

      // Determine if we need a market cycle grid
      const showCycleGrid = chartStore.showCycle && stockStore.advancedData.phases.length > 0

      // Calculate grid layout
      // Base: K-line + volume. Each indicator adds a sub-chart. Cycle adds a narrow strip.
      const klineHeight = 35
      const volumeHeight = 12
      const indicatorHeight = 15
      const cycleHeight = 3
      const gap = 2
      let totalHeight = klineHeight + gap + volumeHeight + gap
      totalHeight += activeIndicators.length * (indicatorHeight + gap)
      if (showCycleGrid) {
        totalHeight += cycleHeight + gap
      }

      // Scale factor to fit everything in 100%
      const scale = totalHeight > 100 ? 100 / totalHeight : 1
      const scaledKline = klineHeight * scale
      const scaledVolume = volumeHeight * scale
      const scaledIndicator = indicatorHeight * scale
      const scaledCycle = cycleHeight * scale
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
        { key: 'ma5', name: 'MA5', data: ma5Data },
        { key: 'ma10', name: 'MA10', data: ma10Data },
        { key: 'ma20', name: 'MA20', data: ma20Data },
        { key: 'ma60', name: 'MA60', data: ma60Data }
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

      // Candlestick series with optional S/R markLine
      const candlestickSeries = {
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
      }

      // Add support/resistance markLine to candlestick series
      // Show only top N levels by strength to avoid clutter
      if (chartStore.showSR && stockStore.advancedData.levels.length > 0) {
        const sortedLevels = [...stockStore.advancedData.levels]
          .sort((a, b) => b.strength - a.strength)
          .slice(0, 8)
        const srMarkLineData = sortedLevels.map((level) => {
          let lineColor, labelPrefix
          if (level.type === 'resistance') {
            lineColor = 'rgba(239,83,80,0.6)'
            labelPrefix = '阻力'
          } else if (level.type === 'support') {
            lineColor = 'rgba(38,166,154,0.6)'
            labelPrefix = '支撑'
          } else {
            lineColor = 'rgba(255,235,59,0.5)'
            labelPrefix = '支撑/阻力'
          }
          return {
            yAxis: level.price,
            name: `${labelPrefix} ${level.price}`,
            lineStyle: { type: 'dashed', color: lineColor, width: 1 },
            label: {
              show: true,
              position: 'end',
              formatter: `${labelPrefix} ${level.price}`,
              color: lineColor.replace(/[\d.]+\)$/, '1)'),
              fontSize: 10
            }
          }
        })
        candlestickSeries.markLine = {
          silent: true,
          symbol: 'none',
          data: srMarkLineData
        }
      }

      series.push(candlestickSeries)

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

      // BOLL overlay (skip in multi-timeframe mode)
      if (!isMultiTimeframe && chartStore.showBOLL && stockStore.indicatorData.boll) {
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

      // Trend lines (shared toggle with S/R per D-03)
      if (chartStore.showSR && stockStore.advancedData.trendLines.length > 0) {
        // Build date-to-index lookup
        const dateIndexMap = new Map(dates.map((d, i) => [d, i]))

        for (const line of stockStore.advancedData.trendLines) {
          const startIdx = dateIndexMap.get(line.start_date)
          const endIdx = dateIndexMap.get(line.end_date)
          if (startIdx == null) continue
          const finalEndIdx = endIdx != null ? endIdx : (dates.length - 1)

          const lineData = new Array(dates.length).fill(null)
          lineData[startIdx] = line.start_price
          lineData[finalEndIdx] = line.end_price

          series.push({
            name: '趋势线',
            type: 'line',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: lineData,
            smooth: false,
            showSymbol: false,
            connectNulls: true,
            lineStyle: { type: 'dashed', color: '#787b86', width: 1, opacity: 0.6 },
            z: 3,
            tooltip: { show: false }
          })
        }
      }

      // Build signal and pattern lookup maps (skip in multi-timeframe mode)
      const signalMap = isMultiTimeframe ? new Map() : new Map(
        (stockStore.vpaData.signals || []).map(s => [s.trade_date, s])
      )
      const patternMap = isMultiTimeframe ? new Map() : new Map(
        (stockStore.vpaData.patterns || []).map(p => [p.trade_date, p])
      )

      // Build divergence lookup map
      const divergenceMap = new Map(
        (stockStore.advancedData.divergences || []).map(d => [d.trade_date, d])
      )

      // Determine anomaly signal types (visually distinct from confirmation)
      const anomalyTypes = ['long_candle_low_volume', 'short_candle_high_volume', 'rising_volume_decline']

      // Confirmation signal markers (triangles) per D-06 (skip in multi-timeframe)
      if (!isMultiTimeframe && chartStore.showSignals) {
        // Build confirmation signal data (up and down separately for different symbols)
        const confirmUpData = []
        const confirmDownData = []

        for (let i = 0; i < dates.length; i++) {
          const signal = signalMap.get(dates[i])
          if (!signal || anomalyTypes.includes(signal.signal_type)) continue
          const high = rawData[i].high
          const low = rawData[i].low
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

        // Anomaly + divergence signal markers (diamonds, yellow) per D-07
        const anomalyData = []
        for (let i = 0; i < dates.length; i++) {
          const signal = signalMap.get(dates[i])
          if (signal && anomalyTypes.includes(signal.signal_type)) {
            const high = rawData[i].high
            const low = rawData[i].low
            const offset = (high - low) * 0.3 || high * 0.01
            anomalyData.push({
              value: [i, high + offset],
              itemStyle: { color: '#ffeb3b' }
            })
          }
          // Divergence signals (yellow diamonds) per VPA-04
          const divergence = divergenceMap.get(dates[i])
          if (divergence) {
            const high = rawData[i].high
            const low = rawData[i].low
            const offset = (high - low) * 0.5 || high * 0.015
            anomalyData.push({
              value: [i, high + offset],
              itemStyle: { color: '#ffeb3b' }
            })
          }
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

      // K-line pattern markers (dots above bars) per D-08 (skip in multi-timeframe)
      if (!isMultiTimeframe && chartStore.showPatterns) {
        const patternDotData = []
        for (let i = 0; i < dates.length; i++) {
          const pattern = patternMap.get(dates[i])
          if (!pattern) continue
          const high = rawData[i].high
          const low = rawData[i].low
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

      // VAP histogram overlay (custom series) per ADVAN-04
      if (chartStore.showVAP && stockStore.advancedData.vap.length > 0) {
        const vapData = stockStore.advancedData.vap
        const maxVol = Math.max(...vapData.map(v => v.volume))
        if (maxVol > 0) {
          // Calculate bin size from VAP data
          const priceLevels = vapData.map(v => v.price_level).sort((a, b) => a - b)
          const binSize = priceLevels.length > 1 ? priceLevels[1] - priceLevels[0] : 0.5

          series.push({
            name: 'VAP',
            type: 'custom',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: vapData.map(bin => ({
              value: [dates.length - 1, bin.price_level, bin.volume, bin.up_volume || 0, bin.down_volume || 0]
            })),
            renderItem: function (params, api) {
              const dataIndex = params.dataIndex
              const bin = vapData[dataIndex]
              if (!bin) return

              // Get pixel coordinates for price level boundaries
              const priceTop = api.coord([0, bin.price_level + binSize / 2])
              const priceBottom = api.coord([0, bin.price_level - binSize / 2])
              if (!priceTop || !priceBottom) return

              const barPixelHeight = Math.max(Math.abs(priceTop[1] - priceBottom[1]), 2)

              // Use coordSys for the actual visible grid pixel boundaries
              // This works correctly regardless of zoom/pan state
              const gridRight = params.coordSys.x + params.coordSys.width
              const gridPixelWidth = params.coordSys.width
              // VAP bars occupy the rightmost 20% of the chart
              const vapMaxWidth = gridPixelWidth * 0.2
              const barPixelWidth = (bin.volume / maxVol) * vapMaxWidth

              const color = (bin.up_volume || 0) > (bin.down_volume || 0)
                ? 'rgba(239,83,80,0.3)'
                : 'rgba(38,166,154,0.3)'

              return {
                type: 'rect',
                shape: {
                  x: gridRight - barPixelWidth,
                  y: priceBottom[1],
                  width: barPixelWidth,
                  height: barPixelHeight
                },
                style: {
                  fill: color
                },
                clip: true
              }
            },
            z: 2,
            silent: true
          })
        }
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

      // Market cycle grid and bands
      if (showCycleGrid) {
        const cycleGridIndex = grids.length
        const cycleXAxisIndex = xAxes.length
        const cycleYAxisIndex = yAxes.length

        grids.push({
          left: 60,
          right: 60,
          top: currentTop + '%',
          height: scaledCycle + '%'
        })

        xAxes.push({
          type: 'category',
          data: dates,
          gridIndex: cycleGridIndex,
          axisLine: { lineStyle: { color: BORDER_COLOR } },
          axisLabel: { show: false },
          axisTick: { show: false },
          boundaryGap: true,
          min: 'dataMin',
          max: 'dataMax'
        })

        yAxes.push({
          type: 'value',
          gridIndex: cycleGridIndex,
          show: false,
          min: 0,
          max: 1
        })

        allXAxisIndices.push(cycleXAxisIndex)

        // Build markArea data for phases
        const dateIndexMap = new Map(dates.map((d, i) => [d, i]))
        const phaseMarkArea = []

        for (const phase of stockStore.advancedData.phases) {
          const startIdx = dateIndexMap.get(phase.start_date)
          let endIdx = dateIndexMap.get(phase.end_date)
          if (startIdx == null) continue
          if (endIdx == null) endIdx = dates.length - 1

          const phaseColor = CYCLE_COLORS[phase.phase] || '#787b86'
          phaseMarkArea.push({
            name: phase.phase,
            xAxis: startIdx,
            xAxisEnd: endIdx,
            itemStyle: {
              color: phaseColor,
              opacity: 0.3
            }
          })
        }

        // Invisible line series with markArea for cycle bands
        series.push({
          name: '市场循环',
          type: 'line',
          xAxisIndex: cycleXAxisIndex,
          yAxisIndex: cycleYAxisIndex,
          data: dates.map(() => 0.5),
          showSymbol: false,
          lineStyle: { width: 0 },
          markArea: {
            silent: true,
            data: phaseMarkArea.map(area => [
              {
                xAxis: area.xAxis,
                itemStyle: area.itemStyle,
                name: area.name
              },
              {
                xAxis: area.xAxisEnd
              }
            ])
          }
        })

        // Add legend entries for the 4 cycle phases
        const phaseLabels = {
          accumulation: '吸筹',
          markup: '上涨',
          distribution: '派发',
          markdown: '下跌'
        }
        for (const [phaseKey, phaseLabel] of Object.entries(phaseLabels)) {
          legendData.push(phaseLabel)
          series.push({
            name: phaseLabel,
            type: 'line',
            xAxisIndex: cycleXAxisIndex,
            yAxisIndex: cycleYAxisIndex,
            data: [],
            showSymbol: false,
            lineStyle: { color: CYCLE_COLORS[phaseKey], width: 8 }
          })
        }

        currentTop += scaledCycle + scaledGap
      }

      // Buy/Sell markers for practice mode
      if (props.buySellMarkers && props.buySellMarkers.length > 0) {
        const buyMarkers = props.buySellMarkers
          .filter(m => m.type === 'buy')
          .map(m => {
            const idx = rawData.findIndex(d => d.trade_date === m.date)
            return idx >= 0 ? [idx, m.price] : null
          })
          .filter(Boolean)

        const sellMarkers = props.buySellMarkers
          .filter(m => m.type === 'sell')
          .map(m => {
            const idx = rawData.findIndex(d => d.trade_date === m.date)
            return idx >= 0 ? [idx, m.price] : null
          })
          .filter(Boolean)

        if (buyMarkers.length > 0) {
          series.push({
            type: 'scatter',
            name: '买入',
            data: buyMarkers,
            symbol: 'triangle',
            symbolSize: 14,
            symbolRotate: 0,
            itemStyle: { color: '#ef5350' },
            zlevel: 10,
            xAxisIndex: 0,
            yAxisIndex: 0
          })
        }

        if (sellMarkers.length > 0) {
          series.push({
            type: 'scatter',
            name: '卖出',
            data: sellMarkers,
            symbol: 'triangle',
            symbolSize: 14,
            symbolRotate: 180,
            itemStyle: { color: '#26a69a' },
            zlevel: 10,
            xAxisIndex: 0,
            yAxisIndex: 0
          })
        }
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

            // Signal and pattern info in tooltip (skip in multi-timeframe)
            let vpaInfo = ''
            if (!isMultiTimeframe) {
              const dateStr = candleParam.axisValue
              const signal = signalMap.get(dateStr)
              const pattern = patternMap.get(dateStr)
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
            }

            // Divergence info in tooltip
            const divergence = divergenceMap.get(candleParam.axisValue)
            let divInfo = ''
            if (divergence) {
              divInfo = '<div style="margin-top:4px;border-top:1px solid #363a45;padding-top:4px">'
              divInfo += `<div style="color:#ffeb3b">背离: ${divergence.description}</div>`
              divInfo += '</div>'
            }

            // Timeframe label
            const tfLabel = isMultiTimeframe ? (chartStore.timeframe === 'weekly' ? '周K' : '月K') : ''

            return `<div style="font-size:12px;line-height:1.6">
              <div style="margin-bottom:4px;font-weight:600">${tfLabel ? tfLabel + ' ' : ''}${date}</div>
              <div>开盘: ${open}  收盘: <span style="color:${changeColor}">${close}</span></div>
              <div>最高: ${high}  最低: ${low}</div>
              <div>涨跌: <span style="color:${changeColor}">${arrow} ${change.toFixed(2)} (${changePct}%)</span></div>
              <div>成交量: ${typeof vol === 'object' ? vol.value : vol}</div>
              <div style="margin-top:4px;border-top:1px solid ${BORDER_COLOR};padding-top:4px">${maLines}</div>
              ${indicatorLines.join('')}
              ${vpaInfo}
              ${divInfo}
            </div>`
          }
        },
        series: series
      }
    })

    return {
      chartContainer,
      chartRef,
      chartOption,
      stockStore,
      handleDataZoom
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
