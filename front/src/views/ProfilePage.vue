<template>
  <div>
    <Navbar />
    <router-view />
  </div>
  <main class="profile-page">
    <h1 class="Profile123">Профіль користувача</h1>

    <div class="user-info">
      <p>
        <strong><span class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-3-3.87 4 4 0 0 0-6 0A4 4 0 0 0 8 19v2"/>
            <circle cx="14" cy="7" r="4"/>
          </svg>
        </span></strong>
        {{ user.username }}
      </p>

      <p>
        <strong><span class="icon">
          <svg xmlns="http://www.w3.org/2000/svg" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 6l10 7 10-7"/>
            <path d="M3 3h18c.552 0 1 .448 1 1v16c0 .552-.448 1-1 1H3c-.552 0-1-.448-1-1V4c0-.552.448-1 1-1z"/>
          </svg>
        </span></strong>
        {{ user.email }}
      </p>
      <p v-if="user.rating !== null && user.rating !== undefined">
        <strong>Рейтинг:</strong> {{ user.rating }}
      </p>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'startups' }" @click="activeTab = 'startups'">Мої стартапи</button>
      <button :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'">Активні завдання</button>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'startups'">
        <h2>Мої стартапи</h2>
        <button class="create-startup-btn" @click="createStartup">+ Створити стартап</button>
        <ul v-if="startups.length">
          <li v-for="startupItem in startups" :key="startupItem.id" class="task-item">
            <div class="task-header" @click="toggleExpand('startup', startupItem.id)">
              <div class="task-title centered-title">{{ startupItem.name }}</div>
              <span class="expand-toggle">{{ expandedIds.startups[startupItem.id] ? '▲' : '▼' }}</span>
            </div>
            <transition name="expand">
              <div v-show="expandedIds.startups[startupItem.id]" class="task-details expandable">
                <p>{{ startupItem.description }}</p>
                <h4>Завдання:</h4>
                <ul v-if="startupItem.tasks && startupItem.tasks.length">
                  <li v-for="taskItem in startupItem.tasks" :key="taskItem.id">
                    <div class="task-toggle" @click="toggleExpand('task', taskItem.id)">
                      <span class="task-title-text">{{ taskItem.title }}</span>
                      <span class="expand-toggle">{{ expandedIds.tasks[taskItem.id] ? '▲' : '▼' }}</span>
                    </div>
                    <transition name="expand">
                      <div v-show="expandedIds.tasks[taskItem.id]" class="task-details expandable">
                        <p>{{ taskItem.description }}</p>
                        <p>Статус: {{ getStatusText(taskItem.status) }}</p>
                        <button v-if="taskItem.status !== 'in_progress' && taskItem.status !== 'paid'" class="edit-btn" @click.stop="editTask(taskItem.id)">Редагувати</button>
                        <button v-if="taskItem.status === 'paid'" class="complete-btn" @click.stop="viewTaskResult(taskItem.id)">Переглянути результат</button>
                        <button v-if="taskItem.status === 'in_progress'" class="remove-executor-btn" @click.stop="removeExecutorByOwner(taskItem.id)">Відключити виконавця</button>
                      </div>
                    </transition>
                  </li>
                </ul>
                <p v-else>Немає завдань</p>

                <div class="startup-actions">
                  <button class="complete-btn" @click.stop="editStartup(startupItem.id)">Редагувати стартап</button>
                  <button class="edit-btn" @click.stop="createTask(startupItem.id)">+ Додати завдання</button>
                </div>

                <h4 class="comments-heading">Коментарі до стартапу:</h4>
                <ul v-if="startupItem.comments && startupItem.comments.length" class="startup-comments-list">
                  <li v-for="commentEntry in startupItem.comments" :key="commentEntry.id" class="comment-entry">
                    <div class="comment-entry-header">
                      <strong class="comment-author">{{ commentEntry.author_username }}</strong>
                      <div class="comment-meta-and-actions">
                        <span class="comment-date-small">{{ new Date(commentEntry.created_at).toLocaleString() }}</span>
                        <button @click.stop="confirmDeleteStartupComment(startupItem.id, commentEntry.id)" class="delete-comment-icon" title="Видалити коментар">
                          &#x2715; </button>
                      </div>
                    </div>
                    <p class="comment-text-small">{{ commentEntry.text }}</p>
                  </li>
                </ul>
                <p v-else class="no-comments-text">До цього стартапу ще немає коментарів.</p>
              </div>
            </transition>
          </li>
        </ul>
        <p v-else>Немає стартапів.</p>
      </div>

      <div v-if="activeTab === 'tasks'">
        <h2>Активні завдання</h2>
        <ul v-if="tasks.length">
          <li v-for="task in tasks" :key="task.id" class="task-item">
            <div class="task-header" @click="toggleExpand('task', task.id)">
              <div class="task-title centered-title">{{ task.title }}</div>
              <span class="expand-toggle">{{ expandedIds.tasks[task.id] ? '▲' : '▼' }}</span>
            </div>

            <transition name="expand">
              <div
                  v-show="expandedIds.tasks[task.id]"
                  class="task-details expandable"
              >
                <p>{{ task.description }}</p>
                <p>Статус: {{ getStatusText(task.status) }}</p>
                <p v-if="task.owner_name">Замовник: {{ task.owner_name }}</p>

                <button
                    v-if="task.status === 'in_progress'"
                    class="complete-btn"
                    @click.stop="markTaskAsCompleted(task.id)"
                >
                  Виконати
                </button>
                <button
                    v-if="task.status === 'in_progress'"
                    class="refuse-btn"
                    @click.stop="refuseTask(task.id)"
                >
                  Відмовитися
                </button>
                <button
                    v-else-if="task.status === 'done'"
                    class="complete-btn"
                    @click.stop="markTaskAsPaid(task.id)"
                >
                  Відправити замовнику
                </button>
              </div>
            </transition>
          </li>
        </ul>
        <p v-else>Немає активних завдань.</p>
      </div>
    </div>
  </main>
