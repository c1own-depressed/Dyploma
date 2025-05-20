<template>
  <main class="task-page"> <div class="task-card">
    <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

    <form class="task-form" @submit.prevent="submitCompletion" v-if="taskTitleFetched">
      <h2>Виконати завдання</h2>

      <h3 class="task-title" v-if="taskTitle">{{ taskTitle }}</h3>
      <div v-if="fetchError" class="error-message standalone">
        {{ fetchError }}
        <button type="button" @click="fetchTask" class="retry-button">Спробувати ще раз</button>
      </div>

      <div class="input-group">
          <textarea
              v-model="completionText"
              placeholder="Опишіть виконання завдання..."
              required
              rows="6"
          ></textarea>
      </div>

      <div class="input-group file-input-group">
        <label for="file-upload" class="file-upload-label">
          Прикріпити файл:
        </label>
        <input
            type="file"
            id="file-upload"
            ref="fileInputRef"
            @change="handleFileUpload"
            class="file-input"
            accept="image/*,application/pdf,.doc,.docx,.txt,.zip,.rar,.7z,.xls,.xlsx,.ppt,.pptx"
        />
        <span v-if="selectedFile" class="file-name-display">
            Обраний файл: {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})
            <button type="button" @click="removeSelectedFile" class="remove-file-btn" title="Видалити файл">×</button>
          </span>
        <small v-if="fileError" class="file-error-text">{{ fileError }}</small>
      </div>
      <input type="submit" value="Надіслати на перевірку" :disabled="isSubmitting" />

    </form>
    <div v-if="!taskTitleFetched && !fetchError" class="loading-placeholder">Завантаження даних завдання...</div>
  </div>

    <div v-if="showModal" class="complete-task-modal-overlay" @click.self="cancelModalAction">
      <div class="complete-task-modal-content">
        <div class="complete-task-modal-header">
          <h4>
            <svg :class="['complete-task-modal-header-icon', modalConfig.type]" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" v-if="modalConfig.type === 'success'"></path>
              <polyline points="22 4 12 14.01 9 11.01" v-if="modalConfig.type === 'success'"></polyline>
              <circle cx="12" cy="12" r="10" v-if="modalConfig.type === 'error'"></circle>
              <line x1="12" y1="8" x2="12" y2="12" v-if="modalConfig.type === 'error'"></line>
              <line x1="12" y1="16" x2="12.01" y2="16" v-if="modalConfig.type === 'error'"></line>
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" v-if="modalConfig.type === 'confirm'"></path>
              <line x1="12" y1="9" x2="12" y2="13" v-if="modalConfig.type === 'confirm'"></line>
              <line x1="12" y1="17" x2="12.01" y2="17" v-if="modalConfig.type === 'confirm'"></line>
            </svg>
            {{ modalConfig.title }}
          </h4>
        </div>
        <p v-html="modalConfig.message"></p>
        <div class="complete-task-modal-actions">
          <button v-if="!modalConfig.isNotification" @click="cancelModalAction" class="complete-task-modal-button cancel">{{ modalConfig.cancelButtonText }}</button>
          <button @click="proceedWithModalAction" :class="['complete-task-modal-button', modalConfig.isNotification ? (modalConfig.type === 'error' ? 'error-ok' : 'ok') : 'confirm']">{{ modalConfig.confirmButtonText }}</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const taskId = route.params.taskId;
const completionText = ref('');
const fetchError = ref('');
const taskTitle = ref('');
const taskTitleFetched = ref(false);
const jwt = localStorage.getItem('jwtToken');
const selectedFile = ref(null);
const fileInputRef = ref(null);
const fileError = ref('');
const isSubmitting = ref(false);

// --- Стан для універсального модального вікна ---
const showModal = ref(false);
const modalConfig = ref({
  title: '',
  message: '',
  isNotification: false,
  type: 'confirm',
  confirmButtonText: 'Так',
  cancelButtonText: 'Скасувати',
  onConfirm: null,
  onCancel: null
});
// --- Кінець стану для модального вікна ---

const openModal = (config) => {
  modalConfig.value = {
    title: '', message: '', isNotification: false, type: 'confirm',
    confirmButtonText: 'Так', cancelButtonText: 'Скасувати',
    onConfirm: null, onCancel: null, ...config
  };
  showModal.value = true;
};

const showNotificationModal = (title, message, type = 'success', onOkCallback = null) => {
  openModal({
    title, message, isNotification: true, type: type,
    confirmButtonText: 'OK',
    onConfirm: onOkCallback || closeModal
  });
};

