<template>
  <div class="sidebar-container">
    <button class="home-button" @click="goHome">🏠 На головну</button>

    <div
        v-for="chat in chats"
        :key="chat.id"
        @click="goToChat(chat.id)"
        class="chat-preview"
    >
      <div class="chat-id">Чат з {{ chat.partner_name }}</div>
      <!-- <div class="last-message">{{ chat.lastMessage }}</div> -->
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const jwt = localStorage.getItem('jwtToken')
const router = useRouter()
const chats = ref([])

onMounted(async () => {
  try {
    const res = await axios.get('http://localhost:8000/chats', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    chats.value = res.data
  } catch (e) {
    console.error('Не вдалося завантажити чати', e)
  }
})

function goToChat(chatId) {
  router.push(`/chats/${chatId}`)
}

function goHome() {
  router.push('/main-page')
}

</script>

<style scoped>
.sidebar-container {
  padding: 16px;
  width: 300px;
  background: linear-gradient(to bottom right, #4b0082, #6a0dad);
  height: 100vh;
  overflow-y: auto;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.5);
}

.chat-preview {
  background-color: #8a2be2;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: transform 0.2s, background-color 0.3s;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.chat-preview:hover {
  background-color: #a64cf3;
  transform: translateY(-2px);
}

.chat-id {
  font-weight: bold;
  font-size: 16px;
  color: #f8f0ff;
}

.last-message {
  font-size: 14px;
  color: #d8c5f3;
  margin-top: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.home-button {
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  font-weight: bold;
  background-color: #6a0dad;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.home-button:hover {
  background-color: #8a2be2;
}

</style>
