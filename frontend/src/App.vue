<template>
  <div id="app">
    <!-- View Toggle (Public/Staff) -->
    <div v-if="!token" class="view-toggle">
      <button 
        @click="currentView = 'public'" 
        :class="{ active: currentView === 'public' }"
        class="view-toggle-btn"
      >
        👁️ Public View
      </button>
      <button 
        @click="currentView = 'auth'" 
        :class="{ active: currentView === 'auth' }"
        class="view-toggle-btn"
      >
        🔒 Staff Login
      </button>
    </div>

    <!-- Public View Component -->
    <PublicView v-if="!token && currentView === 'public'" />

    <!-- Auth View Component (Login/Register) -->
    <AuthView 
      v-if="!token && currentView === 'auth'"
      @login-success="handleLoginSuccess"
    />

    <!-- Main App (Logged In) -->
    <MainApp 
      v-if="token"
      :token="token"
      :user-data="userData"
      @logout="handleLogout"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PublicView from './components/PublicView.vue'
import AuthView from './components/AuthView.vue'
import MainApp from './components/MainApp.vue'

const currentView = ref('auth') // เปลี่ยนจาก 'public' เป็น 'auth'
const token = ref('')
const userData = ref({
  username: '',
  fullName: '',
  role: ''
})

onMounted(() => {
  // Check for saved session
  const savedToken = localStorage.getItem('authToken')
  if (savedToken) {
    token.value = savedToken
    userData.value = {
      username: localStorage.getItem('currentUsername') || '',
      fullName: localStorage.getItem('userFullName') || '',
      role: localStorage.getItem('userRole') || ''
    }
  }
})

function handleLoginSuccess(loginData) {
  token.value = loginData.token
  userData.value = {
    username: loginData.username,
    fullName: loginData.fullName,
    role: loginData.role
  }
  
  // Save to localStorage
  localStorage.setItem('authToken', loginData.token)
  localStorage.setItem('currentUsername', loginData.username)
  localStorage.setItem('userFullName', loginData.fullName)
  localStorage.setItem('userRole', loginData.role)
}

function handleLogout() {
  token.value = ''
  userData.value = { username: '', fullName: '', role: '' }
  
  localStorage.removeItem('authToken')
  localStorage.removeItem('currentUsername')
  localStorage.removeItem('userFullName')
  localStorage.removeItem('userRole')
  
  currentView.value = 'public'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

#app {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #f8f9fa;
}

.view-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 10px;
}

.view-toggle-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.view-toggle-btn.active {
  background: #4a90e2;
  color: white;
}

.view-toggle-btn:hover:not(.active) {
  background: white;
  transform: translateY(-2px);
}

.background-video {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: -2;
}

.video-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  z-index: -1;
}
</style>