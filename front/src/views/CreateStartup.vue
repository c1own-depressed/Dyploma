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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

.create-startup-page {
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

.startup-card {
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

.input-group {
  position: relative;
  margin-bottom: 1.5rem;
}

.input-group input,
.input-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  outline: none;
  resize: none;
}

.input-group input::placeholder,
.input-group textarea::placeholder {
  color: #ccc;
}

input[type="submit"] {
  background: transparent;
  color: white;
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
  background: #c786e4;
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

</style>
