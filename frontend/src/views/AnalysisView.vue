<template>
  <div class="analysis-page">
    <!-- 頂部導航欄 -->
    <header class="top-navbar">
      <div class="navbar-left">
        <h1 class="system-title">🎓 學生資料分析系統</h1>
        <nav class="nav-links">
          <router-link to="/dashboard" class="nav-link">主控台</router-link>
          <router-link to="/data-management" class="nav-link">數據管理</router-link>
          <router-link to="/analysis" class="nav-link">數據分析</router-link>
        </nav>
      </div>
      <div class="navbar-right">
        <span class="current-time">{{ currentTime }}</span>
        <span class="user-info">👤 {{ currentUser }}</span>
        <button @click="handleLogout" class="logout-btn">🚪 登出</button>
      </div>
    </header>

    <div class="main-content">
      <!-- 數據來源選擇 -->
      <div class="data-source-section">
        <el-divider>選擇數據來源</el-divider>
        
        <div class="database-source-section">
          <h3>從資料庫選擇數據</h3>
          <p>選擇已存入資料庫的數據表格進行分析</p>
          
          <el-select 
            v-model="selectedTable" 
            placeholder="請選擇資料表格" 
            style="width: 100%; max-width: 500px;" 
            @change="loadTableColumns"
            filterable
          >
            <el-option
              v-for="table in databaseTables"
              :key="table.table_name"
              :label="table.display_name"
              :value="table.table_name"
            />
          </el-select>
          
          <!-- 自動選擇欄位提示 -->
          <div v-if="selectedTable && columns.length > 0" class="auto-select-info">
            <h4>🤖 智能欄位識別</h4>
            <p>系統已自動為您識別和選擇合適的欄位：</p>
            <div class="auto-select-items">
              <div v-if="yearCol" class="auto-select-item">
                📅 年度欄位: <strong>{{ yearCol }}</strong>
              </div>
              <div v-if="genderCol" class="auto-select-item">
                👥 性別欄位: <strong>{{ genderCol }}</strong>
              </div>
              <div v-if="schoolNameCol" class="auto-select-item">
                🏫 學校欄位: <strong>{{ schoolNameCol }}</strong>
              </div>
              <div v-if="admissionMethodCol" class="auto-select-item">
                🎯 入學管道欄位: <strong>{{ admissionMethodCol }}</strong>
              </div>
              <div v-if="geoRegionCol" class="auto-select-item">
                🗺️ 地區欄位: <strong>{{ geoRegionCol }}</strong>
              </div>
              <div v-if="selectedSubjects.length > 0" class="auto-select-item">
                📊 科目欄位: <strong>{{ selectedSubjects.join(', ') }}</strong>
              </div>
            </div>
            <p class="auto-select-note">您可以在各分析區塊中手動調整這些選擇</p>
          </div>
        </div>

        <el-divider>或上傳新檔案到資料庫</el-divider>
        
        <div class="upload-hint">
          <p>如需上傳新的 Excel 檔案，請前往 <router-link to="/data-management">數據管理</router-link> 頁面</p>
        </div>

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

        <!-- 地理區域分析 -->
        <div 
          class="analysis-block" 
          :class="{ active: activeBlock === 'geographic' }"
          @click="setActiveBlock('geographic')"
        >
          <div class="block-header">
            <span class="nav-icon">🗺️</span>
            <h3>地理區域分析</h3>
          </div>
          <p>分析學生來源地理區域分布，按北、西、南、東台灣等區域統計</p>
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
        <div class="form-group">
          <label>性別欄位（可選）：</label>
          <el-select v-model="genderCol" placeholder="請選擇性別欄位" style="width: 300px" clearable>
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
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 13px; color: #666;">
          <strong>說明：</strong>系統會自動識別入學管道類型（申請入學、繁星推薦、自然組、社會組、僑生、願景、其他）
        </div>
      </div>

      <!-- 地理區域分析區塊 -->
      <div v-if="activeBlock === 'geographic'" class="analysis-content">
        <el-divider>地理區域分析</el-divider>
        <div class="form-group">
          <label>年份欄位：</label>
          <el-select v-model="geoYearCol" placeholder="請選擇年份欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="form-group">
          <label>地區欄位：</label>
          <el-select v-model="geoRegionCol" placeholder="請選擇地區欄位" style="width: 300px">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
        <div class="button-group">
          <el-button type="success" @click="getGeographicStats" :disabled="!geoYearCol || !geoRegionCol">分析地理區域分布</el-button>
        </div>
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 13px; color: #666;">
          <strong>說明：</strong>系統會自動將各縣市分類為：<br>
          <strong>北台灣：</strong>台北市、新北市、基隆市、宜蘭縣、桃園市、新竹市、新竹縣<br>
          <strong>中台灣：</strong>苗栗縣、台中市、彰化縣、南投縣、雲林縣<br>
          <strong>南台灣：</strong>嘉義市、嘉義縣、台南市、高雄市、屏東縣<br>
          <strong>東台灣：</strong>花蓮縣、台東縣<br>
          <strong>其他：</strong>澎湖縣、金門縣、連江縣、大陸台商子學校等其他地區
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
          <div class="chart-with-export">
            <canvas id="statsChart" style="width: 100%; height: 400px;"></canvas>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showExportDialog('statsChart', '單欄位統計分析', columnStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
        </div>

        <div v-if="multiSubjectStats" class="stats-card">
          <el-divider>多科目分年平均分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ multiSubjectStats.year_range }}</p>
            <p><strong>科目數量：</strong>{{ multiSubjectStats.subjects.length }} 個</p>
            <p><strong>分析科目：</strong>{{ multiSubjectStats.subjects.join(', ') }}</p>
          </div>
          <div class="chart-with-export">
            <canvas id="multiSubjectChart" style="width: 100%; height: 400px;"></canvas>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showExportDialog('multiSubjectChart', '多科目分年平均分析', multiSubjectStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
        </div>

        <div v-if="yearlyAdmissionStats" class="stats-card">
          <el-divider>每年入學生數量分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ yearlyAdmissionStats.year_range }}</p>
            <p><strong>總入學人數：</strong>{{ yearlyAdmissionStats.total_students }} 人</p>
            <p v-if="yearlyAdmissionStats.has_gender">
              最高入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.max(...yearlyAdmissionStats.total_counts))] }}
              （{{ Math.max(...yearlyAdmissionStats.total_counts) }}人）
            </p>
            <p v-if="yearlyAdmissionStats.has_gender">
              最低入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.min(...yearlyAdmissionStats.total_counts))] }}
              （{{ Math.min(...yearlyAdmissionStats.total_counts) }}人）
            </p>
            <p v-if="!yearlyAdmissionStats.has_gender">
              最高入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.max(...yearlyAdmissionStats.total_counts))] }}
              （{{ Math.max(...yearlyAdmissionStats.total_counts) }}人）
            </p>
            <p v-if="!yearlyAdmissionStats.has_gender">
              最低入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.min(...yearlyAdmissionStats.total_counts))] }}
              （{{ Math.min(...yearlyAdmissionStats.total_counts) }}人）
            </p>
          </div>
          <div class="chart-with-export">
            <canvas id="yearlyAdmissionChart" style="width: 100%; height: 400px;"></canvas>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showExportDialog('yearlyAdmissionChart', '每年入學生數量分析', yearlyAdmissionStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
          
          <el-divider>詳細數據</el-divider>
          <el-table 
            :data="yearlyAdmissionStats.years.map((year, i) => ({
              year,
              female_count: yearlyAdmissionStats.has_gender ? yearlyAdmissionStats.female_counts[i] : null,
              male_count: yearlyAdmissionStats.has_gender ? yearlyAdmissionStats.male_counts[i] : null,
              total_count: yearlyAdmissionStats.total_counts[i],
              female_percentage: yearlyAdmissionStats.has_gender ? yearlyAdmissionStats.female_percentages[i] : null,
              male_percentage: yearlyAdmissionStats.has_gender ? yearlyAdmissionStats.male_percentages[i] : null
            }))"
            border 
            style="width: 100%"
          >
            <el-table-column prop="year" label="年份" width="100" fixed>
              <template #default="scope">
                <strong>{{ scope.row.year }}</strong>
              </template>
            </el-table-column>
            <el-table-column v-if="yearlyAdmissionStats.has_gender" prop="female_count" label="女性人數">
              <template #default="scope">
                {{ scope.row.female_count }}
              </template>
            </el-table-column>
            <el-table-column v-if="yearlyAdmissionStats.has_gender" prop="male_count" label="男性人數">
              <template #default="scope">
                {{ scope.row.male_count }}
              </template>
            </el-table-column>
            <el-table-column prop="total_count" label="總人數">
              <template #default="scope">
                <strong>{{ scope.row.total_count }}</strong>
              </template>
            </el-table-column>
            <el-table-column v-if="yearlyAdmissionStats.has_gender" prop="female_percentage" label="女性比例">
              <template #default="scope">
                {{ scope.row.female_percentage }}%
              </template>
            </el-table-column>
            <el-table-column v-if="yearlyAdmissionStats.has_gender" prop="male_percentage" label="男性比例">
              <template #default="scope">
                {{ scope.row.male_percentage }}%
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="schoolSourceStats" class="stats-card">
          <el-divider>入學生學校來源分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ schoolSourceStats.year_range }}</p>
            <p><strong>總人數：</strong>{{ schoolSourceStats.total_students }} 人</p>
            <p v-if="schoolSourceStats.summary.peak_year">
              最高入學年份：{{ schoolSourceStats.summary.peak_year }}（{{ schoolSourceStats.summary.peak_count }}人）
            </p>
            <p v-if="schoolSourceStats.summary.low_year">
              最低入學年份：{{ schoolSourceStats.summary.low_year }}（{{ schoolSourceStats.summary.low_count }}人）
            </p>
          </div>
          <div class="chart-with-export">
            <canvas id="schoolSourceChart" style="width: 100%; height: 400px;"></canvas>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showExportDialog('schoolSourceChart', '入學生學校來源分析', schoolSourceStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
          
          <el-divider>各年度學校類型分布詳細數據</el-divider>
          <el-table 
            :data="schoolSourceStats.years.map((year, index) => ({
              year,
              ...Object.fromEntries(schoolSourceStats.school_types.map(type => [
                type,
                {
                  count: schoolSourceStats.data[type].counts[index],
                  percentage: schoolSourceStats.data[type].percentages[index]
                }
              ])),
              total: schoolSourceStats.year_totals[index]
            }))"
            border 
            style="width: 100%"
            :max-height="500"
          >
            <el-table-column 
              prop="year" 
              label="年份" 
              width="100"
              fixed
            >
              <template #default="scope">
                <strong>{{ scope.row.year }}</strong>
              </template>
            </el-table-column>
            
            <el-table-column 
              v-for="type in schoolSourceStats.school_types" 
              :key="type" 
              :prop="type" 
              :label="type"
              min-width="150"
            >
              <template #default="scope">
                {{ scope.row[type].count }}
                <span style="color: #999; font-size: 12px;">
                  ({{ scope.row[type].percentage }}%)
                </span>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="total" 
              label="年度總計"
              width="120"
              fixed="right"
            >
              <template #default="scope">
                <strong>{{ scope.row.total }}</strong>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="admissionMethodStats" class="stats-card">
          <el-divider>入學生入學管道分析結果</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ admissionMethodStats.year_range }}</p>
            <p><strong>總人數：</strong>{{ admissionMethodStats.total_students }} 人</p>
            <p v-if="admissionMethodStats.summary.peak_year">
              最高入學年份：{{ admissionMethodStats.summary.peak_year }}（{{ admissionMethodStats.summary.peak_count }}人）
            </p>
            <p v-if="admissionMethodStats.summary.low_year">
              最低入學年份：{{ admissionMethodStats.summary.low_year }}（{{ admissionMethodStats.summary.low_count }}人）
            </p>
          </div>
          <div class="chart-with-export">
            <canvas id="admissionMethodChart" style="width: 100%; height: 400px;"></canvas>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showExportDialog('admissionMethodChart', '入學生入學管道分析', admissionMethodStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
          
          <el-divider>各年度入學管道分布詳細數據</el-divider>
          <el-table 
            :data="admissionMethodStats.years.map((year, index) => ({
              year,
              ...Object.fromEntries(admissionMethodStats.method_types.map(type => [
                type,
                {
                  count: admissionMethodStats.data[type].counts[index],
                  percentage: admissionMethodStats.data[type].percentages[index]
                }
              ])),
              total: admissionMethodStats.year_totals[index]
            }))"
            border 
            style="width: 100%"
            :max-height="500"
          >
            <el-table-column 
              prop="year" 
              label="年份" 
              width="100"
              fixed
            >
              <template #default="scope">
                <strong>{{ scope.row.year }}</strong>
              </template>
            </el-table-column>
            
            <el-table-column 
              v-for="type in admissionMethodStats.method_types" 
              :key="type" 
              :prop="type" 
              :label="type"
              min-width="150"
            >
              <template #default="scope">
                {{ scope.row[type].count }}
                <span style="color: #999; font-size: 12px;">
                  ({{ scope.row[type].percentage }}%)
                </span>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="total" 
              label="年度總計"
              width="120"
              fixed="right"
            >
              <template #default="scope">
                <strong>{{ scope.row.total }}</strong>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 地理區域分析結果 -->
        <div v-if="geoStats" class="stats-card">
          <el-divider>地理區域分布統計</el-divider>
          <div class="stats-summary">
            <p><strong>分析期間：</strong>{{ geoStats.year_range }}</p>
            <p><strong>總人數：</strong>{{ geoStats.total_students }} 人</p>
            <p><strong>說明：</strong>圖表顯示各年度不同地區的入學人數分布，橫軸為年度，縱軸為人數</p>
          </div>
          <div class="chart-with-export">
            <div id="geoChart" style="width: 100%; height: 400px;"></div>
            <el-button 
              type="primary" 
              class="export-btn"
              @click="showEChartsExportDialog('geoChart', '地理區域分布統計', geoStats)"
              icon="Download"
            >
              📊 導出圖表
            </el-button>
          </div>
          
          <el-divider>地區縣市人數詳細分析</el-divider>
          <div class="stats-summary">
            <p><strong>說明：</strong>以下圖表顯示各區域內不同縣市的入學人數分布，橫軸為年度，縱軸為人數</p>
          </div>
          
          <el-tabs type="border-card" @tab-click="handleTabChange">
            <el-tab-pane label="北台灣縣市分析">
              <div class="chart-container">
                <div class="chart-with-export">
                  <div id="geoChart-北台灣" style="width: 100%; height: 400px;"></div>
                  <el-button 
                    type="primary" 
                    class="export-btn"
                    @click="showEChartsExportDialog('geoChart-北台灣', '北台灣縣市分析', geoStats)"
                    icon="Download"
                  >
                    📊 導出圖表
                  </el-button>
                </div>
              </div>
              <div class="region-data-table" v-if="geoStats.detailed && geoStats.detailed['北台灣']">
                <h4>北台灣各縣市學生統計表</h4>
                <el-table :data="formatRegionTableData('北台灣')" stripe border style="width: 100%">
                  <el-table-column prop="city" label="縣市"></el-table-column>
                  <el-table-column 
                    v-for="year in geoStats.years" 
                    :key="String(year)" 
                    :prop="String(year)" 
                    :label="String(year)">
                  </el-table-column>
                  <el-table-column prop="total" label="總計"></el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
            <el-tab-pane label="中台灣縣市分析">
              <div class="chart-container">
                <div class="chart-with-export">
                  <div id="geoChart-中台灣" style="width: 100%; height: 400px;"></div>
                  <el-button 
                    type="primary" 
                    class="export-btn"
                    @click="showEChartsExportDialog('geoChart-中台灣', '中台灣縣市分析', geoStats)"
                    icon="Download"
                  >
                    📊 導出圖表
                  </el-button>
                </div>
              </div>
              <div class="region-data-table" v-if="geoStats.detailed && geoStats.detailed['中台灣']">
                <h4>中台灣各縣市學生統計表</h4>
                <el-table :data="formatRegionTableData('中台灣')" stripe border style="width: 100%">
                  <el-table-column prop="city" label="縣市"></el-table-column>
                  <el-table-column 
                    v-for="year in geoStats.years" 
                    :key="String(year)" 
                    :prop="String(year)" 
                    :label="String(year)">
                  </el-table-column>
                  <el-table-column prop="total" label="總計"></el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
            <el-tab-pane label="南台灣縣市分析">
              <div class="chart-container">
                <div class="chart-with-export">
                  <div id="geoChart-南台灣" style="width: 100%; height: 400px;"></div>
                  <el-button 
                    type="primary" 
                    class="export-btn"
                    @click="showEChartsExportDialog('geoChart-南台灣', '南台灣縣市分析', geoStats)"
                    icon="Download"
                  >
                    📊 導出圖表
                  </el-button>
                </div>
              </div>
              <div class="region-data-table" v-if="geoStats.detailed && geoStats.detailed['南台灣']">
                <h4>南台灣各縣市學生統計表</h4>
                <el-table :data="formatRegionTableData('南台灣')" stripe border style="width: 100%">
                  <el-table-column prop="city" label="縣市"></el-table-column>
                  <el-table-column 
                    v-for="year in geoStats.years" 
                    :key="String(year)" 
                    :prop="String(year)" 
                    :label="String(year)">
                  </el-table-column>
                  <el-table-column prop="total" label="總計"></el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
            <el-tab-pane label="東台灣縣市分析">
              <div class="chart-container">
                <div class="chart-with-export">
                  <div id="geoChart-東台灣" style="width: 100%; height: 400px;"></div>
                  <el-button 
                    type="primary" 
                    class="export-btn"
                    @click="showEChartsExportDialog('geoChart-東台灣', '東台灣縣市分析', geoStats)"
                    icon="Download"
                  >
                    📊 導出圖表
                  </el-button>
                </div>
              </div>
              <div class="region-data-table" v-if="geoStats.detailed && geoStats.detailed['東台灣']">
                <h4>東台灣各縣市學生統計表</h4>
                <el-table :data="formatRegionTableData('東台灣')" stripe border style="width: 100%">
                  <el-table-column prop="city" label="縣市"></el-table-column>
                  <el-table-column 
                    v-for="year in geoStats.years" 
                    :key="String(year)" 
                    :prop="String(year)" 
                    :label="String(year)">
                  </el-table-column>
                  <el-table-column prop="total" label="總計"></el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
          </el-tabs>
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

  <!-- 導出選項對話框 -->
  <el-dialog
    v-model="exportDialogVisible"
    title="選擇導出格式"
    width="500px"
    align-center
  >
    <div class="export-options">
      <h4>📊 {{ currentExportTitle }}</h4>
      <p>請選擇要導出的格式：</p>
      
      <div class="format-grid">
        <!-- 圖片格式 -->
        <div class="format-section">
          <h5>🖼️ 圖片格式</h5>
          <el-button @click="exportInFormat('png')" type="primary" plain>
            PNG (高品質)
          </el-button>
          <el-button @click="exportInFormat('jpeg')" type="primary" plain>
            JPEG (小檔案)
          </el-button>
          <el-button @click="exportInFormat('svg')" type="primary" plain>
            SVG (向量圖)
          </el-button>
        </div>
        
        <!-- 文件格式 -->
        <div class="format-section">
          <h5>📄 文件格式</h5>
          <el-button @click="exportInFormat('pdf')" type="success" plain>
            PDF (列印報告)
          </el-button>
          <el-button @click="exportInFormat('pdf-advanced')" type="success">
            PDF (高級版)
          </el-button>
        </div>
        
        <!-- 數據格式 -->
        <div class="format-section">
          <h5>📊 數據格式</h5>
          <el-button @click="exportInFormat('csv')" type="warning" plain>
            CSV (數據表)
          </el-button>
          <el-button @click="exportInFormat('json')" type="warning" plain>
            JSON (結構化)
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Chart from 'chart.js/auto'
import * as echarts from 'echarts'

