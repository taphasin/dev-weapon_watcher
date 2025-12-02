<template>
  <div class="logs-tab">
    <div class="logs-header">
      <h2>📋 Detection Logs</h2>
      <div class="logs-filters">
        <select v-model="filterCamera" @change="loadLogs" class="filter-select">
          <option :value="null">All Cameras</option>
          <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
            {{ camera.camera_name }}
          </option>
        </select>
        
        <select v-model="filterWeapon" @change="loadLogs" class="filter-select">
          <option :value="null">All Weapons</option>
          <option value="knife">Knife</option>
          <option value="pistol">Pistol</option>
          <option value="heavy_weapon">Heavy Weapon</option>
        </select>
        
        <select v-model="filterDays" @change="loadLogs" class="filter-select">
          <option :value="1">Last 24 hours</option>
          <option :value="7">Last 7 days</option>
          <option :value="30">Last 30 days</option>
          <option :value="90">Last 90 days</option>
        </select>
        
        <button @click="loadLogs" class="refresh-btn" title="Refresh">
          🔄 Refresh
        </button>
      </div>
    </div>

    <div class="logs-table-container">
      <table class="logs-table">
        <thead>
          <tr>
            <th>Date & Time</th>
            <th>Camera</th>
            <th>Location</th>
            <th>Weapon Type</th>
            <th>Confidence</th>
            <th>Detected By</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="isLoading">
            <td colspan="6" class="loading-cell">Loading logs...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="6" class="no-data">No detection logs found</td>
          </tr>
          <tr v-else v-for="log in logs" :key="log.id">
            <td>{{ formatDateTime(log.detection_time) }}</td>
            <td><strong>{{ log.camera_name }}</strong></td>
            <td>{{ log.location }}</td>
            <td>
              <span :class="['weapon-badge', log.weapon_type]">
                {{ formatWeaponName(log.weapon_type) }}
              </span>
            </td>
            <td>
              <span class="confidence-badge">
                {{ Math.round(log.confidence_score * 100) }}%
              </span>
            </td>
            <td>{{ log.username }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="logs-footer">
      <span class="total-count">Total: {{ logs.length }} records</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  token: String
})

const cameras = ref([])
const logs = ref([])
const filterCamera = ref(null)
const filterWeapon = ref(null)
const filterDays = ref(7)
const isLoading = ref(false)

onMounted(async () => {
  await loadCameras()
  await loadLogs()
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

async function loadLogs() {
  isLoading.value = true
  
  try {
    let url = `/api/detection-logs?days=${filterDays.value}&limit=100`
    if (filterCamera.value) url += `&camera_id=${filterCamera.value}`
    if (filterWeapon.value) url += `&weapon_type=${filterWeapon.value}`
    
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    
    if (res.ok) {
      const data = await res.json()
      logs.value = data.logs
    }
  } catch (error) {
    console.error('Could not load logs:', error)
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

function formatDateTime(dateTimeString) {
  if (!dateTimeString) return 'N/A'
  try {
    const date = new Date(dateTimeString)
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`
  } catch {
    return dateTimeString
  }
}
</script>

<style scoped>
.logs-tab {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.logs-header h2 {
  color: #2c3e50;
}

.logs-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 0.95rem;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #4a90e2;
}

.refresh-btn {
  padding: 8px 16px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease;
}

.refresh-btn:hover {
  background: #357ab7;
}

.logs-table-container {
  overflow-x: auto;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
}

.logs-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e0e0e0;
}

.logs-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
  color: #2c3e50;
}

.logs-table tr:hover {
  background: #f8f9fa;
}

.loading-cell,
.no-data {
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
  padding: 40px !important;
}

.weapon-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-block;
}

.weapon-badge.knife {
  background: #ffebee;
  color: #e74c3c;
}

.weapon-badge.pistol {
  background: #fff3e0;
  color: #f39c12;
}

.weapon-badge.heavy_weapon {
  background: #f3e5f5;
  color: #9b59b6;
}

.confidence-badge {
  padding: 4px 12px;
  background: #e8f4fd;
  color: #3498db;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-block;
}

.logs-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e9ecef;
  text-align: right;
}

.total-count {
  color: #7f8c8d;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .logs-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .logs-filters {
    flex-direction: column;
    width: 100%;
  }
  
  .filter-select,
  .refresh-btn {
    width: 100%;
  }
  
  .logs-table {
    font-size: 0.85rem;
  }
  
  .logs-table th,
  .logs-table td {
    padding: 8px;
  }
}
</style>