</template>

<script setup>
import Navbar from '../components/Navbar.vue'
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = ref({ username: '', email: '', rating: null })
const startups = ref([]) // Тепер startups будуть містити коментарі
const tasks = ref([])
// const userComments = ref([]) // Цей ref більше не потрібен, якщо немає окремої вкладки
const activeTab = ref('startups')
const expandedIds = ref({ startups: {}, tasks: {} }) // Для розгортання стартапів та їхніх завдань
const jwt = localStorage.getItem('jwtToken')

const fetchProfile = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/profile', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    user.value = res.data
  } catch (e) {
    console.error('Не вдалося завантажити профіль', e)
  }
}

// fetchStartups тепер завантажує стартапи з їхніми завданнями та коментарями
const fetchStartups = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/startups', { // Ендпоінт тепер повертає і коментарі
      headers: { Authorization: `Bearer ${jwt}` }
    })
    startups.value = res.data.map(startup => ({
      ...startup,
      // Переконуємося, що tasks та comments ініціалізовані як масиви, якщо вони можуть бути відсутні
      tasks: startup.tasks || [],
      comments: startup.comments || []
    }));
    // Ініціалізуємо expandedIds для нових стартапів, якщо потрібно (щоб уникнути помилок)
    startups.value.forEach(s => {
      if (expandedIds.value.startups[s.id] === undefined) {
        expandedIds.value.startups[s.id] = false;
      }
      s.tasks.forEach(t => {
        if (expandedIds.value.tasks[t.id] === undefined) {
          expandedIds.value.tasks[t.id] = false;
        }
      });
    });
  } catch (e) {
    console.error('Помилка при завантаженні стартапів з коментарями', e)
  }
}

const fetchTasks = async () => { // Для вкладки "Активні завдання"
  try {
    const res = await axios.get('http://localhost:8000/user/tasks', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    tasks.value = res.data;
    tasks.value.forEach(t => {
      if (expandedIds.value.tasks[t.id] === undefined) {
        expandedIds.value.tasks[t.id] = false;
      }
    });
  } catch (e) {
    console.error('Помилка при завантаженні завдань', e)
  }
}

// Функція fetchUserComments більше не потрібна, якщо немає окремої вкладки

const getStatusText = (status) => {
  if (status === 'in_progress') return 'Очікує на виконання!'
  if (status === 'pending') return 'Очікує на виконавця'
  if (status === 'done') return 'Очікує оплати!'
  if (status === 'paid') return 'Оплачено'
  return status
}

const toggleExpand = (type, id) => {
  if (type === 'startup') {
    expandedIds.value.startups[id] = !expandedIds.value.startups[id]
  } else if (type === 'task') {
    expandedIds.value.tasks[id] = !expandedIds.value.tasks[id]
  }
}

// --- Функції для навігації та дій з завданнями/стартапами (залишаються) ---
const markTaskAsCompleted = (taskId) => router.push({ name: 'CompleteTask', params: { taskId } });
const markTaskAsPaid = async (taskId) => {
  try {
    await axios.put(`http://localhost:8000/user/tasks/${taskId}/status`, { status: 'paid' }, { headers: { Authorization: `Bearer ${jwt}` } });
    await fetchTasks();
  } catch (e) { console.error('Не вдалося оновити статус на paid', e); }
};
const createStartup = () => router.push('/create-startup');
const editStartup = (startupId) => router.push(`/edit-startup/${startupId}`);
const createTask = (startupId) => router.push(`/create-task?startup_id=${startupId}`);
const editTask = (taskId) => router.push(`/edit-task/${taskId}`);
const viewTaskResult = (taskId) => router.push(`/task-result/${taskId}`);

const fetchUserRating = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/rating', { headers: { Authorization: `Bearer ${jwt}` } });
    user.value.rating = res.data.average_rating;
  } catch (e) { console.error('Не вдалося отримати рейтинг', e); }
};

