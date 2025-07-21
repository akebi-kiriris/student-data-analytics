<template>
  <div class="app-container">
    <!-- 路由導航 -->
    <div class="app-header">
      <nav class="app-nav">
        <router-link to="/login" class="nav-item">登入</router-link>
        <router-link to="/dashboard" class="nav-item">主控台</router-link>
        <router-link to="/data-management" class="nav-item">數據管理</router-link>
        <router-link to="/analysis" class="nav-item">數據分析</router-link>
        <router-link to="/user-management" class="nav-item">用戶管理</router-link>
      </nav>
    </div>

    <!-- 路由視圖或原始內容 -->
    <router-view v-if="$route.name !== 'Home'" />
    
    <!-- 原始數據分析內容 -->
    <div v-else class="original-content">
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

    <el-divider>數據分析選項</el-divider>

    <!-- 分析區塊選擇 -->
    <div class="analysis-blocks">
      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'single-column' }"
        @click="setActiveBlock('single-column')"
      >
        <div class="block-header">
          <i class="el-icon-data-line"></i>
          <h3>單欄位統計分析</h3>
        </div>
        <p>選擇單一欄位進行統計分析，查看平均數、變異數等基本統計資訊</p>
      </div>

      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'multi-subject' }"
        @click="setActiveBlock('multi-subject')"
      >
        <div class="block-header">
          <i class="el-icon-s-data"></i>
          <h3>多科目分年平均分析</h3>
        </div>
        <p>比較多個科目在不同年份的平均分數變化趨勢</p>
      </div>

      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'yearly-admission' }"
        @click="setActiveBlock('yearly-admission')"
      >
        <div class="block-header">
          <i class="el-icon-user"></i>
          <h3>每年入學生數量分析</h3>
        </div>
        <p>統計並視覺化每年的入學生數量變化</p>
      </div>

      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'school-source' }"
        @click="setActiveBlock('school-source')"
      >
        <div class="block-header">
          <i class="el-icon-school"></i>
          <h3>入學生學校來源分析</h3>
        </div>
        <p>分析各年度入學生的高中來源學校類型分布（國立、私立、市立等）</p>
      </div>

      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'admission-method' }"
        @click="setActiveBlock('admission-method')"
      >
        <div class="block-header">
          <i class="el-icon-coordinate"></i>
          <h3>入學生入學管道分析</h3>
        </div>
        <p>分析各年度入學生的入學管道分布（申請入學、繁星推薦、自然組、社會組等）</p>
      </div>

      <div 
        class="analysis-block" 
        :class="{ active: activeBlock === 'geographic' }"
        @click="setActiveBlock('geographic')"
      >
        <div class="block-header">
          <i class="el-icon-map-location"></i>
          <h3>地理區域分析</h3>
        </div>
        <p>分析學生來源地理區域分布，按北、西、南、東台灣等區域統計</p>
      </div>
    </div>

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
        <el-button type="success" @click="getColumnStats" :disabled="!selectedColumn">計算統計</el-button>
        <el-button type="info" @click="showRawData" :disabled="!selectedColumn">顯示原始資料</el-button>
      </div>
    </div>

    <!-- 多科目分年平均分析區塊 -->
    <div v-if="activeBlock === 'multi-subject'" class="analysis-content">
      <el-divider>多科目分年平均分析</el-divider>
      <div class="form-group">
        <label>選擇科目：</label>
        <el-select
          v-model="selectedSubjects"
          multiple
          placeholder="請選擇科目"
          style="width: 400px"
        >
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
        <el-button type="success" @click="getMultiSubjectStats" :disabled="!selectedSubjects.length">開始分析</el-button>
      </div>
    </div>

    <!-- 每年入學生數量分析區塊 -->
    <div v-if="activeBlock === 'yearly-admission'" class="analysis-content">
      <el-divider>每年入學生數量分析</el-divider>
      <div class="form-group">
        <label>年份欄位：</label>
        <el-select v-model="admissionYearCol" placeholder="請選擇年份欄位" style="width: 300px">
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
        <el-button type="success" @click="getYearlyAdmissionStats" :disabled="!admissionYearCol">分析入學生數量</el-button>
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
      <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 13px; color: #666;">
        <strong>說明：</strong>系統會自動識別學校類型（國立、市立、縣立、私立、財團、國大轉、私大轉、科大轉、僑生、其他）
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
        <strong>北台灣：</strong>台北市、新北市、基隆市、宜蘟縣、桃園市、新竹市、新竹縣<br>
        <strong>中台灣：</strong>苗栗縣、台中市、彰化縣、南投縣、雲林縣<br>
        <strong>南台灣：</strong>嘉義市、嘉義縣、台南市、高雄市、屏東縣<br>
        <strong>東台灣：</strong>花蓮縣、台東縣<br>
        <strong>其他：</strong>澎湖縣、金門縣、連江縣、大陸台商子學校等其他地區
      </div>

      <!-- 地理區域分析圖表 -->
      <div v-if="geoStats" class="stats-card">
        <el-divider>地理區域分布統計</el-divider>
        <div class="stats-summary">
          <p><strong>分析期間：</strong>{{ geoStats.year_range }}</p>
          <p><strong>總人數：</strong>{{ geoStats.total_students }} 人</p>
          <p><strong>說明：</strong>圖表顯示各年度不同地區的入學人數分布，橫軸為年度，縱軸為人數</p>
        </div>
        <div id="geoChart" style="width: 100%; height: 400px;"></div>
        
        <el-divider>地區縣市人數詳細分析</el-divider>
        <div class="stats-summary">
          <p><strong>說明：</strong>以下圖表顯示各區域內不同縣市的入學人數分布，橫軸為年度，縱軸為人數</p>
        </div>
        
        <el-tabs type="border-card" @tab-click="handleTabChange">
          <el-tab-pane label="北台灣縣市分析">
            <div class="chart-container">
              <div id="geoChart-北台灣" style="width: 100%; height: 400px;"></div>
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
              <div id="geoChart-中台灣" style="width: 100%; height: 400px;"></div>
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
              <div id="geoChart-南台灣" style="width: 100%; height: 400px;"></div>
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
              <div id="geoChart-東台灣" style="width: 100%; height: 400px;"></div>
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

    <!-- 下方結果顯示區域 -->
    <div v-if="stats && stats.stats" class="results-panel">
      <h3>統計結果（{{ stats.column }}）</h3>
      <ul>
        <li>平均數：{{ stats.stats.mean?.toFixed(2) }}</li>
        <li>變異數：{{ stats.stats.std?.toFixed(2) }}</li>
        <li>最小值：{{ stats.stats.min?.toFixed(2) }}</li>
        <li>最大值：{{ stats.stats.max?.toFixed(2) }}</li>
        <li>有效筆數：{{ stats.stats.count }}</li>
        <li v-if="stats.stats.skipped && stats.stats.skipped > 0" style="color: #f56c6c;">略過無法計算的資料筆數：{{ stats.stats.skipped }}</li>
      </ul>
      <div style="max-width:1200px;margin:20px auto;">
        <canvas id="chart" style="width: 100%; height: 400px;"></canvas>
      </div>
      <div v-if="stats.stats && stats.stats.count > 0">
        <p>分析：</p>
        <ul>
          <li v-if="stats.stats.std === 0">所有數值都相同。</li>
          <li v-else-if="stats.stats.std < stats.stats.mean * 0.1">數值分布非常集中。</li>
          <li v-else-if="stats.stats.std > stats.stats.mean * 0.5">數值分布較為分散，可能有極端值。</li>
          <li v-else>數值分布適中。</li>
          <li v-if="stats.stats.max === stats.stats.min">最大值與最小值相同，資料無變化。</li>
        </ul>
      </div>

      <div v-if="stats.raw_data && stats.raw_data.length">
        <el-divider>原始資料</el-divider>
        <el-table
          :data="stats.raw_data.map((value, index) => ({ index: index + 1, value }))"
          style="width: 100%"
          :max-height="400"
          border
          stripe
        >
          <el-table-column
            prop="index"
            label="序號"
            width="100"
            fixed
          />
          <el-table-column
            prop="value"
            :label="stats.column"
          >
            <template #default="scope">
              {{ scope.row.value === null || scope.row.value === '' ? '-' : scope.row.value }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div v-if="multiStats">
      <h3>多科目分年平均統計</h3>
      <div style="max-width:1200px;margin:20px auto;">
        <canvas id="multiChart" style="width: 100%; height: 400px;"></canvas>
      </div>
      <div>
        <h4>原始數據</h4>
        <div class="pretty-table-wrapper">
          <table class="pretty-table">
            <thead>
              <tr>
                <th>學科</th>
                <th v-for="(year, i) in multiStats.years" :key="i">{{ year }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="subj in multiStats.subjects" :key="subj">
                <td>{{ subj }}</td>
                <td v-for="(avg, i) in multiStats.data[subj]" :key="i">{{ avg !== null ? avg.toFixed(2) : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 每年入學生數量分析結果 -->
    <div v-if="yearlyAdmissionStats" class="analysis-section">
      <h3>每年入學生數量統計</h3>
      <div class="chart-container">
        <canvas id="yearlyAdmissionChart" style="width: 100%; height: 400px;"></canvas>
      </div>
      <div class="statistics-summary">
        <h4>統計摘要</h4>
        <ul>
          <li>總學生數：{{ yearlyAdmissionStats.total_students }}</li>
          <li>年份範圍：{{ yearlyAdmissionStats.year_range }}</li>
          <li v-if="yearlyAdmissionStats.has_gender">
            最高入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.max(...yearlyAdmissionStats.total_counts))] }}
            （{{ Math.max(...yearlyAdmissionStats.total_counts) }}人）
          </li>
          <li v-if="yearlyAdmissionStats.has_gender">
            最低入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.min(...yearlyAdmissionStats.total_counts))] }}
            （{{ Math.min(...yearlyAdmissionStats.total_counts) }}人）
          </li>
          <li v-if="!yearlyAdmissionStats.has_gender">
            最高入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.max(...yearlyAdmissionStats.total_counts))] }}
            （{{ Math.max(...yearlyAdmissionStats.total_counts) }}人）
          </li>
          <li v-if="!yearlyAdmissionStats.has_gender">
            最低入學年份：{{ yearlyAdmissionStats.years[yearlyAdmissionStats.total_counts.indexOf(Math.min(...yearlyAdmissionStats.total_counts))] }}
            （{{ Math.min(...yearlyAdmissionStats.total_counts) }}人）
          </li>
        </ul>
      </div>
      <div>
        <h4>詳細數據</h4>
        <div class="pretty-table-wrapper">
          <table class="pretty-table">
            <thead>
              <tr>
                <th>年份</th>
                <th v-if="yearlyAdmissionStats.has_gender">女性人數</th>
                <th v-if="yearlyAdmissionStats.has_gender">男性人數</th>
                <th>總人數</th>
                <th v-if="yearlyAdmissionStats.has_gender">女性比例</th>
                <th v-if="yearlyAdmissionStats.has_gender">男性比例</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(year, i) in yearlyAdmissionStats.years" :key="i">
                <td>{{ year }}</td>
                <td v-if="yearlyAdmissionStats.has_gender">{{ yearlyAdmissionStats.female_counts[i] }}</td>
                <td v-if="yearlyAdmissionStats.has_gender">{{ yearlyAdmissionStats.male_counts[i] }}</td>
                <td>{{ yearlyAdmissionStats.total_counts[i] }}</td>
                <td v-if="yearlyAdmissionStats.has_gender">{{ yearlyAdmissionStats.female_percentages[i] }}%</td>
                <td v-if="yearlyAdmissionStats.has_gender">{{ yearlyAdmissionStats.male_percentages[i] }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 入學生學校來源分析結果 -->
    <div v-if="schoolSourceStats">
      <h3>入學生學校來源統計</h3>
      <div style="max-width:1000px;margin:20px 0;">
        <canvas id="schoolSourceChart" style="width: 100%; height: 400px;"></canvas>
      </div>
      <div>
        <h4>統計摘要</h4>
        <ul>
          <li>總學生數：{{ schoolSourceStats.total_students }}</li>
          <li>年份範圍：{{ schoolSourceStats.year_range }}</li>
          <li v-if="schoolSourceStats.summary.peak_year">
            最高入學年份：{{ schoolSourceStats.summary.peak_year }}（{{ schoolSourceStats.summary.peak_count }}人）
          </li>
          <li v-if="schoolSourceStats.summary.low_year">
            最低入學年份：{{ schoolSourceStats.summary.low_year }}（{{ schoolSourceStats.summary.low_count }}人）
          </li>
        </ul>
      </div>
      <div>
        <h4>各年度學校類型分布詳細數據</h4>
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
    </div>

    <!-- 入學生入學管道分析結果 -->
    <div v-if="admissionMethodStats">
      <h3>入學生入學管道統計</h3>
      <div style="max-width:1000px;margin:20px 0;">
        <canvas id="admissionMethodChart" style="width: 100%; height: 400px;"></canvas>
      </div>
      <div>
        <h4>統計摘要</h4>
        <ul>
          <li>總學生數：{{ admissionMethodStats.total_students }}</li>
          <li>年份範圍：{{ admissionMethodStats.year_range }}</li>
          <li v-if="admissionMethodStats.summary.peak_year">
            最高入學年份：{{ admissionMethodStats.summary.peak_year }}（{{ admissionMethodStats.summary.peak_count }}人）
          </li>
          <li v-if="admissionMethodStats.summary.low_year">
            最低入學年份：{{ admissionMethodStats.summary.low_year }}（{{ admissionMethodStats.summary.low_count }}人）
          </li>
        </ul>
      </div>
      <div>
        <h4>各年度入學管道分布詳細數據</h4>
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
    </div>

    </div> <!-- 結束 original-content div -->
  </div>
</template>

<style scoped>
/* 最外層容器 */
.app-container {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

/* 路由導航樣式 */
.app-header {
  background-color: #1976d2;
  padding: 10px 0;
  margin-bottom: 0;
}

.app-nav {
  display: flex;
  gap: 20px;
  padding: 0 20px;
}

.nav-item {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-item:hover,
.nav-item.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}

.original-content {
  padding: 20px;
}

/* 原始樣式 */
.pretty-table-wrapper {
  max-width: 800px;
  overflow-x: auto;
  margin-top: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 8px #0001;
}
.pretty-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
  background: #fff;
}
.pretty-table thead th {
  background: #f5f7fa;
  font-weight: bold;
  padding: 8px 12px;
  border-bottom: 2px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 1;
}
.pretty-table tbody td {
  padding: 7px 12px;
  border-bottom: 1px solid #f0f0f0;
  text-align: center;
}
.pretty-table tbody tr:nth-child(even) {
  background: #f9fafb;
}
.pretty-table tbody tr:hover {
  background: #e6f7ff;
  transition: background 0.2s;
}
.pretty-table th, .pretty-table td {
  min-width: 70px;
}

/* 分析區塊樣式 */
.analysis-blocks {
  display: grid;
  grid-template-columns: repeat(3, 1fr);  /* 固定一行三個 */
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

.block-header i {
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

.analysis-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.options-panel {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.analysis-content {
  padding: 20px;
  background: #fafcff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.results-panel {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
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

.analysis-section {
  padding: 20px;
  margin: 20px 0;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.statistics-summary {
  margin-top: 20px;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
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
.el-tabs__content {
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

/* 調整圖表樣式 */
.chartjs-size-monitor {
  position: absolute;
  width: 100%;
  height: 100%;
  left: 0;
  top: 0;
  pointer-events: none;
  visibility: hidden;
  z-index: -1;
}

.chartjs-size-monitor-expand {
  position: absolute;
  width: 100%;
  height: 100%;
  left: 0;
  top: 0;
  pointer-events: none;
  visibility: hidden;
  z-index: -1;
}

.chartjs-size-monitor-shrink {
  position: absolute;
  width: 200%;
  height: 200%;
  left: 0;
  top: 0;
  pointer-events: none;
  visibility: hidden;
  z-index: -1;
}
</style>


<script setup>
// 用於儲存所有需要清理的函數
const cleanupFunctions = []

const stats = ref(null)
const uploadUrl = 'http://localhost:5000/api/upload'
const fileList = ref([])
const selectedFile = ref(null)
const sheetList = ref([])
const selectedSheet = ref(null)
const columns = ref([])
const selectedColumn = ref(null)
const rawData = ref([])
const selectedSubjects = ref([])
const yearCol = ref('入學年度')
const multiStats = ref(null)
const activeBlock = ref('single-column')
const admissionYearCol = ref(null)
const genderCol = ref(null)
const yearlyAdmissionStats = ref(null)
const schoolSourceYearCol = ref(null)
const schoolNameCol = ref(null)
const schoolSourceStats = ref(null)
const admissionMethodYearCol = ref(null)
const admissionMethodCol = ref(null)
const admissionMethodStats = ref(null)
const geoYearCol = ref('')
const geoRegionCol = ref('')
const geoStats = ref(null)
const geoChartInstance = ref(null)
const geoDetailedChartInstances = ref({})
import { ref, onMounted, onUpdated, onBeforeUnmount, nextTick, watch } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'
import * as echarts from 'echarts'
let chartInstance = null
let multiChartInstance = null
let yearlyAdmissionChartInstance = null
let schoolSourceChartInstance = null
let admissionMethodChartInstance = null
// 當 stats 或 rawData 變動時，繪製圖表
const drawChart = () => {
  // 若沒有資料，主動銷毀 chart
  if (!rawData.value || !stats.value || !rawData.value.length) {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
    return
  }
  
  nextTick(() => {
    const ctx = document.getElementById('chart')
    if (!ctx) {
      if (chartInstance) {
        chartInstance.destroy()
        chartInstance = null
      }
      return
    }
    
    if (chartInstance) {
      chartInstance.destroy()
    }
    
    // 嘗試轉換數值並過濾無效值
    const validData = rawData.value.map((value, index) => ({
      value: Number(value),
      index: index + 1
    })).filter(item => !isNaN(item.value))
    
    // 如果沒有有效數據，不繪製圖表
    if (validData.length === 0) {
      return
    }
    
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: validData.map(item => item.index),
        datasets: [{
          label: stats.value.column,
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

// 分組長條圖
const drawMultiChart = () => {
  if (!multiStats.value || !multiStats.value.years || !multiStats.value.subjects) {
    if (multiChartInstance) {
      multiChartInstance.destroy()
      multiChartInstance = null
    }
    return
  }
  nextTick(() => {
    const ctx = document.getElementById('multiChart')
    if (!ctx) return
    if (multiChartInstance) multiChartInstance.destroy()
    // 準備 datasets: 每個學年一組
    const { years, subjects, data } = multiStats.value
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
      data: subjects.map(subj => data[subj][i]),
      backgroundColor: colors[i % colors.length]
    }))
    multiChartInstance = new Chart(ctx, {
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

// 繪製每年入學生數量圖表（複合圖表：堆疊長條圖 + 折線圖）
const drawYearlyAdmissionChart = () => {
  if (!yearlyAdmissionStats.value || !yearlyAdmissionStats.value.years) {
    if (yearlyAdmissionChartInstance) {
      yearlyAdmissionChartInstance.destroy()
      yearlyAdmissionChartInstance = null
    }
    return
  }
  
  nextTick(() => {
    const ctx = document.getElementById('yearlyAdmissionChart')
    if (!ctx) return
    if (yearlyAdmissionChartInstance) yearlyAdmissionChartInstance.destroy()
    
    const stats = yearlyAdmissionStats.value
    console.log('入學統計數據：', stats) // 用於調試
    
    const datasets = []
    
    // 檢查是否有性別區分
    if (stats.has_gender) {
      // 添加男生資料
      datasets.push({
        type: 'bar',
        label: '男生',
        data: stats.male_counts,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        barPercentage: 0.8
      })
      
      // 添加女生資料
      datasets.push({
        type: 'bar',
        label: '女生',
        data: stats.female_counts,
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
        data: stats.total_counts,
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
      data: stats.total_counts,
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
        labels: stats.years,
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

// 繪製學校來源分析圖表（堆疊長條圖）
const drawSchoolSourceChart = () => {
  if (!schoolSourceStats.value || !schoolSourceStats.value.years) {
    if (schoolSourceChartInstance) {
      schoolSourceChartInstance.destroy()
      schoolSourceChartInstance = null
    }
    return
  }
  nextTick(() => {
    const ctx = document.getElementById('schoolSourceChart')
    if (!ctx) return
    if (schoolSourceChartInstance) schoolSourceChartInstance.destroy()
    
    const stats = schoolSourceStats.value
    
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
    const datasets = stats.school_types.map(schoolType => ({
      label: schoolType,
      data: stats.data[schoolType].counts,
      backgroundColor: colorScheme[schoolType] || '#C4C4C4',
      borderColor: colorScheme[schoolType] || '#C4C4C4',
      borderWidth: 1,
      barPercentage: 0.5,  // 調整長條圖的相對寬度（更細）
      categoryPercentage: 0.9  // 調整分類之間的間距（稍微增加以平衡視覺效果）
    }))
    
    schoolSourceChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: stats.years,
        datasets
      },
      options: {
        responsive: true,
        plugins: {
          title: { 
            display: true, 
            text: '各年度入學生學校來源類型分布' 
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
                const count = stats.data[schoolType].counts[yearIndex]
                const percentage = stats.data[schoolType].percentages[yearIndex]
                const total = stats.year_totals[yearIndex]
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

// 繪製入學管道分析圖表（堆疊長條圖）
const drawAdmissionMethodChart = () => {
  if (!admissionMethodStats.value || !admissionMethodStats.value.years) {
    if (admissionMethodChartInstance) {
      admissionMethodChartInstance.destroy()
      admissionMethodChartInstance = null
    }
    return
  }
  nextTick(() => {
    const ctx = document.getElementById('admissionMethodChart')
    if (!ctx) return
    if (admissionMethodChartInstance) admissionMethodChartInstance.destroy()
    
    const stats = admissionMethodStats.value
    
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
    const datasets = stats.method_types.map(methodType => ({
      label: methodType,
      data: stats.data[methodType].counts,
      backgroundColor: colorScheme[methodType] || '#C4C4C4',
      borderColor: colorScheme[methodType] || '#C4C4C4',
      borderWidth: 1
    }))
    
    admissionMethodChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: stats.years,
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
                const count = stats.data[methodType].counts[yearIndex]
                const percentage = stats.data[methodType].percentages[yearIndex]
                const total = stats.year_totals[yearIndex]
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

// 渲染各區域縣市的圖表
const renderRegionalCityCharts = () => {
  if (!geoStats.value || !geoStats.value.detailed) {
    console.log('缺少地理區域縣市詳細資料')
    return
  }
  
  // 清理現有圖表實例
  if (geoDetailedChartInstances.value) {
    Object.values(geoDetailedChartInstances.value).forEach(chart => {
      if (chart) chart.dispose()
    })
  }
  
  // 初始化圖表對象
  geoDetailedChartInstances.value = {}
  
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

        // 查看縣市詳細圖的數據結構
        console.log(`${region}縣市圖的數據結構：`, {
          cities: regionData.cities,
          cityData: regionData.cities.map(city => ({
            name: city.name,
            data: city.data
          }))
        })

        // 初始化圖表容器尺寸
        const container = chartDom.parentElement
        const containerWidth = container.clientWidth || container.offsetWidth || 600
        chartDom.style.width = '100%'
        chartDom.style.height = '400px' // 確保有固定高度
        chartDom.style.maxWidth = '100%'

        // 初始化 ECharts 實例
        const chart = echarts.init(chartDom)
        geoDetailedChartInstances.value[region] = chart

        // 添加 resize 事件監聽器
        const resizeHandler = () => {
          if (chart && document.getElementById(`geoChart-${region}`)) {
            chart.resize()
          }
        }
        window.addEventListener('resize', resizeHandler)

        // 準備數據系列
        const cities = regionData.cities || []
        let displayCities = [...cities].sort((a, b) => a.name.localeCompare(b.name))

        // 顯示所有縣市，包括0人的縣市，以便完整分析
        displayCities = cities
        
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
              
              // 計算該年度總人數（包含0值）
              params.forEach(param => {
                if (param.data !== undefined && param.data !== null) {
                  yearTotal += param.data
                }
              })
              
              // 按數值大小排序顯示，包含0值的縣市
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
        geoDetailedChartInstances.value[region].setOption(option)
        
        // 等待 DOM 更新後再調整圖表大小
        nextTick(() => {
          if (geoDetailedChartInstances.value[region]) {
            const container = chartDom.parentElement
            if (!container) return

            const containerWidth = container.clientWidth || container.offsetWidth || 600
            
            // 設置容器寬度
            chartDom.style.width = `${containerWidth}px`
            chartDom.style.maxWidth = '100%'
            
            // 重新初始化圖表實例
            geoDetailedChartInstances.value[region].dispose()
            geoDetailedChartInstances.value[region] = echarts.init(chartDom)
            geoDetailedChartInstances.value[region].setOption(option)
            
            // 使用 requestAnimationFrame 確保在下一幀再次設置選項
            requestAnimationFrame(() => {
              if (geoDetailedChartInstances.value[region]) {
                geoDetailedChartInstances.value[region].setOption(option)
              }
            })
          }
        })
        
        // 添加響應式調整
        const handleResize = () => {
          if (geoDetailedChartInstances.value[region]) {
            // 使用 requestAnimationFrame 確保平滑的 resize
            requestAnimationFrame(() => {
              const container = chartDom.parentElement
              if (!container) return

              const containerWidth = container.clientWidth || container.offsetWidth || 600
              chartDom.style.width = `${containerWidth}px`
              
              // 重新設置圖表選項和大小
              geoDetailedChartInstances.value[region].setOption(option)
              geoDetailedChartInstances.value[region].resize()
            })
          }
        }
        
        // 使用節流函數包裝 resize 處理器
        let resizeTimeout
        const throttledResize = () => {
          if (resizeTimeout) {
            clearTimeout(resizeTimeout)
          }
          resizeTimeout = setTimeout(handleResize, 100)
        }
        
        window.addEventListener('resize', throttledResize)
        
        // 註冊清理函數
        const cleanup = () => {
          window.removeEventListener('resize', throttledResize)
          if (resizeTimeout) {
            clearTimeout(resizeTimeout)
          }
          if (geoDetailedChartInstances.value[region]) {
            geoDetailedChartInstances.value[region].dispose()
            geoDetailedChartInstances.value[region] = null
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

// 設置當前分析區塊
const setActiveBlock = (blockName) => {
  activeBlock.value = blockName
  // 切換區塊時清除之前的結果
  stats.value = null
  rawData.value = []
  multiStats.value = null
  yearlyAdmissionStats.value = null
  schoolSourceStats.value = null
  admissionMethodStats.value = null
  geoStats.value = null

  // 根據區塊類型自動選擇相關欄位
  if (columns.value && columns.value.length > 0) {
    if (blockName === 'geographic') {
      // 自動選擇年度欄位
      const yearPattern = /(學年度|年度|年|屆)/
      const yearCol = columns.value.find(col => yearPattern.test(col))
      if (yearCol) {
        geoYearCol.value = yearCol
      }
      
      // 自動選擇地區欄位
      const regionPattern = /(地區|地理區域|區域|縣市|城市)/
      const regionCol = columns.value.find(col => regionPattern.test(col))
      if (regionCol) {
        geoRegionCol.value = regionCol
      }
    }
  }
}

// 學校來源分析
const getSchoolSourceStats = async () => {
  if (!selectedFile.value || !selectedSheet.value || !schoolSourceYearCol.value || !schoolNameCol.value) return
  try {
    const res = await axios.post('http://localhost:5000/api/school_source_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      year_col: schoolSourceYearCol.value,
      school_col: schoolNameCol.value
    })
    schoolSourceStats.value = res.data
    drawSchoolSourceChart()
  } catch (err) {
    schoolSourceStats.value = null
    alert('❌ 學校來源分析失敗')
    console.error(err)
  }
}

// 入學管道分析
const getAdmissionMethodStats = async () => {
  if (!selectedFile.value || !selectedSheet.value || !admissionMethodYearCol.value || !admissionMethodCol.value) return
  try {
    const res = await axios.post('http://localhost:5000/api/admission_method_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      year_col: admissionMethodYearCol.value,
      method_col: admissionMethodCol.value
    })
    admissionMethodStats.value = res.data
    drawAdmissionMethodChart()
  } catch (err) {
    admissionMethodStats.value = null
    alert('❌ 入學管道分析失敗')
    console.error(err)
  }
}

// 每年入學生數量分析
const getYearlyAdmissionStats = async () => {
  if (!selectedFile.value || !selectedSheet.value || !admissionYearCol.value) return
  try {
    const res = await axios.post('http://localhost:5000/api/yearly_admission_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      year_col: admissionYearCol.value,
      gender_col: genderCol.value
    })
    yearlyAdmissionStats.value = res.data
    drawYearlyAdmissionChart()
  } catch (err) {
    yearlyAdmissionStats.value = null
    alert('❌ 每年入學生數量分析失敗')
    console.error(err)
  }
}

// 地理區域分析
const getGeographicStats = async () => {
  try {
    const response = await axios.post('http://localhost:5000/api/geographic_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      year_col: geoYearCol.value,
      region_col: geoRegionCol.value,
      get_city_details: true  // 請求詳細的縣市資料
    })
    
    geoStats.value = response.data
    nextTick(() => {
      renderGeoChart()
      renderRegionalCityCharts() // 渲染各區域縣市的圖表
    })
  } catch (error) {
    console.error('地理區域分析失敗:', error)
    ElMessage.error(error.response?.data?.error || '獲取地理區域統計時發生錯誤')
  }
}

// 渲染地理區域圖表
const renderGeoChart = () => {
  if (!geoStats.value) return

  // 查看第一張圖的數據結構
  console.log('第一張圖（各地區）的數據結構：', {
    regions: geoStats.value.regions,
    data: geoStats.value.data,
    years: geoStats.value.years
  })
    
    // 查看第一張圖的數據結構
    console.log('第一張圖（各地區）的數據結構：', {
      regions: geoStats.value.regions,
      data: geoStats.value.data,
      years: geoStats.value.years
    })
  
  const chartDom = document.getElementById('geoChart')
  if (!chartDom) return
  
  // 如果圖表實例已存在，先銷毀
  if (geoChartInstance.value) {
    geoChartInstance.value.dispose()
  }
  
  geoChartInstance.value = echarts.init(chartDom)
  
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

  geoChartInstance.value.setOption(option)
  
  // 響應視窗大小變化
  window.addEventListener('resize', () => {
    if (geoChartInstance.value) {
      geoChartInstance.value.resize()
    }
  })
}

// 顯示原始資料
const showRawData = async () => {
  if (!selectedFile.value || !selectedSheet.value || !selectedColumn.value) return
  try {
    const res = await axios.get(`http://localhost:5000/api/data/${encodeURIComponent(selectedFile.value)}?sheet=${encodeURIComponent(selectedSheet.value)}`)
    if (res.data && res.data.data) {
      if (!res.data.columns.includes(selectedColumn.value)) {
        rawData.value = []
      } else {
        rawData.value = res.data.data.map(row => row[selectedColumn.value])
      }
    } else {
      rawData.value = []
    }
  } catch (err) {
    rawData.value = []
    alert('❌ 取得原始資料失敗')
    console.error(err)
  }
}

// 上傳成功後的處理
const handleUploadSuccess = (response) => {
  if (response.success) {
    alert('上傳成功！')
    fetchFileList()
  } else {
    alert('❌ 上傳失敗：' + response.error)
  }
}

// 上傳前的驗證
const beforeUpload = (file) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isExcel) {
    alert('請上傳 Excel 檔案！')
    return false
  }
  if (!isLt100M) {
    alert('檔案大小不能超過 100MB！')
    return false
  }
  return true
}

// 載入檔案清單
const fetchFileList = async () => {
  try {
    const res = await axios.get('http://localhost:5000/api/files')
    fileList.value = res.data.files || []
  } catch (err) {
    fileList.value = []
    console.error(err)
  }
}

// 當選擇檔案時，請求工作表清單
const loadFileSheets = async () => {
  
  sheetList.value = []
  selectedSheet.value = null
  columns.value = []
  selectedColumn.value = null
  stats.value = null
  rawData.value = []
  try {
    const res = await axios.post('http://localhost:5000/api/sheets', {
      filename: selectedFile.value
    })
    sheetList.value = res.data.sheets || []
  } catch (err) {
    sheetList.value = []
    alert('❌ 讀取工作表失敗')
    console.error(err)
  }
}

// 當選擇工作表時，請求欄位名稱
const loadFileColumns = async () => {
  if (!selectedFile.value || !selectedSheet.value) return
  columns.value = []
  selectedColumn.value = null
  stats.value = null
  rawData.value = []
  try {
    const res = await axios.post('http://localhost:5000/api/read_columns', {
      filename: selectedFile.value,
      sheet: selectedSheet.value
    })
    columns.value = res.data.columns
    
    // 自動帶入「入學年度」或第一個欄位
    if (columns.value.includes('入學年度')) {
      yearCol.value = '入學年度'
      admissionYearCol.value = '入學年度'
      schoolSourceYearCol.value = '入學年度'
      admissionMethodYearCol.value = '入學年度'
       } else if (columns.value.length > 0) {
      yearCol.value = columns.value[0]
      admissionYearCol.value = columns.value[0]
      schoolSourceYearCol.value = columns.value[0]
      admissionMethodYearCol.value = columns.value[0]
    } else {
      yearCol.value = ''
      admissionYearCol.value = null
      schoolSourceYearCol.value = null
      admissionMethodYearCol.value = null
    }
    
    // 自動偵測性別欄位
    const genderCandidates = ['性別', '性别', 'gender', 'sex', '男女']
    const foundGenderCol = columns.value.find(col => 
      genderCandidates.some(candidate => 
        col.toLowerCase().includes(candidate.toLowerCase())
      )
    )
    if (foundGenderCol) {
      genderCol.value = foundGenderCol
    } else {
      genderCol.value = null
    }
    
    // 自動偵測學校名稱欄位
    const schoolCandidates = ['學校', '高中', '國中', '學校名稱', '畢業學校', '來源學校', '原就讀學校', 'school']
    const foundSchoolCol = columns.value.find(col => 
      schoolCandidates.some(candidate => 
        col.toLowerCase().includes(candidate.toLowerCase())
      )
    )
    if (foundSchoolCol) {
      schoolNameCol.value = foundSchoolCol
    } else {
      schoolNameCol.value = null
    }
    
    // 自動偵測入學管道欄位
    const methodCandidates = ['入學管道', '管道', '入學方式', '方式', 'method', 'admission']
    const foundMethodCol = columns.value.find(col => 
      methodCandidates.some(candidate => 
        col.toLowerCase().includes(candidate.toLowerCase())
      )
    )
    if (foundMethodCol) {
      admissionMethodCol.value = foundMethodCol
    } else {
      admissionMethodCol.value = null
    }
    
  } catch (err) {
    columns.value = []
    alert('❌ 讀取欄位失敗')
    console.error(err)
  }
}

// 查詢欄位統計
const getColumnStats = async () => {
  if (!selectedFile.value || !selectedSheet.value || !selectedColumn.value) return
  try {
    const res = await axios.post('http://localhost:5000/api/column_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      column: selectedColumn.value
    })
    stats.value = res.data
    if (res.data.raw_data) {
      rawData.value = res.data.raw_data
    }
    nextTick(() => {
      drawChart()
    })
  } catch (err) {
    stats.value = null
    rawData.value = []
    alert('❌ 統計失敗，請確認欄位為數值型態')
    console.error(err)
  }
}

// 多科目分年平均查詢
const getMultiSubjectStats = async () => {
  if (!selectedFile.value || !selectedSheet.value || !selectedSubjects.value.length) return
  try {
    const res = await axios.post('http://localhost:5000/api/multi_subject_stats', {
      filename: selectedFile.value,
      sheet: selectedSheet.value,
      subjects: selectedSubjects.value,
      year_col: yearCol.value
    })
    multiStats.value = res.data
    drawMultiChart()
  } catch (err) {
    multiStats.value = null
    alert('❌ 多科目分年平均查詢失敗')
    console.error(err)
  }
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

// 頁面初始化時載入檔案清單
onMounted(fetchFileList)
onUpdated(drawChart)
watch([stats, rawData], drawChart)

// 組件卸載時清理資源
onBeforeUnmount(() => {
  // 清理圖表實例
  if (geoDetailedChartInstances.value) {
    Object.values(geoDetailedChartInstances.value).forEach(chart => {
      if (chart) {
        chart.dispose()
      }
    })
  }
  // 清理事件監聽器
  ['北台灣', '中台灣', '南台灣', '東台灣'].forEach(region => {
    const resizeHandler = chart => () => chart.resize()
    if (geoDetailedChartInstances.value[region]) {
      window.removeEventListener('resize', resizeHandler(geoDetailedChartInstances.value[region]))
    }
  })
})

// 處理標籤頁切換
const handleTabChange = (tab) => {
  // 使用 nextTick 確保 DOM 已更新
  nextTick(() => {
    // 重新調整所有圖表大小
    if (geoDetailedChartInstances.value) {
      // 獲取當前激活的區域
      const activeRegion = tab.props.label.replace('縣市分析', '')
      const chartDom = document.getElementById(`geoChart-${activeRegion}`)
      
      if (chartDom && geoDetailedChartInstances.value[activeRegion]) {
        // 強制設置容器寬度
        const containerWidth = chartDom.parentElement.clientWidth || 600
        chartDom.style.width = containerWidth + 'px'
        
        // 直接修改 canvas 元素的寬度
        const canvasEl = chartDom.querySelector('canvas')
        if (canvasEl) {
          canvasEl.style.width = containerWidth + 'px'
          console.log(`設置 ${activeRegion} canvas 寬度: ${containerWidth}px`)
        }
        
        // 調整圖表大小
        geoDetailedChartInstances.value[activeRegion].resize({
          width: containerWidth,
          height: 400
        })
      }
      
      // 延遲調整所有圖表
      setTimeout(() => {
        Object.keys(geoDetailedChartInstances.value).forEach(region => {
          const chart = geoDetailedChartInstances.value[region]
          const dom = document.getElementById(`geoChart-${region}`)
          if (chart && dom) {
            const containerWidth = dom.parentElement.clientWidth || 600
            dom.style.width = containerWidth + 'px'
            
            const canvasEl = dom.querySelector('canvas')
            if (canvasEl) {
              canvasEl.style.width = containerWidth + 'px'
            }
            
            chart.resize({
              width: containerWidth,
              height: 400
            })
          }
        })
      }, 300)
    }
  })
}
</script>
