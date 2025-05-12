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
          <li v-for="startupItem in startups" :key="startupItem.id" class="task-item"> <div class="task-header" @click="toggleExpand('startup', startupItem.id)">
            <div class="task-title centered-title">{{ startupItem.name }}</div>
            <span class="expand-toggle">{{ expandedIds.startups[startupItem.id] ? '▲' : '▼' }}</span>
          </div>

            <transition name="expand">
              <div
                  v-show="expandedIds.startups[startupItem.id]"
                  class="task-details expandable"
              >
                <p>{{ startupItem.description }}</p>
                <h4>Завдання:</h4>
                <ul v-if="startupItem.tasks && startupItem.tasks.length">
                  <li v-for="taskItem in startupItem.tasks" :key="taskItem.id"> <div class="task-toggle" @click="toggleExpand('task', taskItem.id)">
                    <span class="task-title-text">{{ taskItem.title }}</span>
                    <span class="expand-toggle">{{ expandedIds.tasks[taskItem.id] ? '▲' : '▼' }}</span>
                  </div>

                    <transition name="expand">
                      <div
                          v-show="expandedIds.tasks[taskItem.id]"
                          class="task-details expandable"
                      >
                        <p>{{ taskItem.description }}</p>
                        <p>Статус: {{ getStatusText(taskItem.status) }}</p>

                        <button
                            v-if="taskItem.status !== 'in_progress' && taskItem.status !== 'paid'"
                            class="edit-btn"
                            @click.stop="editTask(taskItem.id)"
                        >
                          Редагувати
                        </button>

                        <button
                            v-if="taskItem.status === 'paid'"
                            class="complete-btn"
                            @click.stop="viewTaskResult(taskItem.id)"
                        >
                          Переглянути результат
                        </button>

                        <button
                            v-if="taskItem.status === 'in_progress'"
                            class="remove-executor-btn"
                            @click.stop="removeExecutorByOwner(taskItem.id)"
                        >
                          Відключити виконавця
                        </button>

                      </div>
                    </transition>
                  </li>
                </ul>
                <p v-else>Немає завдань</p>

                <button class="complete-btn" @click.stop="editStartup(startupItem.id)">Редагувати</button>
                <button class="edit-btn" @click.stop="createTask(startupItem.id)">+ Додати завдання</button>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = ref({ username: '', email: '', rating: null })
const startups = ref([])
const tasks = ref([])
const activeTab = ref('startups')
const expandedIds = ref({ startups: {}, tasks: {} })
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

const fetchStartups = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/startups', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    startups.value = res.data
  } catch (e) {
    console.error('Помилка при завантаженні стартапів', e)
  }
}

const fetchTasks = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/tasks', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    tasks.value = res.data
  } catch (e) {
    console.error('Помилка при завантаженні завдань', e)
  }
}

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

const markTaskAsCompleted = (taskId) => {
  router.push({ name: 'CompleteTask', params: { taskId } })
}

const markTaskAsPaid = async (taskId) => {
  try {
    await axios.put(
        `http://localhost:8000/user/tasks/${taskId}/status`,
        { status: 'paid' },
        { headers: { Authorization: `Bearer ${jwt}` } }
    )
    await fetchTasks() // Оновити список після змін
  } catch (e) {
    console.error('Не вдалося оновити статус на paid', e)
  }
}

const createStartup = () => {
  router.push('/create-startup')
}

const editStartup = (startupId) => {
  router.push(`/edit-startup/${startupId}`)
}

const createTask = (startupId) => {
  router.push(`/create-task?startup_id=${startupId}`)
}

const editTask = (taskId) => {
  router.push(`/edit-task/${taskId}`)
}

