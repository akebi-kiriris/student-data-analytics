<template>
  <div class="analysis-container">
    <!-- 主內容區域 -->
    <main class="main-content">
      <div class="page-header">
        <h2>數據分析</h2>
      </div>

      <!-- 文件上傳和選擇區域 -->
      <div class="file-section">
        <el-upload
          class="upload-demo"
          :action="uploadUrl"
          :on-success="handleUploadSuccess"
          :before-upload="beforeUpload"
          :show-file-list="false"
          accept=".xlsx,.xls"
        >
          <el-button type="primary">上傳 Excel</el-button>
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
              <div class="block-header">
                <span class="nav-icon">�</span>
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
                <span class="nav-icon">📋</span>
                <h3>入學生入學管道分析</h3>
              </div>
              <p>分析各年度入學生的入學管道分布（申請入學、繁星推薦、自然組、社會組等）</p>
            </div>

            <!-- 地理區域分析 -->
            <div 
              class="analysis-block" 
              :class="{ active: activeBlock === 'geographic' }"
              @click="setActiveBlock('geographic')"
            >
              <div class="block-header">
                <span class="nav-icon">�</span>
                <h3>地理區域分析</h3>
              </div>
              <p>分析學生來源地理區域分布，按北、西、南、東台灣等區域統計</p>
            </div>
          </div>

          <!-- 單欄位統計分析區塊 -->
          <div v-if="activeBlock === 'single-column'" class="analysis-content">
            <h3>單欄位統計分析</h3>
            <div class="form-group">
              <label>選擇欄位：</label>
              <select v-model="selectedColumn" class="form-select" :disabled="columns.length === 0">
                <option value="">請選擇欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getColumnStats" :disabled="!selectedColumn" class="btn btn-primary">計算統計</button>
              <button @click="showRawData" :disabled="!selectedColumn" class="btn btn-secondary">顯示原始資料</button>
            </div>
          </div>

          <!-- 多科目分年平均分析區塊 -->
          <div v-if="activeBlock === 'multi-subject'" class="analysis-content">
            <h3>多科目分年平均分析</h3>
            <div class="form-group">
              <label>選擇科目：</label>
              <select v-model="selectedSubjects" multiple class="form-select">
                <option v-for="subject in columns" :key="subject" :value="subject">{{ subject }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>年份欄位：</label>
              <select v-model="yearCol" class="form-select">
                <option value="">請選擇年份欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getMultiSubjectStats" :disabled="!selectedSubjects.length || !yearCol" class="btn btn-primary">開始分析</button>
            </div>
          </div>

          <!-- 每年入學生數量分析區塊 -->
          <div v-if="activeBlock === 'yearly-admission'" class="analysis-content">
            <h3>每年入學生數量分析</h3>
            <div class="form-group">
              <label>年份欄位：</label>
              <select v-model="admissionYearCol" class="form-select">
                <option value="">請選擇年份欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>性別欄位（可選）：</label>
              <select v-model="genderCol" class="form-select">
                <option value="">請選擇性別欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getYearlyAdmissionStats" :disabled="!admissionYearCol" class="btn btn-primary">分析入學生數量</button>
            </div>
          </div>

          <!-- 入學生學校來源分析區塊 -->
          <div v-if="activeBlock === 'school-source'" class="analysis-content">
            <h3>入學生學校來源分析</h3>
            <div class="form-group">
              <label>年份欄位：</label>
              <select v-model="schoolSourceYearCol" class="form-select">
                <option value="">請選擇年份欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>學校名稱欄位：</label>
              <select v-model="schoolNameCol" class="form-select">
                <option value="">請選擇學校名稱欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getSchoolSourceStats" :disabled="!schoolSourceYearCol || !schoolNameCol" class="btn btn-primary">分析學校來源</button>
            </div>
            <div class="info-box">
              <strong>說明：</strong>系統會自動識別學校類型（國立、市立、縣立、私立、財團、國大轉、私大轉、科大轉、僑生、其他）
            </div>
          </div>

          <!-- 入學生入學管道分析區塊 -->
          <div v-if="activeBlock === 'admission-method'" class="analysis-content">
            <h3>入學生入學管道分析</h3>
            <div class="form-group">
              <label>年份欄位：</label>
              <select v-model="admissionMethodYearCol" class="form-select">
                <option value="">請選擇年份欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>入學管道欄位：</label>
              <select v-model="admissionMethodCol" class="form-select">
                <option value="">請選擇入學管道欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getAdmissionMethodStats" :disabled="!admissionMethodYearCol || !admissionMethodCol" class="btn btn-primary">分析入學管道</button>
            </div>
            <div class="info-box">
              <strong>說明：</strong>系統會自動識別入學管道類型（申請入學、繁星推薦、自然組、社會組、僑生、願景、其他）
            </div>
          </div>

          <!-- 地理區域分析區塊 -->
          <div v-if="activeBlock === 'geographic'" class="analysis-content">
            <h3>地理區域分析</h3>
            <div class="form-group">
              <label>年份欄位：</label>
              <select v-model="geoYearCol" class="form-select">
                <option value="">請選擇年份欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>地區欄位：</label>
              <select v-model="geoRegionCol" class="form-select">
                <option value="">請選擇地區欄位</option>
                <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="button-group">
              <button @click="getGeographicStats" :disabled="!geoYearCol || !geoRegionCol" class="btn btn-primary">分析地理分布</button>
            </div>
            <div class="info-box">
              <strong>說明：</strong>系統會將地區分為北台灣、中台灣、南台灣、東台灣等區域進行統計
            </div>
          </div>
        </div>

        <!-- 自定義分析 -->
        <div v-else class="custom-analysis-section">
          <div class="custom-layout">
            <!-- 欄位選擇區 -->
            <div class="field-selection">
              <h3>欄位選擇</h3>
              <div class="field-list">
                <label v-for="field in availableFields" :key="field.value" class="field-item">
                  <input 
                    type="checkbox" 
                    :value="field.value"
                    v-model="customAnalysis.selectedFields"
                  />
                  <span>{{ field.label }}</span>
                </label>
              </div>
            </div>

            <!-- 分析設定區 -->
            <div class="analysis-settings">
              <h3>分析設定</h3>
              
              <div class="setting-group">
                <label>圖表類型:</label>
                <select v-model="customAnalysis.chartType" class="setting-select">
                  <option value="bar">長條圖</option>
                  <option value="line">折線圖</option>
                  <option value="pie">圓餅圖</option>
                  <option value="scatter">散點圖</option>
                </select>
              </div>

              <div class="setting-group">
                <label>X軸:</label>
                <select v-model="customAnalysis.xAxis" class="setting-select">
                  <option value="">請選擇</option>
                  <option v-for="field in selectedFieldOptions" :key="field.value" :value="field.value">
                    {{ field.label }}
                  </option>
                </select>
              </div>

              <div class="setting-group">
                <label>Y軸:</label>
                <select v-model="customAnalysis.yAxis" class="setting-select">
                  <option value="">請選擇</option>
                  <option value="average">平均成績</option>
                  <option value="count">數量</option>
                  <option value="sum">總和</option>
                </select>
              </div>

              <div class="setting-group">
                <label>分組:</label>
                <select v-model="customAnalysis.groupBy" class="setting-select">
                  <option value="">無</option>
                  <option v-for="field in selectedFieldOptions" :key="field.value" :value="field.value">
                    {{ field.label }}
                  </option>
                </select>
              </div>

              <div class="filter-section">
                <h4>篩選條件:</h4>
                
                <div class="filter-group">
                  <label>時間:</label>
                  <select v-model="customAnalysis.timeFilter" class="filter-select">
                    <option value="2020-2024">2020-2024</option>
                    <option value="2021-2024">2021-2024</option>
                    <option value="2022-2024">2022-2024</option>
                  </select>
                </div>

                <div class="filter-group">
                  <label>科系:</label>
                  <select v-model="customAnalysis.departmentFilter" class="filter-select">
                    <option value="">全部</option>
                    <option value="資管系">資管系</option>
                    <option value="企管系">企管系</option>
                    <option value="會計系">會計系</option>
                  </select>
                </div>

                <div class="filter-group">
                  <label>成績範圍:</label>
                  <div class="range-inputs">
                    <input 
                      type="number" 
                      v-model="customAnalysis.scoreMin" 
                      min="0" 
                      max="100" 
                      placeholder="最低"
                      class="range-input"
                    />
                    <span>-</span>
                    <input 
                      type="number" 
                      v-model="customAnalysis.scoreMax" 
                      min="0" 
                      max="100" 
                      placeholder="最高"
                      class="range-input"
                    />
                  </div>
                </div>
              </div>

              <div class="execute-section">
                <button 
                  @click="executeCustomAnalysis" 
                  class="execute-custom-btn"
                  :disabled="!canExecuteCustomAnalysis"
                >
                  ▶️ 執行分析
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分析結果顯示區 -->
        <div v-if="analysisResult" class="result-section">
          <div class="result-header">
            <h3>分析結果</h3>
            <div class="result-actions">
              <button @click="saveResult" class="action-btn save-btn">
                💾 儲存結果
              </button>
              <button @click="exportReport" class="action-btn export-btn">
                📄 匯出報告
              </button>
              <button @click="reAnalyze" class="action-btn refresh-btn">
                🔄 重新分析
              </button>
            </div>
          </div>

          <div class="chart-container">
            <div class="chart-placeholder">
              <div class="chart-info">
                <h4>{{ analysisResult.title }}</h4>
                <p>{{ analysisResult.description }}</p>
                <div class="chart-mock">
                  📊 [這裡顯示 {{ analysisResult.chartType }} 圖表]
                </div>
              </div>
            </div>
          </div>

          <div class="statistics-summary">
            <h4>統計摘要</h4>
            <div class="summary-grid">
              <div class="summary-item">
                <span class="summary-label">總樣本數:</span>
                <span class="summary-value">{{ analysisResult.stats.totalSamples }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">平均值:</span>
                <span class="summary-value">{{ analysisResult.stats.average }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">最大值:</span>
                <span class="summary-value">{{ analysisResult.stats.max }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">最小值:</span>
                <span class="summary-value">{{ analysisResult.stats.min }}</span>
              </div>
            </div>
          </div>
        </div>
      </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'

// 響應式數據
const currentUser = ref('管理者')
const currentTime = ref('')
// 數據來源相關
const selectedFile = ref('')
const selectedSheet = ref('')
const fileList = ref([])
const sheetList = ref([])
const columns = ref([])
// 分析模式相關
const activeMode = ref('quick')
const activeBlock = ref('')
// 分析參數
const selectedColumn = ref('')
const selectedSubjects = ref([])
const yearCol = ref('')
const admissionYearCol = ref('')
const genderCol = ref('')
const schoolSourceYearCol = ref('')
const schoolNameCol = ref('')
const admissionMethodYearCol = ref('')
const admissionMethodCol = ref('')
const geoYearCol = ref('')
const geoRegionCol = ref('')

const quickAnalysis = ref({
  gradeYear: '2020-2024',
  admissionType: 'all',
  region: 'all',
  subjects: [],
  reportYear: '2024'
})

const customAnalysis = ref({
  selectedFields: [],
  chartType: 'bar',
  xAxis: '',
  yAxis: '',
  groupBy: '',
  timeFilter: '2020-2024',
  departmentFilter: '',
  scoreMin: 0,
  scoreMax: 100
})

const availableFields = ref([
  { label: '學號', value: 'studentId' },
  { label: '姓名', value: 'name' },
  { label: '科系', value: 'department' },
  { label: '成績', value: 'score' },
  { label: '入學年度', value: 'admissionYear' },
  { label: '入學管道', value: 'admissionType' },
  { label: '地區', value: 'region' }
])

const analysisResult = ref(null)

// 計算屬性
const isDataReady = computed(() => {
  return selectedFile.value && selectedSheet.value && columns.value.length > 0
})

const selectedFieldOptions = computed(() => {
  return availableFields.value.filter(field => 
    customAnalysis.value.selectedFields.includes(field.value)
  )
})

const canExecuteCustomAnalysis = computed(() => {
  return customAnalysis.value.selectedFields.length > 0 && 
         customAnalysis.value.xAxis && 
         customAnalysis.value.yAxis
})

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-TW')
}

// 數據來源相關方法
const loadFileList = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/files')
    if (response.ok) {
      const data = await response.json()
      fileList.value = data.files || []
    }
  } catch (error) {
    console.error('載入文件列表失敗:', error)
  }
}

const loadFileSheets = async () => {
  if (!selectedFile.value) {
    sheetList.value = []
    columns.value = []
    selectedSheet.value = ''
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/sheets', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ filename: selectedFile.value })
    })
    if (response.ok) {
      const data = await response.json()
      sheetList.value = data.sheets || []
    }
  } catch (error) {
    console.error('載入工作表失敗:', error)
  }
}