const refuseTask = async (taskId) => {
  if (!confirm('Ви впевнені, що хочете відмовитися від цього завдання?')) return;
  try {
    await axios.put(`http://localhost:8000/user/tasks/${taskId}/refuse`, {}, { headers: { Authorization: `Bearer ${jwt}` } });
    await fetchTasks();
    alert('Ви успішно відмовилися від завдання.');
  } catch (e) {
    console.error('Не вдалося відмовитися від завдання', e);
    alert(`Помилка при відмові від завдання: ${e.response?.data?.detail || e.message}`);
  }
};

const removeExecutorByOwner = async (taskId) => {
  if (!confirm('Ви впевнені, що хочете відключити виконавця від цього завдання?')) return;
  try {
    await axios.put(`http://localhost:8000/user/startups/tasks/${taskId}/remove-executor`, {}, { headers: { Authorization: `Bearer ${jwt}` } });
    await fetchStartups(); // Оновлюємо стартапи, оскільки статус завдання змінився
    alert('Виконавця успішно відключено.');
  } catch (e) {
    console.error('Не вдалося відключити виконавця:', e);
    alert(`Помилка при відключенні виконавця: ${e.response?.data?.detail || e.message}`);
  }
};

const deleteStartupComment = async (startupId, commentId) => {
  try {
    // Додаємо префікс /user/ до URL
    await axios.delete(`http://localhost:8000/user/startups/${startupId}/comments/${commentId}`, {
      headers: { Authorization: `Bearer ${jwt}` }
    });
    await fetchStartups(); // Перезавантажуємо стартапи, щоб оновити список коментарів
    alert('Коментар до стартапу успішно видалено.');
  } catch (e) {
    console.error('Помилка при видаленні коментаря стартапу', e);
    // Більш детальне повідомлення про помилку для діагностики
    if (e.response) {
      alert(`Помилка видалення: ${e.response.status} - ${e.response.data.detail || e.message}`);
    } else {
      alert(`Помилка мережі або запиту: ${e.message}`);
    }
  }
};

const confirmDeleteStartupComment = (startupId, commentId) => {
  if (confirm('Ви впевнені, що хочете видалити цей коментар зі стартапу?')) {
    deleteStartupComment(startupId, commentId);
  }
};

// Стара функція deleteComment (якщо була для окремої вкладки "Мої коментарі") тепер не потрібна

// Слідкуємо за зміною активної вкладки для завантаження відповідних даних
watch(activeTab, (newTab, oldTab) => {
  if (newTab === 'startups' && startups.value.length === 0) { // Завантажуємо стартапи, якщо їх ще немає
    fetchStartups();
  } else if (newTab === 'tasks' && tasks.value.length === 0) { // Завантажуємо завдання, якщо їх ще немає
    fetchTasks();
  }
  // Логіка для вкладки "comments" видалена, якщо вкладка прибрана
});

onMounted(() => {
  fetchProfile();
  fetchUserRating();
  // Завантажуємо дані для активної вкладки за замовчуванням
  if (activeTab.value === 'startups') {
    fetchStartups();
  } else if (activeTab.value === 'tasks') {
    fetchTasks();
  }
});

</script>

<style scoped>
/* Стилі для розділу коментарів всередині стартапу */
.startup-actions { /* Обгортка для кнопок "Редагувати стартап" та "+ Додати завдання" */
  margin-top: 1.5rem; /* Відступ зверху перед кнопками */
  display: flex;
  justify-content: center; /* Додано для центрування по горизонталі */
  gap: 0.8rem; /* Відстань між кнопками */
  flex-wrap: wrap; /* Дозволяє кнопкам переноситися, якщо не вистачає місця */
  margin-bottom: 1rem; /* Відступ знизу, перед заголовком коментарів */
}

.comments-heading {
  font-size: 1.1rem;
  font-weight: 600;
  color: #d5d8de;
  /* margin-top: 1.5rem;  Цей відступ тепер регулюється margin-bottom від .startup-actions */
  margin-bottom: 0.8rem;
  padding-top: 0.8rem; /* Можна залишити для внутрішнього відступу, якщо потрібен */
  border-top: 1px solid rgba(255, 255, 255, 0.1); /* Лінія-розділювач */
}