// 導航欄相關
const router = useRouter()
const currentTime = ref('')
const currentUser = ref('管理者')

// 導出對話框相關
const exportDialogVisible = ref(false)
const currentExportTitle = ref('')
const currentChartId = ref('')
const currentChartType = ref('') // 'canvas' 或 'echarts'
const currentChartData = ref(null)

// 更新時間
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-TW')
}

// 登出處理
const handleLogout = () => {
  router.push('/')
}

// 響應式數據
const databaseTables = ref([])
const selectedTable = ref('')
const columns = ref([])
const selectedColumn = ref('')
const selectedSubjects = ref([])
const yearCol = ref('')
const yearlyAdmissionYearCol = ref('')
const schoolSourceYearCol = ref('')
const schoolNameCol = ref('')
const admissionMethodYearCol = ref('')
const admissionMethodCol = ref('')
const geoYearCol = ref('')
const geoRegionCol = ref('')
const genderCol = ref('')
const activeBlock = ref('')
const currentStats = ref(null)
const columnStats = ref(null)
const multiSubjectStats = ref(null)
const yearlyAdmissionStats = ref(null)
const schoolSourceStats = ref(null)
const admissionMethodStats = ref(null)
const geoStats = ref(null)
const rawData = ref([])

// 圖表實例
let columnChartInstance = null
let multiSubjectChartInstance = null
let yearlyAdmissionChartInstance = null
let schoolSourceChartInstance = null
let admissionMethodChartInstance = null
let geoChartInstance = null
let geoDetailedChartInstances = {}

