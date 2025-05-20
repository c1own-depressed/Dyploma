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
        <strong>Рейтинг:</strong> {{ user.rating % 1 === 0 ? user.rating : user.rating.toFixed(1) }}
      </p>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'startups' }" @click="activeTab = 'startups'">Мої ідеї</button>
      <button :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'">Активні завдання</button>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'startups'">
        <h2>Мої ідеї</h2>
        <button class="create-startup-btn" @click="createStartup">+ Створити ідею</button>
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
                  <li v-for="taskItem in displayedTasksInProfile(startupItem)" :key="taskItem.id">
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
                        <button v-if="taskItem.status === 'in_progress'" class="remove-executor-btn" @click.stop="confirmRemoveExecutor(taskItem.id)">Відключити виконавця</button>
                      </div>
                    </transition>
                  </li>
                </ul>
                <button
                    v-if="startupItem.tasks && startupItem.tasks.length > tasksToShowLimitStartups"
                    @click="toggleShowAllTasksInProfile(startupItem)"
                    class="toggle-profile-tasks-button"
                >
                  {{ startupItem.showAllTasksInProfile ? 'Згорнути завдання' : `Показати всі ${startupItem.tasks.length}` }}
                </button>
                <p v-else-if="startupItem.tasks && !startupItem.tasks.length">Немає завдань</p>


                <div class="startup-actions">
                  <button class="complete-btn" @click.stop="editStartup(startupItem.id)">Редагувати ідею</button>
                  <button class="edit-btn" @click.stop="createTask(startupItem.id)">+ Додати завдання</button>
                </div>

                <h4 class="comments-heading">Коментарі до ідеї:</h4>
                <ul v-if="startupItem.comments && startupItem.comments.length" class="startup-comments-list">
                  <li v-for="commentEntry in startupItem.comments" :key="commentEntry.id" class="comment-entry">
                    <div class="comment-entry-header">
                      <strong class="comment-author">{{ commentEntry.author_username }}</strong>
                      <div class="comment-meta-and-actions">
                        <span class="comment-date-small">{{ new Date(commentEntry.created_at).toLocaleString('uk-UA') }}</span>
                        <button @click.stop="confirmDeleteStartupCommentAction(startupItem.id, commentEntry.id, commentEntry.text)" class="delete-comment-icon" title="Видалити коментар">
                          &#x2715; </button>
                      </div>
                    </div>
                    <p class="comment-text-small">{{ commentEntry.text }}</p>
                  </li>
                </ul>
                <p v-else class="no-comments-text">До цієї ідеї ще немає коментарів.</p>
              </div>
            </transition>
          </li>
        </ul>
        <p v-else>Немає ідей.</p>
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
                    @click.stop="confirmRefuseTask(task.id)"
                >
                  Відмовитися
                </button>
                <button
                    v-else-if="task.status === 'done'"
                    class="complete-btn paid-style"
                    @click.stop="markTaskAsPaid(task.id)"
                >
                  Оплачено
                </button>
              </div>
            </transition>
          </li>
        </ul>
        <p v-else>Немає активних завдань.</p>
      </div>
    </div>

    <div v-if="showConfirmModal" class="profile-modal-overlay" @click.self="cancelAction">
      <div class="profile-modal-content">
        <div class="profile-modal-header">
          <h4>
            <svg v-if="!isNotificationModal" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="profile-modal-header-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="profile-modal-header-icon success"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            {{ confirmModalTitle }}
          </h4>
        </div>
        <p v-html="confirmModalMessage"></p>
        <div class="profile-modal-actions">
          <button v-if="!isNotificationModal" @click="cancelAction" class="profile-modal-button cancel">{{ cancelButtonText }}</button>
          <button @click="proceedWithAction" :class="['profile-modal-button', isNotificationModal ? 'ok' : 'confirm']">{{ confirmButtonText }}</button>
        </div>
      </div>
    </div>

  </main>
</template>

