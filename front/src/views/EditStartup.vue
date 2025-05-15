<template>
  <main class="edit-startup-page">
    <div class="startup-card">
      <span class="back-link" @click="goBack">← Повернутися в профіль</span>

      <form class="startup-form" @submit.prevent="updateStartup" v-if="!loading && startupSuccessfullyLoaded">
        <h2>Редагувати стартап</h2>

        <div v-if="formError" class="error-message">{{ formError }}</div>

        <div class="input-group">
          <input
              type="text"
              placeholder="Назва стартапу"
              v-model="form.name"
              required
          />
        </div>

        <div class="input-group">
          <textarea
              placeholder="Опис"
              v-model="form.description"
              required
              rows="6"
          ></textarea>
        </div>

        <input type="submit" value="Зберегти зміни" :disabled="isSubmitting" />
      </form>

      <div v-if="loading" class="loading-placeholder">Завантаження даних стартапу...</div>
      <div v-if="!loading && !startupSuccessfullyLoaded && initialLoadError" class="error-message">{{ initialLoadError }}</div>


      <button class="delete-button" @click="confirmDeleteStartupAction" v-if="!loading && startupSuccessfullyLoaded" :disabled="isDeleting">
        {{ isDeleting ? 'Видалення...' : 'Видалити стартап' }}
      </button>
    </div>

    <div v-if="showModal" class="edit-startup-modal-overlay" @click.self="cancelModalAction">
      <div class="edit-startup-modal-content">
        <div class="edit-startup-modal-header">
          <h4>
            <svg v-if="!modalConfig.isNotification" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="edit-startup-modal-header-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <svg v-else :class="['edit-startup-modal-header-icon', modalConfig.type]" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" v-if="modalConfig.type === 'success'"></path>
              <polyline points="22 4 12 14.01 9 11.01" v-if="modalConfig.type === 'success'"></polyline>
              <circle cx="12" cy="12" r="10" v-if="modalConfig.type === 'error'"></circle>
              <line x1="12" y1="8" x2="12" y2="12" v-if="modalConfig.type === 'error'"></line>
              <line x1="12" y1="16" x2="12.01" y2="16" v-if="modalConfig.type === 'error'"></line>
            </svg>
            {{ modalConfig.title }}
          </h4>
        </div>
        <p v-html="modalConfig.message"></p>
        <div class="edit-startup-modal-actions">
          <button v-if="!modalConfig.isNotification" @click="cancelModalAction" class="edit-startup-modal-button cancel">{{ modalConfig.cancelButtonText }}</button>
          <button @click="proceedWithModalAction" :class="['edit-startup-modal-button', modalConfig.isNotification ? (modalConfig.type === 'error' ? 'error-ok' : 'ok') : 'confirm']">{{ modalConfig.confirmButtonText }}</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const jwt = localStorage.getItem('jwtToken');

const form = ref({
  name: '',
  description: ''
});

const loading = ref(true);
const initialLoadError = ref('');
const formError = ref('');
const startupSuccessfullyLoaded = ref(false);
const isSubmitting = ref(false);
const isDeleting = ref(false);

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

const handleGlobalEscEditStartup = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    cancelModalAction();
  }
};

const fetchStartup = async () => {
  loading.value = true;
  initialLoadError.value = '';
  startupSuccessfullyLoaded.value = false;
  if (!jwt) {
    initialLoadError.value = "Ви не авторизовані.";
    loading.value = false;
    showNotificationModal('Помилка авторизації', 'Будь ласка, увійдіть до системи.', 'error', () => router.push('/login'));
    return;
  }
  try {
    const res = await axios.get(`http://localhost:8000/user/startup/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    form.value.name = res.data.name ?? '';
    form.value.description = res.data.description ?? '';
    startupSuccessfullyLoaded.value = true;
  } catch (e) {
    console.error('Помилка при завантаженні стартапу', e);
    if (e.response && e.response.status === 404) {
      initialLoadError.value = 'Стартап не знайдено.';
    } else if (e.response && e.response.status === 401 ) {
      initialLoadError.value = 'Помилка авторизації.';
      localStorage.removeItem('jwtToken');
      // router.push('/login'); // Замість прямого редиректу, можна показати модалку
      showNotificationModal('Помилка авторизації', 'Ваша сесія закінчилася. Будь ласка, увійдіть знову.', 'error', () => router.push('/login'));

    } else {
      initialLoadError.value = 'Не вдалося завантажити дані стартапу. Спробуйте оновити сторінку.';
    }
  } finally {
    loading.value = false;
  }
};

const updateStartup = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  formError.value = '';

  try {
    await axios.put(`http://localhost:8000/user/startup/${route.params.id}`, form.value, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    showNotificationModal('Успіх!', 'Зміни успішно збережено.', 'success', () => {
      router.push('/profile');
    });
  } catch (e) {
    console.error('Помилка при оновленні стартапу', e);
    let errorMessageText = 'Не вдалося зберегти зміни. Спробуйте ще раз.';
    if (e.response && e.response.data) {
      if (e.response.data.detail) {
        errorMessageText = Array.isArray(e.response.data.detail) ?
            e.response.data.detail.map(d => d.msg || d.message || d).join('; ') :
            e.response.data.detail;
      } else if (e.response.data.errors) {
        errorMessageText = e.response.data.errors.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
      }
    }
    showNotificationModal('Помилка збереження', errorMessageText, 'error');
    formError.value = errorMessageText; // Можна також відобразити у формі, якщо потрібно
  } finally {
    isSubmitting.value = false;
  }
};

