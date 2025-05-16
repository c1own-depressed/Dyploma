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

        <div v-if="!isAlreadyRated" class="rating-section">
          <div class="input-group">
            <div class="rating-container">
              <label for="rating">Оцінка:</label>
              <select id="rating" v-model="rating" :disabled="isAlreadyRated">
                <option value="0" disabled>Оберіть оцінку</option>
                <option v-for="i in 5" :key="i" :value="i">{{ i }}</option>
              </select>
            </div>
          </div>
          <button class="submit-btn" @click="submitRating" :disabled="rating === 0 || isAlreadyRated">
            Подати оцінку
          </button>
        </div>

        <p v-if="ratingMessage" :class="['rating-message', ratingMessage.startsWith('Помилка') ? 'error' : (isAlreadyRated && ratingMessage.includes('вже оцінили') ? 'info' : '')]">
          {{ ratingMessage }}
        </p>
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
  id: number;
  title: string;
  description: string;
  executionResult: string;
  attachedFileName?: string | null;
  isRatedByCustomer?: boolean; // <--- Додано нове поле
}

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId as string;
const result = ref<TaskResult | null>(null)
const rating = ref<number>(0);
const loadingError = ref<string | null>(null);
const ratingMessage = ref<string>('');
const isAlreadyRated = ref<boolean>(false); // <--- Новий ref для стану "вже оцінено"

const token = localStorage.getItem('jwtToken') || localStorage.getItem('jwt_token');

if (!token) {
  console.error('Токен не знайдено!');
  loadingError.value = 'Помилка автентифікації: токен не знайдено.';
}

const fetchTaskResult = async () => {
  loadingError.value = null;
  ratingMessage.value = ''; // Скидаємо повідомлення про оцінку при завантаженні
  isAlreadyRated.value = false; // Скидаємо стан "вже оцінено"

  if (!token) return;

  try {
    const res = await axios.get<TaskResult>(`http://localhost:8000/user/${taskId}/result`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    result.value = res.data;

    if (res.data.isRatedByCustomer) { // <--- Перевіряємо нове поле
      isAlreadyRated.value = true;
      ratingMessage.value = "Ви вже оцінили це завдання."; // Попередньо встановлюємо повідомлення
      // Можна також завантажити попередню оцінку, якщо бэкенд її повертає
      // rating.value = res.data.previousRatingValue; (якщо таке поле є)
    }

    if (!res.data.executionResult && !res.data.attachedFileName && !isAlreadyRated.value) {
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
        Authorization: `Bearer ${token}`
      },
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ratingMessage.value = `Файл "${filename}" успішно завантажено.`;

  } catch (error: any) {
    console.error('Помилка при завантаженні файлу:', error);
    if (error.response) {
      if (error.response.status === 404) {
        ratingMessage.value = `Помилка: Файл "${filename}" не знайдено на сервері.`;
      } else if (error.response.status === 400) {
        ratingMessage.value = `Помилка: Некоректний запит на завантаження файлу.`;
      } else {
        ratingMessage.value = 'Не вдалося завантажити файл.';
      }
    } else {
      ratingMessage.value = 'Не вдалося завантажити файл. Перевірте консоль.';
    }
  }
};

const submitRating = async () => {
  ratingMessage.value = '';
  if (isAlreadyRated.value) { // <--- Додаткова перевірка
    ratingMessage.value = "Ви вже оцінили це завдання.";
    return;
  }
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
    isAlreadyRated.value = true; // <--- Встановлюємо, що оцінка подана

    setTimeout(() => {
      router.push('/profile');
    }, 2000);

  } catch (e: any) {
    console.error('Не вдалося подати оцінку', e);
    if (e.response && e.response.data && e.response.data.detail) {
      const errorMessage = e.response.data.detail;
      ratingMessage.value = `Помилка: ${errorMessage}`;
      // Якщо бэкенд повертає помилку "Ви вже оцінили це завдання."
      // (хоча ми вже маємо isRatedByCustomer з GET запиту, це для узгодженості)
      if (errorMessage.includes("вже оцінили це завдання")) {
        isAlreadyRated.value = true;
      }
    } else {
      ratingMessage.value = 'Не вдалося подати оцінку.';
    }
  }
};

// ... (решта ваших функцій getFileExtension, getFileDisplayInfo, goToProfile) ...
interface FileDisplayInfo {
  icon: string;
  description: string;
  defaultPreview?: boolean;
}

const getFileExtension = (filename: string | undefined | null): string => {
  if (!filename || typeof filename !== 'string') return '';
  return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
};

