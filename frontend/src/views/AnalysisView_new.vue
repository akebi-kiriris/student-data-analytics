<template>
  <div class="analysis-page">
    <div class="main-content">
      <!-- 數據來源選擇 -->
      <div class="data-source-section">
        <el-divider>選擇數據來源</el-divider>
        
        <el-upload
          drag
          action="/api/upload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :show-file-list="false"
          accept=".xlsx,.xls"
          style="width: 100%; margin-bottom: 20px;"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽檔案到此處，或<em>點擊上傳</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上傳 .xlsx/.xls 檔案
            </div>
          </template>
        </el-upload>

        <el-divider>或選擇已上傳的檔案</el-divider>

        <el-select v-model="selectedFile" placeholder="請選擇檔案" style="width: 300px" @change="loadFileSheets">
          <el-option
            v-for="file in fileList"
            :key="file"
            :label="file"
            :value="file"
          />
        </el-select>

        <el-select v-if="sheetList.length" v-model="selectedSheet" placeholder="請選擇工作表" style="width: 300px; margin-top: 10px;" @change="loadFileColumns">
          <el-option
            v-for="sheet in sheetList"
            :key="sheet"
            :label="sheet"
            :value="sheet"
          />
        </el-select>
      </div>
      
      <!-- 分析區塊 -->
      <el-divider>數據分析選項</el-divider>
      
      <div class="analysis-blocks">
        <!-- 單欄位統計分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'single-column' }"
          @click="setActiveBlock('single-column')"
        >
          <div class="block-header">
            <span class="nav-icon">📊</span>
            <h3>單欄位統計分析</h3>
          </div>
          <p>選擇單一欄位進行統計分析，查看平均數、變異數等基本統計資訊</p>
        </div>

        <!-- 多科目分年平均分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'multi-subject' }"
          @click="setActiveBlock('multi-subject')"
        >
          <div class="block-header">
            <span class="nav-icon">📈</span>
            <h3>多科目分年平均分析</h3>
          </div>
          <p>比較多個科目在不同年份的平均分數變化趨勢</p>
        </div>

        <!-- 每年入學生數量分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'yearly-admission' }"
          @click="setActiveBlock('yearly-admission')"
        >
          <div class="block-header">
            <span class="nav-icon">👥</span>
            <h3>每年入學生數量分析</h3>
          </div>
          <p>統計並視覺化每年的入學生數量變化</p>
        </div>

        <!-- 入學生學校來源分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'school-source' }"
          @click="setActiveBlock('school-source')"
        >
          <div class="block-header">
            <span class="nav-icon">🏫</span>
            <h3>入學生學校來源分析</h3>
          </div>
          <p>分析各年度入學生的高中來源學校類型分布（國立、私立、市立等）</p>
        </div>

        <!-- 入學生入學管道分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'admission-method' }"
          @click="setActiveBlock('admission-method')"
        >
          <div class="block-header">
            <span class="nav-icon">🚪</span>
            <h3>入學生入學管道分析</h3>
          </div>
          <p>分析學生透過不同入學管道（推甄、申請、指考等）的比例</p>
        </div>
      </div>

      <!-- 分析內容區塊 -->
      <!-- 單欄位統計分析區塊 -->
      <div v-if="activeBlock === 'single-column'" class="analysis-content">
        <el-divider>單欄位統計分析</el-divider>
        <div class="form-group">
          <label>選擇欄位：</label>
          <el-select v-model="selectedColumn" placeholder="請選擇欄位" style="width: 300px" :disabled="columns.length === 0">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="primary" @click="getColumnStats" :disabled="!selectedColumn">計算統計</el-button>
          <el-button @click="showRawData" :disabled="!selectedColumn">顯示原始資料</el-button>
        </div>
      </div>

      <!-- 多科目分年平均分析區塊 -->
      <div v-if="activeBlock === 'multi-subject'" class="analysis-content">
        <el-divider>多科目分年平均分析</el-divider>
        <div class="form-group">
          <label>選擇科目：</label>
          <el-select v-model="selectedSubjects" multiple placeholder="請選擇科目" style="width: 300px">
            <el-option
              v-for="subject in columns"
              :key="subject"
              :label="subject"
              :value="subject"
            />
          </el-select>
        </div>
        <div class="form-group">
          <label>年份欄位：</label>
          <el-select v-model="yearCol" placeholder="請選擇年份欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="success" @click="getMultiSubjectStats" :disabled="selectedSubjects.length === 0 || !yearCol">分析多科目</el-button>
        </div>
      </div>

      <!-- 每年入學生數量分析區塊 -->
      <div v-if="activeBlock === 'yearly-admission'" class="analysis-content">
        <el-divider>每年入學生數量分析</el-divider>
        <div class="form-group">
          <label>年份欄位：</label>
          <el-select v-model="yearlyAdmissionYearCol" placeholder="請選擇年份欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="success" @click="getYearlyAdmissionStats" :disabled="!yearlyAdmissionYearCol">分析入學生數量</el-button>
        </div>
      </div>

      <!-- 入學生學校來源分析區塊 -->
      <div v-if="activeBlock === 'school-source'" class="analysis-content">
        <el-divider>入學生學校來源分析</el-divider>
        <div class="form-group">
          <label>年份欄位：</label>
          <el-select v-model="schoolSourceYearCol" placeholder="請選擇年份欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="form-group">
          <label>學校名稱欄位：</label>
          <el-select v-model="schoolNameCol" placeholder="請選擇學校名稱欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="success" @click="getSchoolSourceStats" :disabled="!schoolSourceYearCol || !schoolNameCol">分析學校來源</el-button>
        </div>
      </div>

      <!-- 入學生入學管道分析區塊 -->
      <div v-if="activeBlock === 'admission-method'" class="analysis-content">
        <el-divider>入學生入學管道分析</el-divider>
        <div class="form-group">
          <label>年份欄位：</label>
          <el-select v-model="admissionMethodYearCol" placeholder="請選擇年份欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="form-group">
          <label>入學管道欄位：</label>
          <el-select v-model="admissionMethodCol" placeholder="請選擇入學管道欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="success" @click="getAdmissionMethodStats" :disabled="!admissionMethodYearCol || !admissionMethodCol">分析入學管道</el-button>
        </div>
      </div>

      <!-- 結果展示區 -->
      <div v-if="currentStats" class="results-panel">
        <div v-if="columnStats" class="stats-card">
          <el-divider>{{ selectedColumn }} 統計資訊</el-divider>
          <div class="stats-summary">
            <p><strong>欄位名稱：</strong>{{ columnStats.column_name }}</p>
            <p><strong>總計筆數：</strong>{{ columnStats.count }} 筆</p>
            <p><strong>平均值：</strong>{{ columnStats.mean?.toFixed(2) || 'N/A' }}</p>
            <p><strong>標準差：</strong>{{ columnStats.std?.toFixed(2) || 'N/A' }}</p>
            <p><strong>最小值：</strong>{{ columnStats.min || 'N/A' }}</p>
            <p><strong>最大值：</strong>{{ columnStats.max || 'N/A' }}</p>
          </div>
          <div id="statsChart" style="width: 100%; height: 400px;"></div>
        </div>

        <div v-if="multiSubjectStats" class="stats-card">
          <el-divider>多科目分年平均分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ multiSubjectStats.year_range }}</p>
            <p><strong>科目數量：</strong>{{ multiSubjectStats.subjects.length }} 個</p>
            <p><strong>分析科目：</strong>{{ multiSubjectStats.subjects.join(', ') }}</p>
          </div>
          <div id="multiSubjectChart" style="width: 100%; height: 400px;"></div>
        </div>

        <div v-if="yearlyAdmissionStats" class="stats-card">
          <el-divider>每年入學生數量分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ yearlyAdmissionStats.year_range }}</p>
            <p><strong>總入學人數：</strong>{{ yearlyAdmissionStats.total_students }} 人</p>
          </div>
          <div id="yearlyAdmissionChart" style="width: 100%; height: 400px;"></div>
        </div>

        <div v-if="schoolSourceStats" class="stats-card">
          <el-divider>入學生學校來源分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ schoolSourceStats.year_range }}</p>
            <p><strong>總人數：</strong>{{ schoolSourceStats.total_students }} 人</p>
          </div>
          <div id="schoolSourceChart" style="width: 100%; height: 400px;"></div>
        </div>

        <div v-if="admissionMethodStats" class="stats-card">
          <el-divider>入學生入學管道分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ admissionMethodStats.year_range }}</p>
            <p><strong>總人數：</strong>{{ admissionMethodStats.total_students }} 人</p>
          </div>
          <div id="admissionMethodChart" style="width: 100%; height: 400px;"></div>
        </div>
      </div>

      <!-- 原始資料表格 -->
      <div v-if="rawData && rawData.length > 0" class="results-panel">
        <el-divider>原始資料 (前50筆)</el-divider>
        <el-table :data="rawData.slice(0, 50)" stripe border style="width: 100%">
          <el-table-column 
            v-for="col in Object.keys(rawData[0] || {})" 
            :key="col" 
            :prop="col" 
            :label="col">
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import Chart from 'chart.js/auto'
import * as echarts from 'echarts'