const confirmDeleteStartupAction = () => { // Перейменовано з confirmDeleteStartup
  openModal({
    title: 'Видалити стартап?',
    message: 'Ви впевнені, що хочете видалити цей стартап? <br/> Усі пов\'язані з ним завдання, коментарі та інші дані також будуть видалені назавжди.',
    confirmButtonText: 'Видалити',
    cancelButtonText: 'Скасувати',
    type: 'confirm', // Явно вказуємо тип
    onConfirm: actualDeleteStartup // Змінено на actualDeleteStartup
  });
};

const actualDeleteStartup = async () => { // Нова функція для фактичного видалення
  if (isDeleting.value) return;
  isDeleting.value = true;
  closeModal(); // Закриваємо модалку підтвердження перед початком видалення
  try {
    await axios.delete(`http://localhost:8000/user/startup/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    showNotificationModal('Стартап видалено', 'Стартап та всі пов\'язані з ним дані було успішно видалено.', 'success', () => {
      router.push('/profile');
    });
  } catch (e) {
    console.error('Помилка при видаленні стартапу', e);
    showNotificationModal('Помилка видалення', e.response?.data?.detail || 'Не вдалося видалити стартап.', 'error');
  } finally {
    isDeleting.value = false;
  }
};

const goBack = () => {
  if (window.history.length > 2 && document.referrer.includes(window.location.host)) {
    router.go(-1);
  } else {
    router.push('/profile');
  }
};

onMounted(() => {
  if (!jwt) {
    router.push('/login'); // Якщо немає токена, одразу на логін
    return;
  }
  fetchStartup();
  document.addEventListener('keyup', handleGlobalEscEditStartup);
});

onUnmounted(() => {
  document.removeEventListener('keyup', handleGlobalEscEditStartup);
});

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.edit-startup-page {
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

.startup-card {
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

.startup-card h2 {
  font-size: 2rem;
  margin-bottom: 2.5rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.back-link {
  display: inline-block;
  margin-bottom: 2rem;
  color: #c0c5d0;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  padding: 0.3rem 0;
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.input-group {
  position: relative;
  margin-bottom: 1.8rem;
}

.input-group input[type="text"],
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
  transition: background-color 0.2s ease, border-color 0.2s ease;
}
.input-group textarea {
  min-height: 100px;
}

.input-group input[type="text"]::placeholder,
.input-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-group input[type="text"]:focus,
.input-group textarea:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
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
  margin-top: 0.5rem;
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

.delete-button {
  margin-top: 1.5rem;
  background-color: rgba(220, 53, 69, 0.7);
  border: none;
  padding: 0.9rem 1.5rem;
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  color: #ffffff;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.delete-button:hover:not(:disabled) {
  background-color: rgba(200, 33, 49, 0.85);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}
.delete-button:disabled {
  background-color: #8c3237;
  cursor: not-allowed;
  opacity: 0.7;
}

.error-message {
  color: #ffc2c2;
  background-color: rgba(255, 82, 82, 0.2);
  border: 1px solid rgba(255, 82, 82, 0.4);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}

.loading-placeholder {
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  padding: 2rem 0;
}

/* Стилі для універсального модального вікна */
.edit-startup-modal-overlay { /* Унікальний префікс */
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
  animation: fadeInOverlayEditStartup 0.2s forwards;
}

@keyframes fadeInOverlayEditStartup {
  to { opacity: 1; }
}

.edit-startup-modal-content {
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
  animation: scaleInModalEditStartup 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModalEditStartup {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.edit-startup-modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.edit-startup-modal-header-icon {
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}
.edit-startup-modal-header-icon.confirm {
  color: #f0b232;
}
.edit-startup-modal-header-icon.success {
  color: #28a745;
}
.edit-startup-modal-header-icon.error {
  color: #d83c3e;
}

.edit-startup-modal-content h4 {
  margin:0;
  font-size: 1.2em;
  color: #ffffff;
  font-weight: 600;
}

.edit-startup-modal-content p {
  margin-bottom: 25px;
  font-size: 1em;
  line-height: 1.65;
  color: #b9bbbe;
  word-break: break-word;
}

.edit-startup-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.edit-startup-modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.edit-startup-modal-button:active {
  transform: translateY(1px);
}

.edit-startup-modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.edit-startup-modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.edit-startup-modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.edit-startup-modal-button.cancel:hover {
  background-color: #5c626a;
}

.edit-startup-modal-button.ok {
  background-color: #007bff;
  color: white;
}
.edit-startup-modal-button.ok:hover {
  background-color: #0056b3;
}
.edit-startup-modal-button.error-ok {
  background-color: #d83c3e;
}
.edit-startup-modal-button.error-ok:hover {
  background-color: #bf3032;
}
</style>