import { createApp } from 'vue'
import App from './App.vue'
import router from './router'; // Імпортуємо роутер

const app = createApp(App)

// Додаємо логіку редіректу до сторінки логіну
router.beforeEach((to, from, next) => {
    if (to.path === '/') {
        next('/login'); // Перенаправляє на сторінку логіну
    } else {
        next(); // Якщо інший маршрут, просто переходимо
    }
});

app
    .use(router)  // Додаємо роутер до додатку
    .mount('#app');
