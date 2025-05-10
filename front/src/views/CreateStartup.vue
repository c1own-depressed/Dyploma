<template>
  <main class="create-startup-page">
    <div class="startup-card">
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

      <form class="startup-form" @submit.prevent="submitStartup">
        <h2>Створити стартап</h2>

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
              rows="4"
          ></textarea>
        </div>

        <input type="submit" value="Створити" />
      </form>
    </div>
  </main>
</template>


<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const jwt = localStorage.getItem('jwtToken')

const form = ref({
  name: '',
  description: ''
})

const submitStartup = async () => {
  try {
    await axios.post('http://localhost:8000/create_startup/', form.value, {
      headers: {
        Authorization: `Bearer ${jwt}`
      }
    })
    router.push('/profile')
  } catch (error) {
    console.error('Помилка створення стартапу:', error)
  }
}


const goToProfile = () => {
  router.push('/profile')
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.create-startup-page {
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

.startup-card {
  background: rgba(30, 25, 45, 0.85); /* Темний, насичений фон картки */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem 3rem; /* Збалансовані падінги */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45); /* Глибша тінь */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла межа */
  width: 100%;
  max-width: 500px; /* Залишаємо поточну максимальну ширину */
  color: #f0f0f0;
  text-align: left; /* Вирівнювання по лівому краю для вмісту форми */
}

.startup-card h2 {
  font-size: 2rem;
  margin-bottom: 2.2rem; /* Збільшено відступ */
  font-weight: 600;
  color: #ffffff;
  text-align: center; /* Заголовок по центру */
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.back-link {
  display: inline-block; /* Або inline-flex, якщо плануєте іконку */
  margin-bottom: 1.8rem; /* Відступ знизу перед заголовком */
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

.input-group {
  position: relative;
  margin-bottom: 1.8rem;
}

.input-group input[type="text"],
.input-group textarea {
  width: 100%;
  padding: 0.9rem 1.1rem;
  background: rgba(255, 255, 255, 0.08); /* Стандартний фон для полів */
  border: 1px solid rgba(255, 255, 255, 0.18); /* Стандартна межа */
  border-radius: 10px; /* Стандартний радіус */
  color: #ffffff;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  resize: vertical; /* Дозволяємо змінювати висоту textarea */
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.input-group input[type="text"]::placeholder,
.input-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.6); /* Стандартний колір плейсхолдера */
}

.input-group input[type="text"]:focus,
.input-group textarea:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

input[type="submit"] { /* Кнопка "Створити" */
  background-color: #007AFF; /* Синій акцент, як основна дія */
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
  margin-top: 0.5rem; /* Невеликий відступ зверху, якщо потрібно */
}

input[type="submit"]:hover {
  background-color: #005bb5; /* Темніший синій */
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

/* Стилі для повідомлень про помилки (якщо ви їх додасте в HTML) */
.error-message {
  color: #ff9a9a;
  background-color: rgba(255, 82, 82, 0.15);
  border: 1px solid rgba(255, 82, 82, 0.35);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-bottom: 1.5rem; /* Розташуйте його над кнопкою submit або під заголовком */
  text-align: center;
  font-size: 0.95rem;
}
</style>