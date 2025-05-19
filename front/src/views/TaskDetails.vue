<template>
  <main class="task-detail-page">
    <div v-if="task" class="task-card">
      <button class="back-btn" @click="goBack">← Назад на головну</button>
      <h2 class="task-title">{{ task.title }}</h2>
      <p class="task-field"><strong>Опис:</strong> {{ task.description }}</p>
      <p class="task-field"><strong>Дата створення:</strong> {{ formattedCreatedAtDate }}</p>
      <p class="task-field"><strong>Автор:</strong> {{ task.owner_name }}</p>
      <div v-if="errorMessage" class="message-text error-text">{{ errorMessage }}</div>
      <div v-if="successMessage" class="message-text success-text">{{ successMessage }}</div>

      <div class="action-buttons-container">
        <button
            v-if="task.status === 'pending'"
            class="take-btn"
            @click="takeTask"
            :disabled="isTakingTask"
        >
          {{ isTakingTask ? 'Обробка...' : 'Взяти завдання' }}
        </button>

        <p v-if="task.status === 'in_progress' && !successMessage && !errorMessage" class="info-text">
          Завдання вже виконується.
        </p>
        <p v-if="task.status === 'done'" class="info-text">
          Завдання виконано та очікує на оплату.
        </p>
        <p v-if="task.status === 'paid'" class="info-text">
          Завдання виконано та оплачено.
        </p>

        <button
            class="contact-btn"
            @click="contactOwner"
            :disabled="isCreatingChat"
        >
          {{ isCreatingChat ? 'Створення чату...' : 'Зв\'язатися з замовником' }}
        </button>
      </div>
    </div>

    <div v-else-if="initialLoadingError" class="loading-text">
      <p class="error-text">{{ initialLoadingError }}</p>
      <button class="back-btn" @click="goBack" style="margin-top: 1rem;">← Назад на головну</button>
    </div>
    <div v-else class="loading-text">
      <p>Завантаження детальної інформації про завдання...</p>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const task = ref(null);
const jwt = ref(localStorage.getItem('jwtToken'));
const errorMessage = ref('');
const successMessage = ref('');
const initialLoadingError = ref('');

const isTakingTask = ref(false);
const isCreatingChat = ref(false);
// const user = ref(null); // Більше не потрібен для логіки видимості кнопок

// Форматування дати створення завдання
const formattedCreatedAtDate = computed(() => {
  if (task.value && task.value.created_at) {
    return new Date(task.value.created_at).toLocaleDateString('uk-UA', {
      year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
  return '';
});

// async function fetchCurrentUser() { // Більше не потрібна
// }

// const canTakeTask = computed(() => { // Умова перенесена в v-if
//   if (!task.value) return false;
//   return task.value.status === 'pending';
// });

// const canContactOwner = computed(() => { // Кнопка видима завжди, якщо є task
//   return !!task.value;
// });

// Завантаження даних завдання
async function fetchTask() {
  initialLoadingError.value = '';
  if (!jwt.value) {
    initialLoadingError.value = "Ви не авторизовані. Будь ласка, увійдіть до системи.";
    setTimeout(() => router.push('/login'), 3000);
    return;
  }
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${route.params.id}`, {
      headers: {
        Authorization: `Bearer ${jwt.value}`,
      },
    });
    task.value = response.data;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    if (error.response) {
      if (error.response.status === 404) {
        initialLoadingError.value = "Завдання не знайдено.";
      } else if (error.response.status === 401) {
        initialLoadingError.value = "Помилка авторизації. Спробуйте увійти знову.";
        localStorage.removeItem('jwtToken');
        setTimeout(() => router.push('/login'), 3000);
      } else {
        initialLoadingError.value = "Не вдалося завантажити завдання. Спробуйте оновити сторінку.";
      }
    } else {
      initialLoadingError.value = "Не вдалося завантажити завдання. Перевірте з'єднання.";
    }
  }
}

// Взяти завдання
async function takeTask() {
  if (!jwt.value) {
    errorMessage.value = "Не знайдено JWT користувача. Перевірте, чи ви авторизовані.";
    return;
  }
  // Додаткова перевірка на статус, хоча кнопка і так не має рендеритись
  if (task.value && task.value.status !== 'pending') {
    errorMessage.value = "Це завдання вже не доступне для взяття.";
    return;
  }


  errorMessage.value = '';
  successMessage.value = '';
  isTakingTask.value = true;

  try {
    await axios.post(`http://localhost:8000/tasks/${route.params.id}/take`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`,
      },
    });

    // Оновлюємо локально для швидкого візуального відгуку
    // В ідеалі, бекенд має повертати оновлене завдання
    if (task.value) {
      task.value.status = "in_progress";
      // Якщо бекенд повертає ID виконавця, можна його теж оновити
      // task.value.executor_id = decoded_jwt_user_id; // Потрібно було б мати ID поточного користувача
    }
    successMessage.value = `Ви успішно взяли завдання: "${task.value?.title || ''}"!`;

    // Опціонально: перезавантажити дані завдання для актуальності
    // await fetchTask();

    setTimeout(() => {
      successMessage.value = '';
    }, 5000);

  } catch (error) {
    console.error('Помилка при взятті завдання:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = "Не вдалося взяти завдання. Можливо, воно вже зайняте або сталася помилка на сервері.";
    }
  } finally {
    isTakingTask.value = false;
  }
}

