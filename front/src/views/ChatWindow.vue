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
          :class="['message-item', message.sender === 'me' ? 'align-right' : 'align-left']"
      >
        <div :class="['message-bubble', message.sender === 'me' ? 'from-me' : 'from-other']">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-meta">
            <span class="message-time">{{ formatMessageTime(message.created_at) }}</span>
            <span v-if="message.sender === 'me'" class="message-status">
              <svg v-if="message.is_read" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="read-receipt">
                <path d="M20 6L9 17l-5-5"></path>
                <path d="M15 6l-5.5 5.5"></path> </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="sent-receipt">
                <path d="M20 6L9 17l-5-5"></path>
              </svg>
            </span>
          </div>
        </div>
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
const MESSAGES_PER_PAGE = 20;
let updateInterval = null

const formatMessageTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const today = new Date();
  const isToday = date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate();
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const timeString = `${hours}:${minutes}`; // Виправлено: без HTML
  if (isToday) {
    return timeString;
  } else {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month} ${timeString}`; // Виправлено: без HTML
  }
};

async function markMessagesAsReadOnServer() {
  if (!chatId.value || document.hidden) return;
  try {
    await axios.post(
        `http://localhost:8000/chats/${chatId.value}/messages/read`, // Правильна інтерполяція
        {},
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
  } catch (err) {
    console.error('Помилка при позначенні повідомлень як прочитаних:', err);
  }
}

watch(() => route.params.id, async (newId) => {
  if (updateInterval) clearInterval(updateInterval);
  chatId.value = newId;
  page.value = 1;
  messages.value = [];
  if (newId) {
    await loadInitialChatMessages();
    startPolling();
  } else {
    partnerName.value = "";
  }
});

onMounted(async () => {
  if (chatId.value) {
    await loadInitialChatMessages();
    startPolling();
  }
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval);
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});

function handleVisibilityChange() {
  if (!document.hidden && chatId.value) {
    markMessagesAsReadOnServer();
  }
}

