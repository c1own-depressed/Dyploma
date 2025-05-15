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
          <div v-if="message.text" class="message-text">{{ message.text }}</div>

          <div v-if="message.file_url" class="message-file">
            <a :href="message.file_url"
               target="_blank"
               rel="noopener noreferrer"
               class="file-link"
               :download="(message.mime_type && message.mime_type.startsWith('image/')) ? undefined : (message.original_file_name || 'file')">

              <template v-if="message.mime_type && message.mime_type.startsWith('image/')">
                <img :src="message.file_url" :alt="message.original_file_name || 'Зображення'" class="file-image-preview">
              </template>

              <template v-else>
                <svg class="file-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span class="file-name">{{ message.original_file_name || 'Завантажити файл' }}</span>
              </template>
            </a>

            <div v-if="!(message.mime_type && message.mime_type.startsWith('image/'))" class="file-info">
              <span class="file-type-icon">{{ getFileDisplayInfo(message.original_file_name, message.mime_type).icon }}</span>
              <span class="file-type-description">{{ getFileDisplayInfo(message.original_file_name, message.mime_type).description }}</span>
            </div>
          </div>
          <div class="message-meta">
            <span class="message-time">{{ formatMessageTime(message.created_at) }}</span>
            <span v-if="message.sender === 'me'" class="message-status">
              <svg v-if="message.is_read" class="read-receipt" width="16" height="16" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6L9 17l-5-5"></path>
                <path d="M15 6l-5.5 5.5"></path>
              </svg>
              <svg v-else class="sent-receipt" width="16" height="16" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6L9 17l-5-5"></path>
              </svg>
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="partnerIsTyping && chatId" class="typing-indicator">
      {{ partnerName }} пише...
    </div>

    <div class="input-area">
      <button @click="triggerFileInput" class="attach-file-button" title="Прикріпити файл">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path
              d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
        </svg>
      </button>
      <input type="file" ref="fileUploadInput" @change="onFileSelected" style="display: none;"/>

      <input
          v-model="currentMessageText"
          @input="handleUserTypingDebounced" @keyup.enter="handleSendMessage"
          type="text"
          class="chat-input"
          placeholder="Напишіть повідомлення..."
      />
      <button @click="handleSendMessage" class="send-button">Надіслати</button>
    </div>
    <div v-if="selectedFileForUpload" class="file-preview-area">
      Файл: {{ selectedFileForUpload.name }} ({{ formatFileSize(selectedFileForUpload.size) }})
      <button @click="clearSelectedFile" class="clear-file-button">&times;</button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, nextTick, watch} from 'vue'
import {useRoute} from 'vue-router'
import axios from 'axios'

const route = useRoute()
const chatId = ref(route.params.id)
const messages = ref([])
const currentMessageText = ref("")
const messagesContainer = ref(null)
const partnerName = ref("")
const jwt = localStorage.getItem('jwtToken')

let loading = ref(false)
let page = ref(1)
const MESSAGES_PER_PAGE = 20;
let updateInterval = null

const fileUploadInput = ref(null);
const selectedFileForUpload = ref(null);

// --- Додано для індикатора "пише..." ---
const partnerIsTyping = ref(false);
let typingApiCallTimer = null; // для debounce/throttle логіки
// --- Кінець доданого для індикатора "пише..." ---

const formatMessageTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const timeString = `${hours}:${minutes}`;

  const today = new Date();
  const isToday = date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate();

  if (isToday) {
    return timeString;
  } else {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${day}.${month} ${timeString}`;
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

async function markMessagesAsReadOnServer() {
  if (!chatId.value || document.hidden) return;
  try {
    await axios.post(`http://localhost:8000/chats/${chatId.value}/messages/read`, {}, {headers: {Authorization: `Bearer ${jwt}`}});
  } catch (err) {
    console.error('Помилка при позначенні повідомлень як прочитаних:', err);
  }
}