<script setup>
import Navbar from '../components/Navbar.vue'
import { ref, onMounted, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = ref({ username: '', email: '', rating: null })
const startups = ref([])
const tasks = ref([])
const activeTab = ref('startups')
const expandedIds = ref({ startups: {}, tasks: {} })
const jwt = localStorage.getItem('jwtToken')

// Ліміт завдань для показу спочатку у вкладці "Мої ідеї"
const tasksToShowLimitStartups = ref(3);

// --- Стан для універсального модального вікна ---
const showConfirmModal = ref(false)
const confirmModalTitle = ref('')
const confirmModalMessage = ref('')
const confirmActionCallback = ref(null)
const confirmButtonText = ref('Так')
const cancelButtonText = ref('Скасувати')
const isNotificationModal = ref(false);
// --- Кінець стану для модального вікна ---

const fetchProfile = async () => {
  if (!jwt) {
    router.push('/login');
    return;
  }
  try {
    const res = await axios.get('http://localhost:8000/user/profile', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    user.value = res.data
  } catch (e) {
    console.error('Не вдалося завантажити профіль', e)
    if (e.response && e.response.status === 401) {
      localStorage.removeItem('jwtToken');
      router.push('/login');
    }
  }
}

const fetchStartups = async () => {
  if (!jwt) return;
  try {
    const res = await axios.get('http://localhost:8000/user/startups', {
      headers: { Authorization: `Bearer ${jwt}` }
    })
    startups.value = res.data.map(startup => ({
      ...startup,
      tasks: startup.tasks || [],
      comments: startup.comments || [],
      showAllTasksInProfile: false, // Додаємо стан для згортання завдань у профілі
    }));
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
    console.error('Помилка при завантаженні ідей', e)
  }
}

// Функція для відображення завдань у профілі (згортання/розгортання)
const displayedTasksInProfile = (startupItem) => {
  if (!startupItem || !startupItem.tasks) return [];
  if (startupItem.showAllTasksInProfile) {
    return startupItem.tasks;
  }
  return startupItem.tasks.slice(0, tasksToShowLimitStartups.value);
};

// Функція для перемикання відображення всіх завдань у профілі
const toggleShowAllTasksInProfile = (startupItem) => {
  if (startupItem) {
    startupItem.showAllTasksInProfile = !startupItem.showAllTasksInProfile;
  }
};


const fetchTasks = async () => {
  if (!jwt) return;
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

const getStatusText = (status) => {
  const statuses = {
    'in_progress': 'Виконується',
    'pending': 'Очікує на виконавця',
    'done': 'Очікує на оплату',
    'paid': 'Оплачено'
  };
  return statuses[status] || status;
}

const toggleExpand = (type, id) => {
  if (type === 'startup') {
    expandedIds.value.startups[id] = !expandedIds.value.startups[id]
  } else if (type === 'task') {
    expandedIds.value.tasks[id] = !expandedIds.value.tasks[id]
  }
}

const markTaskAsCompleted = (taskId) => router.push({ name: 'CompleteTask', params: { taskId } });

const markTaskAsPaid = async (taskId) => {
  try {
    await axios.put(`http://localhost:8000/user/tasks/${taskId}/status`, { status: 'paid' }, { headers: { Authorization: `Bearer ${jwt}` } });
    if (activeTab.value === 'tasks') {
      await fetchTasks();
    } else if (activeTab.value === 'startups') {
      // Оновлення статусу завдання всередині стартапу
      const startupContainingTask = startups.value.find(s => s.tasks.some(t => t.id === taskId));
      if (startupContainingTask) {
        const taskIndex = startupContainingTask.tasks.findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
          startupContainingTask.tasks[taskIndex].status = 'paid';
        }
      }
    }
    showNotification('Статус оновлено', 'Статус завдання успішно оновлено на "Оплачено".');
  } catch (e) {
    console.error('Не вдалося оновити статус на paid', e);
    showNotification('Помилка', `Не вдалося оновити статус: ${e.response?.data?.detail || e.message}`);
  }
};

const createStartup = () => router.push('/create-startup');
const editStartup = (startupId) => router.push(`/edit-startup/${startupId}`);
const createTask = (startupId) => router.push(`/create-task?startup_id=${startupId}`);
const editTask = (taskId) => router.push(`/edit-task/${taskId}`);
const viewTaskResult = (taskId) => router.push(`/task-result/${taskId}`);

const fetchUserRating = async () => {
  if (!jwt) return;
  try {
    const res = await axios.get('http://localhost:8000/user/rating', { headers: { Authorization: `Bearer ${jwt}` } });
    user.value.rating = res.data.average_rating;
  } catch (e) { console.error('Не вдалося отримати рейтинг', e); }
};

// --- Функції з використанням модального вікна (без змін) ---
const showNotification = (title, message) => {
  confirmModalTitle.value = title;
  confirmModalMessage.value = message;
  isNotificationModal.value = true;
  confirmActionCallback.value = null;
  confirmButtonText.value = 'OK';
  showConfirmModal.value = true;
};

const confirmRemoveExecutor = (taskId) => {
  confirmModalTitle.value = 'Відключити виконавця?';
  confirmModalMessage.value = 'Ви впевнені, що хочете відключити виконавця від цього завдання? <br/> Це поверне завдання у статус "Очікує на виконавця".';
  confirmButtonText.value = 'Відключити';
  cancelButtonText.value = 'Скасувати';
  isNotificationModal.value = false;
  confirmActionCallback.value = () => actualRemoveExecutor(taskId);
  showConfirmModal.value = true;
};

const actualRemoveExecutor = async (taskId) => {
  try {
    await axios.put(`http://localhost:8000/user/startups/tasks/${taskId}/remove-executor`, {}, { headers: { Authorization: `Bearer ${jwt}` } });
    await fetchStartups(); // Оновити список стартапів, щоб відобразити зміни
    showNotification('Успіх!', 'Виконавця успішно відключено від завдання.');
  } catch (e) {
    console.error('Не вдалося відключити виконавця:', e);
    showNotification('Помилка', `Не вдалося відключити виконавця: ${e.response?.data?.detail || e.message}`);
  }
};

const confirmDeleteStartupCommentAction = (startupId, commentId, commentText = '') => {
  confirmModalTitle.value = 'Видалити коментар?';
  let message = 'Ви впевнені, що хочете видалити цей коментар?';
  if (commentText) {
    const snippet = commentText.length > 100 ? commentText.substring(0, 100) + "..." : commentText;
    message += `<br/><br/><div class="comment-snippet-preview">"${snippet}"</div>`;
  }
  confirmModalMessage.value = message;
  confirmButtonText.value = 'Видалити';
  cancelButtonText.value = 'Скасувати';
  isNotificationModal.value = false;
  confirmActionCallback.value = () => actualDeleteStartupComment(startupId, commentId);
  showConfirmModal.value = true;
};

const actualDeleteStartupComment = async (startupId, commentId) => {
  try {
    await axios.delete(`http://localhost:8000/user/startups/${startupId}/comments/${commentId}`, {
      headers: {Authorization: `Bearer ${jwt}`}
    });
    // Оновити коментарі для конкретного стартапу
    const startupToUpdate = startups.value.find(s => s.id === startupId);
    if (startupToUpdate) {
      startupToUpdate.comments = startupToUpdate.comments.filter(c => c.id !== commentId);
    }
    showNotification('Успіх!', 'Коментар успішно видалено.');
  } catch (e) {
    console.error('Помилка при видаленні коментаря ідеї', e);
    let errorMessageText = `Помилка: ${e.message}`;
    if (e.response) {
      errorMessageText = `Помилка видалення: ${e.response.status} - ${e.response.data.detail || e.message}`;
    }
    showNotification('Помилка', errorMessageText);
  }
};

const confirmRefuseTask = (taskId) => {
  confirmModalTitle.value = 'Відмовитися від завдання?';
  confirmModalMessage.value = 'Ви впевнені, що хочете відмовитися від виконання цього завдання? <br/> Це може вплинути на ваш рейтинг, якщо завдання вже було прийнято.';
  confirmButtonText.value = 'Так, відмовитися';
  cancelButtonText.value = 'Залишитися';
  isNotificationModal.value = false;
  confirmActionCallback.value = () => actualRefuseTask(taskId);
  showConfirmModal.value = true;
};

const actualRefuseTask = async (taskId) => {
  try {
    await axios.put(`http://localhost:8000/user/tasks/${taskId}/refuse`, {}, {headers: {Authorization: `Bearer ${jwt}`}});
    await fetchTasks(); // Оновити список активних завдань
    showNotification('Завдання скасовано', 'Ви успішно відмовилися від виконання цього завдання.');
  } catch (e) {
    console.error('Не вдалося відмовитися від завдання', e);
    showNotification('Помилка', `Не вдалося відмовитися від завдання: ${e.response?.data?.detail || e.message}`);
  }
};


const proceedWithAction = () => {
  if (!isNotificationModal.value && typeof confirmActionCallback.value === 'function') {
    confirmActionCallback.value();
  }
  closeConfirmModal();
};

const cancelAction = () => {
  closeConfirmModal();
};

const closeConfirmModal = () => {
  showConfirmModal.value = false;
  setTimeout(() => {
    if (!showConfirmModal.value) {
      confirmModalTitle.value = '';
      confirmModalMessage.value = '';
      confirmActionCallback.value = null;
      confirmButtonText.value = 'Так';
      cancelButtonText.value = 'Скасувати';
      isNotificationModal.value = false;
    }
  }, 300);
};

const handleGlobalEscProfile = (event) => {
  if (event.key === 'Escape' && showConfirmModal.value) {
    cancelAction();
  }
};


watch(activeTab, (newTab) => {
  expandedIds.value = {startups: {}, tasks: {}}; // Скидаємо стани розгортання при зміні вкладки
  if (newTab === 'startups') {
    fetchStartups();
  } else if (newTab === 'tasks') {
    fetchTasks();
  }
});

onMounted(() => {
  if (!jwt) {
    router.push('/login');
    return;
  }
  fetchProfile();
  fetchUserRating();
  if (activeTab.value === 'startups') {
    fetchStartups();
  } else if (activeTab.value === 'tasks') {
    fetchTasks();
  }
  document.addEventListener('keyup', handleGlobalEscProfile);
});

onUnmounted(() => {
  document.removeEventListener('keyup', handleGlobalEscProfile);
});

</script>

<style scoped>
/* ... (попередні стилі) ... */
.toggle-profile-tasks-button { /* Стилі для кнопки згортання/розгортання завдань у профілі */
  background-color: transparent;
  border: 1px solid #007aff; /* Такий же колір, як у активної вкладки для консистентності */
  color: #007aff;
  padding: 0.5rem 1rem;
  margin-top: 0.8rem; /* Відступ зверху від списку завдань */
  margin-bottom: 1rem; /* Відступ знизу перед "Дії зі стартапом" */
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s ease, color 0.2s ease;
  display: inline-block; /* Щоб кнопка не розтягувалася на всю ширину */
}

.toggle-profile-tasks-button:hover {
  background-color: rgba(0, 123, 255, 0.1);
  color: #3395ff;
}

.profile-page {
  padding: 2rem;
  padding-top: 80px; /* Збільшено для Navbar, якщо вона фіксована і висока */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #f0f0f0;
  background-image: url('../assets/img.jpg'); /* Перевірте шлях до зображення */
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center; /* Центруємо основний контент */
  width: 100%; /* Щоб фон займав всю ширину */
}

.Profile123 {
  font-size: 2.2rem;
  font-weight: 600;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  margin-top: 50px; /* Відступ зверху для заголовка */
  margin-bottom: 2.5rem; /* Збільшений відступ знизу */
  text-align: center;
}

.user-info {
  background: rgba(35, 30, 50, 0.65); /* Трохи темніший фон для кращого контрасту */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 1.8rem 2.2rem;
  margin-bottom: 2rem;
  border-radius: 18px; /* Збільшений радіус для м'якшого вигляду */
  border: 1px solid rgba(255, 255, 255, 0.12); /* Тонка світла рамка */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); /* Глибша тінь */
  width: 100%;
  max-width: 280px; /* Обмежуємо ширину для компактності */
  text-align: center; /* Центруємо текст всередині блоку */
}

.user-info p {
  display: flex; /* Для вирівнювання іконки та тексту */
  align-items: center; /* Вертикальне вирівнювання */
  justify-content: center; /* Горизонтальне центрування */
  font-size: 1rem;
  margin-bottom: 0.8rem;
  color: #e0e1e6;
}

.user-info p:last-child {
  margin-bottom: 0;
}

.user-info strong {
  color: #ffffff;
  font-weight: 500; /* Не надто жирний */
}

.icon {
  display: inline-flex;
  align-items: center;
  margin-right: 0.8rem;
  color: #a0a8b5; /* Колір іконок */
}

.icon-svg {
  width: 1.2em; /* Розмір іконки */
  height: 1.2em;
  stroke: currentColor; /* Використовує колір батьківського елемента (.icon) */
}

.tabs {
  display: flex;
  justify-content: center;
  gap: 1rem; /* Проміжок між кнопками */
  margin-bottom: 2rem;
}

.tabs button {
  padding: 0.7rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  background: rgba(50, 50, 70, 0.5); /* Напівпрозорий фон для кнопок */
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
  background: #007aff; /* Яскравий синій для активної вкладки */
  border-color: #007aff;
  color: #ffffff;
  box-shadow: 0 0 10px rgba(0, 123, 255, 0.5); /* Світіння для активної вкладки */
}

.tab-content {
  width: 100%;
  max-width: 800px; /* Обмежуємо ширину контенту вкладок */
}

.tab-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 1.5rem;
  text-align: center;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.tab-content ul {
  list-style: none;
  padding-left: 0; /* Прибираємо стандартний відступ для списків */
  width: 100%;
}

.task-item { /* Стиль для кожного елемента списку (стартапу чи завдання) */
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
  padding: 0.5rem 0; /* Зменшено вертикальний падінг */
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 1rem; /* Відступ під заголовком/перемикачем */
}

.task-item ul .task-toggle { /* Специфічний стиль для перемикача завдання всередині стартапу */
  border-top: 1px solid rgba(255, 255, 255, 0.05); /* Тонка лінія зверху */
  margin-top: 0.5rem;
  padding: 0.5rem 0;
  margin-bottom: 0.5rem; /* Зменшено відступ */
}

.task-item > .task-header { /* Заголовок самого стартапу */
  padding-top: 0;
  margin-bottom: 1rem;
}

.task-title, .task-title-text {
  flex-grow: 1; /* Щоб назва займала доступний простір */
  font-size: 1.1rem;
  font-weight: 600;
  color: #e8e9ed;
}

.centered-title {
  text-align: center;
  font-size: 1.2rem; /* Трохи більший шрифт для заголовків стартапів */
}

.task-title-text { /* Для назв завдань всередині стартапу */
  margin-left: 0; /* Прибираємо відступ, якщо він був */
  white-space: normal; /* Дозволяємо перенос тексту */
  font-size: 1rem; /* Стандартний розмір */
}

.expand-toggle {
  font-size: 1.3rem; /* Розмір стрілочки */
  color: #a0a8b5;
  padding: 0.3rem; /* Невеликий падінг навколо стрілки для кращого кліку */
  transition: transform 0.4s ease-in-out; /* Плавне обертання */
}

.task-details { /* Блок з деталями, що розгортається */
  padding-top: 0.8rem;
  color: #c5c8ce;
  line-height: 1.6;
}

.task-details p {
  margin: 0.6rem 0; /* Відступи для параграфів */
}

.task-details h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #d5d8de;
  margin-top: 1.2rem;
  margin-bottom: 0.5rem;
}