// 響應式數據
const fileList = ref([])
const selectedFile = ref('')
const sheetList = ref([])
const selectedSheet = ref('')
const columns = ref([])
const selectedColumn = ref('')
const selectedSubjects = ref([])
const yearCol = ref('')
const yearlyAdmissionYearCol = ref('')
const schoolSourceYearCol = ref('')
const schoolNameCol = ref('')
const admissionMethodYearCol = ref('')
const admissionMethodCol = ref('')
const activeBlock = ref('')
const currentStats = ref(null)
const columnStats = ref(null)
const multiSubjectStats = ref(null)
const yearlyAdmissionStats = ref(null)
const schoolSourceStats = ref(null)
const admissionMethodStats = ref(null)
const rawData = ref([])

// 設置活動區塊
const setActiveBlock = (blockName) => {
  activeBlock.value = blockName
  currentStats.value = null
  columnStats.value = null
  multiSubjectStats.value = null
  yearlyAdmissionStats.value = null
  schoolSourceStats.value = null
  admissionMethodStats.value = null
  rawData.value = []
}

// 文件上傳成功處理
const handleUploadSuccess = (response) => {
  ElMessage.success('檔案上傳成功')
  loadFileList()
}

const handleUploadError = () => {
  ElMessage.error('檔案上傳失敗')
}