// 清理函數
const cleanupFunctions = []

// 設置活動區塊
const setActiveBlock = (blockName) => {
  activeBlock.value = blockName
  // 清理之前的數據
  currentStats.value = null
  columnStats.value = null
  multiSubjectStats.value = null
  yearlyAdmissionStats.value = null
  schoolSourceStats.value = null
  admissionMethodStats.value = null
  geoStats.value = null
  rawData.value = []
  
  // 清理圖表
  if (columnChartInstance) {
    columnChartInstance.destroy()
    columnChartInstance = null
  }
  if (multiSubjectChartInstance) {
    multiSubjectChartInstance.destroy()
    multiSubjectChartInstance = null
  }
  if (yearlyAdmissionChartInstance) {
    yearlyAdmissionChartInstance.destroy()
    yearlyAdmissionChartInstance = null
  }
  if (schoolSourceChartInstance) {
    schoolSourceChartInstance.destroy()
    schoolSourceChartInstance = null
  }
  if (admissionMethodChartInstance) {
    admissionMethodChartInstance.destroy()
    admissionMethodChartInstance = null
  }
  if (geoChartInstance) {
    geoChartInstance.dispose()
    geoChartInstance = null
  }
  if (geoDetailedChartInstances) {
    Object.values(geoDetailedChartInstances).forEach(chart => {
      if (chart) chart.dispose()
    })
    geoDetailedChartInstances = {}
  }
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
    const response = await axios.get('http://localhost:5000/api/files')
    fileList.value = response.data.files
  } catch (error) {
    ElMessage.error('載入檔案列表失敗')
    console.error(error)
  }
}

// 載入資料庫表格列表
const loadDatabaseTables = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/database_tables')
    databaseTables.value = response.data.tables
  } catch (error) {
    console.error('載入資料庫表格失敗:', error)
    ElMessage.error('載入資料庫表格失敗')
  }
}

// 載入表格欄位
const loadTableColumns = async () => {
  if (!selectedTable.value) return
  
  try {
    const response = await axios.post('http://localhost:5000/api/table_columns', {
      table_name: selectedTable.value
    })
    columns.value = response.data.columns
    
    // 清空之前的選擇
    selectedColumn.value = ''
    selectedSubjects.value = []
    yearCol.value = ''
    yearlyAdmissionYearCol.value = ''
    schoolSourceYearCol.value = ''
    schoolNameCol.value = ''
    admissionMethodYearCol.value = ''
    admissionMethodCol.value = ''
    geoYearCol.value = ''
    geoRegionCol.value = ''
    genderCol.value = ''
    
    // 自動選擇合適的欄位
    autoSelectColumns()
    
  } catch (error) {
    console.error('載入表格欄位失敗:', error)
    ElMessage.error('載入表格欄位失敗')
  }
}

// 載入工作表列表（保留原有功能，但現在主要使用資料庫）
const loadFileSheets = async () => {
  if (!selectedFile.value) return
  
  try {
    const response = await axios.post('http://localhost:5000/api/sheets', {
      filename: selectedFile.value
    })
    sheetList.value = response.data.sheets
    selectedSheet.value = ''
    columns.value = []
  } catch (error) {
    ElMessage.error('載入工作表失敗')
    console.error(error)
  }
}

// 載入欄位
const loadFileColumns = async () => {
  if (!selectedFile.value || !selectedSheet.value) return
  
  try {
    const response = await axios.post('http://localhost:5000/api/read_columns', {
      filename: selectedFile.value,
      sheet: selectedSheet.value
    })
    columns.value = response.data.columns
    autoSelectColumns()
  } catch (error) {
    ElMessage.error('載入欄位失敗')
    console.error(error)
  }
}