.task-details ul { /* Список завдань всередині стартапу */
  padding-left: 1rem; /* Невеликий відступ для вкладеного списку */
  margin-top: 0.5rem;
}

.task-details ul li { /* Елементи вкладеного списку завдань */
  background: transparent; /* Прозорий фон */
  padding: 0.3rem 0;
  border-radius: 0;
  margin-bottom: 0.3rem;
  box-shadow: none; /* Без тіні */
  border: none; /* Без рамки */
}

.create-startup-btn, .edit-btn, .complete-btn, .refuse-btn, .remove-executor-btn {
  padding: 0.7rem 1.3rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
  margin-right: 0.8rem; /* Відступ між кнопками */
  margin-top: 1rem; /* Відступ зверху для кнопок */
}

.startup-actions button:last-child,
.task-details button:last-child {
  margin-right: 0; /* Прибираємо відступ для останньої кнопки в ряду */
}

.create-startup-btn {
  background-color: #007aff;
  color: #ffffff;
  display: block; /* Щоб margin: auto спрацював для центрування */
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 1.5rem; /* Відступ під кнопкою */
}

.create-startup-btn:hover {
  background-color: #005bb5;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.4);
}

.edit-btn { /* "Редагувати ідею", "+ Додати завдання" */
  background-color: rgba(147, 38, 198, 0.7); /* Фіолетовий */
  color: #ffffff;
}

