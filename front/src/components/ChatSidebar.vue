<template>
  <div class="sidebar-container">
    <button class="home-button" @click="goHome">🏠 На головну</button>

    <div class="chat-list-wrapper">
      <div
          v-for="chatItem in chats" :key="chatItem.id"
          @click="goToChat(chatItem.id)"
          :class="['chat-preview', { 'active-chat': isActiveChat(chatItem.id) }]"
      >
        <div class="chat-info">
          <div class="chat-info-top-row">
            <div class="partner-info-wrapper">
              <span class="partner-name">{{ chatItem.partner_name }}</span>
              <span
                  v-if="chatItem.partner_is_online !== undefined"
                  :class="['online-status-indicator', chatItem.partner_is_online ? 'online' : 'offline']"
                  :title="chatItem.partner_is_online ? 'Онлайн' : 'Офлайн'"
              ></span>
            </div>
            <div class="top-row-right">
              <span v-if="chatItem.last_message_sent_by_me && chatItem.last_message_snippet" class="read-status-icons">
                <svg v-if="!chatItem.is_last_message_read_by_partner" class="read-receipt-single-gray" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="2 8 5.5 11.5 14 4.5"></polyline>
                </svg>
                <svg v-if="chatItem.is_last_message_read_by_partner" class="read-receipt-double-blue" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="2 8 5.5 11.5 14 4.5"></polyline>
                  <polyline points="7 8 10.5 11.5 19 4.5" transform="translate(-5,0)"></polyline>
                </svg>
              </span>
              <span v-if="chatItem.last_message_timestamp" class="last-message-time">
                {{ formatChatTimestamp(chatItem.last_message_timestamp) }}
              </span>
            </div>
          </div>
          <div class="chat-info-bottom-row">
            <span v-if="chatItem.partner_is_typing" class="typing-indicator-sidebar">
              пише...
            </span>
            <span v-else class="last-message-snippet" :class="{ 'unread-snippet': chatItem.unread_messages_count > 0 && !chatItem.last_message_sent_by_me }">
              {{ chatItem.last_message_snippet || 'Немає повідомлень' }}
            </span>
            <span v-if="chatItem.unread_messages_count > 0 && !chatItem.partner_is_typing" class="unread-badge">
              {{ chatItem.unread_messages_count }}
            </span>
          </div>
        </div>
        <button
            @click.stop="confirmDeleteChat(chatItem.id, chatItem.partner_name)"
            class="delete-chat-button"
            title="Видалити чат"
        >
          &times; </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'; // Додано watch
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const jwt = localStorage.getItem('jwtToken');
const router = useRouter();
const route = useRoute(); // Зберігаємо route для використання в isActiveChat та watch
const chats = ref([]);
let intervalId = null;

const isActiveChat = (chatId) => {
  // route.params.id може бути undefined або строкою, тому потрібна перевірка та приведення типів
  return route.params.id !== undefined && parseInt(route.params.id) === chatId;
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
    // Замість часу для "вчора" можна показувати "Вчора"
    // return "Вчора";
    return timeString; // Або залишаємо час
  } else {
    const day = messageDate.getDate().toString().padStart(2, '0');
    const month = (messageDate.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month}`;
  }
};

const fetchChats = async () => {
  if (!jwt) { // Якщо немає токена, не робимо запит
    console.warn("JWT token not found, skipping chat fetch.");
    // Можливо, перенаправити на логін, якщо це ще не зроблено
    // router.push('/login');
    return;
  }
  try {
    const res = await axios.get('http://localhost:8000/chats/', {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    // Порівнюємо глибше, щоб уникнути зайвих оновлень, якщо дані ті ж самі
    // але це може бути надлишковим, якщо Vue достатньо розумний з refs
    if (JSON.stringify(chats.value) !== JSON.stringify(res.data)) {
      chats.value = res.data;
    }
  } catch (e) {
    console.error('Не вдалося завантажити чати', e);
    if (e.response && e.response.status === 401) {
      // Обробка неавторизованого доступу
      localStorage.removeItem('jwtToken'); // Видаляємо невалідний токен
      router.push('/login'); // Перенаправляємо на сторінку входу
    }
  }
};

const confirmDeleteChat = (chatId, partnerName) => {
  if (window.confirm(`Ви впевнені, що хочете видалити чат з "${partnerName}"? Це видалить всю історію листування.`)) {
    deleteChatOnBackend(chatId);
  }
};

const deleteChatOnBackend = async (chatId) => {
  try {
    await axios.delete(`http://localhost:8000/chats/${chatId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    chats.value = chats.value.filter(chat => chat.id !== chatId);
    if (isActiveChat(chatId)) {
      router.push('/chats');
    }
    console.log(`Чат ${chatId} успішно видалено`);
  } catch (e) {
    console.error('Не вдалося видалити чат', e);
    if (e.response && e.response.data && e.response.data.detail) {
      alert(`Помилка видалення: ${e.response.data.detail}`);
    } else {
      alert('Не вдалося видалити чат. Спробуйте пізніше.');
    }
  }
};

