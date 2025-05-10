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
  localStorage.removeItem('jwtToken')
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: rgba(40, 30, 55, 0.6); /* Трохи темніший та насиченіший фон, ніж був (0.05) */
  backdrop-filter: blur(12px); /* Трохи сильніший блюр */
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3); /* М'якша, але виразніша тінь */
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;

  position: fixed;
  top: 1rem; /* Відступ зверху від краю вікна */
  left: 1.5rem; /* Відступ зліва від краю вікна */
  right: 1.5rem; /* Відступ справа від краю вікна */
  width: auto; /* Ширина розрахується автоматично (100% - лівий відступ - правий відступ) */
  z-index: 1000;

  padding: 0.8rem 2rem; /* Внутрішні відступи */
  border-radius: 12px; /* Трохи менший радіус для більш строгого вигляду */
  border: 1px solid rgba(255, 255, 255, 0.1); /* Ледь помітна межа */
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.8rem; /* Трохи зменшено проміжок між основними посиланнями */
}

.nav-link {
  color: #e0e1e6; /* Світло-сірий для кращої читабельності */
  font-weight: 500; /* Звичайна насиченість */
  text-decoration: none;
  padding: 0.6rem 1rem; /* Додано падінги для збільшення області кліку */
  border-radius: 8px; /* Округлення для ефекту кнопки */
  transition: color 0.2s ease, background-color 0.2s ease;
  position: relative;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

/* Стиль для активного посилання */
.nav-link.router-link-exact-active {
  background-color: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  font-weight: 600; /* Активне посилання трохи жирніше */
  box-shadow: 0 1px 0px rgba(0, 123, 255, 0.7); /* Тонка синя лінія знизу як акцент */
}

.logout-button {
  background-color: rgba(248, 46, 237, 0.15); /* Дуже легкий фон з рожевим відтінком */
  color: #f5d9f3; /* Світло-рожевий текст */
  padding: 0.7rem 1.3rem; /* Збільшено падінги */
  border-radius: 8px;
  font-weight: 600; /* Зроблено жирнішим */
  border: 1px solid rgba(248, 46, 237, 0.4); /* Рожева межа */
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.logout-button:hover {
  background-color: #f82eed; /* Яскравий рожевий фон при наведенні */
  color: #ffffff; /* Білий текст */
  border-color: #f82eed; /* Межа стає непрозорою */
  box-shadow: 0 0 12px rgba(248, 46, 237, 0.5); /* Рожеве світіння */
}
</style>