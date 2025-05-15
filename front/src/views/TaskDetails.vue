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
            v-if="canContactOwner"
            class="contact-btn"
            @click="contactOwner"
            :disabled="isCreatingChat"
        >
          {{ isCreatingChat ? 'Створення чату...' : 'Зв\'язатися з замовником' }}
        </button>
      </div>
    </div>

    <div v-else-if="initialLoadingError" class="loading-text"> <p class="error-text">{{ initialLoadingError }}</p>
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
const initialLoadingError = ref(''); // Окрема помилка для початкового завантаження

const isTakingTask = ref(false); // Стан для блокування кнопки "Взяти завдання" під час запиту
const isCreatingChat = ref(false); // Стан для блокування кнопки "Зв'язатися" під час запиту

// Покращене форматування дати
const formattedCreatedAtDate = computed(() => {
  if (task.value && task.value.created_at) {
    return new Date(task.value.created_at).toLocaleDateString('uk-UA', {
      year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
  return '';
});

// Визначаємо, чи може користувач зв'язатися з замовником
// Наприклад, якщо завдання ще не взято, або якщо поточний користувач не є автором завдання
const canContactOwner = computed(() => {
  if (!task.value || !user.value) return false;
  // Припускаємо, що у вас є інформація про поточного користувача, наприклад, user.value.id
  // і що task.value.owner_id містить ID автора завдання
  // return task.value.owner_id !== user.value.id; // Приклад: не автор може зв'язатися
  return true; // Поки що дозволяємо завжди, якщо завдання завантажено
});

// Якщо потрібно отримати ID поточного користувача (припускаємо, що він є в JWT або окремому запиті)
const user = ref(null); // Можна завантажувати дані користувача, якщо потрібно для логіки

async function fetchCurrentUser() { // Опціональна функція
  if (!jwt.value) return;
  try {
    // Запит до ендпоінта, який повертає дані поточного користувача
    // const response = await axios.get('http://localhost:8000/users/me', {
    //   headers: { Authorization: `Bearer ${jwt.value}` }
    // });
    // user.value = response.data;
  } catch (error) {
    console.error("Failed to fetch current user", error);
  }
}


async function fetchTask() {
  initialLoadingError.value = '';
  if (!jwt.value) {
    initialLoadingError.value = "Ви не авторизовані. Будь ласка, увійдіть до системи.";
    // Можна додати затримку перед перенаправленням, щоб користувач встиг прочитати
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
    if (error.response && error.response.status === 404) {
      initialLoadingError.value = "Завдання не знайдено.";
    } else if (error.response && error.response.status === 401) {
      initialLoadingError.value = "Помилка авторизації. Спробуйте увійти знову.";
      localStorage.removeItem('jwtToken'); // Видаляємо невалідний токен
      setTimeout(() => router.push('/login'), 3000);
    }
    else {
      initialLoadingError.value = "Не вдалося завантажити завдання. Спробуйте оновити сторінку.";
    }
  }
}

async function takeTask() {
  if (!jwt.value) {
    errorMessage.value = "Не знайдено JWT користувача. Перевірте, чи ви авторизовані.";
    successMessage.value = '';
    return;
  }

  errorMessage.value = '';
  successMessage.value = '';
  isTakingTask.value = true;

  try {
    const response = await axios.post(`http://localhost:8000/tasks/${route.params.id}/take`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`,
      },
    });

    if (task.value) {
      task.value.status = "in_progress";
      // Якщо бекенд повертає оновлене завдання, краще використовувати його:
      // task.value = response.data.updated_task; (якщо така структура відповіді)
    }

    successMessage.value = `Ви успішно взяли завдання: "${task.value?.title || ''}"!`;

    setTimeout(() => {
      successMessage.value = '';
    }, 5000);

  } catch (error) {
    console.error('Помилка при взятті завдання:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = "Не вдалося взяти завдання. Можливо, воно вже зайняте або сталася помилка.";
    }
    // Якщо завдання вже взято, оновимо статус локально, якщо можливо
    if (error.response && error.response.status === 400 && task.value) {
      // Можливо, бекенд повертає актуальний статус або це потрібно перезавантажити
      // fetchTask(); // можна перезавантажити дані завдання
    }
  } finally {
    isTakingTask.value = false;
  }
}

async function contactOwner() {
  if (!task.value || !task.value.id) {
    errorMessage.value = "Інформація про завдання недоступна для створення чату.";
    return;
  }
  if (!jwt.value) {
    errorMessage.value = "Ви не авторизовані.";
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
    console.error('Не вдалося створити чат:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = "Не вдалося зв'язатися із замовником. Спробуйте пізніше.";
    }
  } finally {
    isCreatingChat.value = false;
  }
}

function goBack() {
  // Можна повернутися на попередню сторінку, якщо вона відома, або на головну
  if (window.history.length > 2) { // Перевірка, чи є куди повертатися в історії
    router.go(-1);
  } else {
    router.push('/main-page');
  }
}

onMounted(() => {
  fetchCurrentUser(); // Опціонально, якщо потрібні дані користувача для логіки
  fetchTask();
});
</script>

<style scoped>
.task-detail-page {
  padding: 2rem;
  padding-top: 100px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  color: #f0f0f0;
  display: flex; /* Для центрування .task-card або .loading-text */
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
  align-self: flex-start; /* Вирівнювання кнопки "Назад" по лівому краю картки */
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
  max-width: 650px; /* Трохи ширше для кращого вигляду */
  margin: 2rem auto; /* Відступи зверху/знизу та центрування */
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
  margin-bottom: 0.5rem; /* Відступ знизу, якщо є кнопки після */
  text-align: center;
  font-size: 0.95rem;
  width: 100%;
  box-sizing: border-box;
}

.error-text {
  color: #ffc2c2; /* Світліший червоний для тексту */
  background-color: rgba(255, 82, 82, 0.2); /* Трохи насиченіший фон */
  border: 1px solid rgba(255, 82, 82, 0.4);
}

.success-text {
  color: #c2ffc2; /* Світліший зелений */
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
  font-size: 1.2rem; /* Збільшено для кращої видимості */
  color: #b0b8c5;
  margin-top: 4rem; /* Збільшено відступ */
  width: 100%;
}
.loading-text p {
  margin-bottom: 1rem;
}
.loading-text .error-text { /* Щоб помилка завантаження була теж по центру */
  display: inline-block; /* Або display: block; margin: 0 auto; */
  width: auto;
  max-width: 90%;
}
</style>