const loadFileColumns = async () => {
  if (!selectedFile.value || !selectedSheet.value) {
    columns.value = []
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/read_columns', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        filename: selectedFile.value,
        sheet: selectedSheet.value
      })
    })
    if (response.ok) {
      const data = await response.json()
      columns.value = data.columns || []
    }
  } catch (error) {
    console.error('載入欄位失敗:', error)
  }
}

// 分析區塊相關方法
const setActiveBlock = (block) => {
  activeBlock.value = block
}

// 分析執行方法
const getColumnStats = async () => {
  if (!isDataReady.value || !selectedColumn.value) {
    alert('請確保已選擇數據來源和分析欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/column_stats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        column: selectedColumn.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('單欄位統計分析', data)
    }
  } catch (error) {
    console.error('統計分析失敗:', error)
    alert('統計分析失敗: ' + error.message)
  }
}

const getMultiSubjectStats = async () => {
  if (!isDataReady.value || !selectedSubjects.value.length || !yearCol.value) {
    alert('請確保已選擇數據來源、科目和年份欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/multi_subject_stats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        subjects: selectedSubjects.value,
        year_col: yearCol.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('多科目分年平均分析', data)
    }
  } catch (error) {
    console.error('多科目分析失敗:', error)
    alert('多科目分析失敗: ' + error.message)
  }
}

