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
            @click.stop="openDeleteChatModal(chatItem)" class="delete-chat-button"
            title="Видалити чат"
        >
          &times; </button>
      </div>
    </div>

    <div v-if="showChatDeleteConfirmModal" class="modal-overlay-sidebar" @click.self="cancelChatDelete">
      <div class="modal-content-sidebar">
        <div class="modal-header-sidebar">
          <h4>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="modal-header-icon-sidebar"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            Видалити чат?
          </h4>
        </div>
        <p v-if="chatToDelete">Ви дійсно бажаєте видалити чат з <strong>{{ chatToDelete.partner_name }}</strong>? <br/> Вся історія листування буде втрачена назавжди.</p>
        <div class="modal-actions-sidebar">
          <button @click="cancelChatDelete" class="modal-button-sidebar cancel">Скасувати</button>
          <button @click="proceedWithChatDelete" class="modal-button-sidebar confirm">Видалити</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const jwt = localStorage.getItem('jwtToken');
const router = useRouter();
const route = useRoute();
const chats = ref([]);
let intervalId = null;

// --- Стан для модального вікна видалення чату ---
const showChatDeleteConfirmModal = ref(false);
const chatToDelete = ref(null); // Буде зберігати { id: number, partner_name: string }

const isActiveChat = (chatId) => {
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
    return timeString;
  } else {
    const day = messageDate.getDate().toString().padStart(2, '0');
    const month = (messageDate.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month}`;
  }
};

const fetchChats = async () => {
  if (!jwt) {
    console.warn("JWT token not found, skipping chat fetch.");
    return;
  }
  try {
    const res = await axios.get('http://localhost:8000/chats/', {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    if (JSON.stringify(chats.value) !== JSON.stringify(res.data)) {
      chats.value = res.data;
    }
  } catch (e) {
    console.error('Не вдалося завантажити чати', e);
    if (e.response && e.response.status === 401) {
      localStorage.removeItem('jwtToken');
      router.push('/login');
    }
  }
};

// --- Оновлено для модального вікна ---
const openDeleteChatModal = (chatItem) => {
  chatToDelete.value = { id: chatItem.id, partner_name: chatItem.partner_name };
  showChatDeleteConfirmModal.value = true;
};

const cancelChatDelete = () => {
  showChatDeleteConfirmModal.value = false;
  chatToDelete.value = null;
};

const proceedWithChatDelete = async () => {
  if (!chatToDelete.value) return;
  await deleteChatOnBackend(chatToDelete.value.id);
  cancelChatDelete(); // Сховати модалку та скинути chatToDelete
};
// --- Кінець оновлень для модального вікна ---


const deleteChatOnBackend = async (chatId) => {
  try {
    await axios.delete(`http://localhost:8000/chats/${chatId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    chats.value = chats.value.filter(chat => chat.id !== chatId);
    if (isActiveChat(chatId)) {
      router.push('/chats'); // Або на головну, якщо /chats перекине на перший чат
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
  fetchChats();
  intervalId = setInterval(fetchChats, 2000);
  document.addEventListener('keyup', handleGlobalEscKeySidebar);
});

onUnmounted(() => {
  clearInterval(intervalId);
  document.removeEventListener('keyup', handleGlobalEscKeySidebar);
});

const handleGlobalEscKeySidebar = (event) => {
  if (event.key === 'Escape') {
    if (showChatDeleteConfirmModal.value) {
      cancelChatDelete();
    }
  }
};

watch(() => route.params.id, (newId, oldId) => {
  // ...
});

function goToChat(chatId) {
  if (!isActiveChat(chatId)) {
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
/* Стилі для модального вікна видалення чату */
.modal-overlay-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* Вищий z-index, якщо сайдбар має свій z-index */
  opacity: 0;
  animation: fadeInOverlaySidebar 0.2s forwards;
}

@keyframes fadeInOverlaySidebar {
  to { opacity: 1; }
}

.modal-content-sidebar {
  background-color: #36393f;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
  width: 90%;
  max-width: 420px;
  color: #dcddde;
  text-align: left;
  transform: scale(0.95) translateY(0px);
  opacity: 0;
  animation: scaleInModalSidebar 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModalSidebar {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.modal-header-sidebar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.modal-header-icon-sidebar { /* Унікальний клас для іконки */
  color: #f0b232;
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}

.modal-content-sidebar h4 {
  margin:0;
  font-size: 1.15em;
  color: #ffffff;
  font-weight: 600;
}

.modal-content-sidebar p {
  margin-bottom: 24px;
  font-size: 1em;
  line-height: 1.6;
  color: #b9bbbe;
}
.modal-content-sidebar p strong {
  color: #ffffff; /* Виділяємо ім'я партнера */
}


.modal-actions-sidebar { /* Унікальний клас для контейнера кнопок */
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-button-sidebar { /* Унікальний клас для кнопок */
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.modal-button-sidebar:active {
  transform: translateY(1px);
}

.modal-button-sidebar.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.modal-button-sidebar.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.modal-button-sidebar.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.modal-button-sidebar.cancel:hover {
  background-color: #5c626a;
}
</style>