.startup-comments-list {
  list-style: none;
  padding-left: 0;
  margin-top: 0.5rem;
}

.comment-entry {
  background-color: rgba(255, 255, 255, 0.03);
  padding: 0.8rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.8rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.comment-entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.comment-author {
  font-weight: 600;
  color: #c8c9ce;
  font-size: 0.95rem;
  margin-right: auto; /* Щоб ім'я автора займало доступний простір зліва */
}

.comment-meta-and-actions { /* Нова обгортка для дати та кнопки видалення */
  display: flex;
  align-items: center;
  gap: 0.75rem; /* Проміжок між датою та хрестиком */
  margin-left: 0.5rem; /* Невеликий відступ зліва від імені автора */
}

.comment-date-small {
  font-size: 0.8rem;
  color: #8a8f9c;
}

.delete-comment-icon { /* Стиль для іконки-хрестика */
  background: none;
  border: none;
  color: #e74c3c; /* Червоний колір, як у кнопки "Відмовитися" */
  font-size: 1.2rem; /* Розмір хрестика */
  font-weight: bold;
  cursor: pointer;
  padding: 0.1rem 0.3rem; /* Невеликий паддінг для зручності кліку */
  line-height: 1; /* Для кращого вертикального вирівнювання */
  transition: color 0.2s ease;
}

.delete-comment-icon:hover {
  color: #c0392b; /* Темніший червоний при наведенні */
}

.comment-text-small {
  font-size: 0.9rem;
  color: #b0b3b8;
  line-height: 1.5;
  margin-bottom: 0.3rem; /* Зменшив відступ, оскільки кнопка тепер не текстова */
  white-space: pre-wrap;
}

/* Стиль для старої кнопки видалення, якщо вона ще десь використовується, або можна видалити */
/*
.delete-comment-btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  margin-top: 0.3rem;
  align-self: flex-end;
}
*/

.no-comments-text {
  color: #a0a8b5;
  font-style: italic;
  margin-top: 0.5rem;
  padding-left: 0.5rem;
}

/* ... (решта ваших стилів) ... */
.profile-page {
  padding: 2rem;
  padding-top: 80px; /* Відступ для Navbar */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #f0f0f0;
  background-image: url('../assets/img.jpg'); /* Переконайтесь, що шлях правильний */
  background-size: cover;
  background-position: center;
  background-attachment: fixed; /* Фіксований фон */
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center; /* Центруємо основний контент */
  width: 100%;
}

.Profile123 {
  font-size: 2.2rem;
  font-weight: 600;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  margin-top: 50px;
  margin-bottom: 2.5rem;
  text-align: center;
}

.user-info {
  background: rgba(35, 30, 50, 0.65);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 1.8rem 2.2rem;
  margin-bottom: 2rem;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 240px;
  text-align: center;
}

.user-info p {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  margin-bottom: 0.8rem;
  color: #e0e1e6;
}
.user-info p:last-child {
  margin-bottom: 0;
}
.user-info strong {
  color: #ffffff;
  font-weight: 500;
}
.icon {
  display: inline-flex;
  align-items: center;
  margin-right: 0.8rem;
  color: #a0a8b5;
}
.icon-svg {
  width: 1.2em;
  height: 1.2em;
  stroke: currentColor;
}

.tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.tabs button {
  padding: 0.7rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  background: rgba(50, 50, 70, 0.5);
  color: #e0e1e6;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 500;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.tabs button:hover {
  background: rgba(70, 70, 90, 0.65);
  border-color: rgba(255, 255, 255, 0.3);
}

.tabs button.active {
  background: #007aff;
  border-color: #007aff;
  color: #ffffff;
  box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
}

.tab-content {
  width: 100%;
  max-width: 800px;
}
.tab-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 1.5rem;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.tab-content ul {
  list-style: none;
  padding-left: 0;
  width: 100%;
}

.task-item { /* Загальний стиль для елементів списку, включаючи коментарі */
  background: rgba(35, 30, 50, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 1.5rem;
  border-radius: 16px;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: box-shadow 0.3s ease;
}
.task-item:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.35);
}

.task-header, .task-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 1rem;
}
.task-item ul .task-toggle { /* Стилі для списку завдань всередині стартапу */
  border-top: 1px solid rgba(255,255,255,0.05);
  margin-top: 0.5rem;
  padding: 0.5rem 0; /* Додав padding для консистентності */
  margin-bottom: 0.5rem; /* Додав margin-bottom */
}
.task-item > .task-header { /* Стилі для заголовку самого стартапу */
  padding-top: 0;
  margin-bottom: 1rem;
}