// 自動選擇欄位
const autoSelectColumns = () => {
  if (columns.value.length === 0) return
  
  console.log('可用欄位:', columns.value)
  
  // 自動選擇年份欄位（更完整的匹配）
  const yearColumns = columns.value.filter(col => {
    const colLower = col.toLowerCase()
    return col.includes('年') || 
           col.includes('學年') || 
           col.includes('入學年') ||
           colLower.includes('year') ||
           col.includes('年度') ||
           col.includes('學年度')
  })
  if (yearColumns.length > 0) {
    yearCol.value = yearColumns[0]
    yearlyAdmissionYearCol.value = yearColumns[0]
    schoolSourceYearCol.value = yearColumns[0]
    admissionMethodYearCol.value = yearColumns[0]
    geoYearCol.value = yearColumns[0]
    console.log('自動選擇年份欄位:', yearColumns[0])
  }
  
  // 自動選擇學校欄位（更完整的匹配）
  const schoolColumns = columns.value.filter(col => {
    const colLower = col.toLowerCase()
    return col.includes('學校') || 
           col.includes('高中') || 
           col.includes('高職') ||
           col.includes('國中') ||
           col.includes('畢業學校') ||
           colLower.includes('school') ||
           col.includes('校名')
  })
  if (schoolColumns.length > 0) {
    schoolNameCol.value = schoolColumns[0]
    console.log('自動選擇學校欄位:', schoolColumns[0])
  }
  
  // 自動選擇入學管道欄位
  const admissionColumns = columns.value.filter(col => {
    const colLower = col.toLowerCase()
    return col.includes('管道') || 
           col.includes('入學方式') || 
           col.includes('類別') ||
           col.includes('入學管道') ||
           col.includes('錄取方式') ||
           colLower.includes('admission') ||
           col.includes('招生方式')
  })
  if (admissionColumns.length > 0) {
    admissionMethodCol.value = admissionColumns[0]
    console.log('自動選擇入學管道欄位:', admissionColumns[0])
  }
  
  // 自動選擇性別欄位
  const genderColumns = columns.value.filter(col => {
    const colLower = col.toLowerCase()
    return col.includes('性別') || 
           colLower.includes('gender') || 
           colLower.includes('sex') ||
           col.includes('男女')
  })
  if (genderColumns.length > 0) {
    genderCol.value = genderColumns[0]
    console.log('自動選擇性別欄位:', genderColumns[0])
  }
  
  // 自動選擇地區欄位
  const regionColumns = columns.value.filter(col => {
    const colLower = col.toLowerCase()
    return col.includes('地區') || 
           col.includes('縣市') || 
           col.includes('城市') || 
           col.includes('地理') ||
           col.includes('縣') ||
           col.includes('市') ||
           col.includes('戶籍') ||
           colLower.includes('region') ||
           colLower.includes('city') ||
           col.includes('居住地')
  })
  if (regionColumns.length > 0) {
    geoRegionCol.value = regionColumns[0]
    console.log('自動選擇地區欄位:', regionColumns[0])
  }
  
  // 自動選擇科目欄位（用於多科目分析）
  const subjectColumns = columns.value.filter(col => {
    return col.includes('國文') || 
           col.includes('英文') || 
           col.includes('數學') ||
           col.includes('物理') ||
           col.includes('化學') ||
           col.includes('生物') ||
           col.includes('歷史') ||
           col.includes('地理') ||
           col.includes('公民') ||
           col.includes('成績') ||
           col.includes('分數') ||
           /\d+分/.test(col) // 匹配包含"分"的數字欄位
  })
  if (subjectColumns.length > 0) {
    // 預設選擇前3個科目
    selectedSubjects.value = subjectColumns.slice(0, 3)
    console.log('自動選擇科目欄位:', selectedSubjects.value)
  }
  
  // 自動選擇第一個數值型欄位作為統計欄位
  const numericColumns = columns.value.filter(col => {
    return col.includes('成績') || 
           col.includes('分數') || 
           col.includes('分') ||
           col.includes('總分') ||
           /\d/.test(col) // 包含數字的欄位
  })
  if (numericColumns.length > 0 && !selectedColumn.value) {
    selectedColumn.value = numericColumns[0]
    console.log('自動選擇統計欄位:', numericColumns[0])
  }
}

// 分析方法
const getColumnStats = async () => {
  if (!selectedTable.value || !selectedColumn.value) {
    ElMessage.warning('請先選擇資料表格和欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/column_stats', {
      table_name: selectedTable.value,
      column: selectedColumn.value
    })
    columnStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderColumnChart(response.data)
  } catch (error) {
    ElMessage.error('統計分析失敗')
    console.error(error)
  }
}

const getMultiSubjectStats = async () => {
  if (!selectedTable.value || !selectedSubjects.value.length || !yearCol.value) {
    ElMessage.warning('請先選擇資料表格、科目和年度欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/multi_subject_stats', {
      table_name: selectedTable.value,
      subjects: selectedSubjects.value,
      year_col: yearCol.value
    })
    multiSubjectStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderMultiSubjectChart(response.data)
  } catch (error) {
    ElMessage.error('多科目分析失敗')
    console.error(error)
  }
}


const getYearlyAdmissionStats = async () => {
  if (!selectedTable.value || !yearlyAdmissionYearCol.value) {
    ElMessage.warning('請先選擇資料表格和年度欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/yearly_admission_stats', {
      table_name: selectedTable.value,
      year_col: yearlyAdmissionYearCol.value,
      gender_col: genderCol.value
    })
    yearlyAdmissionStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderYearlyAdmissionChart(response.data)
  } catch (error) {
    ElMessage.error('入學生數量分析失敗')
    console.error(error)
  }
}

const getSchoolSourceStats = async () => {
  if (!selectedTable.value || !schoolSourceYearCol.value || !schoolNameCol.value) {
    ElMessage.warning('請先選擇資料表格、年度欄位和學校欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/school_source_stats', {
      table_name: selectedTable.value,
      year_col: schoolSourceYearCol.value,
      school_col: schoolNameCol.value
    })
    schoolSourceStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderSchoolSourceChart(response.data)
  } catch (error) {
    ElMessage.error('學校來源分析失敗')
    console.error(error)
  }
}


const getAdmissionMethodStats = async () => {
  if (!selectedTable.value || !admissionMethodYearCol.value || !admissionMethodCol.value) {
    ElMessage.warning('請先選擇資料表格、年度欄位和入學管道欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/admission_method_stats', {
      table_name: selectedTable.value,
      year_col: admissionMethodYearCol.value,
      method_col: admissionMethodCol.value
    })
    admissionMethodStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderAdmissionMethodChart(response.data)
  } catch (error) {
    ElMessage.error('入學管道分析失敗')
    console.error(error)
  }
}


// 地理區域分析
const getGeographicStats = async () => {
  if (!selectedTable.value || !geoYearCol.value || !geoRegionCol.value) {
    ElMessage.warning('請先選擇資料表格、年度欄位和地區欄位')
    return
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/geographic_stats', {
      table_name: selectedTable.value,
      year_col: geoYearCol.value,
      region_col: geoRegionCol.value,
      get_city_details: true
    })
    
    geoStats.value = response.data
    currentStats.value = response.data
    await nextTick()
    renderGeoChart()
    renderRegionalCityCharts()
  } catch (error) {
    ElMessage.error('地理區域分析失敗')
    console.error(error)
  }
}

const showRawData = async () => {
  try {
    const response = await axios.post('http://localhost:5000/api/raw_data', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      column: selectedColumn.value
    })
    rawData.value = response.data.data
  } catch (error) {
    ElMessage.error('載入原始資料失敗')
    console.error(error)
  }
}

// 圖表渲染方法
const renderColumnChart = (data) => {
  if (!data || !data.data) return
  
  nextTick(() => {
    const canvas = document.getElementById('statsChart')
    if (!canvas) {
      console.error('Canvas element not found: statsChart')
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Cannot get 2d context from canvas')
      return
    }
    
    if (columnChartInstance) {
      columnChartInstance.destroy()
      columnChartInstance = null
    }
    
    // 處理數據
    const validData = data.data.map((value, index) => ({
      value: Number(value),
      index: index + 1
    })).filter(item => !isNaN(item.value))
    
    if (validData.length === 0) return
    
    columnChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: validData.map(item => item.index),
        datasets: [{
          label: data.column_name,
          data: validData.map(item => item.value),
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: { 
            display: true, 
            text: '數值分布圖',
            font: { size: 16 }
          },
          legend: { position: 'top' }
        },
        scales: {
          x: {
            title: { 
              display: true, 
              text: '資料序號' 
            }
          },
          y: {
            title: { 
              display: true, 
              text: '數值' 
            },
            beginAtZero: true
          }
        }
      }
    })
  })
}

const renderMultiSubjectChart = (data) => {
  if (!data || !data.years || !data.subjects) return
  
  nextTick(() => {
    const canvas = document.getElementById('multiSubjectChart')
    if (!canvas) {
      console.error('Canvas element not found: multiSubjectChart')
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Cannot get 2d context from canvas')
      return
    }
    
    if (multiSubjectChartInstance) {
      multiSubjectChartInstance.destroy()
      multiSubjectChartInstance = null
    }
    
    const { years, subjects, data: chartData } = data
    const colors = [
      'rgba(54, 162, 235, 0.7)',
      'rgba(255, 99, 132, 0.7)',
      'rgba(255, 206, 86, 0.7)',
      'rgba(75, 192, 192, 0.7)',
      'rgba(153, 102, 255, 0.7)',
      'rgba(255, 159, 64, 0.7)'
    ]
    
    const datasets = years.map((year, i) => ({
      label: year,
      data: subjects.map(subj => chartData[subj][i]),
      backgroundColor: colors[i % colors.length]
    }))
    
    multiSubjectChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: subjects,
        datasets
      },
      options: {
        responsive: true,
        plugins: {
          title: { display: true, text: '各學年各科平均分數' },
          legend: { position: 'top' }
        },
        scales: {
          x: { title: { display: true, text: '學科' } },
          y: { title: { display: true, text: '平均分數' }, beginAtZero: true }
        }
      }
    })
  })
}

