<template>
  <main class="task-result-page">
    <div class="task-result-card">
      <!-- Додаємо кнопку для повернення до профілю -->
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

      <h2>Результат завдання</h2>

      <div v-if="result">
        <div class="result-block">
          <h3>{{ result.title }}</h3>
          <p>{{ result.description }}</p>
          <p><strong>Результат виконання:</strong> {{ result.executionResult }}</p>
        </div>

        <div class="input-group">
          <div class="rating-container">
            <label for="rating">Оцінка:</label>
            <select id="rating" v-model="rating">
              <option v-for="i in 5" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
        </div>

        <button class="submit-btn" @click="submitRating">Подати оцінку</button>
      </div>

      <div v-else>
        <p>Завантаження результатів...</p>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface TaskResult {
  title: string;
  description: string;
  executionResult: string;
}

const route = useRoute()
const router = useRouter()  // Ініціалізуємо router

const taskId = route.params.taskId
const result = ref<TaskResult | null>(null)
const rating = ref<number>(0)

const token = localStorage.getItem('jwt_token')

if (!token) {
  console.error('Токен не знайдено!')
}

const fetchTaskResult = async () => {
  try {
    const res = await axios.get(`http://localhost:8000/user/${taskId}/result`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    result.value = res.data
  } catch (e) {
    console.error('Не вдалося завантажити результат завдання', e)
  }
}

const submitRating = async () => {
  try {
    const response = await axios.post(`http://localhost:8000/user/${taskId}/rate`,
        { rating: rating.value },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
    console.log('Оцінка подана успішно:', response.data)

    // Перекидаємо на сторінку профілю
    router.push('/profile')

  } catch (e) {
    console.error('Не вдалося подати оцінку', e)
  }
}

const goToProfile = () => {
  router.push('/profile')  // Повертаємо на сторінку профілю
}

onMounted(() => {
  fetchTaskResult()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.task-result-page {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(to bottom, #2b1055, #7597de);
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

.task-result-card {
  background: rgba(30, 25, 45, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.2rem; /* Трохи зменшено падінг для компактності */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 580px; /* Трохи скориговано */
  color: #f0f0f0;
  text-align: center;
}

.back-link {
  display: block;
  margin-bottom: 1.5rem; /* Відступ перед головним заголовком */
  color: #b0b8c5;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.2s ease;
  text-align: left;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-result-card h2 { /* "Результат завдання" */
  font-size: 1.8rem; /* Трохи менший головний заголовок */
  margin-bottom: 1.8rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.result-block {
  margin-bottom: 1.8rem; /* Відступ після блоку результатів */
  /* border-bottom: 1px solid rgba(255, 255, 255, 0.08); */ /* Прибрано межу, використовуємо відступи */
  /* padding-bottom: 1.2rem; */
}

.result-block h3 { /* Назва завдання */
  font-size: 1.3rem; /* Менший, ніж h2 */
  margin-bottom: 0.8rem;
  font-weight: 600; /* Можна 500 для меншого акценту */
  color: #e8e9ed;
  text-align: center; /* Назва завдання зліва */
  line-height: 1.4;
}

.result-block p {
  font-size: 0.95rem; /* Трохи менший текст опису */
  color: #d5d8de;
  margin-bottom: 0.6rem;
  line-height: 1.6;
}
.result-block p strong {
  color: #f0f0f0;
  font-weight: 600;
}

/* Секція оцінки - робимо її більш інтегрованою */
.input-group { /* Цей div вже центрує вміст через flex у вашому HTML/CSS */
  margin-top: 1rem;
  margin-bottom: 1.8rem;
  display: flex; /* Залишаємо для центрування .rating-container */
  justify-content: center;
  align-items: center;
}

.rating-container {
  display: flex;
  align-items: center;
  gap: 0.8rem; /* Проміжок між "Оцінка:" та select */
  /* Забираємо фон та межу з .rating-container, стилізуємо label та select окремо */
}

.rating-container label {
  color: #d5d8de;
  font-weight: 500;
  font-size: 1rem;
}

.rating-container select {
  width: auto;
  min-width: 60px; /* Мінімальна ширина */
  padding: 0.6rem 0.8rem;
  border-radius: 8px; /* Менший радіус для select */
  background: rgba(255, 255, 255, 0.1); /* Схоже на інші поля вводу */
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #2c63a6;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}
.rating-container select:focus {
  border-color: rgba(255,255,255,0.4);
  background-color: rgba(255,255,255,0.15);
}

.submit-btn { /* Кнопка "Подати оцінку" */
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  /* width: 100%; -- Забираємо, щоб кнопка не була на всю ширину */
  display: block; /* Для центрування через margin:auto */
  margin: 1.5rem auto 0; /* Відступ зверху, центрування */
  min-width: 200px; /* Мінімальна ширина */
  width: auto; /* Ширина по контенту + падінги */
  max-width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.submit-btn:hover {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

/* Стиль для тексту завантаження */
div > p[data-loading-text="true"] { /* Якщо ви додасте data- атрибут до <p>Завантаження...</p> */
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  margin-top: 2rem;
}
/* Або якщо текст завжди однаковий: */
.task-result-card div > p:first-child:last-child { /* Спроба вибрати <p>Завантаження...</p> якщо він єдиний дочірній */
  color: #b0b8c5;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  margin-top: 2rem;
}

</style>