const getYearlyAdmissionAnalysis = async () => {
  if (!isDataReady.value || !admissionYearCol.value || !genderCol.value) {
    alert('請確保已選擇數據來源、入學年度和性別欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/yearly_admission_analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        admission_year_col: admissionYearCol.value,
        gender_col: genderCol.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('入學年度分析', data)
    }
  } catch (error) {
    console.error('入學年度分析失敗:', error)
    alert('入學年度分析失敗: ' + error.message)
  }
}

const getSchoolSourceAnalysis = async () => {
  if (!isDataReady.value || !schoolSourceYearCol.value || !schoolNameCol.value) {
    alert('請確保已選擇數據來源、學校年度和學校名稱欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/school_source_analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        year_col: schoolSourceYearCol.value,
        school_col: schoolNameCol.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('學校來源分析', data)
    }
  } catch (error) {
    console.error('學校來源分析失敗:', error)
    alert('學校來源分析失敗: ' + error.message)
  }
}

const getAdmissionMethodAnalysis = async () => {
  if (!isDataReady.value || !admissionMethodYearCol.value || !admissionMethodCol.value) {
    alert('請確保已選擇數據來源、入學管道年度和入學管道欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/admission_method_analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        year_col: admissionMethodYearCol.value,
        method_col: admissionMethodCol.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('入學管道分析', data)
    }
  } catch (error) {
    console.error('入學管道分析失敗:', error)
    alert('入學管道分析失敗: ' + error.message)
  }
}