// --- Додано логіку для індикатора "пише..." ---
watch(currentMessageText, (newValue, oldValue) => {
  if (!chatId.value) return;

  // Надсилаємо статус, якщо починаємо друкувати або продовжуємо після того, як поле було порожнім
  if (newValue.trim() !== "" && (!oldValue || oldValue.trim() === "")) {
    sendTypingStatus(); // Негайно надсилаємо перший сигнал
  }
  // Дебаунсинг для наступних сигналів під час друку
  handleUserTypingDebounced();
});

const handleUserTypingDebounced = () => {
  if (typingApiCallTimer) {
    clearTimeout(typingApiCallTimer);
  }
  typingApiCallTimer = setTimeout(() => {
    if (currentMessageText.value.trim() !== "" && chatId.value) {
      sendTypingStatus();
    }
  }, 800); // Надсилати статус кожні 800ms, якщо користувач продовжує друкувати
};

async function sendTypingStatus() {
  if (!chatId.value) return;
  try {
    await axios.post(`http://localhost:8000/chats/${chatId.value}/typing`, {}, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
  } catch (err) {
    console.error('Помилка надсилання статусу набору тексту:', err);
  }
}

async function fetchChatDetails() {
  if (!chatId.value) {
    partnerIsTyping.value = false;
    return;
  }
  try {
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    // partnerName.value = res.data.partner_name; // Це вже оновлюється в loadInitialChatMessages
    if (partnerIsTyping.value !== res.data.partner_is_typing) {
      partnerIsTyping.value = res.data.partner_is_typing;
    }
  } catch (err) {
    console.error('Помилка при завантаженні деталей чату (статус набору):', err.response || err);
    if (partnerIsTyping.value) { // Скидаємо тільки якщо було true, щоб уникнути зайвих оновлень
      partnerIsTyping.value = false;
    }
  }
}
// --- Кінець доданої логіки для індикатора "пише..." ---


watch(() => route.params.id, async (newId) => {
  if (updateInterval) clearInterval(updateInterval);
  chatId.value = newId;
  page.value = 1;
  messages.value = [];
  currentMessageText.value = "";
  selectedFileForUpload.value = null;
  if (fileUploadInput.value) fileUploadInput.value.value = '';
  partnerIsTyping.value = false; // <--- Скидання індикатора

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
  if (typingApiCallTimer) clearTimeout(typingApiCallTimer); // Очистка таймера при розмонтуванні
});

function handleVisibilityChange() {
  if (!document.hidden && chatId.value) {
    markMessagesAsReadOnServer();
    // Можливо, варто також викликати fetchChatDetails, щоб оновити статус "пише"
    // якщо вкладка була неактивна деякий час
    fetchChatDetails();
  }
}

async function loadInitialChatMessages() {
  if (!chatId.value) return;
  loading.value = true;
  try {
    // Одночасно запитуємо інформацію про чат (включаючи статус друку) та повідомлення
    const chatInfoPromise = axios.get(`http://localhost:8000/chats/${chatId.value}`, {headers: {Authorization: `Bearer ${jwt}`}});
    const messagesPromise = axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, {headers: {Authorization: `Bearer ${jwt}`}});

    const [chatInfoRes, messagesRes] = await Promise.all([chatInfoPromise, messagesPromise]);

    partnerName.value = chatInfoRes.data.partner_name;
    partnerIsTyping.value = chatInfoRes.data.partner_is_typing; // Оновлюємо статус друку
    messages.value = messagesRes.data;

    await nextTick();
    scrollToBottom();
    await markMessagesAsReadOnServer();
  } catch (err) {
    console.error('Помилка при завантаженні чату:', err.response || err);
    if (err.response && err.response.status === 404) {
      chatId.value = null;
      partnerName.value = "";
      messages.value = [];
      partnerIsTyping.value = false; // Скидання
    }
  } finally {
    loading.value = false;
  }
}

const triggerFileInput = () => {
  if (fileUploadInput.value) {
    fileUploadInput.value.click();
  }
};

const onFileSelected = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFileForUpload.value = file;
  }
};

const clearSelectedFile = () => {
  selectedFileForUpload.value = null;
  if (fileUploadInput.value) {
    fileUploadInput.value.value = '';
  }
};

