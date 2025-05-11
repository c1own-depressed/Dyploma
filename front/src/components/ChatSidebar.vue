<template>
  <div class="sidebar-container">
    <button class="home-button" @click="goHome">🏠 На головну</button>

    <div class="chat-list-wrapper">
      <div
          v-for="chat in chats"
          :key="chat.id"
          @click="goToChat(chat.id)"
          :class="['chat-preview', { 'active-chat': isActiveChat(chat.id) }]"
      >
        <div class="chat-info">
          <div class="chat-info-top-row">
            <div class="partner-info-wrapper">
              <span class="partner-name">{{ chat.partner_name }}</span>
              <span
                  v-if="chat.partner_is_online !== undefined"
                  :class="['online-status-indicator', chat.partner_is_online ? 'online' : 'offline']"
                  :title="chat.partner_is_online ? 'Онлайн' : 'Офлайн'"
              ></span>
            </div>
            <div class="top-row-right">
              <span v-if="chat.last_message_sent_by_me && chat.last_message_snippet" class="read-status-icons">
                <svg v-if="!chat.is_last_message_read_by_partner" class="read-receipt-single-gray" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="2 8 5.5 11.5 14 4.5"></polyline>
                </svg>
                <svg v-if="chat.is_last_message_read_by_partner" class="read-receipt-double-blue" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="2 8 5.5 11.5 14 4.5"></polyline>
                  <polyline points="7 8 10.5 11.5 19 4.5" transform="translate(-5,0)"></polyline>
                </svg>
              </span>
              <span v-if="chat.last_message_timestamp" class="last-message-time">
                {{ formatChatTimestamp(chat.last_message_timestamp) }}
              </span>
            </div>
          </div>
          <div class="chat-info-bottom-row">
            <span class="last-message-snippet" :class="{ 'unread-snippet': chat.unread_messages_count > 0 && !chat.last_message_sent_by_me }">
              {{ chat.last_message_snippet || 'Немає повідомлень' }}
            </span>
            <span v-if="chat.unread_messages_count > 0" class="unread-badge">
              {{ chat.unread_messages_count }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'; // computed не використовується в цьому файлі
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const jwt = localStorage.getItem('jwtToken');
const router = useRouter();
const route = useRoute();
const chats = ref([]);
let intervalId = null;

const isActiveChat = (chatId) => {
  return route.params.id && parseInt(route.params.id) === chatId;
};

const formatChatTimestamp = (timestamp) => {
  if (!timestamp) return '';
  const messageDate = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  const hours = messageDate.getHours().toString().padStart(2, '0');
  const minutes = messageDate.getMinutes().toString().padStart(2, '0');
  const timeString = `${hours}:${minutes}`;

  if (messageDate.toDateString() === today.toDateString()) {
    return timeString;
  } else if (messageDate.toDateString() === yesterday.toDateString()) {
    // Для вчорашніх можна теж просто час, або "Вчора, ЧЧ:ХХ"
    return timeString; // Або 'Вчора, ' + timeString;
  } else {
    const day = messageDate.getDate().toString().padStart(2, '0');
    const month = (messageDate.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month}`;
  }
};

const fetchChats = async () => {
  try {
    const res = await axios.get('http://localhost:8000/chats/', { // Додано слеш в кінці
      headers: { Authorization: `Bearer ${jwt}` }
    });
    // Перевіряємо чи дані змінилися, щоб уникнути непотрібних оновлень Vue
    // Це проста перевірка, для складних даних може знадобитися глибше порівняння
    if (JSON.stringify(chats.value) !== JSON.stringify(res.data)) {
      chats.value = res.data;
    }
  } catch (e) {
    console.error('Не вдалося завантажити чати', e);
    // Можна обробити помилки, наприклад, якщо токен недійсний (401), перенаправити на логін
    if (e.response && e.response.status === 401) {
      router.push('/login'); // Або ваш шлях до сторінки логіну
    }
  }
};

onMounted(() => {
  fetchChats();
  intervalId = setInterval(fetchChats, 2000);
});

onUnmounted(() => {
  clearInterval(intervalId);
});

function goToChat(chatId) {
  router.push(`/chats/${chatId}`);
}

function goHome() {
  router.push('/main-page');
}
</script>

<style scoped>
.sidebar-container {
  padding: 8px 0 0 0;
  width: 300px;
  background-color: #17212b;
  height: 100vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.home-button {
  width: calc(100% - 16px);
  margin: 0 8px 8px 8px;
  padding: 10px 12px;
  font-weight: 500;
  font-size: 14px;
  background-color: transparent;
  color: #a3b1c2;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-align: left;
  flex-shrink: 0;
}
.home-button:hover {
  background-color: #2b3745;
}

.chat-list-wrapper {
  flex-grow: 1;
  overflow-y: auto;
}

.chat-preview {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 0 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;
  min-height: 58px;
  box-sizing: border-box;
}
.chat-preview:hover {
  background-color: #2b3745;
}
.chat-preview.active-chat {
  background-color: #4082c3;
}
.chat-preview.active-chat .partner-name,
.chat-preview.active-chat .last-message-snippet,
.chat-preview.active-chat .last-message-time {
  color: #ffffff;
}
.chat-preview.active-chat .read-status-icons svg {
  stroke: #ffffff;
}
.chat-preview.active-chat .last-message-snippet.unread-snippet {
  color: #ffffff;
  font-weight: 500;
}

.chat-info {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  width: 100%;
}

.chat-info-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center; /* Змінено на center для кращого вирівнювання */
  width: 100%;
}

/* Нова обгортка для імені та статусу */
.partner-info-wrapper {
  display: flex;
  align-items: center;
  overflow: hidden; /* Щоб ellipsis для імені працював */
  flex-grow: 1; /* Дозволяє зайняти доступний простір */
  margin-right: 8px; /* Відступ від правого блоку (час, іконки) */
}

.partner-name {
  font-weight: 500;
  font-size: 14px;
  color: #e1e3e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* flex-grow: 1; -- тепер не потрібно, бо є обгортка */
}
.chat-preview.active-chat .partner-name {
  color: #ffffff;
}

/* Стилі для індикатора онлайн статусу */
.online-status-indicator {
  width: 9px; /* Трохи більше для видимості */
  height: 9px;
  border-radius: 50%;
  margin-left: 7px; /* Відступ від імені */
  flex-shrink: 0; /* Щоб не стискався */
  display: inline-block;
  border: 1px solid #17212b; /* Маленька рамка кольору фону для кращого вигляду */
}
.online-status-indicator.online {
  background-color: #e2a9fd; /* Зелений */
}
.chat-preview.active-chat .online-status-indicator.online {
  background-color: #a5d6a7; /* Світліший зелений на синьому фоні */
  border-color: #4082c3;
}
.online-status-indicator.offline {
  background-color: #7f8c9a; /* Сірий */
}
.chat-preview.active-chat .online-status-indicator.offline {
  background-color: #aeb8c2; /* Світліший сірий на синьому фоні */
  border-color: #4082c3;
}


.top-row-right {
  display: flex;
  align-items: center;
  flex-shrink: 0; /* Щоб не стискався */
}

.chat-info-bottom-row {
  display: flex;
  align-items: center;
  margin-top: 2px;
  width: 100%;
}

.last-message-time {
  font-size: 12px;
  color: #8a99ab;
  white-space: nowrap;
  margin-left: 6px;
}
.chat-preview.active-chat .last-message-time {
  color: #b8d4f0;
}

.read-status-icons {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}
.read-status-icons svg {
  width: 15px;
  height: 15px;
  stroke-width: 1.2;
}
.read-receipt-single-gray { stroke: #8a99ab; }
.chat-preview.active-chat .read-receipt-single-gray { stroke: #b8d4f0; }
.read-receipt-double-blue { stroke: #529ef4; }
.chat-preview.active-chat .read-receipt-double-blue { stroke: #ffffff; }

.last-message-snippet {
  font-size: 13px;
  color: #8a99ab;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-grow: 1;
  text-align: left;
  margin-right: 5px;
}
.last-message-snippet.unread-snippet {
  color: #cdd3da;
  font-weight: 500;
}

.unread-badge {
  background-color: #4a93d7;
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 15px;
  flex-shrink: 0;
  margin-left: auto;
}
.chat-preview.active-chat .unread-badge {
  background-color: #ffffff;
  color: #4082c3;
}

.chat-list-wrapper::-webkit-scrollbar { width: 6px; }
.chat-list-wrapper::-webkit-scrollbar-track { background: transparent; margin: 4px 0; }
.chat-list-wrapper::-webkit-scrollbar-thumb { background: #434c58; border-radius: 3px; }
.chat-list-wrapper::-webkit-scrollbar-thumb:hover { background: #525c68; }
</style>