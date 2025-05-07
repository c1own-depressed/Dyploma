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

        <ul v-if="expandedId === startup.id" class="task-list">
          <li
              v-for="task in startup.tasks"
              :key="task.id"
              class="clickable-task"
          >
            <router-link :to="`/task/${task.id}`">{{ task.title }}</router-link>
          </li>
        </ul>

        <p class="owner">Власник: {{ startup.owner_username }}</p>

        <!-- Коментарі -->
        <div v-if="expandedId === startup.id" class="comments-section">
          <h4>Коментарі</h4>
          <ul class="comment-list">
            <li v-for="comment in startup.comments" :key="comment.id">
              <div class="comment-meta">
                <strong>{{ comment.author }}</strong> –
                <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
              </div>
              <div class="comment-text">{{ comment.text }}</div>
            </li>
          </ul>

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
.main-page {
  padding: 2rem;
  font-family: 'Segoe UI', sans-serif;
  background-image: url('../assets/img.jpg');
  min-height: 100vh;
  color: white;
}

.content {
  max-width: 100%;
  margin: 0 auto;
}

.owner {
  font-size: 0.9rem;
  color: #ccc;
  margin-bottom: 0.5rem;
}

.search-input {
  margin-top: 70px;
  width: 100%;
  padding: 0.8rem 1rem;
  margin-bottom: 1.5rem;
  border-radius: 10px;
  border: none;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  outline: none;
}

.search-input::placeholder {
  color: white;
}

.startup-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  padding: 1.5rem 2rem;
  border-radius: 15px;
  margin-bottom: 1.5rem;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  position: relative;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #fff;
}

.description-wrapper {
  overflow: hidden;
  height: 0;
  transition: height 0.5s ease, margin 0.3s ease;
  margin-bottom: 0;
}

.description-wrapper.expanded {
  height: auto;
  margin-bottom: 1rem;
}

.description-text {
  padding-top: 0.5rem;
  color: #eee;
  line-height: 1.5;
}

.expand-toggle {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
  cursor: pointer;
}

.expand-toggle span {
  font-size: 1.5rem;
  transition: transform 0.3s ease;
  color: #ccc;
}

.expand-toggle span.rotated {
  transform: rotate(180deg);
}

.task-list {
  margin-top: 1rem;
  padding-left: 1.2rem;
  color: #ddd;
  list-style-type: none;
}

.task-list li {
  margin-bottom: 0.3rem;
}

.clickable-task a {
  color: white;
  text-decoration: none;
}

.clickable-task a:hover {
  text-decoration: underline;
}

/* Коментарі */
.comments-section {
  margin-top: 1rem;
  background: rgba(255, 255, 255, 0.03);
  padding: 1rem;
  border-radius: 10px;
}

.comment-list {
  list-style: none;
  padding: 0;
  margin-bottom: 1rem;
  color: #ddd;
}

.comment-list li {
  margin-bottom: 0.8rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 0.5rem;
}

.comment-meta {
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 0.2rem;
}

.comment-text {
  font-size: 1rem;
  color: #eee;
}

.add-comment {
  display: flex;
  gap: 0.5rem;
}

.comment-input {
  flex: 1;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  outline: none;
}

.comment-button {
  padding: 0.5rem 1rem;
  background-color: transparent;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.comment-button:hover {
  background-color: #f82eed;
}
</style>