.edit-btn:hover {
  background-color: rgba(120, 30, 160, 0.8);
  box-shadow: 0 2px 8px rgba(147, 38, 198, 0.4);
}

.complete-btn { /* "Переглянути результат", "Виконати" */
  background-color: transparent;
  color: #82ddf0; /* Світло-блакитний */
  border: 1px solid #82ddf0;
}

.complete-btn:hover {
  background-color: rgba(130, 221, 240, 0.15);
  border-color: #a0e5f3;
  box-shadow: 0 2px 8px rgba(130, 221, 240, 0.3);
}

.complete-btn.paid-style { /* "Оплачено" */
  border-color: #5cb85c; /* Зелений */
  color: #5cb85c;
}

.complete-btn.paid-style:hover {
  background-color: rgba(92, 184, 92, 0.15);
  border-color: #77c977;
  box-shadow: 0 2px 8px rgba(92, 184, 92, 0.3);
}


.refuse-btn { /* "Відмовитися" */
  background-color: #e74c3c; /* Червоний */
  color: white;
}

.refuse-btn:hover {
  background-color: #c0392b;
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4);
}

.remove-executor-btn { /* "Відключити виконавця" */
  background-color: #e67e22; /* Помаранчевий */
  color: white;
}

.remove-executor-btn:hover {
  background-color: #d35400;
  box-shadow: 0 2px 8px rgba(230, 126, 34, 0.4);
}