const getFileDisplayInfo = (filename: string | undefined | null): FileDisplayInfo => {
  const extension = getFileExtension(filename);
  let icon = '📎';
  let description = 'Файл';
  let defaultPreview = false;

  if (extension) {
    switch (extension) {
      case 'pdf': icon = '📜'; description = 'PDF Документ'; break;
      case 'doc': case 'docx': icon = '📄'; description = 'Документ Word'; break;
      case 'xls': case 'xlsx': icon = '📊'; description = 'Документ Excel'; break;
      case 'ppt': case 'pptx': icon = '🖥️'; description = 'Презентація'; break;
      case 'zip': case 'rar': case '7z': icon = '🗜️'; description = 'Архів'; break;
      case 'txt': icon = '📝'; description = 'Текстовий файл'; break;
      case 'mp3': case 'wav': case 'ogg': icon = '🎵'; description = 'Аудіофайл'; break;
      case 'mp4': case 'avi': case 'mov': case 'mkv': icon = '🎞️'; description = 'Відеофайл'; break;
      case 'jpg': case 'jpeg': case 'png': case 'gif': case 'bmp': case 'webp': case 'svg':
        icon = '🖼️'; description = 'Зображення'; defaultPreview = true; break;
      default: description = `Файл ${extension.toUpperCase()}`;
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
/* ... (Ваші існуючі стилі залишаються тут) ... */
/* Додайте або модифікуйте, якщо потрібно, стиль для .rating-section */
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
  padding: 2.2rem;
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.12);
  width: 100%;
  max-width: 580px;
  color: #f0f0f0;
  text-align: center;
}

.back-link {
  display: block;
  margin-bottom: 1.5rem;
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

.task-result-card h2 {
  font-size: 1.8rem;
  margin-bottom: 1.8rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.result-block {
  margin-bottom: 1.8rem;
}

.result-block h3 {
  font-size: 1.3rem;
  margin-bottom: 0.8rem;
  font-weight: 600;
  color: #e8e9ed;
  text-align: center;
  line-height: 1.4;
}

.result-block p {
  font-size: 0.95rem;
  color: #d5d8de;
  margin-bottom: 0.8rem;
  line-height: 1.6;
  text-align: left;
  word-break: break-word;
}
.result-block p strong {
  color: #f0f0f0;
  font-weight: 600;
  display: block;
  margin-bottom: 0.3rem;
}


.rating-section { /* Новий клас для обгортки блоку оцінки */
  margin-top: 1.5rem; /* Або інший потрібний відступ */
}

.input-group {
  margin-top: 1rem;
  margin-bottom: 1.8rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.rating-container {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.rating-container label {
  color: #d5d8de;
  font-weight: 500;
  font-size: 1rem;
}

.rating-container select {
  width: auto;
  min-width: 60px;
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #f0f0f0; /* Змінено колір тексту на світлий для кращої видимості */
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
/* Стиль для заблокованого select */
.rating-container select:disabled {
  background-color: rgba(255, 255, 255, 0.05);
  color: #888;
  cursor: not-allowed;
  opacity: 0.7;
}


.submit-btn {
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.9rem 1.5rem;
  display: block;
  margin: 1.5rem auto 0;
  min-width: 200px;
  width: auto;
  max-width: 100%;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.submit-btn:hover:not(:disabled) { /* :not(:disabled) щоб ховер не спрацьовував на заблокованій кнопці */
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}


div > p[data-loading-text="true"] {
  color: #b0b8c5 !important;
  font-size: 1.1rem;
  text-align: center;
  font-weight: 500;
  margin-top: 2rem;
}

.task-result-card div > p:first-child:last-child {
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
  gap: 1rem;
}

.file-name {
  font-size: 0.95rem;
  color: #c0c8d5;
  word-break: break-all;
  flex-grow: 1;
}

.download-btn {
  background-color: #007AFF;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
  text-transform: none;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.download-btn:hover {
  background-color: #005bb5;
  transform: translateY(-1px);
}

.download-btn:active {
  transform: translateY(0);
}

.error-message {
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
  padding: 0.5rem 0.8rem; /* Додано падінг для всіх повідомлень */
  border-radius: 6px;     /* Додано радіус для всіх повідомлень */
  font-size: 0.9rem;
  color: #b0b8c5;
  text-align: center;
  font-weight: 500; /* Зроблено жирнішим для кращої видимості */
}
.rating-message.error {
  color: #ff9a9a;
  background-color: rgba(255, 82, 82, 0.1);
  border: 1px solid rgba(255, 82, 82, 0.2);
}
.rating-message.info { /* Додатковий стиль для інформаційних повідомлень, наприклад "вже оцінено" */
  color: #90cdf4; /* Світло-блакитний */
  background-color: rgba(144, 205, 244, 0.1);
  border: 1px solid rgba(144, 205, 244, 0.2);
}


.submit-btn:disabled {
  background-color: #555 !important; /* Важливо для перевизначення */
  cursor: not-allowed !important;
  opacity: 0.6 !important;
  transform: none !important;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2) !important;
}
.submit-btn:disabled:hover { /* Перевизначаємо ховер для заблокованої кнопки */
  background-color: #555 !important;
  transform: none !important;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2) !important;
}

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
  background-color: rgba(60, 55, 80, 0.7);
  border-radius: 12px;
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
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-bubble-icon {
  font-size: 24px;
  color: #e0e1e6;
}

.file-bubble-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-right: 10px;
}

.file-bubble-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-bubble-description {
  font-size: 0.8rem;
  color: #b0b8c5;
}

.file-bubble-download-btn {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #00aaff;
  padding: 8px;
  border-radius: 50%;
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

</style>