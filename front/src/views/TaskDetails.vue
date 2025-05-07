<template>
  <main class="task-detail-page">
    <button class="back-btn" @click="goBack">← Назад на головну</button>

    <div v-if="task" class="task-card">
      <h2 class="task-title">{{ task.title }}</h2>
      <p class="task-field"><strong>Опис:</strong> {{ task.description }}</p>
      <p class="task-field"><strong>Дата створення:</strong> {{ task.created_at }}</p>
      <p class="task-field"><strong>Автор:</strong> {{ task.owner_name }}</p>

      <button v-if="task.status === 'pending'" class="take-btn" @click="takeTask">Взяти завдання</button>
      <p v-if="task.status === 'in_progress'" class="error-text">Завдання вже взято!</p>
      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <!-- Кнопка для зв'язку з замовником -->
      <button v-if="task.status === 'pending'" class="contact-btn" @click="contactOwner">Зв'язатися з замовником</button>
    </div>

    <div v-else class="loading-text">
      <p>Завантаження...</p>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const task = ref(null);
const jwt = ref(localStorage.getItem('jwtToken')); // JWT з localStorage
const errorMessage = ref('');

// Функція для отримання завдання
async function fetchTask() {
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${route.params.id}`, {
      headers: {
        Authorization: `Bearer ${jwt.value}`, // Використовуємо JWT з localStorage
      },
    });
    task.value = response.data;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    errorMessage.value = "Помилка при завантаженні завдання.";
  }
}

// Функція для взяття завдання
async function takeTask() {
  if (!jwt.value) {
    errorMessage.value = "Не знайдено JWT користувача. Перевірте, чи ви авторизовані.";
    return;
  }

  if (task.value.status === 'in_progress') {
    errorMessage.value = "Завдання вже взято!";
    return;
  }

  try {
    const response = await axios.post(`http://localhost:8000/tasks/${route.params.id}/take`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`, // Використовуємо JWT
      },
    });

    // Оновлюємо локальний статус завдання після успішного виконання запиту
    task.value.status = "in_progress";

    alert(`Ви взяли завдання: ${task.value.title}`);
  } catch (error) {
    console.error('Помилка при взятті завдання:', error);
    errorMessage.value = "Не вдалося взяти завдання.";
  }
}

// Функція для зв'язку з замовником
function contactOwner() {
  const email = task.value.owner_email;
  if (email) {
    window.location.href = `mailto:${email}`;
  } else {
    errorMessage.value = "Email замовника не вказано.";
  }
}

// Функція для переходу назад на головну
function goBack() {
  router.push('/main-page');
}

onMounted(fetchTask);
</script>

<style scoped>
.task-detail-page {
  padding: 2rem;
  font-family: 'Segoe UI', sans-serif;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  min-height: 100vh;
  color: white;
}

.back-btn {
  margin-bottom: 1.5rem;
  background: none;
  border: none;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
}

.task-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  padding: 2rem;
  border-radius: 15px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  margin: 0 auto;
}

.task-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #fff;
}

.task-field {
  margin-bottom: 0.8rem;
  color: #eee;
  line-height: 1.5;
}

.take-btn {
  margin-top: 1.2rem;
  background: transparent;
  color: white;
  padding: 0.8rem 1.5rem;
  font-size: 1rem;
  border: 2px solid white;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.3s ease, color 0.3s ease;
}

.take-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #8ecfff;
}

.contact-btn {
  margin-top: 1.2rem;
  margin-left: 10px;
  background: transparent;
  color: white;
  padding: 0.8rem 1.5rem;
  font-size: 1rem;
  border: 2px solid white;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.3s ease, color 0.3s ease;
}

.contact-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #8ecfff;
}

.error-text {
  color: red;
  margin-top: 10px;
}

.loading-text {
  text-align: center;
  font-size: 1.2rem;
  color: #ccc;
}
</style>