.expandable {
  overflow: hidden; /* Важливо для анімації висоти */
}

/* Анімація розгортання/згортання */
.expand-enter-active,
.expand-leave-active {
  transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1), /* Плавна анімація висоти */ opacity 0.45s cubic-bezier(0.4, 0, 0.2, 1) 0.05s, /* Анімація прозорості з невеликою затримкою */ padding-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  padding-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-top 0.5s cubic-bezier(0.4, 0, 0.2, 1),
  margin-bottom 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 1000px; /* Достатньо велика максимальна висота */
  opacity: 1;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0 !important; /* !important, щоб перебити інші стилі під час анімації */
  padding-bottom: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

.startup-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center; /* Кнопки по центру */
  gap: 0.8rem;
  flex-wrap: wrap; /* Дозволяємо перенос кнопок */
  margin-bottom: 1rem; /* Відступ під кнопками дій зі стартапом */
}

.comments-heading {
  font-size: 1.1rem;
  font-weight: 600;
  color: #d5d8de;
  margin-bottom: 0.8rem;
  padding-top: 0.8rem; /* Відступ зверху, щоб відокремити від кнопок */
  border-top: 1px solid rgba(255, 255, 255, 0.1); /* Лінія для візуального розділення */
}

.startup-comments-list {
  list-style: none;
  padding-left: 0;
  margin-top: 0.5rem;
}

