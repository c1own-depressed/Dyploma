<template>
  <main class="task-detail-page">


    <div v-if="task" class="task-card">
      <button class="back-btn" @click="goBack">← Назад на головну</button>
      <h2 class="task-title">{{ task.title }}</h2>
      <p class="task-field"><strong>Опис:</strong> {{ task.description }}</p>
      <p class="task-field"><strong>Дата створення:</strong> {{ task.created_at }}</p>
      <p class="task-field"><strong>Автор:</strong> {{ task.owner_name }}</p>

      <button v-if="task.status === 'pending'" class="take-btn" @click="takeTask">Взяти завдання</button>
      <p v-if="task.status === 'in_progress'" class="error-text">Завдання вже взято!</p>
      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <!-- Кнопка для зв'язку з замовником -->
      <button v-if="task.status === 'pending'" class="contact-btn" @click="contactOwner">Зв'язатися з замовником</button>
    </div>

    <div v-else class="loading-text">
      <p>Завантаження...</p>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const task = ref(null);
const jwt = ref(localStorage.getItem('jwtToken')); // JWT з localStorage
const errorMessage = ref('');

// Функція для отримання завдання
async function fetchTask() {
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${route.params.id}`, {
      headers: {
        Authorization: `Bearer ${jwt.value}`, // Використовуємо JWT з localStorage
      },
    });
    task.value = response.data;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    errorMessage.value = "Помилка при завантаженні завдання.";
  }
}

// Функція для взяття завдання
async function takeTask() {
  if (!jwt.value) {
    errorMessage.value = "Не знайдено JWT користувача. Перевірте, чи ви авторизовані.";
    return;
  }

  if (task.value.status === 'in_progress') {
    errorMessage.value = "Завдання вже взято!";
    return;
  }

  try {
    const response = await axios.post(`http://localhost:8000/tasks/${route.params.id}/take`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`, // Використовуємо JWT
      },
    });

    // Оновлюємо локальний статус завдання після успішного виконання запиту
    task.value.status = "in_progress";

    alert(`Ви взяли завдання: ${task.value.title}`);
  } catch (error) {
    console.error('Помилка при взятті завдання:', error);
    errorMessage.value = "Не вдалося взяти завдання.";
  }
}

async function contactOwner() {
  try {
    const response = await axios.post(`http://localhost:8000/chats/with-owner/${task.value.id}`, {}, {
      headers: {
        Authorization: `Bearer ${jwt.value}`
      }
    });

    const chatId = response.data.chat_id;

    // Перенаправлення на конкретний чат
    router.push(`/chats/${chatId}`);
  } catch (error) {
    console.error('Не вдалося створити чат:', error);
    errorMessage.value = "Не вдалося зв'язатися із замовником.";
  }
}




// Функція для переходу назад на головну
function goBack() {
  router.push('/main-page');
}

onMounted(fetchTask);
</script>

<style scoped>
.task-detail-page {
  padding: 2rem;
  padding-top: 100px; /* Відступ для Navbar */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  color: #f0f0f0;
}

.back-btn {
  display: inline-block; /* Щоб відступи працювали коректно і кнопка не займала всю ширину */
  margin-bottom: 1.5rem; /* Відступ знизу перед заголовком картки */
  background: none; /* Без фону */
  border: none; /* Без рамки */
  color: #b0b8c5; /* Світло-сіро-блакитний, добре для посилань */
  font-size: 0.95rem; /* Розмір тексту */
  font-weight: 500; /* Напівжирний */
  cursor: pointer;
  text-decoration: none; /* Без підкреслення за замовчуванням */
  padding: 0.2rem 0; /* Невеликий вертикальний падінг для кращої клікабельності, без горизонтального */
  transition: color 0.2s ease;
}

.back-btn:hover {
  color: #ffffff; /* Білий колір при наведенні */
  text-decoration: underline; /* Підкреслення при наведенні для ясності, що це посилання */
}

.task-card {
  background: rgba(30, 25, 45, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 2.2rem 2.5rem;
  border-radius: 18px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 600px;
  margin: 0 auto; /* Центрування картки на сторінці */
  text-align: left;
}

.task-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.8rem;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.task-field {
  margin-bottom: 1.1rem;
  color: #dfe2e8;
  line-height: 1.6;
  font-size: 1rem;
}

.task-field strong {
  color: #f8f9fa;
  font-weight: 600;
  margin-right: 0.6em;
}

/* Обгортка для кнопок, якщо вони мають бути в рядку */
/* Якщо кнопки залишаються одна під одною, ця обгортка не потрібна в HTML,
   а стилі для кнопок нижче вже враховують це */
.action-buttons {
  display: flex;
  flex-direction: column; /* За замовчуванням кнопки одна під одною */
  gap: 1rem;
  margin-top: 2.2rem;
}

/* Медіа-запит для розташування кнопок в ряд на більших екранах, ЯКЩО ви додасте .action-buttons в HTML */
@media (min-width: 500px) {
  .action-buttons.horizontal { /* Додайте клас .horizontal до div.action-buttons для цього ефекту */
    flex-direction: row;
    justify-content: center;
  }
  .action-buttons.horizontal .take-btn,
  .action-buttons.horizontal .contact-btn {
    flex-grow: 1;
    max-width: 240px;
  }
}

.take-btn, .contact-btn {
  display: block; /* Кожна кнопка на новому рядку (якщо не в .action-buttons.horizontal) */
  width: 100%; /* Кнопки на всю ширину картки (якщо не в .action-buttons.horizontal) */
  padding: 0.9rem 1.5rem;
  font-size: 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  border: none;
  color: white;
  text-align: center;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}
.take-btn:hover, .contact-btn:hover {
  transform: translateY(-2px);
}

.take-btn {
  /* margin-top залишено з вашого HTML, він перший після полів */
  background-color: #007AFF;
}
.take-btn:hover {
  background-color: #005bb5;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.contact-btn {
  margin-top: 1rem; /* Відступ зверху для другої кнопки */
  background-color: #9326C6;
}
.contact-btn:hover {
  background-color: #7a1fcf;
  box-shadow: 0 4px 12px rgba(147, 38, 198, 0.4);
}

.error-text {
  color: #ff9a9a;
  background-color: rgba(255, 82, 82, 0.15);
  border: 1px solid rgba(255, 82, 82, 0.35);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}
p.error-text { /* Щоб повідомлення про помилку не розтягувалось на всю ширину, якщо воно коротке */
  width: auto;
  display: inline-block;
  /* Для центрування inline-block елемента, його батьківський елемент (наприклад, .task-card)
     мав би мати text-align: center; але картка має text-align: left.
     Тому це правило може не центрувати так, як очікується, якщо текст помилки всередині картки.
     Якщо помилка завжди має бути по центру картки, краще обгорнути її в div з text-align: center.
     Поки що залишаємо так, як є у вашій структурі.
  */
}


.loading-text {
  text-align: center;
  font-size: 1.1rem;
  color: #b0b8c5;
  margin-top: 3rem;
}
</style>