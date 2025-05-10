<template>
  <div class="layout">
    <aside class="sidebar">
      <ChatSidebar />
    </aside>
    <main class="chat-window">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import ChatSidebar from '@/components/ChatSidebar.vue'
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background: linear-gradient(to bottom right, #3b0a57, #4c1d95); /* фіолетовий фон */
  color: #f3e8ff;
}

.sidebar {
  width: 301px;
  background: linear-gradient(to bottom, #4b0082, #6a0dad);
  border-right: 1px solid #7b2cbf;
  overflow-y: auto;
  box-shadow: 4px 0 10px rgba(0, 0, 0, 0.3);
}

.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #2d014d; /* темно-фіолетовий */
  overflow-y: auto;
}
</style>