.comment-entry {
  background-color: rgba(255, 255, 255, 0.03); /* Дуже легкий фон для коментарів */
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
  margin-right: auto; /* Автор зліва, решта справа */
}

.comment-meta-and-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem; /* Проміжок між датою та кнопкою видалення */
  margin-left: 0.5rem; /* Відступ від автора */
}

.comment-date-small {
  font-size: 0.8rem;
  color: #8a8f9c;
}

.delete-comment-icon {
  background: none;
  border: none;
  color: #e74c3c; /* Червоний для видалення */
  font-size: 1.2rem; /* Трохи більша іконка */
  font-weight: bold;
  cursor: pointer;
  padding: 0.1rem 0.3rem; /* Невеликий падінг для зручності кліку */
  line-height: 1; /* Щоб іконка не займала зайвої висоти */
  transition: color 0.2s ease;
}

.delete-comment-icon:hover {
  color: #c0392b; /* Темніший червоний при наведенні */
}

.comment-text-small {
  font-size: 0.9rem;
  color: #b0b3b8;
  line-height: 1.5;
  margin-bottom: 0.3rem; /* Невеликий відступ під текстом коментаря */
  white-space: pre-wrap; /* Зберігаємо переноси рядків */
  word-break: break-word; /* Дозволяємо перенос довгих слів */
}

