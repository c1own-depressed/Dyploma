<template>
  <div>
    <Navbar />
    <router-view />
  </div>
  <main class="main-page">
    <div class="content">
      <input
          type="text"
          v-model="searchQuery"
          placeholder="Пошук ідеї..."
          class="search-input"
      />

      <div
          v-for="startupItem in filteredStartups" :key="startupItem.id"
          class="startup-card"
      >
        <h3 class="title">{{ startupItem.name }}</h3>

        <div
            class="description-wrapper"
            :class="{ expanded: expandedId === startupItem.id }"
            :ref="el => setDescriptionRef(el, startupItem.id)"
        >
          <p class="description-text">
            {{ startupItem.description }}
          </p>
        </div>

        <div class="expand-toggle" @click="toggleExpandDescription(startupItem.id)">
          <span :class="{ rotated: expandedId === startupItem.id }">▼</span>
        </div>

        <transition name="slide-fade">
          <div v-if="expandedId === startupItem.id" class="additional-content">
            <h4>Завдання:</h4>
            <ul v-if="startupItem.tasks && startupItem.tasks.length" class="task-list">
              <li
                  v-for="taskItem in displayedTasks(startupItem)"
                  :key="taskItem.id"
                  :class="['task-list-item', { 'non-clickable': taskItem.status !== 'pending' }]"
              >
                <component
                    :is="taskItem.status === 'pending' ? 'router-link' : 'span'"
                    :to="taskItem.status === 'pending' ? `/task/${taskItem.id}` : null"
                    class="task-link"
                >
                  {{ taskItem.title }}
                  <span v-if="taskItem.status !== 'pending'" class="task-status-indicator">
                     ({{ getTaskStatusText(taskItem.status) }})
                  </span>
                </component>
              </li>
            </ul>
            <button
                v-if="startupItem.tasks && startupItem.tasks.length > tasksToShowLimit"
                @click="toggleShowAllTasks(startupItem)"
                class="toggle-tasks-button"
            >
              {{ startupItem.showAllTasks ? 'Згорнути завдання' : `Показати всі ${startupItem.tasks.length} завдань` }}
            </button>
            <p v-else-if="startupItem.tasks && !startupItem.tasks.length" class="empty-message">Немає завдань для цієї ідеї.</p>


            <p class="owner">Власник: {{ startupItem.owner_username }}</p>

            <div class="comments-section">
              <h4>Коментарі</h4>
              <ul class="comment-list" v-if="startupItem.comments && startupItem.comments.length">
                <li v-for="comment in startupItem.comments" :key="comment.id">
                  <div class="comment-meta">
                    <strong>{{ comment.author }}</strong> –
                    <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
                  </div>
                  <div class="comment-text">{{ comment.text }}</div>
                </li>
              </ul>
              <p v-else class="empty-message">Коментарів ще немає.</p>

              <div class="add-comment">
                <input
                    v-model="startupItem.newComment"
                    placeholder="Написати коментар..."
                    class="comment-input"
                    @keyup.enter="addComment(startupItem.id)"
                />
                <button @click="addComment(startupItem.id)" class="comment-button">Надіслати</button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </main>
</template>

<script setup>
import Navbar from '../components/Navbar.vue'
import {ref, computed, onMounted, nextTick} from 'vue'
import axios from 'axios'
// useRouter не використовується, якщо навігація тільки через router-link
// import {useRouter} from 'vue-router'
// const router = useRouter()

const startups = ref([])
const searchQuery = ref('')
const expandedId = ref(null) // Для розгортання опису та контенту
const descriptionRefs = ref({})
const jwt = localStorage.getItem('jwtToken')

const tasksToShowLimit = ref(3); // Ліміт завдань для показу спочатку

