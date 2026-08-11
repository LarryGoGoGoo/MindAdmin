<script setup>
/**
 * @description 管理员查看单个用户的心理测试记录
 */
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import dayjs from 'dayjs'

import { getExamrecordResultAPI, getGroupAPI } from '@/api/common'
import ExamRecordTable from './ExamRecordTable.vue'

defineOptions({
  inheritAttrs: false,
})

let { data } = defineProps(['data'])
const user = data?.row || {}

const attempts = ref([])
const selectedAttempt = ref(null)
const report = ref(null)
const isLoading = ref(false)
const isReportLoading = ref(false)
const detailVisible = ref(false)
const chartRef = ref(null)
let chartInstance = null

const userName = computed(() => user.yonghuxingming || user.yonghuzhanghao || `用户${user.id || ''}`)
const factors = computed(() => {
  let list = report.value?.result?.factors
  return Array.isArray(list) ? list : []
})
const warningFactors = computed(() => factors.value.filter(item => item.warning))
const hasScl90Result = computed(() => factors.value.length > 0)

function formatDate(value) {
  if (!value) return '-'
  let date = dayjs(value)
  return date.isValid() ? date.format('YYYY-MM-DD HH:mm') : value
}

function formatScore(value, digits = 2) {
  let number = Number(value)
  if (Number.isNaN(number)) return value ?? '-'
  return number.toFixed(digits)
}

function getAnsweredText(row) {
  if (row.questionCount) {
    return `${row.answeredCount || 0}/${row.questionCount}`
  }
  return row.answeredCount || row.recordCount || 0
}

function getAttemptKey(row) {
  return [row.userid, row.paperid, row.examno || '', row.createdAt || ''].join('-')
}

async function fetchAttempts() {
  if (!user.id) return
  isLoading.value = true
  try {
    let res = await getGroupAPI('examrecord', {
      page: 1,
      limit: 9999,
      userid: user.id,
    })
    attempts.value = res.data.list || []
    if (attempts.value.length) {
      await selectAttempt(attempts.value[0])
    }
  } catch (error) {
    ElMessage.error(error.msg || error.message || '心理测试记录加载失败')
  }
  isLoading.value = false
}

async function selectAttempt(row) {
  selectedAttempt.value = row
  detailVisible.value = false
  await fetchReport(row)
}

async function fetchReport(row) {
  report.value = null
  destroyChart()
  if (!row?.paperid) return

  isReportLoading.value = true
  try {
    let res = await getExamrecordResultAPI({
      paperid: row.paperid,
      userid: user.id,
      examno: row.examno,
    })
    report.value = res.data || {}
    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error(error.msg || error.message || '心理测试报告加载失败')
  }
  isReportLoading.value = false
}

function renderChart() {
  if (!chartRef.value || !factors.value.length || !window.echarts) return
  if (!chartInstance) {
    chartInstance = window.echarts.init(chartRef.value)
  }

  chartInstance.setOption({
    color: ['#4f7cff', '#f56c6c'],
    grid: {
      left: 42,
      right: 20,
      top: 28,
      bottom: 70,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        let item = params?.[0]
        if (!item) return ''
        return `${item.name}<br/>因子分：${formatScore(item.value)}`
      },
    },
    xAxis: {
      type: 'category',
      data: factors.value.map(item => item.name),
      axisTick: { show: false },
      axisLabel: {
        interval: 0,
        rotate: 28,
        color: '#5f6b7a',
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
      splitLine: {
        lineStyle: { color: '#eef1f6' },
      },
      axisLabel: { color: '#7a8594' },
    },
    series: [
      {
        name: '因子分',
        type: 'bar',
        barMaxWidth: 34,
        data: factors.value.map(item => ({
          value: Number(item.score || 0),
          itemStyle: {
            color: item.warning ? '#f56c6c' : '#4f7cff',
            borderRadius: [6, 6, 0, 0],
          },
        })),
        markLine: {
          symbol: 'none',
          lineStyle: {
            color: '#e6a23c',
            type: 'dashed',
          },
          label: {
            formatter: '预警阈值 2',
            color: '#b88230',
          },
          data: [{ yAxis: 2 }],
        },
      },
    ],
  })
}

function resizeChart() {
  chartInstance?.resize()
}

function destroyChart() {
  chartInstance?.dispose()
  chartInstance = null
}

function getAttemptRowClass({ row }) {
  return getAttemptKey(selectedAttempt.value || {}) === getAttemptKey(row) ? 'is-selected-attempt' : ''
}

onMounted(() => {
  fetchAttempts()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  destroyChart()
})
</script>

