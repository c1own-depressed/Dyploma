<template>
  <main class="register-page">
    <div class="login-card">
      <form class="login-form" @submit.prevent="submitRegister">
        <h2>Реєстрація</h2>

        <div class="input-group">
          <input
              type="text"
              placeholder="Ім'я користувача"
              v-model="register_form.username"
              required
          />
          <span class="icon">
            <!-- Іконка користувача -->
            <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-3-3.87 4 4 0 0 0-6 0A4 4 0 0 0 8 19v2" />
              <circle cx="14" cy="7" r="4" />
            </svg>
          </span>
        </div>

        <div class="input-group">
          <input
              type="email"
              placeholder="Електронна пошта"
              v-model="register_form.email"
              required
          />
          <span class="icon">
            <!-- Іконка конверта -->
            <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 6l10 7 10-7" />
              <path d="M3 3h18c.552 0 1 .448 1 1v16c0 .552-.448 1-1 1H3c-.552 0-1-.448-1-1V4c0-.552.448-1 1-1z" />
            </svg>
          </span>
        </div>

        <div class="input-group">
          <input
              type="password"
              placeholder="Пароль"
              v-model="register_form.password"
              required
          />
          <span class="icon">
            <!-- Іконка замка -->
            <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
        </div>

        <input type="submit" value="Зареєструватися" />
        <p class="error" v-if="registerError">{{ registerError }}</p>
        <p class="register-switch">
          Вже маєте акаунт?
          <a href="#" @click="goToLogin">Увійти</a>
        </p>
      </form>
    </div>
  </main>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

export default {
  setup() {
    const register_form = ref({ username: '', email: '', password: '' });
    const registerError = ref(null);
    const router = useRouter();

    const submitRegister = async () => {
      if (!register_form.value.username || !register_form.value.email || !register_form.value.password) {
        alert('Будь ласка, заповніть усі обов’язкові поля');
        registerError.value = 'Не вдалося зареєструватися. Спробуйте ще раз.';
        return;
      }

      try {
        const data = {
          email: register_form.value.email,
          password: register_form.value.password,
          is_active: true,
          is_verified: false,
          username: register_form.value.username,
          role_id: 1,
        };

        await axios.post('http://localhost:8000/auth/register', data);
        router.push('/login');  // Перенаправлення на сторінку входу після реєстрації
      } catch (error) {
        registerError.value = 'Registration failed. Please try again.';
        console.error(error);
      }
    };

    // Перехід на сторінку входу
    const goToLogin = () => {
      router.push('/login');
    };

    return {
      register_form,
      registerError,
      submitRegister,
      goToLogin,
    };
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.register-page { /* Змінено клас для сторінки */
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

.login-card { /* Клас картки залишаємо .login-card для узгодженості з логіном, якщо стилі спільні */
  background: rgba(30, 25, 45, 0.85); /* Темний, насичений фон картки */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem; /* Однаковий падінг з усіх боків */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45); /* Глибша тінь */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла межа */
  width: 100%;
  max-width: 450px; /* Можна трохи збільшити, бо полів більше */
  color: #f0f0f0;
  text-align: left; /* Вирівнювання по лівому краю для вмісту форми */
}

.login-card h2 { /* Селектор для h2 всередині картки */
  font-size: 2rem;
  margin-bottom: 2.2rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center; /* Заголовок по центру */
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.input-group {
  position: relative;
  margin-bottom: 1.8rem; /* Відстань між полями вводу */
}

.input-group input { /* Стиль для всіх input type="text", type="email", type="password" */
  width: 100%;
  padding: 0.9rem 3rem 0.9rem 1.1rem; /* Збільшено падінги, правий падінг для іконки */
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  color: #ffffff;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.input-group input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-group input:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.input-group .icon {
  position: absolute;
  right: 1rem; /* Відступ іконки справа */
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.7); /* Трохи менш яскрава іконка */
  pointer-events: none; /* Щоб іконка не заважала кліку на поле */
}

.icon-svg { /* Розмір SVG іконок */
  width: 20px;
  height: 20px;
  stroke: currentColor; /* Колір успадковується від .icon */
}

input[type="submit"] { /* Кнопка "Зареєструватися" */
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
  margin-top: 0.5rem; /* Невеликий відступ зверху */
}

input[type="submit"]:hover {
  background-color: #005bb5; /* Темніший синій */
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

.register-switch { /* Насправді це "login-switch" на сторінці реєстрації */
  margin-top: 2rem; /* Збільшено відступ */
  font-size: 0.9rem; /* Трохи зменшено */
  color: #b0b8c5; /* Світло-сірий */
  text-align: center; /* Явно центруємо */
}

.register-switch a {
  color: #90caf9; /* Блакитний акцент для посилання */
  font-weight: 600; /* Жирніший */
  text-decoration: none; /* Прибираємо підкреслення за замовчуванням */
  transition: color 0.2s ease, text-decoration 0.2s ease;
}
.register-switch a:hover {
  color: #bbdefb; /* Світліший блакитний при наведенні */
  text-decoration: underline; /* Підкреслення при наведенні */
}
</style>