const getGeographicAnalysis = async () => {
  if (!isDataReady.value || !geoYearCol.value || !geoRegionCol.value) {
    alert('請確保已選擇數據來源、地理年度和地區欄位')
    return
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/geographic_analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        sheet: selectedSheet.value,
        year_col: geoYearCol.value,
        region_col: geoRegionCol.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      displayAnalysisResult('地理區域分析', data)
    }
  } catch (error) {
    console.error('地理區域分析失敗:', error)
    alert('地理區域分析失敗: ' + error.message)
  }
}

const displayAnalysisResult = (title, data) => {
  analysisResult.value = {
    title: title,
    description: `基於 ${selectedFile.value} 的 ${title}`,
    chartType: '統計圖表',
    stats: data.stats || {
      totalSamples: data.total_count || 0,
      average: data.average || 0,
      max: data.max_value || 0,
      min: data.min_value || 0
    },
    data: data
  }
  
  // 滾動到結果區域
  nextTick(() => {
    const resultSection = document.querySelector('.result-section')
    if (resultSection) {
      resultSection.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const executeQuickAnalysis = (type) => {
  // 模擬快速分析
  const analysisTypes = {
    'grade-trend': {
      title: '成績趨勢分析',
      description: `${quickAnalysis.value.gradeYear} 年度成績變化趨勢`,
      chartType: '線圖',
      stats: {
        totalSamples: Math.floor(Math.random() * 1000) + 500,
        average: (Math.random() * 20 + 70).toFixed(1),
        max: Math.floor(Math.random() * 10) + 90,
        min: Math.floor(Math.random() * 20) + 50
      }
    },
    'admission-stats': {
      title: '入學管道統計',
      description: `${quickAnalysis.value.admissionType} 入學管道分析`,
      chartType: '圓餅圖',
      stats: {
        totalSamples: Math.floor(Math.random() * 800) + 300,
        average: (Math.random() * 15 + 75).toFixed(1),
        max: Math.floor(Math.random() * 8) + 92,
        min: Math.floor(Math.random() * 25) + 45
      }
    },
    'regional-distribution': {
      title: '地區分布分析',
      description: `${quickAnalysis.value.region} 地區學生分布`,
      chartType: '地圖圖表',
      stats: {
        totalSamples: Math.floor(Math.random() * 1200) + 400,
        average: (Math.random() * 18 + 72).toFixed(1),
        max: Math.floor(Math.random() * 12) + 88,
        min: Math.floor(Math.random() * 22) + 48
      }
    }
  }

  analysisResult.value = analysisTypes[type]
  
  // 滾動到結果區域
  nextTick(() => {
    const resultSection = document.querySelector('.result-section')
    if (resultSection) {
      resultSection.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const executeCustomAnalysis = async () => {
  if (!canExecuteCustomAnalysis.value) return

  // 模擬自定義分析
  analysisResult.value = {
    title: '自定義分析結果',
    description: `${customAnalysis.value.xAxis} vs ${customAnalysis.value.yAxis} 分析`,
    chartType: customAnalysis.value.chartType,
    stats: {
      totalSamples: Math.floor(Math.random() * 1000) + 500,
      average: (Math.random() * 40 + 60).toFixed(1),
      max: Math.floor(Math.random() * 20) + 80,
      min: Math.floor(Math.random() * 30) + 40
    }
  }

  // 滾動到結果區域
  nextTick(() => {
    const resultSection = document.querySelector('.result-section')
    if (resultSection) {
      resultSection.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const saveResult = () => {
  alert('分析結果已儲存')
}

const exportReport = () => {
  alert('報告匯出功能')
}

const reAnalyze = () => {
  if (activeMode.value === 'quick') {
    // 重新執行上次的快速分析
    alert('重新執行分析')
  } else {
    executeCustomAnalysis()
  }
}

// 生命週期掛鉤
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
  loadFileList()
})
</script>

<style scoped>
      try {
        const response = await fetch('http://localhost:5000/api/files')
        if (response.ok) {
          const data = await response.json()
          this.fileList = data.files || []
        }
      } catch (error) {
        console.error('載入文件列表失敗:', error)
      }
    },
    async loadFileSheets() {
      if (!this.selectedFile) {
        this.sheetList = []
        this.columns = []
        this.selectedSheet = ''
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/sheets', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ filename: this.selectedFile })
        })
        if (response.ok) {
          const data = await response.json()
          this.sheetList = data.sheets || []
        }
      } catch (error) {
        console.error('載入工作表失敗:', error)
      }
    },
    async loadFileColumns() {
      if (!this.selectedFile || !this.selectedSheet) {
        this.columns = []
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/read_columns', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            filename: this.selectedFile,
            sheet: this.selectedSheet
          })
        })
        if (response.ok) {
          const data = await response.json()
          this.columns = data.columns || []
        }
      } catch (error) {
        console.error('載入欄位失敗:', error)
      }
    },
    // 分析區塊相關方法
    setActiveBlock(block) {
      this.activeBlock = block
    },
    // 分析執行方法
    async getColumnStats() {
      if (!this.isDataReady || !this.selectedColumn) {
        alert('請確保已選擇數據來源和分析欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/column_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            column: this.selectedColumn
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('單欄位統計分析', data)
        }
      } catch (error) {
        console.error('統計分析失敗:', error)
        alert('統計分析失敗: ' + error.message)
      }
    },
    
    async getMultiSubjectStats() {
      if (!this.isDataReady || !this.selectedSubjects.length || !this.yearCol) {
        alert('請確保已選擇數據來源、科目和年份欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/multi_subject_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            subjects: this.selectedSubjects,
            year_col: this.yearCol
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('多科目分年平均分析', data)
        }
      } catch (error) {
        console.error('多科目分析失敗:', error)
        alert('多科目分析失敗: ' + error.message)
      }
    },
    
    async getYearlyAdmissionStats() {
      if (!this.isDataReady || !this.admissionYearCol) {
        alert('請確保已選擇數據來源和年份欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/yearly_admission_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            year_col: this.admissionYearCol,
            gender_col: this.genderCol || null
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('每年入學生數量分析', data)
        }
      } catch (error) {
        console.error('入學生數量分析失敗:', error)
        alert('入學生數量分析失敗: ' + error.message)
      }
    },
    
    async getSchoolSourceStats() {
      if (!this.isDataReady || !this.schoolSourceYearCol || !this.schoolNameCol) {
        alert('請確保已選擇數據來源、年份欄位和學校名稱欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/school_source_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            year_col: this.schoolSourceYearCol,
            school_name_col: this.schoolNameCol
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('入學生學校來源分析', data)
        }
      } catch (error) {
        console.error('學校來源分析失敗:', error)
        alert('學校來源分析失敗: ' + error.message)
      }
    },
    
    async getAdmissionMethodStats() {
      if (!this.isDataReady || !this.admissionMethodYearCol || !this.admissionMethodCol) {
        alert('請確保已選擇數據來源、年份欄位和入學管道欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/admission_method_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            year_col: this.admissionMethodYearCol,
            method_col: this.admissionMethodCol
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('入學生入學管道分析', data)
        }
      } catch (error) {
        console.error('入學管道分析失敗:', error)
        alert('入學管道分析失敗: ' + error.message)
      }
    },
    
    async getGeographicStats() {
      if (!this.isDataReady || !this.geoYearCol || !this.geoRegionCol) {
        alert('請確保已選擇數據來源、年份欄位和地區欄位')
        return
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/geographic_stats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: this.selectedFile,
            sheet: this.selectedSheet,
            year_col: this.geoYearCol,
            region_col: this.geoRegionCol
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          this.displayAnalysisResult('地理區域分析', data)
        }
      } catch (error) {
        console.error('地理分析失敗:', error)
        alert('地理分析失敗: ' + error.message)
      }
    },
    
    displayAnalysisResult(title, data) {
      // 顯示分析結果
      this.analysisResult = {
        title,
        data,
        timestamp: new Date().toLocaleString('zh-TW')
      }
      alert(`${title}完成！請查看結果。`)
    },
    
    showRawData() {
      if (!this.isDataReady || !this.selectedColumn) {
        alert('請確保已選擇數據來源和欄位')
        return
      }
      alert('顯示原始資料功能')
    },
    handleLogout() {
      if (confirm('確定要登出嗎？')) {
        this.$router.push('/login')
      }
    },
    async executeQuickAnalysis(type) {
      // 檢查數據來源是否已選擇
      if (!this.isDataReady) {
        alert('請先選擇數據來源（檔案和工作表）')
        return
      }
      
      // 模擬分析執行
      const analysisTypes = {
        'grade-trend': {
          title: '成績趨勢分析',
          description: `分析 ${this.quickAnalysis.gradeYear} 年度成績變化趨勢`,
          chartType: '折線圖',
          stats: {
            totalSamples: 1250,
            average: 78.5,
            max: 98,
            min: 45
          }
        },
        'admission': {
          title: '入學管道分析',
          description: `${this.quickAnalysis.admissionType === 'all' ? '全部' : this.quickAnalysis.admissionType}入學管道統計`,
          chartType: '圓餅圖',
          stats: {
            totalSamples: 1250,
            average: 'N/A',
            max: '考試入學 45%',
            min: '其他 10%'
          }
        },
        'geography': {
          title: '地理分佈分析',
          description: `學生${this.quickAnalysis.region === 'all' ? '全部地區' : this.quickAnalysis.region}分佈統計`,
          chartType: '地圖',
          stats: {
            totalSamples: 1250,
            average: 'N/A',
            max: '北部 60%',
            min: '東部 5%'
          }
        },
        'subject-comparison': {
          title: '科目比較分析',
          description: '各科目平均成績比較',
          chartType: '長條圖',
          stats: {
            totalSamples: 1250,
            average: 76.8,
            max: 85,
            min: 68
          }
        },
        'annual-report': {
          title: `${this.quickAnalysis.reportYear} 年度報告`,
          description: `${this.quickAnalysis.reportYear} 年度完整統計報告`,
          chartType: '綜合圖表',
          stats: {
            totalSamples: 1250,
            average: 77.2,
            max: 98,
            min: 42
          }
        }
      }

      this.analysisResult = analysisTypes[type]
      
      // 滾動到結果區域
      this.$nextTick(() => {
        const resultSection = document.querySelector('.result-section')
        if (resultSection) {
          resultSection.scrollIntoView({ behavior: 'smooth' })
        }
      })
    },
    async executeCustomAnalysis() {
      if (!this.canExecuteCustomAnalysis) return

      // 模擬自定義分析
      this.analysisResult = {
        title: '自定義分析結果',
        description: `${this.customAnalysis.xAxis} vs ${this.customAnalysis.yAxis} 分析`,
        chartType: this.customAnalysis.chartType,
        stats: {
          totalSamples: Math.floor(Math.random() * 1000) + 500,
          average: (Math.random() * 40 + 60).toFixed(1),
          max: Math.floor(Math.random() * 20) + 80,
          min: Math.floor(Math.random() * 30) + 40
        }
      }

      // 滾動到結果區域
      this.$nextTick(() => {
        const resultSection = document.querySelector('.result-section')
        if (resultSection) {
          resultSection.scrollIntoView({ behavior: 'smooth' })
        }
      })
    },
    saveResult() {
      alert('分析結果已儲存')
    },
    exportReport() {
      alert('報告匯出功能')
    },
    reAnalyze() {
      if (this.activeMode === 'quick') {
        // 重新執行上次的快速分析
        alert('重新執行分析')
      } else {
        this.executeCustomAnalysis()
      }
    }
  }
}
</script>

