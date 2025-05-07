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
.register-page {
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

.login-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 3rem 2.5rem;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.4);
  width: 100%;
  max-width: 400px;
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

.input-group input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  outline: none;
}

.input-group input::placeholder {
  color: #ccc;
}

.input-group .icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  color: white;
  opacity: 1;
}

.input-group .icon-svg {
  width: 24px;
  height: 24px;
}

input[type="submit"] {
  background: white;
  color: #2b1055;
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
  background: #eee;
}

.error {
  margin-top: 1rem;
  color: #ff6b6b;
  font-weight: bold;
}

.register-switch {
  margin-top: 1.5rem;
  font-size: 0.95rem;
  color: #ccc;
}

.register-switch a {
  color: #fff;
  font-weight: bold;
  text-decoration: underline;
}
</style>
