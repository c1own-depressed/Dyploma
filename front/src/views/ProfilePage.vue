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
          <li v-for="startup in startups" :key="startup.id" class="task-item">
            <div class="task-header" @click="toggleExpand('startup', startup.id)">
              <div class="task-title centered-title">{{ startup.name }}</div>
              <span class="expand-toggle">{{ expandedIds.startups[startup.id] ? '▲' : '▼' }}</span>
            </div>

            <transition name="expand">
              <div
                  v-show="expandedIds.startups[startup.id]"
                  class="task-details expandable"
              >
                <p>{{ startup.description }}</p>
                <h4>Завдання:</h4>
                <ul v-if="startup.tasks && startup.tasks.length">
                  <li v-for="task in startup.tasks" :key="task.id">
                    <div class="task-toggle" @click="toggleExpand('task', task.id)">
                      <span class="task-title-text">{{ task.title }}</span>
                      <span class="expand-toggle">{{ expandedIds.tasks[task.id] ? '▲' : '▼' }}</span>
                    </div>

                    <transition name="expand">
                      <div
                          v-show="expandedIds.tasks[task.id]"
                          class="task-details expandable"
                      >
                        <p>{{ task.description }}</p>
                        <p>Статус: {{ getStatusText(task.status) }}</p>
                        <!-- Кнопка редагування, тільки якщо статус не in_progress і не paid -->
                        <button
                            v-if="task.status !== 'in_progress' && task.status !== 'paid'"
                            class="edit-btn"
                            @click.stop="editTask(task.id)"
                        >
                          Редагувати
                        </button>

                        <!-- Кнопка перегляду результату, тільки якщо статус paid -->
                        <button
                            v-if="task.status === 'paid'"
                            class="complete-btn"
                            @click.stop="viewTaskResult(task.id)"
                        >
                          Переглянути результат
                        </button>

                      </div>
                    </transition>
                  </li>
                </ul>
                <p v-else>Немає завдань</p>

                <button class="complete-btn" @click.stop="editStartup(startup.id)">Редагувати</button>
                <button class="edit-btn" @click.stop="createTask(startup.id)">+ Додати завдання</button>
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
                <button
                    v-if="task.status === 'in_progress'"
                    class="complete-btn"
                    @click.stop="markTaskAsCompleted(task.id)"
                >
                  Виконати
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


onMounted(() => {
  fetchProfile()
  fetchStartups()
  fetchTasks()
  fetchUserRating()
})
</script>

<style scoped>
.profile-page {
  padding: 2rem;
  font-family: 'Segoe UI', sans-serif;
  color: #fff;
  background-image: url('../assets/img.jpg');
  background-size: cover;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.user-info {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 12px;
}
.Profile123{
  margin-top: 50px;
}
.tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.tabs button {
  padding: 0.5rem 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.4);
  cursor: pointer;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-radius: 8px;
  transition: background 0.3s, border 0.3s;
}

.tabs button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.tabs button.active {
  background: rgba(0, 123, 255, 0.4);
  border-color: #007bff;
}

.tab-content {
  width: 100%;
  max-width: 700px;
}

.tab-content ul {
  list-style: none;
  padding-left: 0;
  width: 100%;
}

.tab-content li {
  background: rgba(255, 255, 255, 0.07);
  padding: 1rem;
  border-radius: 10px;
  margin-bottom: 0.6rem;
  display: flex;
  flex-direction: column;
}

.icon {
  display: inline-flex;
  align-items: center;
  margin-right: 0.5rem;
}

.icon-svg {
  width: 1em;
  height: 1em;
  stroke: white;
}

.task-header {
  padding: 0.6rem;
  cursor: pointer;
}

.task-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  flex-grow: 1;
  text-align: center;
  font-weight: bold;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.task-status {
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.2);
}

.task-status.in_progress {
  color: #7ae3f8;
  background-color: transparent;
}

.task-status.pending {
  color: #7ae3f8;
  background-color: transparent;
}

.task-status.completed {
  color: #7ae3f8;
  background-color: transparent;
}


.centered-title {
  text-align: center;
  width: 100%;
  font-size: 1.2rem;
}

.task-status {
  text-align: center;
}

.task-status.pending {
  color: #ffc107;
}

.task-status.in_progress {
  color: #17a2b8;
}

.task-status.completed {
  color: #28a745;
}

.expand-toggle {
  text-align: right;
  font-size: 1.5rem;
  color: #ccc;
}

.task-details {
  padding-top: 1rem;
  width: 100%;
}

.task-details p {
  margin: 0.5rem 0;
}

.complete-btn {
  margin-top: 1rem;
  padding: 0.6rem 1rem;
  background-color: transparent;
  color: #fff;
  border: 2px solid #007bff;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s, color 0.3s, border-color 0.3s;
  margin-right: 1rem;
}

.complete-btn:hover {
  background-color: rgba(0, 123, 255, 0.2);
  color: #fff;
  border-color: #0056b3;
}

.create-startup-btn {
  margin-bottom: 1rem;
  background-color: rgba(0, 123, 255, 0.4);
  color: #fff;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.create-startup-btn:hover {
  background-color: rgba(0, 123, 255, 0.6);
}

/* Стиль для кнопки редагування */
.edit-btn {
  margin-top: 1rem;
  padding: 0.6rem 1rem;
  background-color: transparent;
  color: #fff;
  border: 2px solid #e2a9fd;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s, color 0.3s, border-color 0.3s;
}

.edit-btn:hover {
  background-color: rgba(142, 68, 173, 0.2);
  color: #fff;
  border-color: #c786e4;
}
.task-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
  padding: 0.3rem 0;
}

.task-title-text {
  margin-left: 20px;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-toggle {
  font-size: 1.2rem;
  color: #ccc;
  margin-left: 0.5rem;
}
.expandable {
  overflow: hidden;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px; /* або підбери значення, яке більше за очікуваний контент */
  opacity: 1;
}

.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}


</style>
