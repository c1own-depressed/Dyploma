<template>
  <main class="login-page">
    <div class="login-card">
      <form class="login-form" @submit.prevent="submitLogin">
        <h2>Вхід</h2>

        <div class="input-group">
          <input
              type="email"
              placeholder="Електронна пошта"
              v-model="login_form.email"
              required
          />
          <span class="icon">
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
              v-model="login_form.password"
              required
          />
          <span class="icon">
            <!-- Lock icon -->
            <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
        </div>

        <input type="submit" value="Увійти" />

        <p class="error" v-if="loginError">{{ loginError }}</p>
        <p class="register-switch">
          Не маєте акаунту?
          <a href="#" @click="goToRegister">Зареєструватися</a>
        </p>
      </form>
    </div>
  </main>
</template>
<script>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

export default {
  setup() {
    const login_form = ref({ email: "", password: "" });
    const loginError = ref(null);
    const router = useRouter();

    const submitLogin = async () => {
      if (!login_form.value.email || !login_form.value.password) {
        alert("Будь ласка, заповніть усі обов'язкові поля");
        loginError.value = "Неправильна електронна пошта або пароль";
        return;
      }

      try {
        const data = new URLSearchParams();
        data.append("grant_type", "password");
        data.append("username", login_form.value.email);
        data.append("password", login_form.value.password);

        const response = await axios.post(
            "http://localhost:8000/auth/jwt/login",
            data,
            {
              headers: {
                "Content-Type": "application/x-www-form-urlencoded",
              },
            }
        );

        const token = response.data.access_token;
        localStorage.setItem("jwtToken", token);
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        try {
          await axios.post('http://localhost:8000/chats/me/ping-online'); // Шлях до вашого пінг-ендпоінту
          // console.log("User explicitly pinged as online immediately after login.");
        } catch (pingError) {
          console.warn("Could not explicitly ping online status post-login:", pingError);
        }
        login_form.value.email = "";
        login_form.value.password = "";
        loginError.value = null;
        router.push("/main-page");
      } catch (error) {
        loginError.value = "Неправильна пошта або пароль";
        console.error(error);
      }
    };

    const goToRegister = () => {
      router.push("/register");
    };

    return {
      login_form,
      loginError,
      submitLogin,
      goToRegister,
    };
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.login-page {
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

.login-card {
  background: rgba(30, 25, 45, 0.85); /* Темний, насичений фон картки */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem; /* Зроблено однаковим з усіх боків */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45); /* Глибша тінь */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла межа */
  width: 100%;
  max-width: 420px; /* Трохи збільшено для комфорту */
  color: #f0f0f0;
  text-align: left; /* Вирівнювання по лівому краю для вмісту форми */
}

.login-card h2 {
  font-size: 2rem;
  margin-bottom: 2.2rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center; /* Заголовок по центру */
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.input-group {
  position: relative;
  margin-bottom: 1.8rem;
}

.input-group input { /* Стиль для input type="email" та type="password" */
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
  width: 20px; /* Або 1.2em */
  height: 20px;
  stroke: currentColor; /* Колір успадковується від .icon */
}

/* .options - такого класу немає у вашому HTML, тому його стилі видалені */

input[type="submit"] { /* Кнопка "Увійти" */
  background-color: #007AFF; /* Синій акцент, як основна дія */
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  width: 100%;
  border-radius: 10px;
  font-weight: 600; /* Збільшено жирність */
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

.register-switch {
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