async function fetchStartups() {
  try {
    const response = await axios.get('http://localhost:8000/startups', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    startups.value = response.data.map(s => ({
      ...s,
      tasks: Array.isArray(s.tasks) ? s.tasks : [],
      comments: [],
      newComment: '',
      showAllTasks: false, // Додаємо стан для кожного стартапу
    }))
  } catch (error) {
    console.error('Помилка при завантаженні ідей:', error)
  }
}

// Обчислювана властивість для відображення завдань
const displayedTasks = (startupItem) => {
  if (startupItem.showAllTasks || !startupItem.tasks) {
    return startupItem.tasks || [];
  }
  return startupItem.tasks.slice(0, tasksToShowLimit.value);
};

// Функція для перемикання відображення всіх завдань
function toggleShowAllTasks(startupItem) {
  startupItem.showAllTasks = !startupItem.showAllTasks;
}


async function fetchComments(startupId) {
  try {
    const response = await axios.get(`http://localhost:8000/startups/${startupId}/comments`, {
      headers: {Authorization: `Bearer ${jwt}`}
    })

    const startup = startups.value.find(s => s.id === startupId)
    if (startup) {
      startup.comments = response.data
    }
  } catch (error) {
    console.error('Помилка при отриманні коментарів:', error)
  }
}

async function addComment(startupId) {
  const startup = startups.value.find(s => s.id === startupId)
  if (!startup || !startup.newComment.trim()) return

  try {
    const response = await axios.post(
        `http://localhost:8000/startups/${startupId}/comments`,
        {text: startup.newComment},
        {
          headers: {
            Authorization: `Bearer ${jwt}`,
            'Content-Type': 'application/json',
          },
        }
    )
    startup.comments.push(response.data)
    startup.newComment = ''
  } catch (error) {
    console.error('Помилка при додаванні коментаря:', error)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr)
  return date.toLocaleString('uk-UA')
}

function getTaskStatusText(status) {
  const statusMap = {
    'in_progress': 'В роботі',
    'pending': 'Очікує',
    'done': 'Виконано',
    'paid': 'Оплачено'
  };
  return statusMap[status] || status;
}

onMounted(fetchStartups)

const filteredStartups = computed(() =>
    startups.value.filter(s =>
        s.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
)

function setDescriptionRef(el, id) {
  if (el) descriptionRefs.value[id] = el
}

async function toggleExpandDescription(id) {
  const prev = expandedId.value

  if (prev === id) {
    collapseDescription(id)
    expandedId.value = null
  } else {
    if (prev !== null) collapseDescription(prev)
    expandedId.value = id
    const startup = startups.value.find(s => s.id === id);
    if (startup && !startup.comments.length) { // Завантажуємо коментарі, тільки якщо їх ще немає
      await fetchComments(id);
    }
    await nextTick(() => expandDescription(id))
  }
}

function expandDescription(id) {
  const el = descriptionRefs.value[id]
  if (el) {
    el.style.height = el.scrollHeight + 'px'
  }
}

function collapseDescription(id) {
  const el = descriptionRefs.value[id]
  if (el) {
    el.style.height = el.scrollHeight + 'px'
    void el.offsetHeight
    el.style.height = '0px'
  }
}
</script>

<style scoped>
/* ... (попередні стилі для .main-page, .content, .search-input, .startup-card, .title і т.д.) ... */
.main-page {
  padding: 2rem;
  padding-top: 100px; /* Відступ для Navbar */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url('../assets/img.jpg'); /* Переконайся, що шлях правильний */
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  color: #f0f0f0;
}

.content {
  max-width: 900px;
  margin: 0 auto;
}

.search-input {
  width: 100%;
  padding: 0.9rem 1.2rem;
  margin-bottom: 2rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  outline: none;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.startup-card {
  width: 100%;
  background: rgba(35, 30, 50, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 1.8rem 2.2rem;
  border-radius: 18px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.35);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.startup-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 35px rgba(0, 0, 0, 0.4);
}

.title {
  font-size: 1.7rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #ffffff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.owner {
  font-size: 0.9rem;
  color: #b0b8c5;
  margin-top: 1.2rem;
  margin-bottom: 1.2rem;
  font-style: italic;
}

.description-wrapper {
  overflow: hidden;
  height: 0;
  transition: height 0.5s ease-in-out;
}

.description-wrapper.expanded {
  margin-bottom: 1.5rem; /* Додаємо відступ знизу, коли опис розгорнуто */
}

.description-text {
  padding-top: 0.5rem; /* Невеликий відступ зверху для тексту опису */
  color: #d5d8de;
  line-height: 1.6;
}

.expand-toggle {
  position: absolute;
  top: 1.8rem;
  right: 2.2rem;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: background-color 0.2s ease;
}

.expand-toggle:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.expand-toggle span {
  font-size: 1.6rem;
  transition: transform 0.4s ease-in-out;
  color: #a0a8b5;
  display: block; /* Важливо для правильного обертання */
}

.expand-toggle span.rotated {
  transform: rotate(180deg);
}

.additional-content h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #e0e1e6;
  margin-top: 1.5rem; /* Збільшено для кращого візуального розділення */
  margin-bottom: 0.8rem;
}

.additional-content > h4:first-of-type {
  margin-top: 0.5rem; /* Зменшено, якщо це перший заголовок після опису */
}

.task-list {
  padding-left: 0; /* Прибираємо стандартний відступ списку */
  list-style-type: none; /* Прибираємо маркери списку */
}

.task-list-item { /* Загальний стиль для елемента списку завдань */
  margin-bottom: 0.5rem;
  padding: 0.3rem 0; /* Невеликий вертикальний падінг */
}

.task-link { /* Стиль для тексту завдання (посилання або span) */
  color: #90caf9; /* Колір для клікабельних завдань */
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.task-list-item.non-clickable .task-link {
  color: #78909c; /* Більш тьмяний колір для неклікабельних */
  cursor: default; /* Показуємо, що елемент не клікабельний */
}

.task-list-item.non-clickable .task-link:hover {
  text-decoration: none; /* Прибираємо підкреслення при наведенні для неклікабельних */
  color: #78909c; /* Колір не змінюється */
}

.task-list-item:not(.non-clickable) .task-link:hover {
  color: #bbdefb; /* Світліший колір при наведенні для клікабельних */
  text-decoration: underline;
}


.task-status-indicator { /* Стиль для тексту статусу завдання */
  font-size: 0.85em;
  font-style: italic;
  margin-left: 8px;
  color: #a0a8b5;
}

.toggle-tasks-button {
  background-color: transparent;
  border: 1px solid #90caf9;
  color: #90caf9;
  padding: 0.4rem 0.8rem;
  margin-top: 0.5rem; /* Відступ зверху від списку завдань */
  margin-bottom: 1rem; /* Відступ знизу перед власником */
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.toggle-tasks-button:hover {
  background-color: rgba(144, 202, 249, 0.1);
  color: #bbdefb;
}


.empty-message {
  font-style: italic;
  color: #a0a8b5;
  padding: 0.5rem 0;
  font-size: 0.9rem;
}

.comments-section {
  margin-top: 1.5rem;
  background: rgba(20, 15, 30, 0.5); /* Трохи інший фон для секції коментарів */
  padding: 1.2rem 1.5rem;
  border-radius: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08); /* Лінія зверху для візуального розділення */
}

.comment-list {
  list-style: none;
  padding: 0;
  margin-bottom: 1.2rem; /* Відступ під списком коментарів */
}

.comment-list li {
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 0.8rem;
}

.comment-list li:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.comment-meta {
  font-size: 0.8rem;
  color: #8a92a0;
  margin-bottom: 0.3rem;
}

.comment-meta strong {
  color: #b0b8c5;
  font-weight: 500;
}

.comment-text {
  font-size: 0.95rem;
  color: #d5d8de;
  line-height: 1.5;
}

.add-comment {
  display: flex;
  gap: 0.8rem;
  margin-top: 1rem; /* Відступ над полем вводу коментаря */
}

.comment-input {
  flex: 1;
  padding: 0.7rem 0.9rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  color: #ffffff;
  outline: none;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.comment-input:focus {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
}

.comment-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.comment-button {
  padding: 0.7rem 1.2rem;
  background-color: #007aff; /* Яскравий синій для кнопки */
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.comment-button:hover {
  background-color: #005bb5; /* Темніший синій при наведенні */
}

/* Анімації (slide-fade) залишаються як є */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-15px); /* Зсув для анімації виїзду/в'їзду */
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

</style>