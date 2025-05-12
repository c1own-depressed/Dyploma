<template>
  <main class="task-result-page">
    <div class="task-result-card">
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>
      <h2>Результат завдання</h2>

      <div v-if="result">
        <div class="result-block">
          <h3>{{ result.title }}</h3>
          <p><strong>Опис завдання:</strong><br>{{ result.description }}</p>
          <p><strong>Результат виконання:</strong><br>{{ result.executionResult || 'Опис не надано.' }}</p>
        </div>

        <div v-if="result.attachedFileName" class="submitted-item-container">
          <h4>Надіслані матеріали:</h4>
          <div class="file-bubble">
            <div class="file-bubble-icon-container">
              <span class="file-bubble-icon">{{ getFileDisplayInfo(result.attachedFileName).icon }}</span>
            </div>
            <div class="file-bubble-details">
              <span class="file-bubble-name" :title="result.attachedFileName">{{ result.attachedFileName }}</span>
              <span class="file-bubble-description">{{ getFileDisplayInfo(result.attachedFileName).description }}</span>
            </div>
            <button class="file-bubble-download-btn" @click="downloadAttachedFile(result.attachedFileName)" title="Завантажити файл">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </button>
          </div>
        </div>
        <div class="input-group">
          <div class="rating-container">
            <label for="rating">Оцінка:</label>
            <select id="rating" v-model="rating">
              <option value="0" disabled>Оберіть оцінку</option>
              <option v-for="i in 5" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
        </div>

        <button class="submit-btn" @click="submitRating" :disabled="rating === 0">Подати оцінку</button>
        <p v-if="ratingMessage" :class="['rating-message', ratingMessage.startsWith('Помилка') ? 'error' : '']">{{ ratingMessage }}</p>
      </div>

      <div v-else-if="loadingError">
        <p class="error-message">{{ loadingError }}</p>
      </div>
      <div v-else>
        <p data-loading-text="true">Завантаження результатів...</p>
      </div>
    </div>
  </main>
</template>
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface TaskResult {
  id: number; // Додано id
  title: string;
  description: string;
  executionResult: string;
  attachedFileName?: string | null; // Поле для імені файлу
}

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId as string; // Явно вказуємо тип
const result = ref<TaskResult | null>(null)
const rating = ref<number>(0); // Початкове значення 0 для вибору
const loadingError = ref<string | null>(null);
const ratingMessage = ref<string>('');


const token = localStorage.getItem('jwtToken') || localStorage.getItem('jwt_token'); // Перевіряємо обидва варіанти

if (!token) {
  console.error('Токен не знайдено!');
  loadingError.value = 'Помилка автентифікації: токен не знайдено.';
  // Можна додати перенаправлення на сторінку логіну
  // router.push('/login');
}

const fetchTaskResult = async () => {
  loadingError.value = null;
  if (!token) return;

  try {
    const res = await axios.get<TaskResult>(`http://localhost:8000/user/${taskId}/result`, { // Вказуємо тип відповіді
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    result.value = res.data;
    if (!res.data.executionResult && !res.data.attachedFileName) {
      // Якщо немає ані опису, ані файлу, можливо, завдання ще не виконане
      // або виконане без деталей. Можна уточнити це повідомлення.
      loadingError.value = "Виконавець ще не надав результат для цього завдання або результат порожній.";
    }
  } catch (e: any) {
    console.error('Не вдалося завантажити результат завдання', e);
    if (e.response && e.response.data && e.response.data.detail) {
      loadingError.value = `Помилка завантаження: ${e.response.data.detail}`;
    } else {
      loadingError.value = 'Не вдалося завантажити результат завдання.';
    }
  }
};

const downloadAttachedFile = async (filename: string | undefined | null) => {
  if (!filename || !token) {
    console.error('Ім\'я файлу або токен відсутні');
    ratingMessage.value = 'Не вдалося завантажити файл: не вказано ім\'я файлу.';
    return;
  }
  try {
    const response = await axios.get(`http://localhost:8000/user/download_attachment/${filename}`, {
      headers: {
        Authorization: `Bearer ${token}` // Якщо ендпоінт завантаження захищений
      },
      responseType: 'blob', // Важливо для завантаження файлів
    });

    // Створення URL для blob та ініціювання завантаження
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename); // Встановлюємо ім'я файлу для завантаження
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url); // Очищення
    ratingMessage.value = `Файл "${filename}" успішно завантажено.`;

  } catch (error: any) {
    console.error('Помилка при завантаженні файлу:', error);
    if (error.response && error.response.data) {
      // Якщо відповідь - blob, її треба буде розпарсити як JSON, якщо помилка у форматі JSON
      // Це складніше, бо відповідь вже blob. Зазвичай сервер надсилає помилки як JSON.
      // Якщо сервер надсилає помилку як JSON, а ми очікуємо blob, це викличе помилку парсингу тут.
      // Краще обробляти помилки HTTP статусів.
      if (error.response.status === 404) {
        ratingMessage.value = `Помилка: Файл "${filename}" не знайдено на сервері.`;
      } else if (error.response.status === 400) {
        ratingMessage.value = `Помилка: Некоректний запит на завантаження файлу.`;
      }
      else {
        ratingMessage.value = 'Не вдалося завантажити файл.';
      }
    } else {
      ratingMessage.value = 'Не вдалося завантажити файл. Перевірте консоль.';
    }
  }
};

