<template>
  <main class="task-page">
    <div class="task-card">
      <span class="back-link" @click="goToProfile">← Повернутися в профіль</span>

      <form class="task-form" @submit.prevent="submitCompletion">
        <h2>Виконати завдання</h2>

        <h3 class="task-title">{{ taskTitle }}</h3>

        <div class="input-group">
          <textarea
              v-model="completionText"
              placeholder="Опишіть виконання завдання..."
              required
          ></textarea>
        </div>

        <div class="input-group file-input-group">
          <label for="file-upload" class="file-upload-label">
            Прикріпити файл (необов'язково):
          </label>
          <input
              type="file"
              id="file-upload"
              @change="handleFileUpload"
              class="file-input"
              accept="image/*,application/pdf,.doc,.docx,.txt,.zip"
          />
          <span v-if="selectedFile" class="file-name-display">
            Обраний файл: {{ selectedFile.name }}
            <button type="button" @click="removeSelectedFile" class="remove-file-btn" title="Видалити файл">×</button>
          </span>
        </div>
        <input type="submit" value="Надіслати" />

        <p class="error" v-if="errorMessage">{{ errorMessage }}</p>
      </form>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const taskId = route.params.taskId;
const completionText = ref('');
const errorMessage = ref('');
const taskTitle = ref('');
const jwt = localStorage.getItem('jwtToken');
const selectedFile = ref(null); // Для зберігання обраного файлу
const fileInputRef = ref(null); // Для доступу до input елемента файлу (для скидання)


// Отримати дані про завдання
const fetchTask = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    taskTitle.value = response.data.title;
  } catch (error) {
    console.error('Помилка при завантаженні завдання:', error);
    errorMessage.value = 'Не вдалося завантажити завдання';
  }
};

onMounted(() => {
  fetchTask();
  // Зберігаємо посилання на елемент input type="file" для можливості скидання
  // Оскільки input знаходиться в шаблоні, доступ до нього краще отримати тут або через watch
  // Але для простоти, припускаємо, що він буде доступний для скидання значення
});

// Обробник зміни файлу
const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    // Опціонально: перевірка розміру або типу файлу тут
    // Наприклад:
    // const maxSize = 5 * 1024 * 1024; // 5MB
    // if (file.size > maxSize) {
    //   errorMessage.value = 'Файл занадто великий. Максимальний розмір: 5MB.';
    //   event.target.value = null; // Скидаємо вибір файлу
    //   selectedFile.value = null;
    //   return;
    // }
    // const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    // if (!allowedTypes.includes(file.type)) {
    //   errorMessage.value = 'Недопустимий тип файлу. Дозволені: JPG, PNG, PDF.';
    //   event.target.value = null; // Скидаємо вибір файлу
    //   selectedFile.value = null;
    //   return;
    // }
    selectedFile.value = file;
    errorMessage.value = ''; // Очищаємо помилку, якщо була
    // console.log('Обраний файл:', file);
  } else {
    selectedFile.value = null;
  }
};

const removeSelectedFile = () => {
  selectedFile.value = null;
  // Скидаємо значення input type="file"
  // Це трохи складніше, оскільки v-model не працює напряму з input type="file"
  // Один із способів - перестворити елемент або скинути його значення через ref
  const fileInputElement = document.getElementById('file-upload');
  if (fileInputElement) {
    fileInputElement.value = ""; // Це спрацює у більшості сучасних браузерів
  }
};