// Зв'язатися з замовником (створити/знайти чат)
async function contactOwner() {
  if (!task.value || !task.value.id) { // Перевіряємо, чи завантажено завдання
    errorMessage.value = "Інформація про завдання недоступна для створення чату.";
    return;
  }
  if (!jwt.value) {
    errorMessage.value = "Ви не авторизовані для цієї дії.";
    return;
  }

  errorMessage.value = '';
  successMessage.value = '';
  isCreatingChat.value = true;

  try {
    const response = await axios.post(`http://localhost:8000/chats/with-owner/${task.value.id}`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`
      }
    });

    const chatId = response.data.chat_id;
    router.push(`/chats/${chatId}`);
  } catch (error) {
    console.error('Не вдалося створити або знайти чат:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail; // Бекенд обробить випадок "Cannot create chat with yourself"
    } else {
      errorMessage.value = "Не вдалося зв'язатися із замовником. Спробуйте пізніше.";
    }
  } finally {
    isCreatingChat.value = false;
  }
}

// Повернутися назад
function goBack() {
  if (window.history.length > 2) {
    router.go(-1);
  } else {
    router.push('/main-page'); // Або інший дефолтний маршрут
  }
}

// Хук життєвого циклу onMounted
onMounted(async () => {
  // await fetchCurrentUser(); // Більше не викликаємо
  await fetchTask();      // Завантажуємо тільки завдання
});
</script>

<style scoped>
/* Ваші стилі залишаються без змін */
.task-detail-page {
  padding: 2rem;
  padding-top: 100px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url('../assets/img.jpg'); /* Переконайтеся, що шлях правильний */
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  color: #f0f0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.back-btn {
  display: inline-block;
  margin-bottom: 1.5rem;
  background: none;
  border: none;
  color: #b0b8c5;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  padding: 0.2rem 0;
  transition: color 0.2s ease;
  align-self: flex-start;
}

.back-btn:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-card {
  background: rgba(30, 25, 45, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 2.2rem 2.5rem;
  border-radius: 18px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 650px;
  margin: 2rem auto;
  text-align: left;
}

.task-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.8rem;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.task-field {
  margin-bottom: 1.1rem;
  color: #dfe2e8;
  line-height: 1.6;
  font-size: 1rem;
}

.task-field strong {
  color: #f8f9fa;
  font-weight: 600;
  margin-right: 0.6em;
}

.action-buttons-container {
  margin-top: 2.2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.take-btn, .contact-btn {
  display: block;
  width: 100%;
  padding: 0.9rem 1.5rem;
  font-size: 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  border: none;
  color: white;
  text-align: center;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}
.take-btn:hover:not(:disabled), .contact-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.take-btn {
  background-color: #007AFF;
}
.take-btn:hover:not(:disabled) {
  background-color: #005bb5;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}
.take-btn:disabled {
  background-color: #5a6268;
  color: #adafaf;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}


.contact-btn {
  background-color: #9326C6;
}
.contact-btn:hover:not(:disabled) {
  background-color: #7a1fcf;
  box-shadow: 0 4px 12px rgba(147, 38, 198, 0.4);
}
.contact-btn:disabled {
  background-color: #714883;
  color: #adafaf;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}


.message-text {
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  text-align: center;
  font-size: 0.95rem;
  width: 100%;
  box-sizing: border-box;
}

.error-text {
  color: #ffc2c2;
  background-color: rgba(255, 82, 82, 0.2);
  border: 1px solid rgba(255, 82, 82, 0.4);
}

.success-text {
  color: #c2ffc2;
  background-color: rgba(82, 200, 82, 0.2);
  border: 1px solid rgba(82, 200, 82, 0.4);
}

.info-text {
  color: #b0b8c5;
  margin-top: 1rem;
  text-align: center;
  font-size: 0.95rem;
  padding: 0.5rem;
  background-color: rgba(80, 80, 100, 0.15);
  border-radius: 6px;
}


.loading-text {
  text-align: center;
  font-size: 1.2rem;
  color: #b0b8c5;
  margin-top: 4rem;
  width: 100%;
}
.loading-text p {
  margin-bottom: 1rem;
}
.loading-text .error-text {
  display: inline-block;
  width: auto;
  max-width: 90%;
}
</style>