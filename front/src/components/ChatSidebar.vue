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
            <span class="partner-name">{{ chat.partner_name }}</span>
            <div class="top-row-right"> <span v-if="chat.last_message_sent_by_me && chat.last_message_snippet" class="read-status-icons">
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
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // Додано useRoute
import axios from 'axios';

const jwt = localStorage.getItem('jwtToken');
const router = useRouter();
const route = useRoute(); // Для визначення активного чату
const chats = ref([]);

// Приклад очікуваної структури даних для одного чату:
// {
//   id: 1,
//   partner_name: "Ім'я Партнера",
//   last_message_snippet: "Останнє повідомлення тут...",
//   last_message_timestamp: "2025-05-10T22:00:00Z",
//   last_message_sent_by_me: true, // true, якщо останнє повідомлення від поточного користувача
//   is_last_message_read_by_partner: false, // true, якщо партнер прочитав останнє повідомлення поточного користувача
//   unread_messages_count: 3 // Кількість непрочитаних повідомлень для поточного користувача
// }

const isActiveChat = (chatId) => {
  // Перевіряємо, чи є параметр id в поточному маршруті і чи він співпадає
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
    return timeString; // ГГ:ХХ для сьогодні
  } else if (messageDate.toDateString() === yesterday.toDateString()) {
    return timeString; // ГГ:ХХ для вчора (ЗАМІСТЬ "Вчора")
  } else {
    // Для старіших повідомлень можна показувати ДД.ММ
    const day = messageDate.getDate().toString().padStart(2, '0');
    const month = (messageDate.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month}`;
  }
};

onMounted(async () => {
  try {
    // ВАЖЛИВО: Ваш бекенд на http://localhost:8000/chats тепер має повертати дані
    // у розширеному форматі, як описано вище.
    const res = await axios.get('http://localhost:8000/chats', {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    chats.value = res.data;
  } catch (e) {
    console.error('Не вдалося завантажити чати', e);
    // Можна додати тестові дані для розробки UI, якщо бекенд ще не готовий:
    // chats.value = [
    //   { id: 1, partner_name: "Тест Юзер 1", last_message_snippet: "Привіт! Як справи?", last_message_timestamp: new Date().toISOString(), last_message_sent_by_me: false, is_last_message_read_by_partner: false, unread_messages_count: 2 },
    //   { id: 2, partner_name: "Інший Тест", last_message_snippet: "Все добре, дякую!", last_message_timestamp: "2025-05-09T10:30:00Z", last_message_sent_by_me: true, is_last_message_read_by_partner: true, unread_messages_count: 0 },
    // ];
  }
});

function goToChat(chatId) {
  router.push(`/chats/${chatId}`);
}

function goHome() {
  router.push('/main-page');
}
</script>

<style scoped>
/* ... (стилі для .sidebar-container, .home-button, .chat-list-wrapper, .chat-preview) ... */
/* Залишаємо їх як у попередній відповіді, якщо вони вас влаштовують */

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
.chat-preview.active-chat .last-message-snippet, /* Змінено колір для активного чату */
.chat-preview.active-chat .last-message-time {
  color: #ffffff;
}
.chat-preview.active-chat .read-status-icons svg {
  stroke: #ffffff;
}
/* Якщо є .unread-snippet на активному чаті, він теж має бути білим */
.chat-preview.active-chat .last-message-snippet.unread-snippet {
  color: #ffffff;
  font-weight: 500; /* Або 600, якщо хочете жирніший для непрочитаних */
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
  align-items: baseline;
  width: 100%;
}

.top-row-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.chat-info-bottom-row {
  display: flex;
  /* justify-content: space-between; -- Прибираємо це, щоб текст був зліва */
  align-items: center;
  margin-top: 2px;
  width: 100%;
}

.partner-name {
  font-weight: 500;
  font-size: 14px;
  color: #e1e3e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* flex-grow: 1; -- не обов'язково, якщо top-row-right має flex-shrink:0 */
  padding-right: 5px;
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
  flex-grow: 1; /* Дозволяє тексту зайняти доступний простір */
  text-align: left; /* Явно вказуємо вирівнювання по лівому краю */
  margin-right: 5px; /* Відступ до значка непрочитаних, якщо він є */
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
  flex-shrink: 0; /* Важливо, щоб значок не стискався */
  margin-left: auto; /* Притискає значок до правого краю, якщо justify-content: space-between видалено */
}
.chat-preview.active-chat .unread-badge {
  background-color: #ffffff;
  color: #4082c3;
}

/* Скролбар */
.chat-list-wrapper::-webkit-scrollbar { width: 6px; }
.chat-list-wrapper::-webkit-scrollbar-track { background: transparent; margin: 4px 0; }
.chat-list-wrapper::-webkit-scrollbar-thumb { background: #434c58; border-radius: 3px; }
.chat-list-wrapper::-webkit-scrollbar-thumb:hover { background: #525c68; }
</style>
