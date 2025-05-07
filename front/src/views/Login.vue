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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

.login-page {
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

.options {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  color: #ccc;
}

.options a {
  color: #bbb;
  text-decoration: none;
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

.icon-svg {
  width: 24px;
  height: 24px;
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