const viewTaskResult = (taskId) => {
  router.push(`/task-result/${taskId}`)
}
const fetchUserRating = async () => {
  try {
    const res = await axios.get('http://localhost:8000/user/rating', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    console.log('Рейтинг отримано:', res.data.rating); // Додайте цей рядок для перевірки
    user.value.rating = res.data.average_rating

  } catch (e) {
    console.error('Не вдалося отримати рейтинг', e)
  }
}
const refuseTask = async (taskId) => {
  try {
    // Запит на новий ендпоінт для відмови від завдання
    await axios.put(
        `http://localhost:8000/user/tasks/${taskId}/refuse`,
        {}, // Тіло запиту може бути порожнім, якщо дані не потрібні
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    // Оновити список активних завдань (завдання має зникнути зі списку)
    await fetchTasks();
    // Тут можна додати сповіщення для користувача (наприклад, alert або через систему нотифікацій)
    // alert('Ви успішно відмовилися від завдання.');
  } catch (e) {
    console.error('Не вдалося відмовитися від завдання', e);
    // Обробка помилки, сповіщення користувача
    // alert(`Помилка при відмові від завдання: ${e.response?.data?.detail || e.message}`);
  }
};
const removeExecutorByOwner = async (taskId) => {
  // Можна додати запит на підтвердження дії
  // if (!confirm('Ви впевнені, що хочете відключити виконавця від цього завдання?')) {
  //   return;
  // }
  try {
    await axios.put(
        `http://localhost:8000/user/startups/tasks/${taskId}/remove-executor`,
        {}, // Тіло запиту не потрібне
        { headers: { Authorization: `Bearer ${jwt}` } }
    );
    // Оновити список стартапів, щоб відобразити зміни в завданнях
    await fetchStartups();
    // alert('Виконавця успішно відключено, завдання переведено в статус "Очікує на виконавця".');
  } catch (e) {
    console.error('Не вдалося відключити виконавця:', e);
    // alert(`Помилка при відключенні виконавця: ${e.response?.data?.detail || e.message}`);
  }
};
onMounted(() => {
  fetchProfile()
  fetchStartups()
  fetchTasks()
  fetchUserRating()
})
</script>

<style scoped>
/* ... (всі ваші попередні стилі для .profile-page, .user-info, .tabs, .task-item, кнопок і т.д. ЗАЛИШАЮТЬСЯ ЯК Є) ... */

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

/* Заголовок сторінки */
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
  max-width: 240px; /* У вашому коді було 240px, якщо це ок, залишаємо */
  text-align: center; /* Текст всередині user-info буде по центру */
}

.user-info p {
  display: flex;
  align-items: center;
  justify-content: center; /* Для центрування іконки та тексту, якщо text-align:center у батька */
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

.task-item {
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
.task-item ul .task-toggle {
  border-top: 1px solid rgba(255,255,255,0.05);
  margin-top: 0.5rem;
}
.task-item > .task-header {
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
.task-title-text {
  margin-left: 0;
  white-space: normal;
}

.expand-toggle {
  font-size: 1.3rem;
  color: #a0a8b5;
  padding: 0.3rem;
  transition: transform 0.4s ease-in-out; /* Збільшено тривалість для стрілки */
}
/* .task-header .expand-toggle, .task-toggle .expand-toggle {
  transform: translateY(0);
} */
/* Цей блок вище не потрібен, якщо ви просто змінюєте текст стрілки ▲/▼ */
/* Якщо ви використовуєте CSS для обертання стрілки, тоді клас .rotated потрібен */


.task-details {
  padding-top: 0.8rem; /* Збільшено для кращого ефекту при розгортанні */
  color: #c5c8ce;
  line-height: 1.6;
}
.task-details p {
  margin: 0.6rem 0;
}
.task-details h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #d5d8de;
  margin-top: 1.2rem;
  margin-bottom: 0.5rem;
}
.task-details ul {
  padding-left: 1rem;
  margin-top: 0.5rem;
}
.task-details ul li {
  background: transparent;
  padding: 0.3rem 0;
  border-radius: 0;
  margin-bottom: 0.3rem;
  box-shadow: none;
  border: none;
}

/* Кнопки дій */
.create-startup-btn, .edit-btn, .complete-btn {
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
.task-details button:last-child {
  margin-right: 0;
}

.create-startup-btn {
  background-color: #007aff;
  color: #ffffff;
  display: block;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 1.5rem;
}
.create-startup-btn:hover {
  background-color: #005bb5;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.4);
}

.edit-btn {
  background-color: rgba(147, 38, 198, 0.7);
  color: #ffffff;
}
.edit-btn:hover {
  background-color: rgba(120, 30, 160, 0.8);
  box-shadow: 0 2px 8px rgba(147, 38, 198, 0.4);
}

.complete-btn {
  background-color: transparent;
  color: #82ddf0;
  border: 1px solid #82ddf0;
}
.complete-btn:hover {
  background-color: rgba(130, 221, 240, 0.15);
  border-color: #a0e5f3;
  box-shadow: 0 2px 8px rgba(130, 221, 240, 0.3);
}
.complete-btn.paid-style {
  border-color: #5cb85c;
  color: #5cb85c;
}
.complete-btn.paid-style:hover {
  background-color: rgba(92, 184, 92, 0.15);
  border-color: #77c977;
  box-shadow: 0 2px 8px rgba(92, 184, 92, 0.3);
}

/* ОНОВЛЕНІ СТИЛІ АНІМАЦІЇ */
.expandable {
  overflow: hidden;
}
.expand-enter-active,
.expand-leave-active {
  transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  opacity 0.45s cubic-bezier(0.4, 0, 0.2, 1) 0.05s, /* Opacity анімується з невеликою затримкою */
  padding-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  padding-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 1000px; /* Або більше, якщо контент може бути дуже високим */
  opacity: 1;
  /* padding-top та padding-bottom будуть взяті з .task-details або встановлені тут */
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0 !important; /* !important для перевизначення, якщо є конфлікти */
  padding-bottom: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  /* Сюди можна додати інші властивості, які мають анімуватися до 0, наприклад, border-width */
}
.refuse-btn {
  background-color: #e74c3c; /* Червоний колір */
  color: white;
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

.refuse-btn:hover {
  background-color: #c0392b; /* Темніший червоний при наведенні */
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4);
}
.remove-executor-btn {
  background-color: #e67e22; /* Наприклад, помаранчевий */
  color: white;
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

.remove-executor-btn:hover {
  background-color: #d35400; /* Темніший помаранчевий */
  box-shadow: 0 2px 8px rgba(230, 126, 34, 0.4);
}
</style>