const handleSendMessage = async () => {
  const textToSend = currentMessageText.value.trim();
  const fileToSend = selectedFileForUpload.value;

  if ((!textToSend && !fileToSend) || !chatId.value) {
    return;
  }

  // Очищаємо таймер та повідомляємо, що перестали друкувати (опціонально, якщо сервер сам не скидає швидко)
  if (typingApiCallTimer) clearTimeout(typingApiCallTimer);
  // Можна додати sendStoppedTypingStatus() якщо є такий ендпоінт, або покластись на серверний таймаут

  const formData = new FormData();
  if (textToSend) {
    formData.append('text', textToSend);
  }
  if (fileToSend) {
    formData.append('file', fileToSend, fileToSend.name);
  }

  try {
    const response = await axios.post(
        `http://localhost:8000/chats/${chatId.value}/messages`,
        formData,
        {headers: {Authorization: `Bearer ${jwt}`}}
    );
    messages.value.push(response.data);
    currentMessageText.value = ""; // Це викличе watch, який може надіслати typing статус, якщо логіка не ідеальна.
    // Поки що залишимо так, бо поле стає порожнім.
    clearSelectedFile();
    await nextTick();
    scrollToBottom();
  } catch (err) {
    console.error('Не вдалося відправити повідомлення:', err.response ? err.response.data : err.message);
    alert(`Помилка відправки: ${err.response && err.response.data ? err.response.data.detail : err.message}`);
  }
};

const onScroll = async () => {
  if (!messagesContainer.value) return;
  const {scrollTop} = messagesContainer.value;
  if (scrollTop === 0 && !loading.value && messages.value.length >= MESSAGES_PER_PAGE * page.value) {
    page.value++;
    await loadMoreMessages();
  }
};

