<template>
  <main class="edit-startup-page">
    <div class="startup-card">
      <span class="back-link" @click="goBack">← Повернутися в профіль</span>

      <form class="startup-form" @submit.prevent="updateStartup" v-if="!loading">
        <h2>Редагувати стартап</h2>

        <div v-if="error" class="error-message">{{ error }}</div>

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

        <input type="submit" value="Зберегти зміни" />
      </form>

      <div v-else style="color:white; margin-top: 2rem;">Завантаження...</div>

      <button class="delete-button" @click="deleteStartup" v-if="!loading">
        Видалити стартап
      </button>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const jwt = localStorage.getItem('jwtToken')

const form = ref({
  name: '',
  description: ''
})

const loading = ref(true)
const error = ref('')

const fetchStartup = async () => {
  loading.value = true
  try {
    const res = await axios.get(`http://localhost:8000/user/startup/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    })

    // Перевіряємо, чи поля дійсно є в відповіді
    form.value.name = res.data.name ?? ''
    form.value.description = res.data.description ?? ''
  } catch (e) {
    console.error('Помилка при завантаженні стартапу', e)
    error.value = 'Не вдалося завантажити дані. Перевірте зʼєднання або авторизацію.'
  } finally {
    loading.value = false
  }
}

const updateStartup = async () => {
  try {
    await axios.put(`http://localhost:8000/user/startup/${route.params.id}`, form.value, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    router.push('/profile')
  } catch (e) {
    console.error('Помилка при оновленні стартапу', e)
    alert('Не вдалося зберегти зміни. Спробуйте ще раз.')
  }
}

const deleteStartup = async () => {
  if (!confirm('Ви впевнені, що хочете видалити цей стартап?')) return
  try {
    await axios.delete(`http://localhost:8000/user/startup/${route.params.id}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    router.push('/profile')
  } catch (e) {
    console.error('Помилка при видаленні стартапу', e)
    alert('Не вдалося видалити стартап.')
  }
}

const goBack = () => {
  router.push('/profile')
}

onMounted(fetchStartup)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

.edit-startup-page {
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

.delete-button {
  margin-top: 1.5rem;
  background: transparent;
  border: none;
  padding: 0.75rem;
  width: 100%;
  border-radius: 10px;
  font-weight: bold;
  color: #fff;
  cursor: pointer;
  transition: background 0.3s ease;
  text-transform: uppercase;
}

.delete-button:hover {
  background: rgba(255, 0, 0, 0.5);
}

.error-message {
  color: #ffaaaa;
  margin-bottom: 1rem;
}
</style>
