<template>
  <main class="create-task-page">
    <div class="task-card">
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

      <form class="task-form" @submit.prevent="submitTask">
        <h2>Створити завдання</h2>

        <div v-if="formError" class="error-message">{{ formError }}</div>

        <div class="input-group">
          <input
              type="text"
              placeholder="Назва завдання"
              v-model="form.title"
              required
          />
        </div>

        <div class="input-group">
          <textarea
              placeholder="Опис завдання"
              v-model="form.description"
              required
              rows="6"
          ></textarea>
        </div>

        <input type="submit" value="Створити завдання" :disabled="isSubmitting" />
      </form>
    </div>

    <div v-if="showModal" class="create-task-modal-overlay" @click.self="cancelModalAction">
      <div class="create-task-modal-content">
        <div class="create-task-modal-header">
          <h4>
            <svg :class="['create-task-modal-header-icon', modalConfig.type]" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
        <div class="create-task-modal-actions">
          <button v-if="!modalConfig.isNotification" @click="cancelModalAction" class="create-task-modal-button cancel">{{ modalConfig.cancelButtonText }}</button>
          <button @click="proceedWithModalAction" :class="['create-task-modal-button', modalConfig.isNotification ? (modalConfig.type === 'error' ? 'error-ok' : 'ok') : 'confirm']">{{ modalConfig.confirmButtonText }}</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue' // Додано onUnmounted
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const jwt = localStorage.getItem('jwtToken')

const form = ref({
  title: '',
  description: '',
  startup_id: parseInt(route.query.startup_id)
})

const formError = ref(''); // Для помилок валідації форми або інших помилок при сабміті
const isSubmitting = ref(false);

// --- Стан для універсального модального вікна ---
const showModal = ref(false);
const modalConfig = ref({
  title: '',
  message: '',
  isNotification: false,
  type: 'confirm', // 'confirm', 'success', 'error'
  confirmButtonText: 'Так',
  cancelButtonText: 'Скасувати',
  onConfirm: null,
  onCancel: null
});
// --- Кінець стану для модального вікна ---

const openModal = (config) => {
  modalConfig.value = {
    title: '',
    message: '',
    isNotification: false,
    type: 'confirm',
    confirmButtonText: 'Так',
    cancelButtonText: 'Скасувати',
    onConfirm: null,
    onCancel: null,
    ...config
  };
  showModal.value = true;
};

const showNotificationModal = (title, message, type = 'success', onOkCallback = null) => {
  openModal({
    title,
    message,
    isNotification: true,
    type: type,
    confirmButtonText: 'OK',
    onConfirm: onOkCallback || closeModal
  });
};

const proceedWithModalAction = () => {
  if (typeof modalConfig.value.onConfirm === 'function') {
    modalConfig.value.onConfirm();
  }
  // Закриваємо тільки якщо це сповіщення, для confirm закриття буде в onConfirm або onCancel
  if (modalConfig.value.isNotification) {
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

const handleGlobalEscCreateTask = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    cancelModalAction();
  }
};

const submitTask = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  formError.value = ''; // Скидаємо попередні помилки

  if (!form.value.startup_id || isNaN(form.value.startup_id)) {
    formError.value = 'Не вдалося визначити ID стартапу. Спробуйте створити завдання зі сторінки стартапу.';
    showNotificationModal('Помилка', formError.value, 'error');
    isSubmitting.value = false;
    return;
  }

  try {
    await axios.post('http://localhost:8000/create_task/', form.value, {
      headers: {
        Authorization: `Bearer ${jwt}`
      }
    });
    showNotificationModal('Успіх!', 'Завдання успішно створено.', 'success', () => {
      router.push('/profile'); // Редирект після натискання "ОК" на модалці
    });
    // Очищаємо форму після успішного створення, якщо користувач не переходить одразу
    form.value.title = '';
    form.value.description = '';

  } catch (error) {
    console.error('Помилка створення завдання:', error);
    let errorMessageText = 'Не вдалося створити завдання. Спробуйте ще раз.';
    if (error.response && error.response.data) {
      if (error.response.data.detail) {
        errorMessageText = error.response.data.detail;
      } else if (error.response.data.errors) {
        errorMessageText = error.response.data.errors.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
      }
    }
    showNotificationModal('Помилка створення', errorMessageText, 'error');
    formError.value = errorMessageText; // Можна також показувати помилку біля форми
  } finally {
    isSubmitting.value = false;
  }
};

const goToProfile = () => {
  router.push('/profile');
};

onMounted(() => {
  if (!jwt) {
    router.push('/login');
  }
  if (!form.value.startup_id || isNaN(form.value.startup_id)) {
    console.warn('Startup ID is missing or invalid from query params.');
    // Можна показати помилку користувачу або перенаправити
    showNotificationModal(
        'Помилка',
        'Необхідний ID стартапу для створення завдання. Будь ласка, спробуйте створити завдання зі сторінки відповідного стартапу.',
        'error',
        goToProfile // Перенаправити в профіль по кліку "ОК"
    );
  }
  document.addEventListener('keyup', handleGlobalEscCreateTask);
});

onUnmounted(() => {
  document.removeEventListener('keyup', handleGlobalEscCreateTask);
});

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.create-task-page {
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
  max-width: 500px;
  color: #f0f0f0;
  text-align: left;
}

.task-card h2 {
  font-size: 2rem;
  margin-bottom: 2.2rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
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
  min-height: 120px; /* Збільшена мінімальна висота */
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

.error-message { /* Для помилок валідації форми */
  color: #ffc2c2;
  background-color: rgba(255, 82, 82, 0.2);
  border: 1px solid rgba(255, 82, 82, 0.4);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}

/* Стилі для універсального модального вікна */
.create-task-modal-overlay { /* Унікальний префікс */
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
  animation: fadeInOverlayCreateTask 0.2s forwards;
}

@keyframes fadeInOverlayCreateTask {
  to { opacity: 1; }
}

.create-task-modal-content {
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
  animation: scaleInModalCreateTask 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModalCreateTask {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.create-task-modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.create-task-modal-header-icon {
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}
.create-task-modal-header-icon.confirm { /* За замовчуванням - попередження */
  color: #f0b232;
}
.create-task-modal-header-icon.success {
  color: #28a745;
}
.create-task-modal-header-icon.error {
  color: #d83c3e;
}

.create-task-modal-content h4 {
  margin:0;
  font-size: 1.2em;
  color: #ffffff;
  font-weight: 600;
}

.create-task-modal-content p {
  margin-bottom: 25px;
  font-size: 1em;
  line-height: 1.65;
  color: #b9bbbe;
  word-break: break-word;
}

.create-task-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.create-task-modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.create-task-modal-button:active {
  transform: translateY(1px);
}

.create-task-modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.create-task-modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.create-task-modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.create-task-modal-button.cancel:hover {
  background-color: #5c626a;
}

.create-task-modal-button.ok {
  background-color: #007bff;
  color: white;
}
.create-task-modal-button.ok:hover {
  background-color: #0056b3;
}
.create-task-modal-button.error-ok {
  background-color: #d83c3e;
}
.create-task-modal-button.error-ok:hover {
  background-color: #bf3032;
}

</style>