.no-comments-text {
  color: #a0a8b5;
  font-style: italic;
  margin-top: 0.5rem;
  padding-left: 0.5rem; /* Невеликий відступ для тексту "немає коментарів" */
}


/* Стилі для універсального модального вікна (залишаються без змін) */
.profile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  opacity: 0;
  animation: fadeInOverlayProfile 0.2s forwards;
}

@keyframes fadeInOverlayProfile {
  to {
    opacity: 1;
  }
}

.profile-modal-content {
  background-color: #36393f; /* Темний фон модалки */
  padding: 25px 30px;
  border-radius: 8px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  width: 90%;
  max-width: 450px; /* Максимальна ширина модалки */
  color: #dcddde; /* Світлий текст */
  text-align: left; /* Вирівнювання тексту в модалці */
  transform: scale(0.95) translateY(0px);
  opacity: 0;
  animation: scaleInModalProfile 0.25s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes scaleInModalProfile {
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.profile-modal-header {
  display: flex;
  align-items: center; /* Іконка і заголовок на одному рівні */
  margin-bottom: 15px;
}

.profile-modal-header-icon {
  margin-right: 12px;
  flex-shrink: 0; /* Щоб іконка не стискалася */
  width: 22px;
  height: 22px;
}

/* Іконка за замовчуванням (попередження) */
.profile-modal-header-icon {
  color: #f0b232; /* Жовтий для попередження */
}

/* Іконка для успіху/інформації */
.profile-modal-header-icon.success {
  color: #28a745; /* Зелений */
}


.profile-modal-content h4 {
  margin: 0;
  font-size: 1.2em;
  color: #ffffff;
  font-weight: 600;
}

.profile-modal-content p {
  margin-bottom: 25px;
  font-size: 1em;
  line-height: 1.65;
  color: #b9bbbe;
}

.comment-snippet-preview {
  color: #dcddde;
  background-color: rgba(255, 255, 255, 0.05);
  padding: 8px 10px;
  border-radius: 4px;
  font-style: italic;
  margin-top: 10px;
  max-height: 60px; /* Обмеження висоти прев'ю коментаря */
  overflow-y: auto; /* Додаємо скрол, якщо текст не влазить */
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9em;
}


.profile-modal-actions {
  display: flex;
  justify-content: flex-end; /* Кнопки справа */
  gap: 12px;
}

.profile-modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
}

.profile-modal-button:active {
  transform: translateY(1px); /* Ефект натискання */
}

.profile-modal-button.confirm { /* "Видалити", "Так, відмовитися" */
  background-color: #d83c3e; /* Червоний */
  color: white;
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.2);
}

.profile-modal-button.confirm:hover {
  background-color: #bf3032;
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.25);
}

.profile-modal-button.cancel { /* "Скасувати", "Залишитися" */
  background-color: #4f545c; /* Темно-сірий */
  color: #dcddde;
}

.profile-modal-button.cancel:hover {
  background-color: #5c626a;
}

.profile-modal-button.ok { /* Кнопка "ОК" для сповіщень */
  background-color: #007bff; /* Синій */
  color: white;
}

.profile-modal-button.ok:hover {
  background-color: #0056b3;
}
</style>