// 載入文件列表
const loadFileList = async () => {
  try {
    const response = await axios.get('/api/files')
    fileList.value = response.data.files
  } catch (error) {
    ElMessage.error('載入檔案列表失敗')
  }
}

// 載入工作表列表
const loadFileSheets = async () => {
  if (!selectedFile.value) return
  
  try {
    const response = await axios.get(`/api/sheets?filename=${selectedFile.value}`)
    sheetList.value = response.data.sheets
    selectedSheet.value = ''
    columns.value = []
  } catch (error) {
    ElMessage.error('載入工作表失敗')
  }
}

// 載入欄位
const loadFileColumns = async () => {
  if (!selectedFile.value || !selectedSheet.value) return
  
  try {
    const response = await axios.get(`/api/read_columns?filename=${selectedFile.value}&sheet=${selectedSheet.value}`)
    columns.value = response.data.columns
    autoSelectColumns()
  } catch (error) {
    ElMessage.error('載入欄位失敗')
  }
}

// 自動選擇欄位
const autoSelectColumns = () => {
  if (columns.value.length === 0) return
  
  // 自動選擇年份欄位
  const yearColumns = columns.value.filter(col => 
    col.includes('年') || col.includes('學年') || col.includes('入學年')
  )
  if (yearColumns.length > 0) {
    yearCol.value = yearColumns[0]
    yearlyAdmissionYearCol.value = yearColumns[0]
    schoolSourceYearCol.value = yearColumns[0]
    admissionMethodYearCol.value = yearColumns[0]
  }
  
  // 自動選擇學校欄位
  const schoolColumns = columns.value.filter(col => 
    col.includes('學校') || col.includes('高中') || col.includes('高職')
  )
  if (schoolColumns.length > 0) {
    schoolNameCol.value = schoolColumns[0]
  }
  
  // 自動選擇入學管道欄位
  const admissionColumns = columns.value.filter(col => 
    col.includes('管道') || col.includes('入學方式') || col.includes('類別')
  )
  if (admissionColumns.length > 0) {
    admissionMethodCol.value = admissionColumns[0]
  }
}

