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
          :class="['message-item', message.sender === 'me' ? 'align-right' : 'align-left', messageToEdit && messageToEdit.id === message.id ? 'is-editing-highlight' : '']"
      >
        <div
            class="message-interactive-area"
            @mouseover="message.sender === 'me' && !messageToEdit ? handleMouseOverMessageArea(message.id) : null"
            @mouseleave="message.sender === 'me' ? handleMouseLeaveMessageArea() : null"
        >
          <div :class="['message-bubble', message.sender === 'me' ? 'from-me' : 'from-other']">
            <div>
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
            </div>

            <div class="message-meta">
              <span v-if="message.is_edited" class="edited-indicator">(ред.)</span>
              <span class="message-time">{{ formatMessageTime(message.updated_at || message.created_at) }}</span>
              <span v-if="message.sender === 'me'" class="message-status">
                <svg v-if="message.is_read" class="read-receipt" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 6L9 17l-5-5"></path><path d="M15 6l-5.5 5.5"></path>
                </svg>
                <svg v-else class="sent-receipt" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 6L9 17l-5-5"></path>
                </svg>
              </span>
            </div>
          </div>

          <div
              v-if="message.sender === 'me' && showMessageActions === message.id && !messageToEdit"
              class="message-actions"
              @mouseenter="handleMouseEnterActions"
              @mouseleave="handleMouseLeaveActions"
          >
            <button v-if="!message.file_url" @click.stop="startEditMessage(message)" class="action-icon edit-icon" title="Редагувати">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
            <button @click.stop="initiateDeleteMessage(message.id)" class="action-icon delete-icon" title="Видалити">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="partnerIsTyping && chatId" class="typing-indicator">
      {{ partnerName }} пише...
    </div>

    <div class="input-area-wrapper">
      <div v-if="messageToEdit" class="edit-mode-indicator">
        <span>Редагування повідомлення...</span>
        <button @click="cancelEditMessage" class="cancel-edit-main-button" title="Скасувати редагування">&times;</button>
      </div>
      <div class="input-area">
        <button @click="triggerFileInput" class="attach-file-button" title="Прикріпити файл" :disabled="!!messageToEdit">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
          </svg>
        </button>
        <input type="file" ref="fileUploadInput" @change="onFileSelected" style="display: none;" :disabled="!!messageToEdit"/>

        <input
            v-model="currentMessageText"
            @input="handleUserTypingDebounced"
            @keyup.enter.exact.prevent="submitMessage"
            @keyup.esc="handleEscKey"
            type="text"
            class="chat-input"
            :placeholder="messageToEdit ? 'Внесіть зміни...' : 'Напишіть повідомлення...'"
            ref="mainChatInput"
        />
        <button @click="submitMessage" class="send-button">
          {{ messageToEdit ? 'Зберегти' : 'Надіслати' }}
        </button>
      </div>
      <div v-if="selectedFileForUpload && !messageToEdit" class="file-preview-area">
        Файл: {{ selectedFileForUpload.name }} ({{ formatFileSize(selectedFileForUpload.size) }})
        <button @click="clearSelectedFile" class="clear-file-button">&times;</button>
      </div>
    </div>

    <div v-if="showDeleteConfirmationModal" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal-content modal-scale-enter-active">
        <div class="modal-header">
          <h4>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="modal-header-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            Підтвердити видалення
          </h4>
        </div>
        <p>Ви дійсно бажаєте видалити це повідомлення? Цю дію неможливо буде скасувати.</p>
        <div class="modal-actions">
          <button @click="cancelDelete" class="modal-button cancel">Скасувати</button>
          <button @click="confirmDelete" class="modal-button confirm">Видалити</button>
        </div>
      </div>
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
const currentMessageText = ref("")
const messagesContainer = ref(null)
const partnerName = ref("")
const jwt = localStorage.getItem('jwtToken')
const mainChatInput = ref(null);

let loading = ref(false)
let page = ref(1)
const MESSAGES_PER_PAGE = 20;
let updateInterval = null

const fileUploadInput = ref(null);
const selectedFileForUpload = ref(null);

const partnerIsTyping = ref(false);
let typingApiCallTimer = null;

const showMessageActions = ref(null);
const messageToEdit = ref(null);

const showDeleteConfirmationModal = ref(false);
const messageIdToDelete = ref(null);

