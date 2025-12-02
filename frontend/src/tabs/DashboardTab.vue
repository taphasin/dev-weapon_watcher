<template>
  <div class="dashboard-tab">
    <div class="dashboard-header">
      <h3>📊 Detection Analytics</h3>
      <div class="dashboard-filters">
        <select v-model="filterCamera" @change="loadDashboard" class="filter-select">
          <option :value="null">All Cameras</option>
          <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
            {{ camera.camera_name }}
          </option>
        </select>
        
        <select v-model="filterDays" @change="loadDashboard" class="date-select">
          <option value="1">1 day</option>
          <option value="7">7 days</option>
          <option value="30">30 days</option>
          <option value="90">90 days</option>
        </select>
      </div>
    </div>

    <div v-if="isLoading" class="loading-state">
      Loading analytics...
    </div>

    <div v-else class="dashboard-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <h4>Total Detections</h4>
          <div class="card-value">{{ totalDetections }}</div>
        </div>
        <div class="summary-card">
          <h4>Most Detected</h4>
          <div class="card-value">{{ mostDetectedWeapon }}</div>
        </div>
        <div class="summary-card">
          <h4>Avg Confidence</h4>
          <div class="card-value">{{ avgConfidence }}%</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-section">
        <div class="chart-container">
          <h4>Detection by Weapon Type</h4>
          <div v-if="weaponTotals.length === 0" class="no-data-chart">
            No data available
          </div>
          <div v-else class="weapon-chart">
            <div v-for="weapon in weaponTotals" :key="weapon.weapon_type" class="weapon-bar">
              <div class="weapon-label">{{ formatWeaponName(weapon.weapon_type) }}</div>
              <div class="bar-container">
                <div class="bar" :style="{ width: (weapon.total / maxDetections) * 100 + '%' }"></div>
                <span class="bar-value">{{ weapon.total }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-container">
          <h4>Daily Timeline</h4>
          <div v-if="dailyTimeline.length === 0" class="no-data-chart">
            No data available
          </div>
          <div v-else class="timeline-chart">
            <div v-for="day in dailyTimeline" :key="day.date" class="timeline-day">
              <div class="day-label">{{ formatDate(day.date) }}</div>
              <div class="day-detections">
                <div v-for="(weapon, index) in day.weapons" :key="index" 
                     class="weapon-dot" :class="weapon.type"
                     :title="`${weapon.type}: ${weapon.count}`"></div>
                <span class="day-total">{{ day.total }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  token: String
})

const cameras = ref([])
const dashboardData = ref(null)
const filterCamera = ref(null)
const filterDays = ref(7)
const isLoading = ref(false)

const totalDetections = computed(() => {
  if (!dashboardData.value) return 0
  return dashboardData.value.weapon_totals.reduce((sum, weapon) => sum + weapon.total, 0)
})

const mostDetectedWeapon = computed(() => {
  if (!dashboardData.value || dashboardData.value.weapon_totals.length === 0) return 'None'
  const top = dashboardData.value.weapon_totals[0]
  return formatWeaponName(top.weapon_type)
})

const avgConfidence = computed(() => {
  if (!dashboardData.value || dashboardData.value.weapon_totals.length === 0) return 0
  const avg = dashboardData.value.weapon_totals.reduce((sum, w) => 
    sum + (w.avg_conf || 0), 0) / dashboardData.value.weapon_totals.length
  return Math.round(avg * 100)
})

const weaponTotals = computed(() => {
  return dashboardData.value ? dashboardData.value.weapon_totals : []
})

const maxDetections = computed(() => {
  if (!weaponTotals.value.length) return 1
  return Math.max(...weaponTotals.value.map(w => w.total))
})

const dailyTimeline = computed(() => {
  if (!dashboardData.value) return []
  
  const timeline = {}
  dashboardData.value.daily_summary.forEach(item => {
    if (!timeline[item.detection_date]) {
      timeline[item.detection_date] = {
        date: item.detection_date,
        weapons: [],
        total: 0
      }
    }
    timeline[item.detection_date].weapons.push({
      type: item.weapon_type,
      count: item.total_detections
    })
    timeline[item.detection_date].total += item.total_detections
  })
  
  return Object.values(timeline).sort((a, b) => new Date(b.date) - new Date(a.date))
})

onMounted(async () => {
  await loadCameras()
  await loadDashboard()
  
  // Auto-refresh every 30 seconds
  setInterval(loadDashboard, 30000)
})

async function loadCameras() {
  try {
    const res = await fetch('/api/cameras')
    if (res.ok) {
      const data = await res.json()
      cameras.value = data.cameras
    }
  } catch (error) {
    console.error('Could not load cameras:', error)
  }
}

async function loadDashboard() {
  isLoading.value = true
  
  try {
    let url = `/api/dashboard-data?days=${filterDays.value}`
    if (filterCamera.value) url += `&camera_id=${filterCamera.value}`
    
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    
    if (res.ok) {
      const data = await res.json()
      dashboardData.value = data
    }
  } catch (error) {
    console.error('Could not load dashboard:', error)
  }
  
  isLoading.value = false
}

function formatWeaponName(weaponType) {
  const names = {
    'knife': 'Knife',
    'pistol': 'Pistol',
    'heavy_weapon': 'Heavy Weapon'
  }
  return names[weaponType] || weaponType
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString()
  } catch {
    return dateString
  }
}
</script>

<style scoped>
.dashboard-tab {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
  gap: 15px;
}

.dashboard-header h3 {
  color: #2c3e50;
}

.dashboard-filters {
  display: flex;
  gap: 10px;
}

.filter-select,
.date-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.loading-state {
  background: white;
  padding: 60px;
  border-radius: 12px;
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.summary-card {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.summary-card h4 {
  color: #7f8c8d;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
}

.chart-container {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container h4 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.no-data-chart {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
  font-style: italic;
}

.weapon-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weapon-bar {
  display: flex;
  align-items: center;
  gap: 15px;
}

.weapon-label {
  min-width: 100px;
  font-weight: 500;
  color: #2c3e50;
}

.bar-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar {
  height: 20px;
  background: linear-gradient(90deg, #4a90e2, #357ab7);
  border-radius: 10px;
  min-width: 4px;
  transition: width 0.3s ease;
}

.bar-value {
  font-weight: 600;
  color: #2c3e50;
}

.timeline-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline-day {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #ecf0f1;
}

.day-label {
  min-width: 80px;
  font-weight: 500;
  color: #2c3e50;
}

.day-detections {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.weapon-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.weapon-dot:hover {
  transform: scale(1.5);
}

.weapon-dot.knife { background: #e74c3c; }
.weapon-dot.pistol { background: #f39c12; }
.weapon-dot.heavy_weapon { background: #8e44ad; }

.day-total {
  font-weight: 600;
  color: #2c3e50;
  margin-left: auto;
}

@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .dashboard-filters {
    flex-direction: column;
    width: 100%;
  }
  
  .filter-select,
  .date-select {
    width: 100%;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>