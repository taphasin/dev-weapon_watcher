<template>
  <div class="public-view">
    <h1 class="public-title">🛡️ Security Monitoring System</h1>
    <p class="public-subtitle">Real-time Weapon Detection Status</p>

    <!-- Camera Status Grid -->
    <div class="public-cameras">
      <h2>📹 Camera Status</h2>
      <div class="camera-grid">
        <div v-for="camera in cameras" :key="camera.id" class="camera-card">
          <div class="camera-header">
            <h3>{{ camera.camera_name }}</h3>
            <span :class="['status-badge', camera.is_active ? 'active' : 'inactive']">
              {{ camera.is_active ? '🟢 Active' : '🔴 Offline' }}
            </span>
          </div>
          <p class="camera-location">📍 {{ camera.location }}</p>
          <div class="camera-stats">
            <div class="stat">
              <span class="stat-label">Today:</span>
              <span class="stat-value">{{ camera.detections_today || 0 }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Last:</span>
              <span class="stat-value">{{ formatTime(camera.last_detection) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Current Detections -->
    <div class="public-detections">
      <h2>⚠️ Recent Detections (Last Hour)</h2>
      <div v-if="detections.length === 0" class="no-detections-public">
        ✅ No weapons detected in the last hour
      </div>
      <div v-else class="detection-cards">
        <div v-for="(det, index) in detections" :key="index" class="detection-card-public">
          <div class="detection-icon">🚨</div>
          <div class="detection-details">
            <h4>{{ formatWeaponName(det.weapon_type) }}</h4>
            <p class="detection-location">📍 {{ det.location }}</p>
            <p class="detection-camera">📹 {{ det.camera_name }}</p>
            <p class="detection-time">🕐 {{ formatTime(det.detection_time) }}</p>
            <p class="detection-count">Count: {{ det.detection_count }}x</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const cameras = ref([])
const detections = ref([])

onMounted(() => {
  loadPublicData()
  // Refresh every 30 seconds
  setInterval(loadPublicData, 30000)
})

async function loadPublicData() {
  try {
    const [camerasRes, detectionsRes] = await Promise.all([
      fetch('/api/public/camera-status'),
      fetch('/api/public/current-detections?minutes=60')
    ])
    
    if (camerasRes.ok) {
      const data = await camerasRes.json()
      cameras.value = data.cameras
    }
    
    if (detectionsRes.ok) {
      const data = await detectionsRes.json()
      detections.value = data.detections
    }
  } catch (error) {
    console.error('Could not load public data:', error)
  }
}

function formatWeaponName(weaponType) {
  const names = {
    'knife': 'Knife',
    'pistol': 'Pistol',
    'heavy_weapon': 'Heavy Weapon'
  }
  return names[weaponType] || weaponType
}

function formatTime(timeString) {
  if (!timeString) return 'N/A'
  try {
    return new Date(timeString).toLocaleTimeString()
  } catch {
    return 'N/A'
  }
}
</script>

<style scoped>
.public-view {
  padding: 100px 40px 40px 40px;
  overflow-y: auto;
  height: 100%;
}

.public-title {
  font-size: 3rem;
  color: #2c3e50;
  text-align: center;
  margin-bottom: 10px;
}

.public-subtitle {
  font-size: 1.2rem;
  color: #7f8c8d;
  text-align: center;
  margin-bottom: 40px;
}

.public-cameras,
.public-detections {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.public-cameras h2,
.public-detections h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.camera-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  border-left: 4px solid #3498db;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.camera-header h3 {
  color: #2c3e50;
  font-size: 1.1rem;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.camera-location {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 15px;
}

.camera-stats {
  display: flex;
  gap: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  color: #7f8c8d;
  font-size: 0.8rem;
}

.stat-value {
  color: #2c3e50;
  font-weight: 600;
  font-size: 1.1rem;
}

.no-detections-public {
  text-align: center;
  padding: 40px;
  color: #27ae60;
  font-size: 1.2rem;
  font-weight: 600;
}

.detection-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.detection-card-public {
  display: flex;
  gap: 15px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 20px;
  border-radius: 10px;
}

.detection-icon {
  font-size: 2rem;
}

.detection-details h4 {
  color: #e74c3c;
  margin-bottom: 8px;
}

.detection-details p {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 4px 0;
}

.detection-count {
  color: #f39c12 !important;
  font-weight: 600;
}

@media (max-width: 768px) {
  .public-view {
    padding: 80px 20px 20px 20px;
  }
  
  .public-title {
    font-size: 2rem;
  }
  
  .camera-grid {
    grid-template-columns: 1fr;
  }
  
  .detection-cards {
    grid-template-columns: 1fr;
  }
}
</style>