const renderYearlyAdmissionChart = (data) => {
  if (!data || !data.years) return
  
  nextTick(() => {
    const canvas = document.getElementById('yearlyAdmissionChart')
    if (!canvas) {
      console.error('Canvas element not found: yearlyAdmissionChart')
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Cannot get 2d context from canvas')
      return
    }
    
    if (yearlyAdmissionChartInstance) {
      yearlyAdmissionChartInstance.destroy()
      yearlyAdmissionChartInstance = null
    }
    
    const datasets = []
    
    // 檢查是否有性別區分
    if (data.has_gender) {
      // 添加男生資料
      datasets.push({
        type: 'bar',
        label: '男生',
        data: data.male_counts,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        barPercentage: 0.8
      })
      
      // 添加女生資料
      datasets.push({
        type: 'bar',
        label: '女生',
        data: data.female_counts,
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        barPercentage: 0.8
      })
    } else {
      // 沒有性別區分，使用總人數
      datasets.push({
        type: 'bar',
        label: '入學人數',
        data: data.total_counts,
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        barPercentage: 0.8
      })
    }
    
    // 添加總人數趨勢線
    datasets.push({
      type: 'line',
      label: '總人數趨勢',
      data: data.total_counts,
      borderColor: 'rgba(153, 102, 255, 1)',
      borderWidth: 2,
      fill: false,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6
    })
    
    yearlyAdmissionChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          title: {
            display: true,
            text: '每年入學生數量統計',
            font: { size: 16 }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.parsed.y !== null) {
                  label += context.parsed.y + ' 人';
                }
                return label;
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '年度'
            },
            stacked: true
          },
          y: {
            title: {
              display: true,
              text: '人數'
            },
            stacked: true,
            beginAtZero: true
          }
        }
      }
    })
  })
}

const renderSchoolSourceChart = (data) => {
  if (!data || !data.years) return
  
  nextTick(() => {
    const canvas = document.getElementById('schoolSourceChart')
    if (!canvas) {
      console.error('Canvas element not found: schoolSourceChart')
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Cannot get 2d context from canvas')
      return
    }
    
    if (schoolSourceChartInstance) {
      schoolSourceChartInstance.destroy()
      schoolSourceChartInstance = null
    }
    
    // 定義顏色方案
    const colorScheme = {
      '國立': '#FF6B6B',
      '市立': '#4ECDC4', 
      '縣立': '#45B7D1',
      '私立': '#96CEB4',
      '財團': '#FECA57',
      '國大轉': '#FF9FF3',
      '私大轉': '#54A0FF',
      '科大轉': '#5F27CD',
      '僑生': '#00D2D3',
      '其他': '#C4C4C4'
    }
    
    // 準備 datasets
    const datasets = data.school_types.map(schoolType => ({
      label: schoolType,
      data: data.data[schoolType].counts,
      backgroundColor: colorScheme[schoolType] || '#C4C4C4',
      borderColor: colorScheme[schoolType] || '#C4C4C4',
      borderWidth: 1,
      barPercentage: 0.5,
      categoryPercentage: 0.9
    }))
    
    schoolSourceChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.years,
        datasets
      },
      options: {
        responsive: true,
        plugins: {
          title: { 
            display: true, 
            text: '(下方圖表中各年度入學生學校來源類型分布)' 
          },
          legend: { 
            position: 'top',
            labels: {
              boxWidth: 12,
              padding: 8
            }
          },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const yearIndex = context.dataIndex
                const schoolType = context.dataset.label
                const count = data.data[schoolType].counts[yearIndex]
                const percentage = data.data[schoolType].percentages[yearIndex]
                const total = data.year_totals[yearIndex]
                return [`人數: ${count}人`, `比例: ${percentage}%`, `該年總計: ${total}人`]
              }
            }
          }
        },
        scales: {
          x: { 
            title: { display: true, text: '年份' },
            stacked: true
          },
          y: {
            title: { display: true, text: '人數' },
            stacked: true,
            beginAtZero: true
          }
        }
      }
    })
  })
}

const renderAdmissionMethodChart = (data) => {
  if (!data || !data.years) return
  
  nextTick(() => {
    const canvas = document.getElementById('admissionMethodChart')
    if (!canvas) {
      console.error('Canvas element not found: admissionMethodChart')
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Cannot get 2d context from canvas')
      return
    }
    
    if (admissionMethodChartInstance) {
      admissionMethodChartInstance.destroy()
      admissionMethodChartInstance = null
    }
    
    // 定義顏色方案
    const colorScheme = {
      '申請入學': '#FF6B6B',
      '繁星推薦': '#4ECDC4', 
      '自然組': '#45B7D1',
      '社會組': '#96CEB4',
      '僑生': '#00D2D3',
      '願景': '#FECA57',
      '其他': '#C4C4C4'
    }
    
    // 準備 datasets
    const datasets = data.method_types.map(methodType => ({
      label: methodType,
      data: data.data[methodType].counts,
      backgroundColor: colorScheme[methodType] || '#C4C4C4',
      borderColor: colorScheme[methodType] || '#C4C4C4',
      borderWidth: 1
    }))
    
    admissionMethodChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.years,
        datasets
      },
      options: {
        responsive: true,
        plugins: {
          title: { 
            display: true, 
            text: '各年度入學生入學管道分布' 
          },
          legend: { 
            position: 'top',
            labels: {
              boxWidth: 12,
              padding: 8
            }
          },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const yearIndex = context.dataIndex
                const methodType = context.dataset.label
                const count = data.data[methodType].counts[yearIndex]
                const percentage = data.data[methodType].percentages[yearIndex]
                const total = data.year_totals[yearIndex]
                return [`人數: ${count}人`, `比例: ${percentage}%`, `該年總計: ${total}人`]
              }
            }
          }
        },
        scales: {
          x: { 
            title: { display: true, text: '年份' },
            stacked: true
          },
          y: {
            title: { display: true, text: '人數' },
            stacked: true,
            beginAtZero: true
          }
        }
      }
    })
  })
}

// 顯示導出對話框
const showExportDialog = (chartId, title, data) => {
  currentChartId.value = chartId
  currentExportTitle.value = title
  currentChartType.value = 'canvas'
  currentChartData.value = data
  exportDialogVisible.value = true
}

const showEChartsExportDialog = (chartId, title, data) => {
  currentChartId.value = chartId
  currentExportTitle.value = title
  currentChartType.value = 'echarts'
  currentChartData.value = data
  exportDialogVisible.value = true
}

// 根據格式導出
const exportInFormat = (format) => {
  exportDialogVisible.value = false
  
  switch (format) {
    case 'png':
      exportAsImage('png')
      break
    case 'jpeg':
      exportAsImage('jpeg')
      break
    case 'svg':
      exportAsSVG()
      break
    case 'pdf':
      exportAsPDF()
      break
    case 'pdf-advanced':
      exportAsPDFAdvanced()
      break
    case 'csv':
      exportAsCSV()
      break
    case 'json':
      exportAsJSON()
      break
    default:
      ElMessage.error('不支援的導出格式')
  }
}

// 導出為圖片
const exportAsImage = (format) => {
  if (currentChartType.value === 'canvas') {
    exportCanvasAsImage(format)
  } else if (currentChartType.value === 'echarts') {
    exportEChartsAsImage(format)
  }
}

const exportCanvasAsImage = (format) => {
  const canvas = document.getElementById(currentChartId.value)
  if (!canvas) {
    ElMessage.error('找不到圖表，請先生成圖表')
    return
  }
  
  try {
    let dataURL
    
    if (format === 'jpeg') {
      // 為JPEG格式創建白色背景
      const tempCanvas = document.createElement('canvas')
      const tempCtx = tempCanvas.getContext('2d')
      tempCanvas.width = canvas.width
      tempCanvas.height = canvas.height
      
      // 填充白色背景
      tempCtx.fillStyle = '#FFFFFF'
      tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height)
      
      // 繪製原圖表
      tempCtx.drawImage(canvas, 0, 0)
      
      dataURL = tempCanvas.toDataURL('image/jpeg', 0.9)
    } else {
      const mimeType = 'image/png'
      dataURL = canvas.toDataURL(mimeType, 1.0)
    }
    
    const link = document.createElement('a')
    link.download = `${currentExportTitle.value}_${new Date().toISOString().slice(0, 10)}.${format}`
    link.href = dataURL
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`圖表已導出為 ${format.toUpperCase()}`)
  } catch (error) {
    console.error('圖表導出失敗:', error)
    ElMessage.error('圖表導出失敗，請重試')
  }
}

const exportEChartsAsImage = (format) => {
  const chartInstance = getEChartsInstance(currentChartId.value)
  if (!chartInstance) {
    ElMessage.error('找不到圖表，請先生成圖表')
    return
  }
  
  try {
    const backgroundColor = format === 'jpeg' ? '#FFFFFF' : '#fff'
    const type = format === 'jpeg' ? 'jpeg' : 'png'
    
    const base64 = chartInstance.getDataURL({
      type: type,
      pixelRatio: 2,
      backgroundColor: backgroundColor
    })
    
    const link = document.createElement('a')
    link.download = `${currentExportTitle.value}_${new Date().toISOString().slice(0, 10)}.${format}`
    link.href = base64
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`圖表已導出為 ${format.toUpperCase()}`)
  } catch (error) {
    console.error('圖表導出失敗:', error)
    ElMessage.error('圖表導出失敗，請重試')
  }
}

