<template>
  <main class="edit-task-page">
    <div class="task-card">
      <span class="back-link" @click="goBack">← Повернутися до профілю</span>

      <form class="task-form" @submit.prevent="updateTask" v-if="!loading && taskSuccessfullyLoaded">
        <h2>Редагувати завдання</h2>

        <div v-if="loadError" class="error-message">{{ loadError }}</div>

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
              rows="4"
          ></textarea>
        </div>

        <input type="submit" value="Зберегти зміни" :disabled="isSubmitting"/>
      </form>

      <div v-if="loading" class="loading-placeholder" style="color:white; margin-top: 2rem; text-align: center;">Завантаження даних завдання...</div>
      <div v-if="!loading && !taskSuccessfullyLoaded && !loadError" class="error-message">Не вдалося завантажити завдання.</div>


      <button class="delete-button" @click="confirmDeleteTaskAction" v-if="!loading && taskSuccessfullyLoaded" :disabled="isDeleting">
        {{ isDeleting ? 'Видалення...' : 'Видалити завдання' }}
      </button>
    </div>

    <div v-if="showModal" class="edit-task-modal-overlay" @click.self="cancelModalAction">
      <div class="edit-task-modal-content">
        <div class="edit-task-modal-header">
          <h4>
            <svg v-if="!modalConfig.isNotification" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="edit-task-modal-header-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <svg v-else :class="['edit-task-modal-header-icon', modalConfig.type === 'success' ? 'success' : 'error']" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
        <div class="edit-task-modal-actions">
          <button v-if="!modalConfig.isNotification" @click="cancelModalAction" class="edit-task-modal-button cancel">{{ modalConfig.cancelButtonText }}</button>
          <button @click="proceedWithModalAction" :class="['edit-task-modal-button', modalConfig.isNotification ? 'ok' : 'confirm', modalConfig.type === 'error' && modalConfig.isNotification ? 'error-ok' : '']">{{ modalConfig.confirmButtonText }}</button>
        </div>
      </div>
    </div>

  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const jwt = localStorage.getItem('jwtToken')

const form = ref({
  title: '',
  description: '',
})

const loading = ref(true)
const loadError = ref('') // Для помилки завантаження даних завдання
const taskSuccessfullyLoaded = ref(false);
const isSubmitting = ref(false);
const isDeleting = ref(false);


// --- Стан для універсального модального вікна ---
const showModal = ref(false)
const modalConfig = ref({
  title: '',
  message: '',
  isNotification: false,
  type: 'confirm', // 'confirm', 'success', 'error'
  confirmButtonText: 'Так',
  cancelButtonText: 'Скасувати',
  onConfirm: null,
  onCancel: null // Додамо для можливості кастомної дії при скасуванні/закритті
})
// --- Кінець стану для модального вікна ---

const openModal = (config) => {
  modalConfig.value = {
    ...modalConfig.value, // Зберігаємо дефолтні кнопки, якщо не передані нові
    isNotification: false, // За замовчуванням це підтвердження
    type: 'confirm',      // За замовчуванням тип 'confirm'
    ...config
  };
  showModal.value = true;
}

const showNotificationModal = (title, message, type = 'success', onOkCallback = null) => {
  openModal({
    title,
    message,
    isNotification: true,
    type: type, // 'success' або 'error'
    confirmButtonText: 'OK',
    onConfirm: onOkCallback // onConfirm тут буде дією для кнопки "ОК"
  });
}

const proceedWithModalAction = () => {
  if (typeof modalConfig.value.onConfirm === 'function') {
    modalConfig.value.onConfirm();
  }
  closeModal();
};

const cancelModalAction = () => {
  if (typeof modalConfig.value.onCancel === 'function') {
    modalConfig.value.onCancel();
  }
  closeModal();
};

const closeModal = () => {
  showModal.value = false;
  // Затримка для очищення конфігурації після анімації
  setTimeout(() => {
    if (!showModal.value) { // Перевіряємо, чи модалка все ще закрита
      modalConfig.value = { // Скидаємо до дефолтних значень
        title: '',
        message: '',
        isNotification: false,
        type: 'confirm',
        confirmButtonText: 'Так',
        cancelButtonText: 'Скасувати',
        onConfirm: null,
        onCancel: null
      };
    }
  }, 300);
};

const handleGlobalEscEditTask = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    cancelModalAction();
  }
};