const loadMoreMessages = async () => {
  if (!chatId.value || loading.value) return;
  loading.value = true;
  try {
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=${page.value}&page_size=${MESSAGES_PER_PAGE}`, {headers: {Authorization: `Bearer ${jwt}`}});
    if (res.data && res.data.length > 0) {
      const olderMessages = res.data;
      const oldScrollHeight = messagesContainer.value.scrollHeight;
      messages.value = [...olderMessages, ...messages.value];
      await nextTick();
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight - oldScrollHeight;
    } else {
      page.value--; // Якщо даних більше немає, зменшуємо сторінку назад
    }
  } catch (err) {
    console.error('Помилка при завантаженні старих повідомлень:', err.response || err);
    page.value--; // У випадку помилки також повертаємо номер сторінки
  } finally {
    loading.value = false;
  }
};

async function fetchLatestMessagesAndUpdate() {
  if (!chatId.value || document.hidden) return;

  // Спочатку отримуємо деталі чату (включно зі статусом набору)
  await fetchChatDetails(); // <--- Додано виклик

  try {
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, {headers: {Authorization: `Bearer ${jwt}`}});
    const latestMessagesOnServer = res.data;
    let newMessagesFound = false;
    let readStatusChanged = false; // Прапорець для відстеження змін статусу прочитання

    latestMessagesOnServer.forEach(serverMsg => {
      const existingMsgIndex = messages.value.findIndex(m => m.id === serverMsg.id);
      if (existingMsgIndex !== -1) {
        // Перевіряємо, чи змінився статус is_read
        if (messages.value[existingMsgIndex].is_read !== serverMsg.is_read) {
          messages.value[existingMsgIndex].is_read = serverMsg.is_read;
          readStatusChanged = true; // Позначаємо, що статус змінився
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
      // Логіка для автоскролу, якщо користувач близько до низу або це його власне нове повідомлення
      const isNearBottom = container && (container.scrollHeight - container.scrollTop <= container.clientHeight + 200);
      const myNewMessage = latestMessagesOnServer.some(m => m.sender === 'me' && !messages.value.slice(0, -latestMessagesOnServer.length).find(lm => lm.id === m.id));

      if (isNearBottom || myNewMessage) {
        scrollToBottom();
      }
    } else if (readStatusChanged) {
      // Якщо нових повідомлень немає, але статус прочитання змінився,
      // Vue може не оновити DOM, тому примусово оновимо, якщо потрібно (хоча ref має це робити)
      // messages.value = [...messages.value]; // Це може бути зайвим
      await nextTick(); // Даємо Vue час оновити DOM
    }

    // Перевірка на нові непрочитані повідомлення від співрозмовника для позначення їх як прочитаних
    const hasNewUnreadFromOther = latestMessagesOnServer.some(m =>
        m.sender === 'other' &&
        !messages.value.find(localMsg => localMsg.id === m.id)?.is_read // Перевіряємо саме is_read локального повідомлення
    );

    if (hasNewUnreadFromOther && !document.hidden) {
      await markMessagesAsReadOnServer();
    }

  } catch (err) {
    console.error('Помилка при опитуванні нових повідомлень:', err.response || err);
  }
}

function startPolling() {
  if (updateInterval) clearInterval(updateInterval);
  fetchLatestMessagesAndUpdate(); // Перший виклик одразу
  updateInterval = setInterval(fetchLatestMessagesAndUpdate, 2000); // Зменшено інтервал для частішого оновлення статусу "пише"
}

const scrollToBottom = () => {
  const container = messagesContainer.value;
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
};
const getFileExtension = (filename) => {
  if (!filename || typeof filename !== 'string') return '';
  return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
};

const getFileDisplayInfo = (originalFileName, mimeType) => {
  const extension = getFileExtension(originalFileName);
  let icon = '📄';
  let description = 'Файл';

  if (extension) {
    switch (extension) {
      case 'pdf': icon = '📜'; description = 'PDF Документ'; break;
      case 'doc': case 'docx': icon = '📄'; description = 'Документ Word'; break;
      case 'xls': case 'xlsx': icon = '📊'; description = 'Документ Excel'; break;
      case 'ppt': case 'pptx': icon = '🖥️'; description = 'Презентація'; break;
      case 'zip': case 'rar': case '7z': icon = '🗜️'; description = 'Архів'; break;
      case 'txt': icon = '📝'; description = 'Текстовий файл'; break;
      case 'mp3': case 'wav': case 'ogg': case 'flac': icon = '🎵'; description = 'Аудіофайл'; break;
      case 'mp4': case 'avi': case 'mov': case 'mkv': case 'webm': icon = '🎞️'; description = 'Відеофайл'; break;
      case 'jpg': case 'jpeg': case 'png': case 'gif': case 'bmp': case 'webp': icon = '🖼️'; description = 'Зображення'; break;
      default:
        if (mimeType) {
          if (mimeType.startsWith('audio/')) { icon = '🎵'; description = 'Аудіофайл'; }
          else if (mimeType.startsWith('video/')) { icon = '🎞️'; description = 'Відеофайл'; }
          else if (mimeType.startsWith('text/')) { icon = '📝'; description = 'Текстовий файл'; }
          else if (mimeType === 'application/pdf') { icon = '📜'; description = 'PDF Документ'; }
          else if (mimeType.includes('zip')) { icon = '🗜️'; description = 'Архів'; }
        }
        if (description === 'Файл' && extension) { description = `Файл ${extension.toUpperCase()}`; }
    }
  } else if (mimeType) {
    if (mimeType.startsWith('audio/')) { icon = '🎵'; description = 'Аудіофайл'; }
    else if (mimeType.startsWith('video/')) { icon = '🎞️'; description = 'Відеофайл'; }
    else if (mimeType.startsWith('text/')) { icon = '📝'; description = 'Текстовий документ'; }
    else if (mimeType === 'application/pdf') { icon = '📜'; description = 'PDF Документ'; }
    else if (mimeType.includes('wordprocessingml') || mimeType === 'application/msword') { icon = '📄'; description = 'Документ Word'; }
    else if (mimeType.includes('spreadsheetml') || mimeType === 'application/vnd.ms-excel') { icon = '📊'; description = 'Документ Excel'; }
    else if (mimeType.includes('presentationml') || mimeType === 'application/vnd.ms-powerpoint') { icon = '🖥️'; description = 'Презентація'; }
    else if (mimeType.includes('zip')) { icon = '🗜️'; description = 'Архів'; }
  }
  return { icon, description };
};
</script>

<style scoped>
/* ... (ваші існуючі стилі) ... */

.typing-indicator {
  font-style: italic;
  color: #cccccc; /* Або інший колір, який підходить до вашої теми */
  padding: 0px 0px 8px 5px; /* Відступи, щоб було акуратно */
  font-size: 0.85em;
  height: 18px; /* Зафіксувати висоту, щоб не було стрибків контенту */
  opacity: 0.7;
  transition: opacity 0.3s ease-in-out; /* Плавна поява/зникнення */
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  backdrop-filter: blur(8px);
  border-radius: 0;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);
}

.chat-header {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 15px;
  color: white;
  text-shadow: 0 0 5px rgba(0, 0, 0, 0.7);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.align-right {
  align-self: flex-end;
}

.align-left {
  align-self: flex-start;
}

.message-bubble {
  padding: 8px 12px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.4;
  word-break: break-word;
  color: white;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
  position: relative;
}

.message-text {
  margin-bottom: 2px;
}

.message-time {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.65);
  text-align: right;
  margin-top: 3px;
}

.from-me {
  background-color: #2c63a6;
  border-bottom-right-radius: 5px;
}

.from-me .message-time {
  color: rgba(220, 240, 255, 0.75);
}

.from-other {
  background-color: #9326c6;
  border-bottom-left-radius: 5px;
}

.from-other .message-time {
  color: rgba(200, 200, 200, 0.7);
}

.input-area {
  display: flex;
  gap: 8px;
  margin-top: 10px; /* Зменшено відступ, бо є typing-indicator */
  align-items: center;
}

.chat-input {
  flex-grow: 1;
  padding: 10px 15px;
  border-radius: 18px;
  background-color: rgba(40, 40, 40, 0.75);
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

.chat-input::placeholder {
  color: #a0a0a0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-size: 17px;
  height: 100%;
}

.send-button {
  padding: 10px 18px;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 18px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.send-button:hover {
  background-color: #005bb5;
}

.messages::-webkit-scrollbar {
  width: 5px;
}

.messages::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.4);
}

.message-meta {
  display: flex;
  align-items: center;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.65);
  margin-top: 3px;
  align-self: flex-end;
}

.message-time {
  margin-right: 5px;
}

.message-status svg {
  width: 16px;
  height: 16px;
  stroke-width: 1.5;
  fill: none;
  vertical-align: middle;
}

.from-me .message-meta {
  color: rgba(220, 240, 255, 0.75);
}

.from-me .message-status .sent-receipt {
  stroke: rgba(220, 240, 255, 0.75);
}

.from-me .message-status .read-receipt {
  stroke: #34B7F1;
}

.from-other .message-meta {
  color: rgba(200, 200, 200, 0.7);
}

.message-file {
  margin-top: 6px;
}

.file-link {
  display: inline-flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  text-decoration: none;
  color: #e1e3e6;
  background-color: rgba(255, 255, 255, 0.05);
  transition: background-color 0.2s;
  max-width: 100%;
}

.file-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  text-decoration: underline;
}

.from-me .file-link {
  color: #e0f0ff;
}

.from-other .file-link {
  color: #d0d8e0;
}

.file-image-preview {
  max-width: 220px;
  max-height: 180px;
  border-radius: 6px;
  object-fit: cover;
  cursor: pointer;
}

.file-icon {
  margin-right: 8px;
  vertical-align: middle;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.file-info {
  font-size: 0.8em;
  color: rgba(255, 255, 255, 0.65);
  margin-top: 5px;
  display: flex;
  align-items: center;
}

.attach-file-button {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #b0b8c5;
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
  flex-shrink: 0;
}

.attach-file-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.attach-file-button svg {
  width: 20px;
  height: 20px;
}

.file-preview-area {
  margin-top: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 0.9em;
  color: #ccc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-file-button {
  background: none;
  border: none;
  color: #ff6b6b;
  font-size: 1.2em;
  cursor: pointer;
  padding: 0 5px;
}

.clear-file-button:hover {
  color: #ff4757;
}

.file-type-icon {
  margin-right: 6px;
  font-size: 1.2em;
  line-height: 1;
}

.file-type-description {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}
</style>