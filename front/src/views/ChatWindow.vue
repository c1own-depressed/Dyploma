<template>
  <div v-if="!chatId" class="empty-state">
    Виберіть чат, щоб почати спілкування
  </div>

  <div v-else class="chat-container">
    <div class="chat-header">Чат з {{ partnerName }}</div>

    <div class="messages" ref="messagesContainer" @scroll="onScroll">
      <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-bubble', message.sender === 'me' ? 'from-me' : 'from-other']"
      >
        {{ message.text }}
      </div>
    </div>

    <div class="input-container" style="display: flex; gap: 8px;">
      <input
          v-model="newMessage"
          @keyup.enter="sendMessage"
          type="text"
          class="chat-input"
          placeholder="Напишіть повідомлення..."
      />
      <button @click="sendMessage" class="send-button">Надіслати</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const chatId = ref(route.params.id)
const messages = ref([])
const newMessage = ref("")
const messagesContainer = ref(null)
const partnerName = ref("")
const jwt = localStorage.getItem('jwtToken')

let loading = ref(false)
let page = ref(1)
let updateInterval = null

// При зміні чату — перезавантажуємо та стартуємо опитування
watch(() => route.params.id, async (newId) => {
  if (updateInterval) clearInterval(updateInterval)

  chatId.value = newId
  page.value = 1
  messages.value = []
  await loadChat()
  startPolling()
})

onMounted(async () => {
  if (chatId.value) {
    await loadChat()
    startPolling()
  }
})

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval)
})

async function loadChat() {
  try {
    // інформація про чат
    const chatInfo = await axios.get(
        `http://localhost:8000/chats/${chatId.value}`,
        { headers: { Authorization: `Bearer ${jwt}` } }
    )
    partnerName.value = chatInfo.data.partner_name

    // повідомлення (поточна сторінка)
    const res = await axios.get(
        `http://localhost:8000/chats/${chatId.value}/messages?page=${page.value}`,
        { headers: { Authorization: `Bearer ${jwt}` } }
    )
    messages.value = res.data
    scrollToBottom()
  } catch (err) {
    console.error('Помилка при завантаженні чату:', err)
  }
}

// Функція відправки
const sendMessage = async () => {
  if (!newMessage.value.trim()) return

  try {
    const response = await axios.post(
        `http://localhost:8000/chats/${chatId.value}/messages`,
        { text: newMessage.value },
        { headers: { Authorization: `Bearer ${jwt}` } }
    )
    messages.value.push(response.data)
    newMessage.value = ""
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error('Не вдалося відправити повідомлення:', err)
  }
}

// Прокрутка до низу
const scrollToBottom = () => {
  const container = messagesContainer.value
  if (container) container.scrollTop = container.scrollHeight
}

// Завантаження старих повідомлень при скролі вгору
const onScroll = () => {
  const container = messagesContainer.value
  if (container.scrollTop === 0 && !loading.value) {
    loading.value = true
    page.value++
    loadMoreMessages()
  }
}

const loadMoreMessages = async () => {
  try {
    const res = await axios.get(
        `http://localhost:8000/chats/${chatId.value}/messages?page=${page.value}`,
        { headers: { Authorization: `Bearer ${jwt}` } }
    )
    messages.value = [...res.data, ...messages.value]
  } catch (err) {
    console.error('Помилка при завантаженні старих повідомлень:', err)
  } finally {
    loading.value = false
  }
}

// Опитування кожної секунди
function startPolling() {
  updateInterval = setInterval(async () => {
    await loadChat()
  }, 1000)
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  background-image: url('../assets/img.jpg');
  backdrop-filter: blur(10px);
  border-radius: 0px;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.4);
}

.chat-header {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 16px;
  color: white;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-bubble {
  max-width: 60%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  word-break: break-word;
  background-color: #444;
  color: white;
}

.from-me { align-self: flex-end; background-color: #007aff; }
.from-other { align-self: flex-start; background-color: #5d1485; }

.input-container { margin-top: 16px; }
.chat-input {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  background-color: transparent;
  color: white;
  border: 1px solid white;
  outline: none;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.2); /* фіолетова тінь */
}


.chat-input::placeholder { color: #ccc; }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 18px;
  height: 100%;
}

.send-button {
  padding: 12px 16px;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}
.send-button:hover { background-color: #005bb5; }
</style>