const proceedWithModalAction = () => {
  if (typeof modalConfig.value.onConfirm === 'function') {
    modalConfig.value.onConfirm();
  }
  if (modalConfig.value.isNotification || modalConfig.value.type !== 'confirm') {
    closeModal();
  }
};

const cancelModalAction = () => {
  if (typeof modalConfig.value.onCancel === 'function') {
    modalConfig.value.onCancel();
  }
  closeModal();
};

const closeModal = () => {
  showModal.value = false;
  setTimeout(() => {
    if (!showModal.value) {
      modalConfig.value = {
        title: '', message: '', isNotification: false, type: 'confirm',
        confirmButtonText: 'Так', cancelButtonText: 'Скасувати',
        onConfirm: null, onCancel: null
      };
    }
  }, 300);
};

const handleGlobalEscCompleteTask = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    cancelModalAction();
  }
};

const fetchTask = async () => {
  fetchError.value = '';
  taskTitleFetched.value = false;
  if (!jwt) {
    showNotificationModal(
        'Помилка авторизації',
        'Будь ласка, увійдіть до системи, щоб виконати цю дію.',
        'error',
        () => router.push('/login')
    );
    return;
  }
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${taskId}`, { // Перевірте URL, чи правильний він для отримання завдання
      headers: { Authorization: `Bearer ${jwt}` }
    });
    taskTitle.value = response.data.title;
    taskTitleFetched.value = true;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    let errorMsg = 'Не вдалося завантажити інформацію про завдання.';
    if (error.response) {
      if (error.response.status === 404) {
        errorMsg = 'Завдання не знайдено.';
      } else if (error.response.status === 401) {
        errorMsg = 'Помилка авторизації. Спробуйте увійти знову.';
        localStorage.removeItem('jwtToken');
        // Негайно перенаправляємо або показуємо модалку з опцією переходу на логін
        showNotificationModal('Помилка авторизації', errorMsg, 'error', () => router.push('/login'));
        return; // Важливо вийти, щоб не показувати fetchError нижче
      } else if (error.response.data && error.response.data.detail) {
        errorMsg = error.response.data.detail;
      }
    }
    fetchError.value = errorMsg; // Показуємо помилку на сторінці
  }
};

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  fileError.value = '';
  selectedFile.value = null; // Скидаємо попередній файл
  if(fileInputRef.value) fileInputRef.value.value = null; // Скидаємо інпут

  if (file) {
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      fileError.value = 'Файл занадто великий. Максимальний розмір: 5MB.';
      return;
    }
    const allowedMimeTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf',
      'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
      'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const allowedExtensions = ['zip', 'rar', '7z', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf'];

    if (!allowedMimeTypes.includes(file.type) && !allowedExtensions.includes(fileExtension) ) {
      fileError.value = 'Недопустимий тип файлу.';
      return;
    }
    selectedFile.value = file;
  }
};

const removeSelectedFile = () => {
  selectedFile.value = null;
  fileError.value = '';
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};

const submitCompletion = async () => {
  if (!completionText.value.trim()) {
    showNotificationModal('Помилка валідації', 'Будь ласка, опишіть виконання завдання.', 'error');
    return;
  }
  if (fileError.value) {
    showNotificationModal('Помилка файлу', fileError.value, 'error');
    return;
  }

  isSubmitting.value = true;
  const formData = new FormData();
  formData.append('execution_description', completionText.value);

  if (selectedFile.value) {
    formData.append('file', selectedFile.value);
  }

  try {
    const response = await axios.post(`http://localhost:8000/tasks/${taskId}/complete`, formData, {
      headers: {
        Authorization: `Bearer ${jwt}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    showNotificationModal('Успіх!', 'Завдання успішно виконано та надіслано на перевірку замовнику.', 'success', () => {
      router.push('/profile');
    });
    completionText.value = '';
    removeSelectedFile();

  } catch (error) {
    console.error('Деталі помилки при надсиланні:', error.response || error);
    let errorMessageText = 'Сталася невідома помилка при надсиланні.';
    if (error.response && error.response.data && error.response.data.detail) {
      if (typeof error.response.data.detail === 'string') {
        errorMessageText = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        errorMessageText = error.response.data.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ');
      }
    }
    showNotificationModal('Помилка', errorMessageText, 'error');
  } finally {
    isSubmitting.value = false;
  }
};

const goToProfile = () => {
  if (window.history.length > 2 && document.referrer.includes(window.location.host)) {
    router.go(-1);
  } else {
    router.push('/profile');
  }
};

onMounted(() => {
  if (!jwt) {
    router.push('/login');
    return;
  }
  fetchTask();
  document.addEventListener('keyup', handleGlobalEscCompleteTask);
});

onUnmounted(() => {
  document.removeEventListener('keyup', handleGlobalEscCompleteTask);
});

</script>

<style scoped>
/* Ваші стилі з попереднього прикладу... */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.task-page {
  font-family: 'Poppins', sans-serif;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: #f0f0f0;
}

.task-card {
  background: rgba(30, 25, 45, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem 3rem;
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 550px;
  color: #f0f0f0;
  text-align: left;
}

.back-link {
  display: inline-block;
  margin-bottom: 1.8rem;
  color: #b0b8c5;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  padding: 0.2rem 0;
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-form h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.task-title {
  font-size: 1.25rem;
  margin-bottom: 1.8rem;
  font-weight: 500;
  color: #e0e1e6;
  text-align: center;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  background-color: rgba(255,255,255,0.05);
  padding: 0.5rem;
  border-radius: 8px;
}

.input-group {
  position: relative;
  margin-bottom: 1.5rem;
}
.file-input-group {
  margin-bottom: 2rem;
}

.input-group textarea {
  width: 100%;
  padding: 0.9rem 1.1rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  color: #ffffff;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  resize: vertical;
  min-height: 120px;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.input-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-group textarea:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.file-upload-label {
  display: block;
  color: #b0b8c5;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.file-input {
  width: 100%;
  padding: 0.7rem 0.9rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  color: #f0f0f0;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.file-input::file-selector-button {
  padding: 0.6rem 1rem;
  margin-right: 1rem;
  background-color: #007AFF;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.file-input::file-selector-button:hover {
  background-color: #005bb5;
}

.file-input:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.file-name-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #c0c8d5;
  background-color: rgba(0,0,0,0.25);
  padding: 0.6rem 0.9rem;
  border-radius: 6px;
  word-break: break-all;
}

.remove-file-btn {
  background: none;
  border: none;
  color: #ff9a9a;
  font-size: 1.3rem;
  font-weight: bold;
  cursor: pointer;
  margin-left: 0.75rem;
  padding: 0 0.3rem;
  line-height: 1;
}
.remove-file-btn:hover {
  color: #ff6b6b;
}
.file-error-text {
  display: block;
  color: #ff9a9a;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}


input[type="submit"] {
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
  margin-top: 1rem;
}

input[type="submit"]:hover:not(:disabled) {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}
input[type="submit"]:disabled {
  background-color: #5a6268;
  cursor: not-allowed;
  opacity: 0.7;
}

.error-message.standalone {
  color: #ffc2c2;
  background-color: rgba(255, 82, 82, 0.2);
  border: 1px solid rgba(255, 82, 82, 0.4);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}
.retry-button {
  display: block;
  margin: 1rem auto 0;
  padding: 0.5rem 1rem;
  background-color: #007AFF;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.retry-button:hover {
  background-color: #005bb5;
}

.loading-placeholder {
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  padding: 2rem 0;
}

/* Стилі для універсального модального вікна */
.complete-task-modal-overlay { /* Унікальний префікс */
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  opacity: 0;
  animation: fadeInOverlayCompleteTask 0.2s forwards;
}

@keyframes fadeInOverlayCompleteTask {
  to { opacity: 1; }
}

.complete-task-modal-content {
  background-color: #36393f;
  padding: 25px 30px;
  border-radius: 8px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  width: 90%;
  max-width: 450px;
  color: #dcddde;
  text-align: left;
  transform: scale(0.95) translateY(0px);
  opacity: 0;
  animation: scaleInModalCompleteTask 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModalCompleteTask {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.complete-task-modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.complete-task-modal-header-icon {
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}
.complete-task-modal-header-icon.confirm {
  color: #f0b232;
}
.complete-task-modal-header-icon.success {
  color: #28a745;
}
.complete-task-modal-header-icon.error {
  color: #d83c3e;
}

.complete-task-modal-content h4 {
  margin:0;
  font-size: 1.2em;
  color: #ffffff;
  font-weight: 600;
}

.complete-task-modal-content p {
  margin-bottom: 25px;
  font-size: 1em;
  line-height: 1.65;
  color: #b9bbbe;
  word-break: break-word;
}

.complete-task-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.complete-task-modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.complete-task-modal-button:active {
  transform: translateY(1px);
}

.complete-task-modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.complete-task-modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.complete-task-modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.complete-task-modal-button.cancel:hover {
  background-color: #5c626a;
}

.complete-task-modal-button.ok {
  background-color: #007bff;
  color: white;
}
.complete-task-modal-button.ok:hover {
  background-color: #0056b3;
}
.complete-task-modal-button.error-ok {
  background-color: #d83c3e;
}
.complete-task-modal-button.error-ok:hover {
  background-color: #bf3032;
}
</style>