// 分析方法
const getColumnStats = async () => {
  try {
    const response = await axios.get(`/api/column_stats?filename=${selectedFile.value}&sheet=${selectedSheet.value}&column=${selectedColumn.value}`)
    columnStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderColumnChart(response.data)
  } catch (error) {
    ElMessage.error('統計分析失敗')
  }
}

const getMultiSubjectStats = async () => {
  try {
    const response = await axios.get(`/api/multi_subject_stats?filename=${selectedFile.value}&sheet=${selectedSheet.value}&subjects=${selectedSubjects.value.join(',')}&year_col=${yearCol.value}`)
    multiSubjectStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderMultiSubjectChart(response.data)
  } catch (error) {
    ElMessage.error('多科目分析失敗')
  }
}

const getYearlyAdmissionStats = async () => {
  try {
    const response = await axios.get(`/api/yearly_admission_stats?filename=${selectedFile.value}&sheet=${selectedSheet.value}&year_col=${yearlyAdmissionYearCol.value}`)
    yearlyAdmissionStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderYearlyAdmissionChart(response.data)
  } catch (error) {
    ElMessage.error('入學生數量分析失敗')
  }
}

const getSchoolSourceStats = async () => {
  try {
    const response = await axios.get(`/api/school_source_stats?filename=${selectedFile.value}&sheet=${selectedSheet.value}&year_col=${schoolSourceYearCol.value}&school_col=${schoolNameCol.value}`)
    schoolSourceStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderSchoolSourceChart(response.data)
  } catch (error) {
    ElMessage.error('學校來源分析失敗')
  }
}

const getAdmissionMethodStats = async () => {
  try {
    const response = await axios.get(`/api/admission_method_stats?filename=${selectedFile.value}&sheet=${selectedSheet.value}&year_col=${admissionMethodYearCol.value}&method_col=${admissionMethodCol.value}`)
    admissionMethodStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderAdmissionMethodChart(response.data)
  } catch (error) {
    ElMessage.error('入學管道分析失敗')
  }
}

const showRawData = async () => {
  try {
    const response = await axios.get(`/api/raw_data?filename=${selectedFile.value}&sheet=${selectedSheet.value}&column=${selectedColumn.value}`)
    rawData.value = response.data.data
  } catch (error) {
    ElMessage.error('載入原始資料失敗')
  }
}

// 圖表渲染方法
const renderColumnChart = (data) => {
  // 實現單欄位統計圖表
  console.log('渲染單欄位統計圖表', data)
}

const renderMultiSubjectChart = (data) => {
  // 實現多科目圖表
  console.log('渲染多科目圖表', data)
}

const renderYearlyAdmissionChart = (data) => {
  // 實現年度入學生數量圖表
  console.log('渲染年度入學生數量圖表', data)
}

const renderSchoolSourceChart = (data) => {
  // 實現學校來源圖表
  console.log('渲染學校來源圖表', data)
}

const renderAdmissionMethodChart = (data) => {
  // 實現入學管道圖表
  console.log('渲染入學管道圖表', data)
}

// 初始化
onMounted(() => {
  loadFileList()
})
</script>

<style scoped>
.analysis-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  margin: 0;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  min-height: 100vh;
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
}

.data-source-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

/* 分析區塊樣式 */
.analysis-blocks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
  padding: 20px 0;
}

.analysis-block {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.analysis-block:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.analysis-block.active {
  border-color: #409eff;
  background: #f0f8ff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.block-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.nav-icon {
  font-size: 24px;
  color: #409eff;
}

.analysis-block h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.analysis-block p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.analysis-content {
  padding: 20px;
  background: #fafcff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  margin-top: 20px;
}

.results-panel {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-summary {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #303133;
}

.button-group {
  margin-top: 20px;
}

.button-group .el-button {
  margin-right: 10px;
}
</style>