onMounted(() => {
  fetchChats(); // Перший запит при монтуванні
  intervalId = setInterval(fetchChats, 2000); // Полінг кожні 2 секунди
});

onUnmounted(() => {
  clearInterval(intervalId);
});

// Додаємо watch для оновлення активного чату, якщо параметр маршруту змінюється
// Це не стосується "пише...", але є корисним для коректної роботи isActiveChat
watch(() => route.params.id, (newId, oldId) => {
  // Цей watch допоможе оновити клас active-chat, якщо це потрібно
  // Але для відображення "пише..." це не критично, оскільки дані приходять з fetchChats
});


function goToChat(chatId) {
  if (!isActiveChat(chatId)) { // Переходимо тільки якщо це не поточний активний чат
    router.push(`/chats/${chatId}`);
  }
}

function goHome() {
  router.push('/main-page');
}
</script>

<style scoped>
/* ... (ваші існуючі стилі для .sidebar-container, .home-button, і т.д.) ... */

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
  position: relative;
}
.chat-preview:hover {
  background-color: #2b3745;
}
.chat-preview.active-chat {
  background-color: #4082c3;
}
.chat-preview.active-chat .partner-name,
.chat-preview.active-chat .last-message-snippet,
.chat-preview.active-chat .last-message-time,
.chat-preview.active-chat .typing-indicator-sidebar { /* Додано для активного чату */
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
  width: calc(100% - 25px);
}

.chat-info-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.partner-info-wrapper {
  display: flex;
  align-items: center;
  overflow: hidden;
  flex-grow: 1;
  margin-right: 8px;
}

.partner-name {
  font-weight: 500;
  font-size: 14px;
  color: #e1e3e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.online-status-indicator {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-left: 7px;
  flex-shrink: 0;
  display: inline-block;
  border: 1px solid #17212b;
}
.online-status-indicator.online {
  background-color: #e2a9fd;
}
.chat-preview.active-chat .online-status-indicator.online {
  background-color: #a5d6a7;
  border-color: #4082c3;
}
.online-status-indicator.offline {
  background-color: #7f8c9a;
}
.chat-preview.active-chat .online-status-indicator.offline {
  background-color: #aeb8c2;
  border-color: #4082c3;
}


.top-row-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.chat-info-bottom-row {
  display: flex;
  align-items: center;
  margin-top: 2px;
  width: 100%;
  min-height: 18px; /* Щоб рядок не стрибав по висоті */
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

/* Новий стиль для індикатора "пише..." у сайдбарі */
.typing-indicator-sidebar {
  font-size: 13px;
  color: #4F80AD; /* Можете підібрати колір, наприклад, синюватий або зеленуватий */
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-grow: 1;
  text-align: left;
  margin-right: 5px;
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

.delete-chat-button {
  background: none;
  border: none;
  color: #6c7883;
  font-size: 20px;
  line-height: 1;
  padding: 0 5px;
  cursor: pointer;
  position: absolute;
  right: 10px;
  top: 60%;
  transform: translateY(-50%); /* Центрування кнопки */
  opacity: 0;
  transition: opacity 0.2s ease-in-out, color 0.2s ease-in-out;
}
.chat-preview:hover .delete-chat-button {
  opacity: 1;
}
.chat-preview.active-chat .delete-chat-button { /* Завжди показувати на активному чаті */
  opacity: 1;
  color: #d1d5db;
}
.delete-chat-button:hover {
  color: #e53e3e;
}
.chat-preview.active-chat .delete-chat-button:hover {
  color: #ffaaaa;
}


.chat-list-wrapper::-webkit-scrollbar { width: 6px; }
.chat-list-wrapper::-webkit-scrollbar-track { background: transparent; margin: 4px 0; }
.chat-list-wrapper::-webkit-scrollbar-thumb { background: #434c58; border-radius: 3px; }
.chat-list-wrapper::-webkit-scrollbar-thumb:hover { background: #525c68; }
</style>