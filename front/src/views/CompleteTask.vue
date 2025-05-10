<template>
  <main class="task-page">
    <div class="task-card">
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

      <form class="task-form" @submit.prevent="submitCompletion">
        <h2>Виконати завдання</h2>

        <h3 class="task-title">{{ taskTitle }}</h3>

        <div class="input-group">
          <textarea
              v-model="completionText"
              placeholder="Опишіть виконання завдання..."
              required
          ></textarea> </div>

        <input type="submit" value="Надіслати" />

        <p class="error" v-if="errorMessage">{{ errorMessage }}</p>
      </form>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const taskId = route.params.taskId;
const completionText = ref('');
const errorMessage = ref('');
const taskTitle = ref('');
const jwt = localStorage.getItem('jwtToken');

// Отримати дані про завдання
const fetchTask = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    taskTitle.value = response.data.title;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    errorMessage.value = 'Не вдалося завантажити завдання';
  }
};

onMounted(fetchTask);

const submitCompletion = async () => {
  try {
    await axios.post(`http://localhost:8000/tasks/${taskId}/complete`, { execution_description: completionText.value }, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    router.push('/profile');
  } catch (error) {
    errorMessage.value = 'Помилка при надсиланні результату завдання';
    console.error(error);
  }
};

// ДОДАНО ФУНКЦІЮ ДЛЯ ПОВЕРНЕННЯ НА СТОРІНКУ ПРОФІЛЮ
const goToProfile = () => {
  router.push('/profile');
};
</script>


<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.task-page {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(to bottom, #2b1055, #7597de); /* Запасний фон */
  background-image: url('../assets/img.jpg'); /* Переконайтеся, що шлях правильний */
  background-size: cover;
  background-position: center;
  background-attachment: fixed; /* Фіксований фон */
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: #f0f0f0; /* Основний світлий колір тексту */
}

.task-card {
  background: rgba(30, 25, 45, 0.85); /* Темний, насичений фон картки */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem 3rem; /* Збалансовані падінги */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45); /* Глибша тінь */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла межа */
  width: 100%;
  max-width: 550px;
  color: #f0f0f0;
  text-align: left; /* Вирівнювання по лівому краю для вмісту форми */
}

/* СТИЛЬ ДЛЯ ПОСИЛАННЯ "ПОВЕРНУТИСЯ В ПРОФІЛЬ" */
.back-link {
  display: inline-block;
  margin-bottom: 1.8rem; /* Відступ знизу перед заголовком h2 */
  color: #b0b8c5; /* Світло-сіро-блакитний для посилань */
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  padding: 0.2rem 0; /* Мінімальний падінг для текстового посилання */
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-form h2 { /* Головний заголовок форми "Виконати завдання" */
  font-size: 2rem;
  margin-bottom: 1.2rem; /* Відступ до назви завдання */
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

/* Стиль для назви конкретного завдання */
.task-title {
  font-size: 1.25rem;
  margin-bottom: 1.8rem; /* Відступ до поля вводу */
  font-weight: 500;
  color: #e0e1e6; /* Світло-сірий */
  text-align: center; /* Також по центру */
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.input-group {
  position: relative;
  margin-bottom: 2rem; /* Більший відступ після textarea */
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
  min-height: 150px;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.input-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-group textarea:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

input[type="submit"] { /* Кнопка "Надіслати" */
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

input[type="submit"]:hover {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.error { /* Стиль для повідомлення про помилку */
  margin-top: 1.5rem;
  color: #ff9a9a;
  background-color: rgba(255, 82, 82, 0.15);
  border: 1px solid rgba(255, 82, 82, 0.35);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 500;
}
</style>