<template>
  <div class="user-exam-record">
    <div class="user-overview">
      <div>
        <span class="overview-label">用户</span>
        <strong>{{ userName }}</strong>
      </div>
      <div>
        <span class="overview-label">账号</span>
        <strong>{{ user.yonghuzhanghao || '-' }}</strong>
      </div>
      <div>
        <span class="overview-label">记录数</span>
        <strong>{{ attempts.length }}</strong>
      </div>
    </div>

    <el-table
      v-loading="isLoading"
      :data="attempts"
      :row-key="getAttemptKey"
      height="260"
      highlight-current-row
      :row-class-name="getAttemptRowClass"
      @row-click="selectAttempt"
    >
      <el-table-column prop="papername" label="心理测试" min-width="190" />
      <el-table-column prop="myscore" label="总分" width="90" />
      <el-table-column label="作答进度" width="110">
        <template #default="{ row }">{{ getAnsweredText(row) }}</template>
      </el-table-column>
      <el-table-column prop="examno" label="考试编号" min-width="150" />
      <el-table-column label="提交时间" width="170">
        <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click.stop="selectAttempt(row)">查看报告</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="!isLoading && !attempts.length"
      description="该用户暂无心理测试记录"
    />

    <section v-if="selectedAttempt" class="report-panel" v-loading="isReportLoading">
      <div class="report-header">
        <div>
          <h3>{{ selectedAttempt.papername }}</h3>
          <p>考试编号：{{ selectedAttempt.examno || '-' }} · 提交时间：{{ formatDate(selectedAttempt.createdAt) }}</p>
        </div>
        <el-button type="primary" plain @click="detailVisible = !detailVisible">
          {{ detailVisible ? '收起作答明细' : '查看作答明细' }}
        </el-button>
      </div>

      <div class="summary-grid">
        <div class="summary-item">
          <span>总分</span>
          <strong>{{ report?.result?.totalScore ?? report?.score ?? selectedAttempt.myscore ?? '-' }}</strong>
        </div>
        <div class="summary-item">
          <span>总均分</span>
          <strong>{{ report?.result?.averageScore ?? '-' }}</strong>
        </div>
        <div class="summary-item">
          <span>阳性项目</span>
          <strong>{{ report?.result?.positiveItemCount ?? '-' }}</strong>
        </div>
        <div class="summary-item">
          <span>作答题数</span>
          <strong>{{ report?.answeredCount ?? selectedAttempt.answeredCount ?? 0 }}/{{ report?.questionCount ?? selectedAttempt.questionCount ?? 0 }}</strong>
        </div>
      </div>

      <template v-if="hasScl90Result">
        <div class="chart-box" ref="chartRef"></div>

        <div class="factor-list">
          <div v-for="item in factors" :key="item.key" class="factor-row">
            <span class="factor-name">{{ item.name }}</span>
            <div class="factor-bar">
              <span :class="{ warning: item.warning }" :style="{ width: `${Math.min(Number(item.score || 0) / 5 * 100, 100)}%` }"></span>
            </div>
            <strong :class="{ warning: item.warning }">{{ formatScore(item.score) }}</strong>
          </div>
        </div>

        <div class="guidance-box">
          <h4>{{ warningFactors.length ? '预警分析与建议' : '心理分析与建议' }}</h4>
          <template v-if="warningFactors.length">
            <p v-for="item in warningFactors" :key="item.key">
              <strong>{{ item.name }}：</strong>{{ item.guidance }}
            </p>
          </template>
          <p v-else>本次 SCL-90 各因子分未达到预警阈值，建议继续保持稳定作息、适度运动和规律的人际支持。</p>
        </div>
      </template>

      <el-alert
        v-else
        type="info"
        :closable="false"
        show-icon
        title="该测评暂无 SCL-90 因子分析，已展示总分与作答情况。"
      />

      <div v-if="detailVisible" class="detail-table">
        <ExamRecordTable :data="{ row: selectedAttempt }" />
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.user-exam-record {
  width: 100%;
  max-width: 100%;
  color: #273142;
}

.user-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;

  > div {
    padding: 14px 16px;
    border: 1px solid #edf0f5;
    border-radius: 8px;
    background: #fafbfe;
  }

  strong {
    display: block;
    margin-top: 6px;
    font-size: 16px;
  }
}

.overview-label {
  font-size: 12px;
  color: #7a8594;
}

:deep(.is-selected-attempt) {
  --el-table-tr-bg-color: #f2f6ff;
}

.report-panel {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #edf0f5;
}

.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;

  h3 {
    margin: 0 0 6px;
    font-size: 18px;
    font-weight: 650;
  }

  p {
    margin: 0;
    color: #7a8594;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-item {
  padding: 14px;
  border: 1px solid #edf0f5;
  border-radius: 8px;
  background: #fff;

  span {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    color: #7a8594;
  }

  strong {
    font-size: 20px;
  }
}

.chart-box {
  width: 100%;
  height: 320px;
  margin-bottom: 16px;
}

.factor-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  margin-bottom: 18px;
}

.factor-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 48px;
  align-items: center;
  gap: 10px;
  min-height: 28px;
}

.factor-name {
  color: #5f6b7a;
}

.factor-bar {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef1f6;

  span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: #4f7cff;
  }

  span.warning {
    background: #f56c6c;
  }
}

.warning {
  color: #d94f4f;
}

.guidance-box {
  padding: 14px 16px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: #fff8ef;
  border: 1px solid #f6dfbd;

  h4 {
    margin: 0 0 10px;
    color: #9a6118;
  }

  p {
    margin: 8px 0 0;
    line-height: 1.7;
  }
}

.detail-table {
  margin-top: 16px;
}

@media (max-width: 1100px) {
  .user-overview,
  .summary-grid,
  .factor-list {
    grid-template-columns: 1fr;
  }

  .report-header {
    flex-direction: column;
  }
}
</style>