// 導出為SVG (僅支援ECharts)
const exportAsSVG = () => {
  if (currentChartType.value !== 'echarts') {
    ElMessage.warning('SVG 格式僅支援地理區域圖表')
    return
  }
  
  const chartInstance = getEChartsInstance(currentChartId.value)
  if (!chartInstance) {
    ElMessage.error('找不到圖表，請先生成圖表')
    return
  }
  
  try {
    const svgStr = chartInstance.renderToSVGString()
    const blob = new Blob([svgStr], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.download = `${currentExportTitle.value}_${new Date().toISOString().slice(0, 10)}.svg`
    link.href = url
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    ElMessage.success('圖表已導出為 SVG')
  } catch (error) {
    console.error('SVG導出失敗:', error)
    ElMessage.error('SVG導出失敗，請重試')
  }
}

// 導出為PDF
const exportAsPDF = () => {
  try {
    // 創建一個包含圖表的完整HTML頁面
    const chartContainer = createPDFContent()
    
    // 創建新窗口
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('無法打開新窗口，請檢查瀏覽器設定')
      return
    }
    
    // 寫入HTML內容
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${currentExportTitle.value}</title>
        <style>
          @page {
            size: A4;
            margin: 20mm;
          }
          body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
          }
          h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 20px;
            font-size: 24px;
          }
          .chart-container {
            text-align: center;
            margin: 20px 0;
          }
          .chart-image {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          }
          .stats-info {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #409eff;
          }
          .stats-info h3 {
            margin: 0 0 10px 0;
            color: #409eff;
          }
          .stats-item {
            margin: 5px 0;
            color: #666;
          }
          .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
            padding-top: 10px;
          }
          @media print {
            body { margin: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        <h1>📊 ${currentExportTitle.value}</h1>
        <div class="chart-container">
          ${chartContainer}
        </div>
        ${generateStatsInfo()}
        <div class="footer">
          <p>報告生成時間：${new Date().toLocaleString('zh-TW')}</p>
          <p>學生資料分析系統</p>
        </div>
      </body>
      </html>
    `)
    
    printWindow.document.close()
    
    // 等待內容載入完成後列印
    setTimeout(() => {
      printWindow.focus()
      printWindow.print()
      printWindow.close()
    }, 1000)
    
    ElMessage.success('PDF列印對話框已開啟，請選擇"另存為PDF"')
  } catch (error) {
    console.error('PDF導出失敗:', error)
    ElMessage.error('PDF導出失敗，請重試')
  }
}

const createPDFContent = () => {
  if (currentChartType.value === 'canvas') {
    const canvas = document.getElementById(currentChartId.value)
    if (canvas) {
      // 為PDF創建白色背景的圖片
      const tempCanvas = document.createElement('canvas')
      const tempCtx = tempCanvas.getContext('2d')
      tempCanvas.width = canvas.width
      tempCanvas.height = canvas.height
      
      // 填充白色背景
      tempCtx.fillStyle = '#FFFFFF'
      tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height)
      
      // 繪製原圖表
      tempCtx.drawImage(canvas, 0, 0)
      
      const dataURL = tempCanvas.toDataURL('image/png', 1.0)
      return `<img src="${dataURL}" class="chart-image" alt="${currentExportTitle.value}" />`
    }
  } else if (currentChartType.value === 'echarts') {
    const chartInstance = getEChartsInstance(currentChartId.value)
    if (chartInstance) {
      const dataURL = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#FFFFFF'
      })
      return `<img src="${dataURL}" class="chart-image" alt="${currentExportTitle.value}" />`
    }
  }
  return '<p>無法載入圖表</p>'
}

const generateStatsInfo = () => {
  if (!currentChartData.value) return ''
  
  const data = currentChartData.value
  let statsHTML = '<div class="stats-info"><h3>📈 統計資訊</h3>'
  
  if (data.column_name) {
    // 單欄位統計
    statsHTML += `
      <div class="stats-item"><strong>欄位名稱：</strong>${data.column_name}</div>
      <div class="stats-item"><strong>總計筆數：</strong>${data.count} 筆</div>
      <div class="stats-item"><strong>平均值：</strong>${data.mean?.toFixed(2) || 'N/A'}</div>
      <div class="stats-item"><strong>標準差：</strong>${data.std?.toFixed(2) || 'N/A'}</div>
      <div class="stats-item"><strong>最小值：</strong>${data.min || 'N/A'}</div>
      <div class="stats-item"><strong>最大值：</strong>${data.max || 'N/A'}</div>
    `
  } else if (data.year_range) {
    // 時間範圍統計
    statsHTML += `
      <div class="stats-item"><strong>分析期間：</strong>${data.year_range}</div>
      <div class="stats-item"><strong>總人數：</strong>${data.total_students || 'N/A'} 人</div>
    `
    if (data.subjects) {
      statsHTML += `<div class="stats-item"><strong>分析科目：</strong>${data.subjects.join(', ')}</div>`
    }
  }
  
  statsHTML += '</div>'
  return statsHTML
}

// 高級PDF導出 - 使用現代瀏覽器API
const exportAsPDFAdvanced = async () => {
  try {
    // 檢查瀏覽器支援
    if (!window.jsPDF && !window.html2canvas) {
      ElMessage.warning('高級PDF功能需要額外庫支援，將使用基本PDF功能')
      exportAsPDF()
      return
    }
    
    // 創建包含圖表的容器
    const container = document.createElement('div')
    container.style.cssText = `
      width: 800px;
      padding: 40px;
      background: white;
      font-family: 'Microsoft JhengHei', Arial, sans-serif;
      position: absolute;
      left: -9999px;
      top: 0;
    `
    
    // 添加標題
    const title = document.createElement('h1')
    title.textContent = currentExportTitle.value
    title.style.cssText = `
      text-align: center;
      color: #2c3e50;
      margin-bottom: 30px;
      font-size: 28px;
    `
    container.appendChild(title)
    
    // 添加圖表
    const chartDiv = document.createElement('div')
    chartDiv.style.cssText = 'text-align: center; margin: 30px 0;'
    
    const chartImg = document.createElement('img')
    if (currentChartType.value === 'canvas') {
      const canvas = document.getElementById(currentChartId.value)
      if (canvas) {
        // 創建白色背景版本
        const tempCanvas = document.createElement('canvas')
        const tempCtx = tempCanvas.getContext('2d')
        tempCanvas.width = canvas.width
        tempCanvas.height = canvas.height
        
        tempCtx.fillStyle = '#FFFFFF'
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height)
        tempCtx.drawImage(canvas, 0, 0)
        
        chartImg.src = tempCanvas.toDataURL('image/png', 1.0)
      }
    } else if (currentChartType.value === 'echarts') {
      const chartInstance = getEChartsInstance(currentChartId.value)
      if (chartInstance) {
        chartImg.src = chartInstance.getDataURL({
          type: 'png',
          pixelRatio: 2,
          backgroundColor: '#FFFFFF'
        })
      }
    }
    
    chartImg.style.cssText = 'max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;'
    chartDiv.appendChild(chartImg)
    container.appendChild(chartDiv)
    
    // 添加統計資訊
    if (currentChartData.value) {
      const statsDiv = document.createElement('div')
      statsDiv.innerHTML = generateStatsInfo()
      container.appendChild(statsDiv)
    }
    
    // 添加頁腳
    const footer = document.createElement('div')
    footer.innerHTML = `
      <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px;">
        <p>報告生成時間：${new Date().toLocaleString('zh-TW')}</p>
        <p>學生資料分析系統</p>
      </div>
    `
    container.appendChild(footer)
    
    // 添加到DOM中
    document.body.appendChild(container)
    
    // 等待圖片載入
    await new Promise(resolve => {
      if (chartImg.complete) {
        resolve()
      } else {
        chartImg.onload = resolve
        chartImg.onerror = resolve
      }
    })
    
    // 使用瀏覽器列印API
    const printFrame = document.createElement('iframe')
    printFrame.style.cssText = 'position: absolute; left: -9999px; top: 0; width: 1px; height: 1px;'
    document.body.appendChild(printFrame)
    
    const frameDoc = printFrame.contentDocument || printFrame.contentWindow.document
    frameDoc.open()
    frameDoc.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${currentExportTitle.value}</title>
        <style>
          @page { size: A4; margin: 20mm; }
          body { margin: 0; padding: 0; font-family: 'Microsoft JhengHei', Arial, sans-serif; }
          @media print {
            body { background: white !important; }
          }
        </style>
      </head>
      <body>
        ${container.innerHTML}
      </body>
      </html>
    `)
    frameDoc.close()
    
    // 等待載入完成後列印
    setTimeout(() => {
      printFrame.contentWindow.focus()
      printFrame.contentWindow.print()
      
      // 清理
      setTimeout(() => {
        document.body.removeChild(container)
        document.body.removeChild(printFrame)
      }, 1000)
    }, 500)
    
    ElMessage.success('高級PDF列印對話框已開啟')
    
  } catch (error) {
    console.error('高級PDF導出失敗:', error)
    ElMessage.error('高級PDF導出失敗，將使用基本版本')
    exportAsPDF()
  }
}