const fetchTask = async () => {
  loading.value = true
  loadError.value = '';
  taskSuccessfullyLoaded.value = false;
  if (!jwt) {
    loadError.value = "Ви не авторизовані.";
    loading.value = false;
    // router.push('/login'); // Можна перенаправити
    return;
  }
  try {
    const res = await axios.get(`http://localhost:8000/user/task/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    form.value.title = res.data.title ?? ''
    form.value.description = res.data.description ?? ''
    taskSuccessfullyLoaded.value = true;
  } catch (e) {
    console.error('Помилка при завантаженні завдання', e)
    if (e.response && e.response.status === 404) {
      loadError.value = 'Завдання не знайдено.';
    } else if (e.response && e.response.status === 401) {
      loadError.value = 'Помилка авторизації.';
    } else {
      loadError.value = 'Не вдалося завантажити дані завдання.'
    }
  } finally {
    loading.value = false
  }
}

const updateTask = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  loadError.value = ''; // Скидаємо попередні помилки форми

  try {
    await axios.put(`http://localhost:8000/user/task/${route.params.id}`, form.value, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    showNotificationModal('Успіх!', 'Зміни успішно збережено.', 'success', () => {
      router.push('/profile');
    });
  } catch (e) {
    console.error('Помилка при оновленні завдання', e)
    let errorMessageText = e.response?.data?.detail || 'Не вдалося зберегти зміни. Спробуйте ще раз.';
    if (e.response?.data?.errors) { // Якщо є детальні помилки валідації
      errorMessageText = Object.values(e.response.data.errors).flat().join(' ');
    }
    showNotificationModal('Помилка збереження', errorMessageText, 'error');
  } finally {
    isSubmitting.value = false;
  }
}

const confirmDeleteTaskAction = () => {
  openModal({
    title: 'Видалити завдання?',
    message: 'Ви впевнені, що хочете видалити це завдання? <br/> Цю дію неможливо буде скасувати.',
    confirmButtonText: 'Видалити',
    cancelButtonText: 'Скасувати',
    type: 'confirm', // Явно вказуємо тип для кнопки підтвердження
    onConfirm: actualDeleteTask
  });
};

const actualDeleteTask = async () => {
  if (isDeleting.value) return;
  isDeleting.value = true;
  try {
    await axios.delete(`http://localhost:8000/user/task/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    showNotificationModal('Завдання видалено', 'Завдання було успішно видалено.', 'success', () => {
      router.push('/profile');
    });
  } catch (e) {
    console.error('Помилка при видаленні завдання', e)
    showNotificationModal('Помилка видалення', e.response?.data?.detail || 'Не вдалося видалити завдання.', 'error');
  } finally {
    isDeleting.value = false;
  }
}

const goBack = () => {
  // Перевірка, чи є куди повертатися в історії браузера
  if (window.history.length > 2 && document.referrer.includes(window.location.host)) {
    router.go(-1);
  } else {
    router.push('/profile'); // Запасний варіант, якщо немає історії або вона веде на інший сайт
  }
}

onMounted(() => {
  fetchTask();
  document.addEventListener('keyup', handleGlobalEscEditTask);
});

onUnmounted(() => {
  document.removeEventListener('keyup', handleGlobalEscEditTask);
});

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.edit-task-page {
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


.error-message { /* Для помилок валідації або завантаження форми */
  color: #ffc2c2;
  background-color: rgba(255, 82, 82, 0.2);
  border: 1px solid rgba(255, 82, 82, 0.4);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-bottom: 1.5rem; /* Або margin-top, залежно де відображається */
  text-align: center;
  font-size: 0.95rem;
}

.loading-placeholder { /* Стиль для тексту "Завантаження даних завдання..." */
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  padding: 2rem 0;
}


/* Стилі для універсального модального вікна */
.edit-task-modal-overlay { /* Змінено префікс для уникнення конфліктів */
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
  animation: fadeInOverlayEditTask 0.2s forwards;
}

@keyframes fadeInOverlayEditTask {
  to { opacity: 1; }
}

.edit-task-modal-content {
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
  animation: scaleInModalEditTask 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleInModalEditTask {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.edit-task-modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.edit-task-modal-header-icon {
  margin-right: 12px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}
/* Іконка за замовчуванням (попередження для confirm) */
.edit-task-modal-header-icon {
  color: #f0b232;
}
/* Іконка для успіху */
.edit-task-modal-header-icon.success {
  color: #28a745;
}
/* Іконка для помилки */
.edit-task-modal-header-icon.error {
  color: #d83c3e; /* Червоний, як кнопка confirm */
}


.edit-task-modal-content h4 {
  margin:0;
  font-size: 1.2em;
  color: #ffffff;
  font-weight: 600;
}

.edit-task-modal-content p {
  margin-bottom: 25px;
  font-size: 1em;
  line-height: 1.65;
  color: #b9bbbe;
  word-break: break-word;
}

.edit-task-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.edit-task-modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}
.edit-task-modal-button:active {
  transform: translateY(1px);
}

.edit-task-modal-button.confirm {
  background-color: #d83c3e;
  color: white;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.edit-task-modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0,0,0,0.25);
}

.edit-task-modal-button.cancel {
  background-color: #4f545c;
  color: #dcddde;
}
.edit-task-modal-button.cancel:hover {
  background-color: #5c626a;
}

.edit-task-modal-button.ok {
  background-color: #007bff;
  color: white;
}
.edit-task-modal-button.ok:hover {
  background-color: #0056b3;
}
/* Окремий стиль для кнопки ОК, якщо це сповіщення про помилку */
.edit-task-modal-button.error-ok {
  background-color: #d83c3e; /* Червоний, як кнопка confirm */
}
.edit-task-modal-button.error-ok:hover {
  background-color: #bf3032;
}
</style>