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
import {useRouter} from 'vue-router';
import axios from 'axios'; // Імпортуйте axios

const router = useRouter();

const logout = async () => { // Робимо функцію асинхронною
  const jwt = localStorage.getItem('jwtToken');

  if (jwt) {
    try {
      // Викликаємо ендпоінт на бекенді для явного логауту
      await axios.post('http://localhost:8000/auth-actions/logout_explicit', {}, { // Пусте тіло запиту, якщо не потрібно
        headers: {
          Authorization: `Bearer ${jwt}`
        }
      });
      // console.log('Successfully marked as offline on backend');
    } catch (error) {
      console.error('Error marking user as offline on backend:', error);
      // Продовжуємо логаут на фронтенді, навіть якщо запит до бекенду не вдався,
      // щоб не блокувати користувача.
    }
  }

  // Видаляємо токен з localStorage
  localStorage.removeItem('jwtToken');

  // Опціонально: очистити інші дані, пов'язані з користувачем (наприклад, з Vuex store)

  // Перенаправляємо на сторінку логіну
  router.push('/login');
};
</script>

<style scoped>
/* Ваші стилі залишаються без змін */
.navbar {
  background: rgba(40, 30, 55, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;

  position: fixed;
  top: 1rem;
  left: 1.5rem;
  right: 1.5rem;
  width: auto;
  z-index: 1000;

  padding: 0.8rem 2rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.nav-link {
  color: #e0e1e6;
  font-weight: 500;
  text-decoration: none;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  transition: color 0.2s ease, background-color 0.2s ease;
  position: relative;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.nav-link.router-link-exact-active {
  background-color: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 1px 0px rgba(0, 123, 255, 0.7);
}

.logout-button {
  background-color: rgba(248, 46, 237, 0.15);
  color: #f5d9f3;
  padding: 0.7rem 1.3rem;
  border-radius: 8px;
  font-weight: 600;
  border: 1px solid rgba(248, 46, 237, 0.4);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.logout-button:hover {
  background-color: #f82eed;
  color: #ffffff;
  border-color: #f82eed;
  box-shadow: 0 0 12px rgba(248, 46, 237, 0.5);
}
</style>