<template>
  <main class="task-page">
    <div class="task-card">
      <form class="task-form" @submit.prevent="submitCompletion">
        <h2>Виконати завдання</h2>

        <h3 class="task-title">{{ taskTitle }}</h3>

        <div class="input-group">
          <textarea
              v-model="completionText"
              placeholder="Опишіть виконання завдання..."
              required
          ></textarea>
        </div>

        <input type="submit" value="Надіслати" />

        <p class="error" v-if="errorMessage">{{ errorMessage }}</p>
      </form>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId
const completionText = ref('')
const errorMessage = ref('')
const taskTitle = ref('')
const jwt = localStorage.getItem('jwtToken')

// Отримати дані про завдання
const fetchTask = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    taskTitle.value = response.data.title
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error)
    errorMessage.value = 'Не вдалося завантажити завдання'
  }
}

onMounted(fetchTask)

const submitCompletion = async () => {
  try {
    await axios.post(`http://localhost:8000/tasks/${taskId}/complete`, { execution_description: completionText.value }, {
      headers: { Authorization: `Bearer ${jwt}` }
    })

    router.push('/profile')
  } catch (error) {
    errorMessage.value = 'Помилка при надсиланні результату завдання'
    console.error(error)
  }
}
</script>


<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

.task-page {
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

.task-card {
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

.task-form h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.task-number {
  font-size: 1rem;
  margin-bottom: 1.5rem;
  color: #ccc;
}

/* Стиль для назви завдання */
.task-title {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  font-weight: 400;
  color: #fff;
}

.input-group {
  position: relative;
  margin-bottom: 1.5rem;
}

.input-group textarea {
  width: 100%;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  outline: none;
  resize: vertical;
  min-height: 150px;
}

.input-group textarea::placeholder {
  color: #ccc;
}

input[type="submit"] {
  background: transparent;
  color: #ccc;
  border: none;
  padding: 0.8rem;
  width: 100%;
  border-radius: 10px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s ease;
  text-transform: uppercase;
}

input[type="submit"]:hover {
  background: #9326c6;
}

.error {
  margin-top: 1rem;
  color: #ff6b6b;
  font-weight: bold;
}
</style>