<style scoped>
/* 全屏布局樣式 */
.analysis-container {
  min-height: 100vh;
  padding: 20px;
  background-color: var(--bg-secondary);
}

.main-content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  color: var(--primary-color);
  font-size: 28px;
  margin: 0;
}

/* 數據來源選擇樣式 */
.data-source-section {
  margin-bottom: 24px;
}

.source-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.source-title {
  margin: 0 0 20px 0;
  color: #1976d2;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.control-row label {
  min-width: 100px;
  font-weight: 500;
  color: #333;
}

.source-select {
  min-width: 250px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.source-select:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.columns-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 600px;
}

.column-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator {
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
  text-align: center;
  margin-top: 8px;
}

.status-indicator.ready {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.status-indicator.not-ready {
  background: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffcc02;
}

/* 模式選擇樣式 */
.mode-selection {
  margin-bottom: 24px;
}

.mode-tabs {
  display: flex;
  gap: 12px;
  background: white;
  padding: 8px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.mode-tab {
  flex: 1;
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s ease;
}

.mode-tab.active {
  background: var(--primary-color);
  color: white;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
}

.mode-tab:hover:not(.active) {
  background: #f5f5f5;
  color: var(--primary-color);
}

/* 分析區塊樣式 */
.analysis-blocks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.analysis-block {
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.analysis-block:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.2);
}

.analysis-block.active {
  border-color: var(--primary-color);
  background: #f0f8ff;
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
}

.block-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.nav-icon {
  font-size: 24px;
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

/* 分析內容樣式 */
.analysis-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.analysis-content h3 {
  color: var(--primary-color);
  margin: 0 0 20px 0;
  font-size: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-select {
  width: 100%;
  max-width: 300px;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.form-select[multiple] {
  min-height: 120px;
}

.button-group {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
  transform: translateY(-1px);
}

.info-box {
  margin-top: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  border-left: 4px solid var(--primary-color);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .analysis-container {
    padding: 16px;
  }
  
  .analysis-blocks {
    grid-template-columns: 1fr;
  }
  
  .mode-tabs {
    flex-direction: column;
  }
  
  .control-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .control-row label {
    min-width: auto;
  }
  
  .source-select {
    min-width: 100%;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
