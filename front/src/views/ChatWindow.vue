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
          @keyup.enter="handleSendMessage"
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

watch(() => route.params.id, async (newId) => {
  if (updateInterval) clearInterval(updateInterval);
  chatId.value = newId;
  page.value = 1;
  messages.value = [];
  currentMessageText.value = "";
  selectedFileForUpload.value = null;
  if (fileUploadInput.value) fileUploadInput.value.value = '';

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
    const chatInfoPromise = axios.get(`http://localhost:8000/chats/${chatId.value}`, {headers: {Authorization: `Bearer ${jwt}`}});
    const messagesPromise = axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, {headers: {Authorization: `Bearer ${jwt}`}});

    const [chatInfo, messagesRes] = await Promise.all([chatInfoPromise, messagesPromise]);

    partnerName.value = chatInfo.data.partner_name;
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
    currentMessageText.value = "";
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
      page.value--;
    }
  } catch (err) {
    console.error('Помилка при завантаженні старих повідомлень:', err.response || err);
    page.value--;
  } finally {
    loading.value = false;
  }
};

async function fetchLatestMessagesAndUpdate() {
  if (!chatId.value || document.hidden) return;
  try {
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}`, {headers: {Authorization: `Bearer ${jwt}`}});
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
      if (container && (container.scrollHeight - container.scrollTop <= container.clientHeight + 200 || latestMessagesOnServer.some(m => m.sender === 'me' && !messages.value.slice(0, -latestMessagesOnServer.length).find(lm => lm.id === m.id)))) {
        scrollToBottom();
      }
    }
    const hasNewUnreadFromOther = latestMessagesOnServer.some(m => m.sender === 'other' && !messages.value.find(lm => lm.id === m.id)?.is_read);
    if (hasNewUnreadFromOther && !document.hidden) {
      await markMessagesAsReadOnServer();
    }
  } catch (err) {
    console.error('Помилка при опитуванні нових повідомлень:', err.response || err);
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
const getFileExtension = (filename) => {
  if (!filename || typeof filename !== 'string') return '';
  // Забирає все після останньої крапки, приводить до нижнього регістру
  return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
};

const getFileDisplayInfo = (originalFileName, mimeType) => {
  const extension = getFileExtension(originalFileName);
  let icon = '📄'; // Іконка за замовчуванням (документ)
  let description = 'Файл'; // Опис за замовчуванням

  if (extension) {
    switch (extension) {
      case 'pdf':
        icon = '📜'; // Іконка для PDF (сувій)
        description = 'PDF Документ';
        break;
      case 'doc':
      case 'docx':
        icon = '📄'; // Іконка для Word (документ)
        description = 'Документ Word';
        break;
      case 'xls':
      case 'xlsx':
        icon = '📊'; // Іконка для Excel (графік)
        description = 'Документ Excel';
        break;
      case 'ppt':
      case 'pptx':
        icon = '🖥️'; // Іконка для PowerPoint (монітор/презентація)
        description = 'Презентація';
        break;
      case 'zip':
      case 'rar':
      case '7z':
        icon = '🗜️'; // Іконка для архіву (лещата)
        description = 'Архів';
        break;
      case 'txt':
        icon = '📝'; // Іконка для текстового файлу (нотатки)
        description = 'Текстовий файл';
        break;
      case 'mp3':
      case 'wav':
      case 'ogg':
      case 'flac':
        icon = '🎵'; // Іконка для аудіо (нота)
        description = 'Аудіофайл';
        break;
      case 'mp4':
      case 'avi':
      case 'mov':
      case 'mkv':
      case 'webm':
        icon = '🎞️'; // Іконка для відео (кіноплівка)
        description = 'Відеофайл';
        break;
      case 'jpg': // Ці розширення вже обробляються як зображення, але для повноти
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'webp':
        icon = '🖼️'; // Іконка для зображення (картина в рамці)
        description = 'Зображення';
        break;
      default:
        // Якщо розширення невідоме, спробуємо визначити за MIME-типом
        if (mimeType) {
          if (mimeType.startsWith('audio/')) {
            icon = '🎵'; description = 'Аудіофайл';
          } else if (mimeType.startsWith('video/')) {
            icon = '🎞️'; description = 'Відеофайл';
          } else if (mimeType.startsWith('text/')) {
            icon = '📝'; description = 'Текстовий файл';
          } else if (mimeType === 'application/pdf') {
            icon = '📜'; description = 'PDF Документ';
          } else if (mimeType.includes('zip')) { // Більш загальне для архівів
            icon = '🗜️'; description = 'Архів';
          }
        }
        // Якщо опис все ще "Файл", і є розширення, додамо його
        if (description === 'Файл' && extension) {
          description = `Файл ${extension.toUpperCase()}`;
        }
    }
  } else if (mimeType) { // Якщо немає розширення, використовуємо MIME-тип
    if (mimeType.startsWith('audio/')) {
      icon = '🎵'; description = 'Аудіофайл';
    } else if (mimeType.startsWith('video/')) {
      icon = '🎞️'; description = 'Відеофайл';
    } else if (mimeType.startsWith('text/')) {
      icon = '📝'; description = 'Текстовий документ';
    } else if (mimeType === 'application/pdf') {
      icon = '📜'; description = 'PDF Документ';
    } else if (mimeType.includes('wordprocessingml') || mimeType === 'application/msword') {
      icon = '📄'; description = 'Документ Word';
    } else if (mimeType.includes('spreadsheetml') || mimeType === 'application/vnd.ms-excel') {
      icon = '📊'; description = 'Документ Excel';
    } else if (mimeType.includes('presentationml') || mimeType === 'application/vnd.ms-powerpoint') {
      icon = '🖥️'; description = 'Презентація';
    } else if (mimeType.includes('zip')) {
      icon = '🗜️'; description = 'Архів';
    }
  }

  return { icon, description };
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
  text-shadow: 0 0 5px rgba(0, 0, 0, 0.7); /* Тінь для кращої читабельності */
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
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
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

.chat-input::placeholder {
  color: #a0a0a0;
}

/* Світліший placeholder */

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

.send-button:hover {
  background-color: #005bb5;
}

/* Стилізація скролбару (опціонально, для webkit браузерів) */
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

.message-file {
  margin-top: 6px; /* Відступ, якщо є текст над файлом */
  /* Можна додати фон або рамку для блоку файлу */
}

.file-link {
  display: inline-flex; /* Для вирівнювання іконки та тексту */
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  text-decoration: none;
  color: #e1e3e6; /* Колір посилання */
  background-color: rgba(255, 255, 255, 0.05); /* Легкий фон */
  transition: background-color 0.2s;
  max-width: 100%; /* Щоб посилання не виходило за межі бульки */
}

.file-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  text-decoration: underline;
}

/* Кольори для своїх/чужих файлів */
.from-me .file-link {
  /* background-color: rgba(var(--my-message-bg-rgb), 0.8); */ /* Якщо є CSS змінна */
  color: #e0f0ff;
}

.from-other .file-link {
  /* background-color: rgba(var(--other-message-bg-rgb), 0.8); */
  color: #d0d8e0;
}


.file-image-preview {
  max-width: 220px; /* Максимальна ширина прев'ю */
  max-height: 180px; /* Максимальна висота прев'ю */
  border-radius: 6px;
  object-fit: cover; /* Щоб зображення гарно вписувалось */
  cursor: pointer; /* Вказує, що можна клікнути для повного розміру */
}

.file-icon {
  /* font-size: 20px;  Для SVG розмір задається атрибутами width/height */
  margin-right: 8px;
  /* Забезпечення вертикального вирівнювання, якщо display: inline-flex на батьківському .file-link ще не достатньо */
  vertical-align: middle;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px; /* Обмеження для довгих імен файлів */
}

.file-info {
  font-size: 0.75em;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
  text-align: left; /* Вирівнювання інформації про файл */
}

.input-area { /* Обгортка для інпутів */
  display: flex;
  gap: 8px;
  margin-top: 15px;
  align-items: center; /* Вирівнювання по вертикалі */
}

.attach-file-button {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #b0b8c5;
  padding: 8px; /* Зробити квадратнішим */
  border-radius: 50%; /* Кругла кнопка */
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
  flex-shrink: 0; /* Щоб кнопка не стискалась */
}

.attach-file-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.attach-file-button svg {
  width: 20px; /* Розмір SVG іконки */
  height: 20px;
}

/* Стилі для прев'ю вибраного файлу перед відправкою */
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
/* ... ваші існуючі стилі ... */

.file-info {
  font-size: 0.8em; /* Трохи збільшив для кращої читабельності типу файлу */
  color: rgba(255, 255, 255, 0.65); /* Трохи світліший колір */
  margin-top: 5px; /* Невеликий відступ зверху */
  display: flex; /* Для кращого вирівнювання іконки та тексту */
  align-items: center; /* Вирівнювання по центру вертикалі */
}

.file-type-icon {
  margin-right: 6px; /* Відступ праворуч від іконки типу файлу */
  font-size: 1.2em;  /* Розмір для emoji-іконок, можна налаштувати */
  line-height: 1; /* Для кращого вертикального вирівнювання emoji */
}

.file-type-description {
  /* Додаткові стилі, якщо потрібно */
  white-space: nowrap; /* Щоб опис не переносився, якщо короткий */
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px; /* Обмеження ширини, якщо опис може бути довгим */
}

/* Переконайтесь, що file-icon для SVG завантаження також добре вирівняний */
.file-icon {
  margin-right: 8px;
  vertical-align: middle;
}
</style>