.task-title, .task-title-text {
  flex-grow: 1;
  font-size: 1.1rem;
  font-weight: 600;
  color: #e8e9ed;
}
.centered-title {
  text-align: center;
  font-size: 1.2rem;
}
.task-title-text { /* Назва завдання всередині стартапу */
  margin-left: 0; /* Прибираємо відступ, якщо є */
  white-space: normal;
  font-size: 1rem; /* Трохи менше, ніж назва стартапу */
}

.expand-toggle {
  font-size: 1.3rem;
  color: #a0a8b5;
  padding: 0.3rem;
  transition: transform 0.4s ease-in-out;
}

.task-details { /* Для розгорнутого контенту стартапу та завдання */
  padding-top: 0.8rem;
  color: #c5c8ce;
  line-height: 1.6;
}
.task-details p {
  margin: 0.6rem 0;
}
.task-details h4 { /* Заголовок "Завдання:" всередині стартапу */
  font-size: 1rem;
  font-weight: 600;
  color: #d5d8de;
  margin-top: 1.2rem;
  margin-bottom: 0.5rem;
}
.task-details ul { /* Список завдань або коментарів */
  padding-left: 1rem; /* Відступ для вкладених списків */
  margin-top: 0.5rem;
}
.task-details ul li { /* Елемент завдання або коментаря в списку */
  background: transparent; /* Прозорий фон, якщо не перевизначено */
  padding: 0.3rem 0;
  border-radius: 0;
  margin-bottom: 0.3rem;
  box-shadow: none;
  border: none;
}


.create-startup-btn, .edit-btn, .complete-btn, .refuse-btn, .remove-executor-btn {
  padding: 0.7rem 1.3rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
  margin-right: 0.8rem;
  margin-top: 1rem;
}
/* Останній кнопці в блоці прибираємо правий відступ */
.startup-actions button:last-child { /* Застосовуємо до кнопок всередині .startup-actions */
  margin-right: 0;
}
.comment-entry button:last-child { /* Це для кнопки-хрестика, якщо вона буде останньою, але вона єдина */
  margin-right: 0;
}


.create-startup-btn {
  background-color: #007aff;
  color: #ffffff;
  display: block; /* Щоб margin auto працював */
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 1.5rem;
}
.create-startup-btn:hover {
  background-color: #005bb5;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.4);
}

.edit-btn { /* Кнопка "Редагувати", "+ Додати завдання" */
  background-color: rgba(147, 38, 198, 0.7); /* Фіолетовий */
  color: #ffffff;
}
.edit-btn:hover {
  background-color: rgba(120, 30, 160, 0.8);
  box-shadow: 0 2px 8px rgba(147, 38, 198, 0.4);
}

.complete-btn { /* Кнопка "Виконати", "Переглянути результат", "Редагувати стартап" */
  background-color: transparent;
  color: #82ddf0; /* Світло-блакитний */
  border: 1px solid #82ddf0;
}
.complete-btn:hover {
  background-color: rgba(130, 221, 240, 0.15);
  border-color: #a0e5f3;
  box-shadow: 0 2px 8px rgba(130, 221, 240, 0.3);
}
.complete-btn.paid-style { /* Для кнопки "Відправити замовнику" коли статус paid */
  border-color: #5cb85c; /* Зелений */
  color: #5cb85c;
}
.complete-btn.paid-style:hover {
  background-color: rgba(92, 184, 92, 0.15);
  border-color: #77c977;
  box-shadow: 0 2px 8px rgba(92, 184, 92, 0.3);
}

.refuse-btn { /* Кнопка "Відмовитися" (якщо окрема) */
  background-color: #e74c3c; /* Червоний */
  color: white;
}
.refuse-btn:hover {
  background-color: #c0392b; /* Темніший червоний */
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4);
}
.remove-executor-btn { /* Кнопка "Відключити виконавця" */
  background-color: #e67e22; /* Помаранчевий */
  color: white;
}
.remove-executor-btn:hover {
  background-color: #d35400; /* Темніший помаранчевий */
  box-shadow: 0 2px 8px rgba(230, 126, 34, 0.4);
}


.expandable {
  overflow: hidden;
}
.expand-enter-active,
.expand-leave-active {
  transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  opacity 0.45s cubic-bezier(0.4, 0, 0.2, 1) 0.05s,
  padding-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  padding-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 1000px; /* Або більше, якщо контент може бути дуже високим */
  opacity: 1;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}
</style>