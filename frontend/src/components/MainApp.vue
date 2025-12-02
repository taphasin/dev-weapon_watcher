<template>
  <div class="main-app">
    <!-- Navigation Header -->
    <div class="nav-header">
      <div class="nav-left">
        <h2 class="app-title">🛡️ Weapon Detection System</h2>
        <div class="nav-tabs">
          <button @click="activeTab = 'stream'" :class="{ active: activeTab === 'stream' }" class="nav-tab">
            📹 Live Stream
          </button>
          <button @click="activeTab = 'logs'" :class="{ active: activeTab === 'logs' }" class="nav-tab">
            📋 Detection Logs
          </button>
          <button @click="activeTab = 'dashboard'" :class="{ active: activeTab === 'dashboard' }" class="nav-tab">
            📊 Dashboard
          </button>
          <button @click="activeTab = 'profile'" :class="{ active: activeTab === 'profile' }" class="nav-tab">
            👤 Profile
          </button>
        </div>
      </div>
      <div class="user-info">
        <span class="username-display">{{ userData.fullName || userData.username }}</span>
        <span class="user-role">{{ userData.role }}</span>
        <button @click="$emit('logout')" class="logout-btn">Logout</button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="content-area">
      <StreamTab v-if="activeTab === 'stream'" :token="token" />
      <LogsTab v-if="activeTab === 'logs'" :token="token" />
      <DashboardTab v-if="activeTab === 'dashboard'" :token="token" />
      <ProfileTab v-if="activeTab === 'profile'" :token="token" :user-data="userData" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import StreamTab from '../tabs/StreamTab.vue'
import LogsTab from '../tabs/LogsTab.vue'
import DashboardTab from '../tabs/DashboardTab.vue'
import ProfileTab from '../tabs/ProfileTab.vue'

const props = defineProps({
  token: String,
  userData: Object
})

defineEmits(['logout'])

const activeTab = ref('stream')
</script>

<style scoped>
.main-app {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 25px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 30px;
}

.app-title {
  font-size: 1.3rem;
  color: #2c3e50;
  font-weight: 600;
}

.nav-tabs {
  display: flex;
  gap: 5px;
}

.nav-tab {
  padding: 10px 18px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  color: #7f8c8d;
  transition: all 0.3s ease;
}

.nav-tab.active {
  background: #4a90e2;
  color: white;
}

.nav-tab:hover:not(.active) {
  background: #ecf0f1;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username-display {
  font-weight: 600;
  color: #2c3e50;
}

.user-role {
  padding: 4px 12px;
  background: #e8f4fd;
  color: #3498db;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: capitalize;
}

.logout-btn {
  padding: 8px 16px;
  background-color: #95a5a6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.logout-btn:hover {
  background-color: #7f8c8d;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

@media (max-width: 1024px) {
  .nav-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .nav-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}

@media (max-width: 768px) {
  .content-area {
    padding: 15px;
  }
  
  .nav-tabs {
    flex-wrap: wrap;
  }
  
  .nav-tab {
    font-size: 0.85rem;
    padding: 8px 12px;
  }
  
  .app-title {
    font-size: 1.1rem;
  }
}
</style>