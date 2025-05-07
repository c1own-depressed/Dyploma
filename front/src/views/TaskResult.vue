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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

.task-result-page {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(to bottom, #2b1055, #7597de);
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.task-result-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 3rem 2.5rem;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.4);
  width: 100%;
  max-width: 500px;
  color: white;
  text-align: center;
}

h2 {
  font-size: 2rem;
  margin-bottom: 2rem;
  font-weight: 600;
}

h3 {
  font-size: 1.4rem;
  margin-bottom: 1rem;
  font-weight: 600;
  color: #fff;
}

p {
  font-size: 1rem;
  color: #ccc;
  margin-bottom: 1rem;
}

.input-group {
  margin-top: 1.5rem;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.input-group label {
  margin-right: 1rem;
  color: #ddd;
}

select {
  width: 60px;
  padding: 0.6rem 1rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #7ae3f8;
  font-size: 1rem;
}

.submit-btn {
  margin-top: 1.5rem;
  padding: 0.75rem 2rem;
  background-color: transparent;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s ease;
}

.submit-btn:hover {
  background-color: #9326c6;
}

.back-link {
  display: inline-block;
  margin-bottom: 1rem;
  color: #ffffff;
  cursor: pointer;
  font-weight: 600;
  text-align: left;
  transition: color 0.3s ease;
}

.back-link:hover {
  color: #5d1485;
}

.rating-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}

.rating-container label {
  color: #ddd;
}

.result-block {
  margin-bottom: 1.5rem;
}
</style>