const submitCompletion = async () => {
  errorMessage.value = ''; // Скидаємо попередні помилки
  if (!completionText.value.trim()) {
    errorMessage.value = 'Будь ласка, опишіть виконання завдання.';
    return;
  }

  // Використовуємо FormData для відправки тексту та файлу
  const formData = new FormData();
  formData.append('execution_description', completionText.value);

  if (selectedFile.value) {
    formData.append('file', selectedFile.value); // 'file' - це ключ, який очікуватиме FastAPI
  }

  try {
    const response = await axios.post(`http://localhost:8000/tasks/${taskId}/complete`, formData, {
      headers: {
        Authorization: `Bearer ${jwt}`,
        'Content-Type': 'multipart/form-data' // Важливо для відправки файлів
      }
    });
    console.log('Завдання виконано:', response.data);
    router.push('/profile');
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      if (typeof error.response.data.detail === 'string') {
        errorMessage.value = `Помилка: ${error.response.data.detail}`;
      } else if (Array.isArray(error.response.data.detail)) {
        // Обробка помилок валідації від FastAPI (масив словників)
        errorMessage.value = error.response.data.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ');
      } else {
        errorMessage.value = 'Сталася невідома помилка при надсиланні.';
      }
    } else {
      errorMessage.value = 'Помилка при надсиланні результату завдання. Перевірте консоль.';
    }
    console.error('Деталі помилки:', error.response || error);
  }
};

// ДОДАНО ФУНКЦІЮ ДЛЯ ПОВЕРНЕННЯ НА СТОРІНКУ ПРОФІЛЮ
const goToProfile = () => {
  router.push('/profile');
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

.task-page {
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

.task-card {
  background: rgba(30, 25, 45, 0.85); /* Темний, насичений фон картки */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 2.5rem 3rem; /* Збалансовані падінги */
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45); /* Глибша тінь */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла межа */
  width: 100%;
  max-width: 550px;
  color: #f0f0f0;
  text-align: left; /* Вирівнювання по лівому краю для вмісту форми */
}

.back-link {
  display: inline-block;
  margin-bottom: 1.8rem; /* Відступ знизу перед заголовком h2 */
  color: #b0b8c5; /* Світло-сіро-блакитний для посилань */
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.95rem;
  padding: 0.2rem 0; /* Мінімальний падінг для текстового посилання */
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.task-form h2 {
  font-size: 2rem;
  margin-bottom: 1.2rem;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.task-title {
  font-size: 1.25rem;
  margin-bottom: 1.8rem;
  font-weight: 500;
  color: #e0e1e6;
  text-align: center;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.input-group {
  position: relative;
  margin-bottom: 1.5rem; /* Трохи зменшено для щільності */
}
.file-input-group {
  margin-bottom: 2rem; /* Більший відступ для групи файлу */
}

.input-group textarea {
  width: 100%;
  padding: 0.9rem 1.1rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  color: #ffffff;
  font-size: 1rem;
  font-family: 'Poppins', sans-serif;
  outline: none;
  resize: vertical;
  min-height: 120px; /* Зменшено мінімальну висоту */
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.input-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-group textarea:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

/* СТИЛІ ДЛЯ ПОЛЯ ЗАВАНТАЖЕННЯ ФАЙЛУ */
.file-upload-label {
  display: block;
  color: #b0b8c5;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.file-input {
  width: 100%;
  padding: 0.7rem 0.9rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  color: #f0f0f0;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.file-input::file-selector-button { /* Стилізація кнопки всередині input[type=file] */
  padding: 0.6rem 1rem;
  margin-right: 1rem;
  background-color: #007AFF;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.file-input::file-selector-button:hover {
  background-color: #005bb5;
}

.file-input:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.file-name-display {
  display: block;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #c0c8d5;
  background-color: rgba(0,0,0,0.2);
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  word-break: break-all; /* Для довгих імен файлів */
}

.remove-file-btn {
  background: none;
  border: none;
  color: #ff9a9a;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  margin-left: 0.5rem;
  padding: 0 0.3rem;
  line-height: 1;
  vertical-align: middle; /* Або інше значення для кращого вирівнювання */
}
.remove-file-btn:hover {
  color: #ff6b6b;
}


/* КІНЕЦЬ СТИЛІВ ДЛЯ ПОЛЯ ЗАВАНТАЖЕННЯ ФАЙЛУ */

input[type="submit"] {
  background-color: #007AFF;
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
  margin-top: 1rem; /* Додано відступ зверху */
}

input[type="submit"]:hover {
  background-color: #005bb5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.error {
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
</style>