// 導出為CSV
const exportAsCSV = () => {
  if (!currentChartData.value) {
    ElMessage.error('無可用數據')
    return
  }
  
  try {
    let csvContent = ''
    const data = currentChartData.value
    
    // 根據不同的圖表類型生成不同的CSV格式
    if (data.column_name) {
      // 單欄位統計
      csvContent = '統計項目,數值\n'
      csvContent += `欄位名稱,${data.column_name}\n`
      csvContent += `總計筆數,${data.count}\n`
      csvContent += `平均值,${data.mean || 'N/A'}\n`
      csvContent += `標準差,${data.std || 'N/A'}\n`
      csvContent += `最小值,${data.min || 'N/A'}\n`
      csvContent += `最大值,${data.max || 'N/A'}\n`
    } else if (data.subjects) {
      // 多科目分析
      csvContent = '年份,' + data.subjects.join(',') + '\n'
      data.years.forEach((year, index) => {
        const row = [year]
        data.subjects.forEach(subject => {
          const yearData = data.yearly_data.find(d => d.year === year)
          row.push(yearData ? yearData[subject] || 0 : 0)
        })
        csvContent += row.join(',') + '\n'
      })
    } else if (data.years && data.total_counts) {
      // 年度統計
      csvContent = '年份,總人數\n'
      data.years.forEach((year, index) => {
        csvContent += `${year},${data.total_counts[index]}\n`
      })
    }
    
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `${currentExportTitle.value}_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    ElMessage.success('數據已導出為 CSV')
  } catch (error) {
    console.error('CSV導出失敗:', error)
    ElMessage.error('CSV導出失敗，請重試')
  }
}

// 導出為JSON
const exportAsJSON = () => {
  if (!currentChartData.value) {
    ElMessage.error('無可用數據')
    return
  }
  
  try {
    const jsonData = {
      title: currentExportTitle.value,
      exportDate: new Date().toISOString(),
      data: currentChartData.value
    }
    
    const jsonStr = JSON.stringify(jsonData, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.download = `${currentExportTitle.value}_${new Date().toISOString().slice(0, 10)}.json`
    link.href = url
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    ElMessage.success('數據已導出為 JSON')
  } catch (error) {
    console.error('JSON導出失敗:', error)
    ElMessage.error('JSON導出失敗，請重試')
  }
}

// 圖表導出功能
const exportChart = (canvasId, chartTitle) => {
  const canvas = document.getElementById(canvasId)
  if (!canvas) {
    ElMessage.error('找不到圖表，請先生成圖表')
    return
  }
  
  try {
    // 創建下載連結
    const link = document.createElement('a')
    link.download = `${chartTitle}_${new Date().toISOString().slice(0, 10)}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    
    // 觸發下載
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`圖表已導出: ${chartTitle}`)
  } catch (error) {
    console.error('圖表導出失敗:', error)
    ElMessage.error('圖表導出失敗，請重試')
  }
}

const exportEChart = (chartId, chartTitle) => {
  const chartInstance = getEChartsInstance(chartId)
  if (!chartInstance) {
    ElMessage.error('找不到圖表，請先生成圖表')
    return
  }
  
  try {
    // 取得圖表的base64圖片
    const base64 = chartInstance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    
    // 創建下載連結
    const link = document.createElement('a')
    link.download = `${chartTitle}_${new Date().toISOString().slice(0, 10)}.png`
    link.href = base64
    
    // 觸發下載
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`圖表已導出: ${chartTitle}`)
  } catch (error) {
    console.error('圖表導出失敗:', error)
    ElMessage.error('圖表導出失敗，請重試')
  }
}

const getEChartsInstance = (chartId) => {
  if (chartId === 'geoChart') {
    return geoChartInstance
  } else if (chartId.startsWith('geoChart-')) {
    const region = chartId.replace('geoChart-', '')
    return geoDetailedChartInstances[region]
  }
  return null
}

// 清理函數
onBeforeUnmount(() => {
  cleanupFunctions.forEach(cleanup => cleanup())
  
  if (columnChartInstance) {
    columnChartInstance.destroy()
  }
  if (multiSubjectChartInstance) {
    multiSubjectChartInstance.destroy()
  }
  if (yearlyAdmissionChartInstance) {
    yearlyAdmissionChartInstance.destroy()
  }
  if (schoolSourceChartInstance) {
    schoolSourceChartInstance.destroy()
  }
  if (admissionMethodChartInstance) {
    admissionMethodChartInstance.destroy()
  }
  if (geoChartInstance) {
    geoChartInstance.dispose()
  }
  if (geoDetailedChartInstances) {
    Object.values(geoDetailedChartInstances).forEach(chart => {
      if (chart) chart.dispose()
    })
  }
})

// 渲染地理區域圖表
const renderGeoChart = () => {
  if (!geoStats.value) return

  const chartDom = document.getElementById('geoChart')
  if (!chartDom) return
  
  // 如果圖表實例已存在，先銷毀
  if (geoChartInstance) {
    geoChartInstance.dispose()
  }
  
  geoChartInstance = echarts.init(chartDom)
  
  const colors = {
    '北台灣': '#FF6B6B',
    '西台灣': '#4ECDC4',
    '南台灣': '#45B7D1',
    '東台灣': '#96CEB4',
    '其他': '#FFEEAD'
  }
  
  const series = geoStats.value.regions.map(region => ({
    name: region,
    type: 'bar',
    stack: 'total',
    label: {
      show: true,
      position: 'inside',
      formatter: '{c}人'
    },
    emphasis: {
      focus: 'series'
    },
    data: geoStats.value.data[region]
  }))

  const option = {
    title: {
      text: '各地區學生人數統計',
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: geoStats.value.regions,
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '60px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: geoStats.value.years,
      name: '年度'
    },
    yAxis: {
      type: 'value',
      name: '人數'
    },
    series: series,
    color: Object.values(colors)
  }

  geoChartInstance.setOption(option)
  
  // 響應視窗大小變化
  window.addEventListener('resize', () => {
    if (geoChartInstance) {
      geoChartInstance.resize()
    }
  })
}