async function loadInitialChatMessages() {
  if (!chatId.value) return;
  loading.value = true;
  try {
    const chatInfoPromise = axios.get(
        `http://localhost:8000/chats/${chatId.value}`, // Правильна інтерполяція
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    const messagesPromise = axios.get(
        `http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, // Правильна інтерполяція
        { headers: { Authorization: `Bearer ${jwt}` } }
    );

    const [chatInfo, messagesRes] = await Promise.all([chatInfoPromise, messagesPromise]);

    partnerName.value = chatInfo.data.partner_name;
    messages.value = messagesRes.data;

    await nextTick();
    scrollToBottom();
    await markMessagesAsReadOnServer();

  } catch (err) {
    console.error('Помилка при завантаженні чату:', err);
    if (err.response && err.response.status === 404) {
      chatId.value = null;
      partnerName.value = "";
      messages.value = [];
    }
  } finally {
    loading.value = false;
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || !chatId.value) return;
  try {
    const response = await axios.post(
        `http://localhost:8000/chats/${chatId.value}/messages`, // Правильна інтерполяція
        { text: newMessage.value },
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    messages.value.push(response.data);
    newMessage.value = "";
    await nextTick();
    scrollToBottom();
  } catch (err) {
    console.error('Не вдалося відправити повідомлення:', err);
  }
};

const onScroll = async () => {
  if (!messagesContainer.value) return;
  const { scrollTop } = messagesContainer.value;
  if (scrollTop === 0 && !loading.value && messages.value.length >= MESSAGES_PER_PAGE * page.value) {
    page.value++;
    await loadMoreMessages();
  }
};

const loadMoreMessages = async () => {
  if (!chatId.value || loading.value) return;
  loading.value = true;
  try {
    const res = await axios.get(
        `http://localhost:8000/chats/${chatId.value}/messages?page=${page.value}&page_size=${MESSAGES_PER_PAGE}`, // Правильна інтерполяція
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    if (res.data && res.data.length > 0) {
      const olderMessages = res.data;
      const oldScrollHeight = messagesContainer.value.scrollHeight;
      messages.value = [...olderMessages, ...messages.value];
      await nextTick();
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight - oldScrollHeight;
    } else {
      page.value--;
    }
  } catch (err) {
    console.error('Помилка при завантаженні старих повідомлень:', err);
    page.value--;
  } finally {
    loading.value = false;
  }
};

async function fetchLatestMessagesAndUpdate() {
  if (!chatId.value || document.hidden) return;
  try {
    const res = await axios.get(
        `http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, // Правильна інтерполяція
        { headers: { Authorization: `Bearer ${jwt}` } }
    );

    const latestMessagesOnServer = res.data;

    let newMessagesFound = false;
    latestMessagesOnServer.forEach(serverMsg => {
      const existingMsgIndex = messages.value.findIndex(m => m.id === serverMsg.id);
      if (existingMsgIndex !== -1) {
        if (messages.value[existingMsgIndex].is_read !== serverMsg.is_read) {
          messages.value[existingMsgIndex].is_read = serverMsg.is_read;
        }
      } else {
        messages.value.push(serverMsg);
        newMessagesFound = true;
      }
    });

    if (newMessagesFound) {
      messages.value.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      await nextTick();
      const container = messagesContainer.value;
      if (container && (container.scrollHeight - container.scrollTop <= container.clientHeight + 150 || latestMessagesOnServer.some(m => m.sender === 'me'))) {
        scrollToBottom();
      }
    }

    const hasNewUnreadFromOther = latestMessagesOnServer.some(m => m.sender === 'other' && messages.value.find(lm => lm.id === m.id && !lm.is_read));
    if (hasNewUnreadFromOther && !document.hidden) {
      await markMessagesAsReadOnServer();
    }

  } catch (err) {
    console.error('Помилка при опитуванні нових повідомлень:', err);
  }
}

function startPolling() {
  if (updateInterval) clearInterval(updateInterval);
  fetchLatestMessagesAndUpdate();
  updateInterval = setInterval(fetchLatestMessagesAndUpdate, 3000);
}

const scrollToBottom = () => {
  const container = messagesContainer.value;
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
};

</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px; /* Трохи зменшено padding */
  background-image: url('../assets/img.jpg'); /* Переконайтесь, що шлях правильний */
  background-size: cover;
  background-position: center;
  backdrop-filter: blur(8px); /* Трохи зменшено blur */
  border-radius: 0;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.3); /* Трохи зменшено тінь */
}

.chat-header {
  font-size: 18px; /* Трохи зменшено шрифт */
  font-weight: bold;
  margin-bottom: 15px; /* Трохи зменшено відступ */
  color: white;
  text-shadow: 0 0 5px rgba(0,0,0,0.7); /* Тінь для кращої читабельності */
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px; /* Для скролбару, якщо він з'явиться */
  display: flex;
  flex-direction: column;
  gap: 8px; /* Зменшено gap */
}

/* Новий контейнер для кожного повідомлення, щоб вирівнювати бульку */
.message-item {
  display: flex;
  flex-direction: column; /* Текст і час будуть один під одним в бульці */
  max-width: 75%; /* Максимальна ширина для всього блоку повідомлення */
}

.align-right {
  align-self: flex-end; /* Вирівнює весь .message-item праворуч */
}

.align-left {
  align-self: flex-start; /* Вирівнює весь .message-item ліворуч */
}

.message-bubble {
  padding: 8px 12px;
  border-radius: 16px; /* Більш заокруглені кути */
  font-size: 14px;
  line-height: 1.4;
  word-break: break-word;
  color: white;
  display: inline-block; /* Щоб булька обгортала контент */
  /* max-width не потрібен тут, якщо він є на .message-item */
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  position: relative; /* Для можливих "хвостиків" або позначок */
}

.message-text {
  /* Якщо потрібно, можна додати відступ знизу, якщо час розташований під текстом */
  margin-bottom: 2px; /* Невеликий відступ між текстом та часом */
}

.message-time {
  font-size: 0.68rem; /* Дуже маленький шрифт для часу, як у Telegram */
  color: rgba(255, 255, 255, 0.65); /* Світло-сірий, напівпрозорий */
  text-align: right; /* Час завжди праворуч всередині бульки */
  margin-top: 3px;
  /* display: block; */ /* Щоб час був на новому рядку, якщо текст довгий - вже є flex-direction: column */
}

.from-me {
  background-color: #2c63a6; /* Синій колір для моїх повідомлень */
  /* "Хвостик" для мого повідомлення */
  border-bottom-right-radius: 5px;
}
.from-me .message-time {
  color: rgba(220, 240, 255, 0.75); /* Спеціальний колір часу для моїх повідомлень */
}

.from-other {
  background-color: #9326c6; /* Темно-сірий для чужих повідомлень */
  /* "Хвостик" для чужого повідомлення */
  border-bottom-left-radius: 5px;
}
.from-other .message-time {
  color: rgba(200, 200, 200, 0.7); /* Спеціальний колір часу для чужих повідомлень */
}

.input-container {
  margin-top: 15px;
  display: flex;
  gap: 8px;
}
.chat-input {
  flex-grow: 1;
  padding: 10px 15px;
  border-radius: 18px; /* Більш заокруглений інпут */
  background-color: rgba(40, 40, 40, 0.75); /* Напівпрозорий темний */
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  outline: none;
  font-size: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.chat-input:focus {
  border-color: #007aff;
  box-shadow: 0 0 8px rgba(0, 122, 255, 0.4);
}
.chat-input::placeholder { color: #a0a0a0; } /* Світліший placeholder */

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa; /* Світліший колір */
  font-size: 17px; /* Трохи менший шрифт */
  height: 100%;
}

.send-button {
  padding: 10px 18px; /* Змінено padding */
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 18px; /* Більш заокруглена кнопка */
  cursor: pointer;
  font-weight: 500; /* Менш жирний */
  font-size: 14px;
  transition: background-color 0.2s;
  flex-shrink: 0;
}
.send-button:hover { background-color: #005bb5; }

/* Стилізація скролбару (опціонально, для webkit браузерів) */
.messages::-webkit-scrollbar {
  width: 5px;
}
.messages::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.1);
  border-radius: 3px;
}
.messages::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.25);
  border-radius: 3px;
}
.messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.4);
}
.message-meta {
  display: flex;
  align-items: center;
  font-size: 0.68rem; /* Збережено з попереднього разу */
  color: rgba(255, 255, 255, 0.65); /* Збережено */
  margin-top: 3px; /* Збережено */
  /* text-align: right; -- не потрібно, якщо використовується flex для вирівнювання */
  align-self: flex-end; /* Вирівнює весь блок часу та статусу праворуч всередині бульки */
}

.message-time {
  margin-right: 5px; /* Відступ між часом та статусом */
}

.message-status svg {
  width: 16px; /* Розмір галочок */
  height: 16px;
  stroke-width: 1.5; /* Товщина лінії галочок */
  fill: none; /* Без заливки */
  vertical-align: middle; /* Для кращого вирівнювання з текстом часу */
}

/* Стилі для моїх повідомлень */
.from-me .message-meta {
  color: rgba(220, 240, 255, 0.75); /* Колір часу для моїх повідомлень */
}
.from-me .message-status .sent-receipt {
  stroke: rgba(220, 240, 255, 0.75); /* Сірувата галочка (відправлено) */
}
.from-me .message-status .read-receipt {
  /* stroke: #4FC3F7; Яскраво-синій, як у Telegram Web */
  stroke: #34B7F1; /* Інший варіант синього для прочитаних */
}
.from-me .message-status .read-receipt path:nth-child(2) {
  /* Можна трохи змістити другу галочку, якщо потрібно */
  /* transform: translateX(3px); */
}


/* Стилі для чужих повідомлень (якщо потрібно буде щось специфічне для .message-meta) */
.from-other .message-meta {
  color: rgba(200, 200, 200, 0.7);
}
</style>