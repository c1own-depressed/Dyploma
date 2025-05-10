<template>
  <nav class="navbar">
    <div class="nav-links">
      <router-link to="/main-page" class="nav-link">Головна сторінка</router-link>
      <router-link to="/profile" class="nav-link">Профіль</router-link>
      <router-link to="/chats" class="nav-link">Чати</router-link>
    </div>
    <button @click="logout" class="logout-button">
      Вийти
    </button>
  </nav>
</template>


<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-radius: 15px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  margin: 1rem;
  position: fixed; /* Фіксувати панель на екрані */
  top: 0; /* Панель повинна бути на самому верху */
  left: 0; /* Панель повинна починатися з лівого краю */
  width: 98%; /* Ширина на всю сторінку */
  z-index: 1000; /* Перекриває інші елементи */
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: white;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.3s;
}

.nav-link:hover {
  color: #aaa;
}

.logout-button {
  background: transparent;
  color: #ffffff;
  padding: 0.6rem 1.2rem;
  border-radius: 10px;
  font-weight: bold;
  border: none;
  cursor: pointer;
  transition: background 0.3s;
}

.logout-button:hover {
  background: #f82eed;
}
</style>