// 渲染各區域縣市的圖表
const renderRegionalCityCharts = () => {
  if (!geoStats.value || !geoStats.value.detailed) {
    console.log('缺少地理區域縣市詳細資料')
    return
  }
  
  // 清理現有圖表實例
  if (geoDetailedChartInstances) {
    Object.values(geoDetailedChartInstances).forEach(chart => {
      if (chart) chart.dispose()
    })
  }
  
  // 初始化圖表對象
  geoDetailedChartInstances = {}
  
  // 四個區域：北台灣、中台灣、南台灣、東台灣
  const regions = ['北台灣', '中台灣', '南台灣', '東台灣']
  const colorMap = {
    '北台灣': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD'],
    '中台灣': ['#4ECDC4', '#FF6B6B', '#96CEB4', '#FECA57', '#45B7D1', '#FF9FF3', '#54A0FF', '#5F27CD'],
    '南台灣': ['#45B7D1', '#FF6B6B', '#4ECDC4', '#FECA57', '#96CEB4', '#FF9FF3', '#54A0FF', '#5F27CD'],
    '東台灣': ['#96CEB4', '#FECA57', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FF9FF3', '#54A0FF', '#5F27CD']
  }

  // 使用 nextTick 確保 DOM 已完全更新
  nextTick(() => {
    regions.forEach(region => {
      if (!geoStats.value.detailed || !geoStats.value.detailed[region]) {
        console.log(`找不到 ${region} 的詳細數據`)
        return
      }

      const chartDom = document.getElementById(`geoChart-${region}`)
      if (!chartDom) {
        console.log(`找不到 ${region} 的圖表DOM元素`)
        return
      }

      try {
        // 獲取該區域的縣市數據
        const regionData = geoStats.value.detailed[region]
        if (!regionData || !regionData.cities || regionData.cities.length === 0) {
          console.log(`${region} 沒有縣市數據`)
          return
        }

        // 初始化圖表容器尺寸
        chartDom.style.width = '100%'
        chartDom.style.height = '400px'
        chartDom.style.maxWidth = '100%'

        // 初始化 ECharts 實例
        const chart = echarts.init(chartDom)
        geoDetailedChartInstances[region] = chart

        // 準備數據系列
        const cities = regionData.cities || []
        let displayCities = [...cities]
        
        // 處理每個城市的數據
        const series = displayCities.map((city, index) => {
          // 確保每個城市都有完整的年份數據陣列
          const cityData = Array(geoStats.value.years.length).fill(0)
          if (Array.isArray(city.data)) {
            city.data.forEach((value, idx) => {
              if (idx < cityData.length) {
                cityData[idx] = value || 0
              }
            })
          }

          return {
            name: city.name,
            type: 'bar',
            stack: 'total',
            barWidth: '60%',
            data: cityData,
            label: {
              show: true,
              position: 'inside',
              formatter: function(params) {
                return params.value > 0 ? `${params.value}人` : '';
              },
              fontSize: 10,
              color: '#fff',
              fontWeight: 'bold'
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                shadowBlur: 15,
                shadowColor: 'rgba(0, 0, 0, 0.4)',
                borderColor: '#fff',
                borderWidth: 2
              }
            },
            itemStyle: {
              color: colorMap[region][index % colorMap[region].length]
            }
          }
        })
        
        // 設定圖表選項
        const option = {
          title: {
            text: `${region}縣市學生人數統計`,
            left: 'center',
            top: 10
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ccc',
            borderWidth: 1,
            textStyle: {
              color: '#333',
              fontSize: 13
            },
            formatter: function(params) {
              let result = `<strong style="font-size: 14px;">${params[0].axisValue}年</strong><br/>`
              let yearTotal = 0
              
              // 計算該年度總人數
              params.forEach(param => {
                if (param.data !== undefined && param.data !== null) {
                  yearTotal += param.data
                }
              })
              
              // 按數值大小排序顯示
              const sortedParams = params
                .filter(param => param.data !== undefined && param.data !== null)
                .sort((a, b) => b.data - a.data)
              
              sortedParams.forEach(param => {
                const count = param.data
                const percentage = yearTotal > 0 ? ((count / yearTotal) * 100).toFixed(1) : 0
                
                result += `<span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${param.color};"></span>`
                result += `${param.seriesName}:<br/>`
                result += `&nbsp;&nbsp;人數: <strong>${count}人</strong><br/>`
                result += `&nbsp;&nbsp;比例: <strong>${percentage}%</strong><br/>`
              })
              
              result += `<hr style="margin: 5px 0; border: none; border-top: 1px solid #eee;">` 
              result += `<strong style="font-size: 13px;">該年總計: ${yearTotal}人</strong>`
              return result
            }
          },
          legend: {
            data: displayCities.map(city => city.name),
            bottom: 10,
            type: 'scroll',
            textStyle: {
              fontSize: 12
            },
            pageTextStyle: {
              color: '#666'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '25%',
            top: '60px',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: geoStats.value.years || [],
            name: '年度'
          },
          yAxis: {
            type: 'value',
            name: '人數'
          },
          series: series,
          animationDuration: 1000,
          animationEasing: 'cubicOut',
          emphasis: {
            focus: 'series',
            blurScope: 'coordinateSystem'
          }
        }
        
        // 渲染圖表
        geoDetailedChartInstances[region].setOption(option)
        
        // 添加響應式調整
        const handleResize = () => {
          if (geoDetailedChartInstances[region]) {
            geoDetailedChartInstances[region].resize()
          }
        }
        
        window.addEventListener('resize', handleResize)
        
        // 註冊清理函數
        const cleanup = () => {
          window.removeEventListener('resize', handleResize)
          if (geoDetailedChartInstances[region]) {
            geoDetailedChartInstances[region].dispose()
            geoDetailedChartInstances[region] = null
          }
        }
        
        // 添加到清理函數列表
        cleanupFunctions.push(cleanup)
      } catch (error) {
        console.error(`渲染 ${region} 圖表時出錯:`, error)
      }
    })
  })
}

// 格式化區域表格數據
const formatRegionTableData = (region) => {
  if (!geoStats.value || !geoStats.value.detailed || !geoStats.value.detailed[region]) return []
  
  const regionData = geoStats.value.detailed[region]
  return regionData.cities.map(city => {
    const rowData = {
      city: city.name,
      total: city.data.reduce((sum, count) => sum + count, 0)
    }
    
    // 確保年份是字串類型
    geoStats.value.years.forEach((year, index) => {
      rowData[String(year)] = city.data[index]
    })
    
    return rowData
  })
}

// 處理標籤頁切換
const handleTabChange = (tab) => {
  // 使用 nextTick 確保 DOM 已更新
  nextTick(() => {
    // 重新調整所有圖表大小
    if (geoDetailedChartInstances) {
      // 獲取當前激活的區域
      const activeRegion = tab.props.label.replace('縣市分析', '')
      const chartDom = document.getElementById(`geoChart-${activeRegion}`)
      
      if (chartDom && geoDetailedChartInstances[activeRegion]) {
        // 調整圖表大小
        geoDetailedChartInstances[activeRegion].resize()
      }
      
      // 延遲調整所有圖表
      setTimeout(() => {
        Object.keys(geoDetailedChartInstances).forEach(region => {
          const chart = geoDetailedChartInstances[region]
          if (chart) {
            chart.resize()
          }
        })
      }, 300)
    }
  })
}

// 初始化
onMounted(() => {
  loadDatabaseTables()
  
  // 初始化時間並設置定時更新
  updateTime()
  const timeInterval = setInterval(updateTime, 1000)
  
  // 在組件銷毀時清理定時器
  cleanupFunctions.push(() => clearInterval(timeInterval))
})
</script>

<style scoped>
/* 頂部導航欄 */
.top-navbar {
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.navbar-left .system-title {
  color: #1976d2;
  font-size: 18px;
  margin: 0;
  margin-right: 30px;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: #666;
  text-decoration: none;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: #f5f5f5;
  color: #1976d2;
}

.nav-link.router-link-active {
  background-color: #1976d2;
  color: white;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.current-time, .user-info {
  color: #666;
  font-size: 14px;
}

.logout-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.logout-btn:hover {
  background-color: #f5f5f5;
}


.analysis-page {
  min-height: 100vh;
  background: white;
  padding: 0;
  margin: 0;
  width: 100%;
}

.main-content {
  width: 100%;
  margin: 0;
  padding: 20px;
  background: white;
  min-height: calc(100vh - 70px);
  box-shadow: none;
}

.data-source-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

/* 資料庫來源選擇 */
.database-source-section {
  margin-bottom: 20px;
}

.database-source-section h3 {
  margin: 0 0 8px 0;
  color: #2c5aa0;
  font-size: 18px;
  font-weight: 600;
}

.database-source-section p {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
}

.upload-hint {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed #ddd;
}

.upload-hint p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.upload-hint a {
  color: #2c5aa0;
  text-decoration: none;
  font-weight: 600;
}

.upload-hint a:hover {
  text-decoration: underline;
}

/* 自動選擇欄位提示 */
.auto-select-info {
  margin-top: 20px;
  padding: 16px;
  background: #f0f8ff;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.auto-select-info h4 {
  margin: 0 0 8px 0;
  color: #1976d2;
  font-size: 16px;
  font-weight: 600;
}

.auto-select-info p {
  margin: 0 0 12px 0;
  color: #555;
  font-size: 14px;
}

.auto-select-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.auto-select-item {
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e3f2fd;
  font-size: 14px;
  color: #333;
}

.auto-select-item strong {
  color: #1976d2;
}

.auto-select-note {
  margin: 0;
  font-size: 12px;
  color: #666;
  font-style: italic;
}

/* 圖表導出容器樣式 */
.chart-with-export {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.export-btn {
  align-self: center;
  margin-top: 10px;
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 導出對話框樣式 */
.export-options {
  padding: 20px;
}

.export-options h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 18px;
}

.export-options p {
  margin: 0 0 20px 0;
  color: #666;
}

.format-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.format-section {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.format-section h5 {
  margin: 0 0 12px 0;
  color: #409eff;
  font-size: 14px;
  font-weight: 600;
}

.format-section .el-button {
  margin-right: 8px;
  margin-bottom: 8px;
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

.chart-container {
  width: 100%;
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.chart-container canvas {
  width: 100% !important;
  max-height: 400px !important;
  aspect-ratio: 16/9;
}

/* 確保所有地區圖表容器寬度一致 */
#geoChart-北台灣,
#geoChart-中台灣,
#geoChart-南台灣,
#geoChart-東台灣 {
  width: 100% !important;
  height: 400px !important;
  max-width: 100% !important;
}

.region-data-table {
  margin-top: 30px;
  margin-bottom: 20px;
}

.region-data-table h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 18px;
}

.el-tabs {
  margin-top: 20px;
}

.el-tab-pane {
  padding: 15px;
}

/* 確保圖表有足夠的空間 */
:deep(.el-tabs__content) {
  min-height: 500px;
}

/* 改善表格樣式 */
:deep(.el-table) {
  margin-bottom: 20px;
}

:deep(.el-table__header) th {
  background-color: #f2f6fc;
  color: #606266;
  font-weight: bold;
}

:deep(.el-table__row td) {
  text-align: center;
}

:deep(.el-table__row td:first-child) {
  text-align: left;
  font-weight: bold;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