const submitRating = async () => {
  ratingMessage.value = '';
  if (rating.value === 0) {
    ratingMessage.value = 'Будь ласка, оберіть оцінку перед подачею.';
    return;
  }
  if (!token) return;

  try {
    const response = await axios.post(`http://localhost:8000/user/${taskId}/rate`,
        { rating: rating.value },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
    console.log('Оцінка подана успішно:', response.data);
    ratingMessage.value = response.data.message || 'Оцінка успішно подана!';
    // Перекидаємо на сторінку профілю через деякий час, щоб користувач побачив повідомлення
    setTimeout(() => {
      router.push('/profile');
    }, 2000);

  } catch (e: any) {
    console.error('Не вдалося подати оцінку', e);
    if (e.response && e.response.data && e.response.data.detail) {
      ratingMessage.value = `Помилка: ${e.response.data.detail}`;
    } else {
      ratingMessage.value = 'Не вдалося подати оцінку.';
    }
  }
};

interface FileDisplayInfo {
  icon: string;
  description: string;
  defaultPreview?: boolean; // Чи можна спробувати показати прев'ю (для зображень)
}

const getFileExtension = (filename: string | undefined | null): string => {
  if (!filename || typeof filename !== 'string') return '';
  return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
};

const getFileDisplayInfo = (filename: string | undefined | null): FileDisplayInfo => {
  const extension = getFileExtension(filename);
  let icon = '📎'; // Іконка за замовчуванням (скріпка)
  let description = 'Файл';
  let defaultPreview = false;

  if (extension) {
    switch (extension) {
      case 'pdf':
        icon = '📜'; // Сувій
        description = 'PDF Документ';
        break;
      case 'doc':
      case 'docx':
        icon = '📄'; // Сторінка документу
        description = 'Документ Word';
        break;
      case 'xls':
      case 'xlsx':
        icon = '📊'; // Графік
        description = 'Документ Excel';
        break;
      case 'ppt':
      case 'pptx':
        icon = '🖥️'; // Монітор
        description = 'Презентація';
        break;
      case 'zip':
      case 'rar':
      case '7z':
        icon = '🗜️'; // Лещата (архів)
        description = 'Архів';
        break;
      case 'txt':
        icon = '📝'; // Нотатки
        description = 'Текстовий файл';
        break;
      case 'mp3':
      case 'wav':
      case 'ogg':
        icon = '🎵'; // Нота
        description = 'Аудіофайл';
        break;
      case 'mp4':
      case 'avi':
      case 'mov':
      case 'mkv':
        icon = '🎞️'; // Кіноплівка
        description = 'Відеофайл';
        break;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'webp':
      case 'svg':
        icon = '🖼️'; // Картина в рамці
        description = 'Зображення';
        defaultPreview = true; // Позначаємо, що це зображення
        break;
      default:
        description = `Файл ${extension.toUpperCase()}`;
    }
  }
  return { icon, description, defaultPreview };
};


const goToProfile = () => {
  router.push('/profile');
};

onMounted(() => {
  fetchTaskResult();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.task-result-page {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(to bottom, #2b1055, #7597de);
  background-image: url('../assets/img.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: #f0f0f0;
}

.task-result-card {
  background: rgba(30, 25, 45, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.2rem; /* Трохи зменшено падінг для компактності */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 580px; /* Трохи скориговано */
  color: #f0f0f0;
  text-align: center;
}

.back-link {
  display: block;
  margin-bottom: 1.5rem; /* Відступ перед головним заголовком */
  color: #b0b8c5;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.2s ease;
  text-align: left;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-result-card h2 { /* "Результат завдання" */
  font-size: 1.8rem; /* Трохи менший головний заголовок */
  margin-bottom: 1.8rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.result-block {
  margin-bottom: 1.8rem; /* Відступ після блоку результатів */
  /* border-bottom: 1px solid rgba(255, 255, 255, 0.08); */ /* Прибрано межу, використовуємо відступи */
  /* padding-bottom: 1.2rem; */
}

.result-block h3 { /* Назва завдання */
  font-size: 1.3rem; /* Менший, ніж h2 */
  margin-bottom: 0.8rem;
  font-weight: 600; /* Можна 500 для меншого акценту */
  color: #e8e9ed;
  text-align: center; /* Назва завдання зліва */
  line-height: 1.4;
}

.result-block p {
  font-size: 0.95rem; /* Трохи менший текст опису */
  color: #d5d8de;
  margin-bottom: 0.6rem;
  line-height: 1.6;
}
.result-block p strong {
  color: #f0f0f0;
  font-weight: 600;
}

/* Секція оцінки - робимо її більш інтегрованою */
.input-group { /* Цей div вже центрує вміст через flex у вашому HTML/CSS */
  margin-top: 1rem;
  margin-bottom: 1.8rem;
  display: flex; /* Залишаємо для центрування .rating-container */
  justify-content: center;
  align-items: center;
}

.rating-container {
  display: flex;
  align-items: center;
  gap: 0.8rem; /* Проміжок між "Оцінка:" та select */
  /* Забираємо фон та межу з .rating-container, стилізуємо label та select окремо */
}

.rating-container label {
  color: #d5d8de;
  font-weight: 500;
  font-size: 1rem;
}

.rating-container select {
  width: auto;
  min-width: 60px; /* Мінімальна ширина */
  padding: 0.6rem 0.8rem;
  border-radius: 8px; /* Менший радіус для select */
  background: rgba(255, 255, 255, 0.1); /* Схоже на інші поля вводу */
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #2c63a6;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}
.rating-container select:focus {
  border-color: rgba(255,255,255,0.4);
  background-color: rgba(255,255,255,0.15);
}

.submit-btn { /* Кнопка "Подати оцінку" */
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  /* width: 100%; -- Забираємо, щоб кнопка не була на всю ширину */
  display: block; /* Для центрування через margin:auto */
  margin: 1.5rem auto 0; /* Відступ зверху, центрування */
  min-width: 200px; /* Мінімальна ширина */
  width: auto; /* Ширина по контенту + падінги */
  max-width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.submit-btn:hover {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

/* Стиль для тексту завантаження */
div > p[data-loading-text="true"] { /* Якщо ви додасте data- атрибут до <p>Завантаження...</p> */
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  margin-top: 2rem;
}
/* Або якщо текст завжди однаковий: */
.task-result-card div > p:first-child:last-child { /* Спроба вибрати <p>Завантаження...</p> якщо він єдиний дочірній */
  color: #b0b8c5;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  margin-top: 2rem;
}
.attachment-block {
  margin-top: 1.5rem;
  margin-bottom: 1.8rem;
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: left;
}

.attachment-block h4 {
  font-size: 1.1rem;
  color: #e0e1e6;
  margin-bottom: 0.8rem;
  font-weight: 500;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem; /* Проміжок між назвою файлу та кнопкою */
}

.file-name {
  font-size: 0.95rem;
  color: #c0c8d5;
  word-break: break-all; /* Для довгих імен файлів */
  flex-grow: 1;
}

.download-btn {
  background-color: #007AFF; /* Такий же, як submit-btn */
  color: white;
  border: none;
  padding: 0.6rem 1.2rem; /* Трохи менші падінги */
  border-radius: 8px; /* Трохи менший радіус */
  font-weight: 500; /* Можна 500 */
  font-size: 0.9rem; /* Трохи менший шрифт */
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
  text-transform: none; /* Зазвичай кнопки завантаження не мають uppercase */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.download-btn:hover {
  background-color: #005bb5; /* Темніший при наведенні */
  transform: translateY(-1px);
}

.download-btn:active {
  transform: translateY(0);
}

.error-message { /* Стиль для помилки завантаження даних */
  color: #ff9a9a;
  background-color: rgba(255, 82, 82, 0.15);
  border: 1px solid rgba(255, 82, 82, 0.35);
  padding: 0.9rem 1.2rem;
  border-radius: 8px;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 500;
  margin-top: 1rem;
}

.rating-message {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #b0b8c5; /* Нейтральний колір для повідомлень */
  text-align: center;
}
.rating-message.error { /* Якщо хочете окремий стиль для помилок оцінки */
  color: #ff9a9a;
}

/* Забезпечимо, що кнопка "Подати оцінку" деактивована, коли rating === 0 */
.submit-btn:disabled {
  background-color: #555;
  cursor: not-allowed;
  opacity: 0.7;
}
.submit-btn:disabled:hover {
  background-color: #555;
  transform: none;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}
.result-block p {
  font-size: 0.95rem;
  color: #d5d8de;
  margin-bottom: 0.8rem; /* Зменшено відступ */
  line-height: 1.6;
  text-align: left; /* Вирівнювання тексту вліво */
  word-break: break-word;
}
.result-block p strong {
  color: #f0f0f0;
  font-weight: 600;
  display: block; /* Щоб "Опис завдання:" було на окремому рядку */
  margin-bottom: 0.3rem;
}


/* СТИЛІ ДЛЯ ОНОВЛЕНОГО БЛОКУ ФАЙЛУ */
.submitted-item-container {
  margin-top: 1.8rem;
  margin-bottom: 2rem;
  text-align: left;
}

.submitted-item-container h4 {
  font-size: 1.1rem;
  color: #e0e1e6;
  margin-bottom: 0.8rem;
  font-weight: 500;
}

.file-bubble {
  display: flex;
  align-items: center;
  background-color: rgba(60, 55, 80, 0.7); /* Трохи інший фон, як булька */
  border-radius: 12px; /* Більш заокруглені кути */
  padding: 12px 15px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  transition: background-color 0.2s ease;
}

.file-bubble:hover {
  background-color: rgba(70, 65, 90, 0.8);
}

.file-bubble-icon-container {
  flex-shrink: 0;
  margin-right: 12px;
  background-color: rgba(255, 255, 255, 0.1);
  width: 48px; /* Фіксований розмір контейнера іконки */
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-bubble-icon {
  font-size: 24px; /* Розмір emoji-іконки */
  color: #e0e1e6;
}

.file-bubble-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Для обрізання тексту, якщо потрібно */
  margin-right: 10px; /* Відступ від кнопки завантаження */
}

.file-bubble-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* Додає "..." якщо ім'я задовге */
}

.file-bubble-description {
  font-size: 0.8rem;
  color: #b0b8c5;
}

.file-bubble-download-btn {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #00aaff; /* Яскравий синій для іконки завантаження */
  padding: 8px;
  border-radius: 50%; /* Кругла кнопка */
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.file-bubble-download-btn:hover {
  background-color: rgba(0, 170, 255, 0.15);
  color: #33ceff;
}

.file-bubble-download-btn svg {
  width: 22px;
  height: 22px;
}

/* Стилі для оцінки і кнопки відправки - залишаються як є, або можна підправити за потреби */
.input-group {
  margin-top: 2rem; /* Збільшено відступ, якщо є файл */
  margin-bottom: 1.8rem;
  display: flex;
  justify-content: center;
  align-items: center;
}
/* ... (решта ваших стилів для rating-container, select, submit-btn, error-message, rating-message) ... */

.rating-message {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #b0b8c5;
  text-align: center;
  font-weight: 500;
}
.rating-message.error {
  color: #ff9a9a; /* Червоний для помилок */
  background-color: rgba(255, 82, 82, 0.1);
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  border: 1px solid rgba(255, 82, 82, 0.2);
}

/* Невелике виправлення для розташування "Опис завдання:" та "Результат виконання:" */
.result-block p strong {
  /* ... існуючі стилі ... */
  text-align: left; /* Якщо потрібно, хоча p вже має text-align: left */
}
</style>
