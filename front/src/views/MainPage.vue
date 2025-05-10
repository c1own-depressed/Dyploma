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
          placeholder="Пошук стартапу..."
          class="search-input"
      />

      <div
          v-for="startup in filteredStartups"
          :key="startup.id"
          class="startup-card"
      >
        <h3 class="title">{{ startup.name }}</h3>

        <div
            class="description-wrapper"
            :class="{ expanded: expandedId === startup.id }"
            :ref="el => setDescriptionRef(el, startup.id)"
        >
          <p class="description-text">
            {{ startup.description }}
          </p>
        </div>

        <div class="expand-toggle" @click="toggleExpand(startup.id)">
          <span :class="{ rotated: expandedId === startup.id }">▼</span>
        </div>

        <transition name="slide-fade">
          <div v-if="expandedId === startup.id" class="additional-content">
            <h4>Завдання:</h4>
            <ul v-if="startup.tasks && startup.tasks.length" class="task-list">
              <li
                  v-for="task in startup.tasks"
                  :key="task.id"
                  class="clickable-task"
              >
                <router-link :to="`/task/${task.id}`">{{ task.title }}</router-link>
              </li>
            </ul>
            <p v-else-if="startup.tasks" class="empty-message">Немає завдань для цього стартапу.</p>

            <p class="owner">Власник: {{ startup.owner_username }}</p>

            <div class="comments-section">
              <h4>Коментарі</h4>
              <ul class="comment-list" v-if="startup.comments && startup.comments.length">
                <li v-for="comment in startup.comments" :key="comment.id">
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
                    v-model="startup.newComment"
                    placeholder="Написати коментар..."
                    class="comment-input"
                />
                <button @click="addComment(startup.id)" class="comment-button">Надіслати</button>
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
import {useRouter} from 'vue-router'

const router = useRouter()

const startups = ref([])
const searchQuery = ref('')
const expandedId = ref(null)
const descriptionRefs = ref({})
const jwt = localStorage.getItem('jwtToken')

async function fetchStartups() {
  try {
    const response = await axios.get('http://localhost:8000/startups', {
      headers: { Authorization: `Bearer ${jwt}` }
    })

    startups.value = response.data.map(s => ({
      ...s,
      tasks: s.tasks,
      comments: [],
      newComment: '',
    }))
  } catch (error) {
    console.error('Помилка при завантаженні стартапів:', error)
  }
}

async function fetchComments(startupId) {
  try {
    const response = await axios.get(`http://localhost:8000/startups/${startupId}/comments`, {
      headers: { Authorization: `Bearer ${jwt}` }
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
  const date = new Date(dateStr)
  return date.toLocaleString()
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

async function toggleExpand(id) {
  const prev = expandedId.value

  if (prev === id) {
    collapse(id)
    expandedId.value = null
  } else {
    if (prev !== null) collapse(prev)
    expandedId.value = id
    await fetchComments(id)
    nextTick(() => expand(id))
  }
}

function expand(id) {
  const el = descriptionRefs.value[id]
  if (el) {
    el.style.height = el.scrollHeight + 'px'
  }
}

function collapse(id) {
  const el = descriptionRefs.value[id]
  if (el) {
    el.style.height = el.scrollHeight + 'px'
    void el.offsetHeight
    el.style.height = '0px'
  }
}
</script>

<style scoped>
/* ... (попередні стилі для .main-page, .content, .search-input, .startup-card, .title) ... */
/* Залишаємо їх як є, якщо вони вас влаштовують */

.main-page {
  padding: 2rem;
  padding-top: 100px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url('../assets/img.jpg');
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
  text-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.owner {
  font-size: 0.9rem;
  color: #b0b8c5;
  margin-top: 1.2rem; /* Збільшено відступ, якщо є завдання */
  margin-bottom: 1.2rem; /* Збільшено відступ перед коментарями */
  font-style: italic;
}

.description-wrapper {
  overflow: hidden;
  height: 0;
  transition: height 0.5s ease-in-out; /* Збільшено тривалість для плавності */
}

.description-wrapper.expanded {
  margin-bottom: 1.5rem; /* Збільшено відступ, коли опис розгорнуто */
}

.description-text {
  padding-top: 0.5rem; /* Залишаємо, щоб текст не прилипав до верху при розгортанні */
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
  background-color: rgba(255,255,255,0.1);
}

.expand-toggle span {
  font-size: 1.6rem;
  transition: transform 0.4s ease-in-out; /* Плавніший поворот стрілки */
  color: #a0a8b5;
  display: block;
}

.expand-toggle span.rotated {
  transform: rotate(180deg);
}

.additional-content {
  /* margin-top: 0.5rem; /* Невеликий відступ зверху для всього блоку */
  /* overflow: hidden; -- не потрібен, якщо анімуємо opacity/transform */
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out; /* Збільшено тривалість */
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-15px); /* Починаємо трохи вище і "виїжджаємо" вниз */
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* Блок завдань */
.additional-content h4 { /* Застосується до обох <h4> */
  font-size: 1.1rem;
  font-weight: 600;
  color: #e0e1e6;
  margin-top: 1.5rem; /* Відступ перед списком завдань/коментарів */
  margin-bottom: 0.8rem;
}
.additional-content > h4:first-of-type { /* Перший H4 (Завдання:) */
  margin-top: 0.5rem; /* Менший відступ, якщо це перший елемент в additional-content */
}


.task-list {
  /* margin-top: 1rem; -- відступ тепер через h4 */
  padding-left: 0;
  color: #c5c8ce;
  list-style-type: none;
}

.empty-message { /* Новий клас для повідомлень про відсутність даних */
  font-style: italic;
  color: #a0a8b5;
  padding: 0.5rem 0;
  font-size: 0.9rem;
  /* margin-top: 0.5rem; */ /* Можна додати, якщо потрібно більше простору */
}


.task-list li {
  margin-bottom: 0.5rem;
  padding: 0.3rem 0;
}

.clickable-task a {
  color: #90caf9;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.clickable-task a:hover {
  color: #bbdefb;
  text-decoration: underline;
}

.comments-section {
  margin-top: 1.5rem; /* Відступ від блоку власника або завдань */
  background: rgba(20, 15, 30, 0.5);
  padding: 1.2rem 1.5rem;
  border-radius: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

/* comments-section h4 - вже стилізовано вище */

.comment-list {
  list-style: none;
  padding: 0;
  margin-bottom: 1.2rem;
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
  margin-top: 1rem;
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
  background-color: #007aff;
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.comment-button:hover {
  background-color: #005bb5;
}
</style>