// --- Логіка для таймерів ховеру ---
let hideActionsTimer = null;

const handleMouseOverMessageArea = (messageId) => {
  if (messageToEdit.value) return;
  clearTimeout(hideActionsTimer);
  showMessageActions.value = messageId;
};

const handleMouseLeaveMessageArea = () => {
  if (messageToEdit.value) return;
  clearTimeout(hideActionsTimer);
  hideActionsTimer = setTimeout(() => {
    showMessageActions.value = null;
  }, 300);
};

const handleMouseEnterActions = () => {
  clearTimeout(hideActionsTimer);
};

const handleMouseLeaveActions = () => {
  if (messageToEdit.value) return;
  clearTimeout(hideActionsTimer);
  hideActionsTimer = setTimeout(() => {
    showMessageActions.value = null;
  }, 300);
};
// --- Кінець логіки для таймерів ---


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
watch(currentMessageText, (newValue, oldValue) => {
  if (!chatId.value || messageToEdit.value) return;
  if (newValue.trim() !== "" && (!oldValue || oldValue.trim() === "")) {
    sendTypingStatus();
  }
  handleUserTypingDebounced();
});
const handleUserTypingDebounced = () => {
  if (messageToEdit.value) return;
  if (typingApiCallTimer) {
    clearTimeout(typingApiCallTimer);
  }
  typingApiCallTimer = setTimeout(() => {
    if (currentMessageText.value.trim() !== "" && chatId.value && !messageToEdit.value) {
      sendTypingStatus();
    }
  }, 800);
};
async function sendTypingStatus() {
  if (!chatId.value || messageToEdit.value) return;
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
    if (partnerIsTyping.value !== res.data.partner_is_typing) {
      partnerIsTyping.value = res.data.partner_is_typing;
    }
  } catch (err) {
    console.error('Помилка при завантаженні деталей чату (статус набору):', err.response || err);
    if (partnerIsTyping.value) {
      partnerIsTyping.value = false;
    }
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
  partnerIsTyping.value = false;
  cancelEditMessage();
  showMessageActions.value = null;
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
  document.addEventListener('keyup', handleGlobalEscKey);
});
onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval);
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  if (typingApiCallTimer) clearTimeout(typingApiCallTimer);
  document.removeEventListener('keyup', handleGlobalEscKey);
  clearTimeout(hideActionsTimer); // Очищення таймера
});
const handleGlobalEscKey = (event) => {
  if (event.key === 'Escape') {
    handleEscKey();
  }
};
function handleVisibilityChange() {
  if (!document.hidden && chatId.value) {
    markMessagesAsReadOnServer();
    fetchChatDetails();
  }
}
async function loadInitialChatMessages() {
  if (!chatId.value) return;
  loading.value = true;
  try {
    const chatInfoPromise = axios.get(`http://localhost:8000/chats/${chatId.value}`, {headers: {Authorization: `Bearer ${jwt}`}});
    const messagesPromise = axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}&sort_order=desc`, {headers: {Authorization: `Bearer ${jwt}`}});
    const [chatInfoRes, messagesRes] = await Promise.all([chatInfoPromise, messagesPromise]);
    partnerName.value = chatInfoRes.data.partner_name;
    partnerIsTyping.value = chatInfoRes.data.partner_is_typing;
    messages.value = messagesRes.data.reverse();
    await nextTick();
    scrollToBottom();
    await markMessagesAsReadOnServer();
  } catch (err) {
    console.error('Помилка при завантаженні чату:', err.response || err);
    if (err.response && err.response.status === 404) {
      chatId.value = null;
      partnerName.value = "";
      messages.value = [];
      partnerIsTyping.value = false;
    }
  } finally {
    loading.value = false;
  }
}
const triggerFileInput = () => {
  if (messageToEdit.value) return;
  if (fileUploadInput.value) {
    fileUploadInput.value.click();
  }
};
const onFileSelected = (event) => {
  if (messageToEdit.value) return;
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
const submitMessage = async () => {
  if (messageToEdit.value) {
    await saveEditedMessage();
  } else {
    await sendNewMessage();
  }
};
const handleEscKey = () => {
  if (messageToEdit.value) {
    cancelEditMessage();
  } else if (showDeleteConfirmationModal.value) {
    cancelDelete();
  }
};
const sendNewMessage = async () => {
  const textToSend = currentMessageText.value.trim();
  const fileToSend = selectedFileForUpload.value;
  if ((!textToSend && !fileToSend) || !chatId.value) {
    return;
  }
  if (typingApiCallTimer) clearTimeout(typingApiCallTimer);
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
    if (mainChatInput.value) mainChatInput.value.focus();
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
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=${page.value}&page_size=${MESSAGES_PER_PAGE}&sort_order=desc`, {headers: {Authorization: `Bearer ${jwt}`}});
    if (res.data && res.data.length > 0) {
      const olderMessages = res.data.reverse();
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
  await fetchChatDetails();
  try {
    const res = await axios.get(`http://localhost:8000/chats/${chatId.value}/messages?page=1&page_size=${MESSAGES_PER_PAGE}&sort_order=desc`, {headers: {Authorization: `Bearer ${jwt}`}});
    const latestMessagesOnServer = res.data.reverse();
    let newMessagesFound = false;
    let readStatusChanged = false;
    let messagesUpdated = false;
    const currentEditingId = messageToEdit.value ? messageToEdit.value.id : null;
    latestMessagesOnServer.forEach(serverMsg => {
      const existingMsgIndex = messages.value.findIndex(m => m.id === serverMsg.id);
      if (existingMsgIndex !== -1) {
        const localMsg = messages.value[existingMsgIndex];
        if (localMsg.is_read !== serverMsg.is_read) {
          localMsg.is_read = serverMsg.is_read;
          readStatusChanged = true;
        }
        if (serverMsg.id !== currentEditingId && (localMsg.text !== serverMsg.text || localMsg.is_edited !== serverMsg.is_edited)) {
          localMsg.text = serverMsg.text;
          localMsg.is_edited = serverMsg.is_edited;
          localMsg.updated_at = serverMsg.updated_at;
          messagesUpdated = true;
        }
      } else {
        messages.value.push(serverMsg);
        newMessagesFound = true;
      }
    });
    if (messages.value.length > latestMessagesOnServer.length && !newMessagesFound && !messagesUpdated) {
      const serverIds = new Set(latestMessagesOnServer.map(m => m.id));
      messages.value = messages.value.filter(m => serverIds.has(m.id) || (m.id === currentEditingId));
      if (currentEditingId && !serverIds.has(currentEditingId)) {
        cancelEditMessage();
      }
    }
    if (newMessagesFound) {
      messages.value.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      await nextTick();
      const container = messagesContainer.value;
      const isNearBottom = container && (container.scrollHeight - container.scrollTop <= container.clientHeight + 200);
      const myNewMessage = latestMessagesOnServer.some(m => m.sender === 'me' && !messages.value.slice(0, -latestMessagesOnServer.length).find(lm => lm.id === m.id));
      if (isNearBottom || myNewMessage) {
        scrollToBottom();
      }
    } else if (readStatusChanged || messagesUpdated) {
      await nextTick();
    }
    const hasNewUnreadFromOther = latestMessagesOnServer.some(m =>
        m.sender === 'other' &&
        !messages.value.find(localMsg => localMsg.id === m.id)?.is_read
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
  fetchLatestMessagesAndUpdate();
  updateInterval = setInterval(fetchLatestMessagesAndUpdate, 2000);
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
const startEditMessage = (message) => {
  if (message.file_url) {
    alert("Редагування повідомлень з файлами наразі не підтримується.");
    return;
  }
  if (messageToEdit.value && messageToEdit.value.id !== message.id) {
    return;
  }
  messageToEdit.value = { id: message.id, originalText: message.text };
  currentMessageText.value = message.text;
  showMessageActions.value = null;
  clearSelectedFile();
  nextTick(() => {
    if (mainChatInput.value) {
      mainChatInput.value.focus();
      mainChatInput.value.select();
    }
  });
};
const cancelEditMessage = () => {
  if (messageToEdit.value) {
    currentMessageText.value = "";
  }
  messageToEdit.value = null;
  if (mainChatInput.value) mainChatInput.value.focus();
};
const saveEditedMessage = async () => {
  if (!messageToEdit.value) return;
  const messageId = messageToEdit.value.id;
  const newText = currentMessageText.value.trim();
  if (!newText) {
    alert("Повідомлення не може бути порожнім.");
    currentMessageText.value = messageToEdit.value.originalText;
    if (mainChatInput.value) mainChatInput.value.focus();
    return;
  }
  if (newText === messageToEdit.value.originalText) {
    cancelEditMessage();
    return;
  }
  if (!chatId.value || !messageId) return;
  try {
    const response = await axios.put(
        `http://localhost:8000/chats/${chatId.value}/messages/${messageId}`,
        { text: newText },
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    const updatedMessageFromServer = response.data;
    const index = messages.value.findIndex(m => m.id === messageId);
    if (index !== -1) {
      messages.value[index] = { ...messages.value[index], ...updatedMessageFromServer };
    }
    cancelEditMessage();
  } catch (err) {
    console.error('Помилка редагування повідомлення:', err.response || err);
    alert(`Помилка редагування: ${err.response?.data?.detail || err.message}`);
  }
};
const initiateDeleteMessage = (msgId) => {
  messageIdToDelete.value = msgId;
  showDeleteConfirmationModal.value = true;
};
const confirmDelete = async () => {
  if (messageIdToDelete.value) {
    await actualDeleteMessage(messageIdToDelete.value);
  }
  cancelDelete();
};
const cancelDelete = () => {
  showDeleteConfirmationModal.value = false;
  messageIdToDelete.value = null;
};
const actualDeleteMessage = async (msgId) => {
  if (!chatId.value || !msgId) return;
  try {
    await axios.delete(
        `http://localhost:8000/chats/${chatId.value}/messages/${msgId}`,
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    messages.value = messages.value.filter(m => m.id !== msgId);
    if (messageToEdit.value && messageToEdit.value.id === msgId) {
      cancelEditMessage();
    }
  } catch (err) {
    console.error('Помилка видалення повідомлення:', err.response || err);
    alert(`Помилка видалення: ${err.response?.data?.detail || err.message}`);
  }
};
</script>

<style scoped>
.is-editing-highlight .message-bubble {
  outline: 2px solid #007bff;
  box-shadow: 0 0 10px rgba(0, 122, 255, 0.5);
}

.input-area-wrapper {
  padding: 0px 0px 5px 0px;
  border-top: 1px solid rgba(255,255,255,0.1);
  margin-top: 10px;
}
.edit-mode-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 5px 12px;
  font-size: 0.9em;
  color: #00caff;
  background-color: rgba(0, 100, 150, 0.1);
  border-bottom: 1px dashed rgba(0, 122, 255, 0.3);
}
.edit-mode-indicator span {
  font-style: italic;
}
.cancel-edit-main-button {
  background: none;
  border: none;
  color: #ff6b6b;
  font-size: 1.5em;
  cursor: pointer;
  padding: 0 5px;
  line-height: 1;
}
.cancel-edit-main-button:hover {
  color: #ff4757;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  animation: fadeInOverlay 0.2s forwards;
}

@keyframes fadeInOverlay {
  to { opacity: 1; }
}

.modal-content {
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
  animation: scaleInModal 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModal {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.modal-header-icon {
  color: #f0b232;
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}

.modal-content h4 {
  margin:0;
  font-size: 1.15em;
  color: #ffffff;
  font-weight: 600;
}

.modal-content p {
  margin-bottom: 24px;
  font-size: 1em;
  line-height: 1.6;
  color: #b9bbbe;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.modal-button:active {
  transform: translateY(1px);
}

.modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.modal-button.cancel:hover {
  background-color: #5c626a;
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}
.message-item.align-right { align-self: flex-end; }
.message-item.align-left { align-self: flex-start; }

.message-interactive-area {
  position: relative;
  display: inline-block; /* Обгортає бульку + місце для кнопок */
}

/* === КЛЮЧОВІ ЗМІНИ ДЛЯ СТАБІЛЬНОСТІ ХОВЕРУ === */

/* Для повідомлень користувача (справа), кнопки зліва */
.message-item.align-right .message-interactive-area {
  /* Додаємо padding зліва, де будуть кнопки.
     Розмір padding має бути достатнім для розміщення кнопок + невеликий відступ.
     Припустимо, блок кнопок ~55-60px завширшки. Додамо ще ~5px відступу.
  */
  padding-left: 65px;
  margin-left: -65px; /* Компенсуємо padding, щоб булька повідомлення залишилася на місці */
}

/* Для повідомлень співрозмовника (зліва), кнопки справа (якщо знадобиться) */
.message-item.align-left .message-interactive-area {
  padding-right: 65px;
  margin-right: -65px;
}

.message-actions {
  position: absolute;
  top: 50%;
  transform: translateY(-50%) scale(0.95);

  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #2f3136;
  padding: 6px 9px;
  border-radius: 20px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.3);

  opacity: 0;
  visibility: hidden;
  transition: opacity 0.1s ease-out, visibility 0.1s ease-out, transform 0.1s ease-out .05s;
  z-index: 10;
  white-space: nowrap;
}

.message-interactive-area:hover .message-actions {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) scale(1);
}

/* Позиціонуємо кнопки дій В МЕЖАХ розширеної padding-зони */
.message-item.align-right .message-actions {
  left: 5px; /* Відступ від лівого краю padding-зони message-interactive-area */
  right: auto; /* Важливо скинути right, якщо використовуємо left */
}

.message-item.align-left .message-actions {
  right: 5px; /* Відступ від правого краю padding-зони */
  left: auto; /* Важливо скинути left */
}

/* === Кінець ключових змін для стабільності ховеру === */


.is-editing-highlight .message-bubble {
  outline: 2px solid #007bff;
  box-shadow: 0 0 10px rgba(0, 122, 255, 0.5);
}

.input-area-wrapper {
  padding: 0px 0px 5px 0px;
  border-top: 1px solid rgba(255,255,255,0.1);
  margin-top: 10px;
}
.edit-mode-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 5px 12px;
  font-size: 0.9em;
  color: #00caff;
  background-color: rgba(0, 100, 150, 0.1);
  border-bottom: 1px dashed rgba(0, 122, 255, 0.3);
}
.edit-mode-indicator span {
  font-style: italic;
}
.cancel-edit-main-button {
  background: none;
  border: none;
  color: #ff6b6b;
  font-size: 1.5em;
  cursor: pointer;
  padding: 0 5px;
  line-height: 1;
}
.cancel-edit-main-button:hover {
  color: #ff4757;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  animation: fadeInOverlay 0.2s forwards;
}

@keyframes fadeInOverlay {
  to { opacity: 1; }
}

.modal-content {
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
  animation: scaleInModal 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModal {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.modal-header-icon {
  color: #f0b232;
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}

.modal-content h4 {
  margin:0;
  font-size: 1.15em;
  color: #ffffff;
  font-weight: 600;
}

.modal-content p {
  margin-bottom: 24px;
  font-size: 1em;
  line-height: 1.6;
  color: #b9bbbe;
}

.modal-actions { /* Це стосується кнопок в модалці, не плутати з .message-actions */
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.modal-button:active {
  transform: translateY(1px);
}

.modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.modal-button.cancel:hover {
  background-color: #5c626a;
}

.action-icon {
  background: none;
  border: none;
  color: #b9bbbe;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.action-icon:hover {
  background-color: #3b3e44;
  color: #ffffff;
}
.edited-indicator {font-size: 0.65rem;color: rgba(255, 255, 255, 0.5);margin-right: 4px;font-style: italic;}
.typing-indicator {font-style: italic;color: #cccccc;padding: 0px 0px 8px 5px;font-size: 0.85em;height: 18px;opacity: 0.7;transition: opacity 0.3s ease-in-out;}
.chat-container {display: flex;flex-direction: column;height: 100%;padding: 20px;background-image: url('../assets/img.jpg');background-size: cover;background-position: center;backdrop-filter: blur(8px);border-radius: 0;box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);}
.chat-header {font-size: 18px;font-weight: bold;margin-bottom: 15px;color: white;text-shadow: 0 0 5px rgba(0, 0, 0, 0.7);}
.messages {flex: 1;overflow-y: auto;padding: 0 10px;display: flex;flex-direction: column;gap: 8px;}
.message-bubble {padding: 8px 12px;border-radius: 16px;font-size: 14px;line-height: 1.4;word-break: break-word;color: white;box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);}
.message-text {margin-bottom: 2px;}
.message-time {font-size: 0.68rem;color: rgba(255, 255, 255, 0.65);text-align: right;margin-top: 3px;}
.from-me {background-color: #2c63a6;border-bottom-right-radius: 5px;}
.from-me .message-time {color: rgba(220, 240, 255, 0.75);}
.from-other {background-color: #9326c6;border-bottom-left-radius: 5px;}
.from-other .message-time {color: rgba(200, 200, 200, 0.7);}
.input-area {display: flex;gap: 8px;align-items: center;padding: 8px 12px;}
.chat-input {flex-grow: 1;padding: 10px 15px;border-radius: 18px;background-color: rgba(40, 40, 40, 0.75);color: white;border: 1px solid rgba(255, 255, 255, 0.2);outline: none;font-size: 14px;box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);transition: border-color 0.2s, box-shadow 0.2s;}
.chat-input:focus {border-color: #007aff;box-shadow: 0 0 8px rgba(0, 122, 255, 0.4);}
.chat-input::placeholder {color: #a0a0a0;}
.empty-state {display: flex;align-items: center;justify-content: center;color: #aaa;font-size: 17px;height: 100%;}
.send-button {padding: 10px 18px;background-color: #007aff;color: white;border: none;border-radius: 18px;cursor: pointer;font-weight: 500;font-size: 14px;transition: background-color 0.2s;flex-shrink: 0;}
.send-button:hover {background-color: #005bb5;}
.messages::-webkit-scrollbar {width: 5px;}
.messages::-webkit-scrollbar-track {background: rgba(0, 0, 0, 0.1);border-radius: 3px;}
.messages::-webkit-scrollbar-thumb {background: rgba(255, 255, 255, 0.25);border-radius: 3px;}
.messages::-webkit-scrollbar-thumb:hover {background: rgba(255, 255, 255, 0.4);}
.message-meta {display: flex;align-items: center;font-size: 0.68rem;color: rgba(255, 255, 255, 0.65);margin-top: 3px;align-self: flex-end;justify-content: flex-end;}
.message-status svg {width: 16px;height: 16px;stroke-width: 1.5;fill: none;vertical-align: middle;}
.from-me .message-meta {color: rgba(220, 240, 255, 0.75);}
.from-me .message-status .sent-receipt {stroke: rgba(220, 240, 255, 0.75);}
.from-me .message-status .read-receipt {stroke: #34B7F1;}
.from-other .message-meta {color: rgba(200, 200, 200, 0.7);}
.message-file {margin-top: 6px;}
.file-link {display: inline-flex;align-items: center;padding: 8px 10px;border-radius: 8px;text-decoration: none;color: #e1e3e6;background-color: rgba(255, 255, 255, 0.05);transition: background-color 0.2s;max-width: 100%;}
.file-link:hover {background-color: rgba(255, 255, 255, 0.1);text-decoration: underline;}
.from-me .file-link {color: #e0f0ff;}
.from-other .file-link {color: #d0d8e0;}
.file-image-preview {max-width: 220px;max-height: 180px;border-radius: 6px;object-fit: cover;cursor: pointer;}
.file-icon {margin-right: 8px;vertical-align: middle;}
.file-name {white-space: nowrap;overflow: hidden;text-overflow: ellipsis;max-width: 180px;}
.file-info {font-size: 0.8em;color: rgba(255, 255, 255, 0.65);margin-top: 5px;display: flex;align-items: center;}
.attach-file-button {background: transparent;border: 1px solid rgba(255, 255, 255, 0.25);color: #b0b8c5;padding: 8px;border-radius: 50%;cursor: pointer;display: flex;align-items: center;justify-content: center;transition: background-color 0.2s, color 0.2s;flex-shrink: 0;}
.attach-file-button:hover:not(:disabled) {background-color: rgba(255, 255, 255, 0.1);color: #ffffff;}
.attach-file-button:disabled {cursor: not-allowed;opacity: 0.5;}
.file-preview-area {margin: 8px 12px 0px 12px;padding: 8px;background-color: rgba(0, 0, 0, 0.2);border-radius: 6px;font-size: 0.9em;color: #ccc;display: flex;justify-content: space-between;align-items: center;}
.clear-file-button {background: none;border: none;color: #ff6b6b;font-size: 1.2em;cursor: pointer;padding: 0 5px;}
.clear-file-button:hover {color: #ff4757;}
.file-type-icon {margin-right: 6px;font-size: 1.2em;line-height: 1;}
.file-type-description {white-space: nowrap;overflow: hidden;text-overflow: ellipsis;max-width: 150px;}

</style>