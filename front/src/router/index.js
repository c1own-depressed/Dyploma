import { createRouter, createWebHistory } from 'vue-router';

import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import MainPage from '../views/MainPage.vue';
import TaskDetails from '../views/TaskDetails.vue';
import ProfilePage from '../views/ProfilePage.vue';
import TaskResult from '../views/TaskResult.vue';

import ChatsLayout from '../views/ChatsLayout.vue';
import ChatWindow from '../views/ChatWindow.vue';
import AboutUs from '../views/AboutUs.vue'; // <--- ІМПОРТ ДОДАНО

// Динамічні імпорти
const CreateStartup = () => import('@/views/CreateStartup.vue');
const EditStartup = () => import('@/views/EditStartup.vue');
const CreateTask = () => import('@/views/CreateTask.vue');
const CreateTaskPage = () => import('@/views/CreateTask.vue'); // Зверніть увагу, ви двічі імпортуєте CreateTask.vue
const EditTask = () => import('@/views/EditTask.vue');
const CompleteTask = () => import('@/views/CompleteTask.vue');

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path: '/register',
        name: 'Register',
        component: Register
    },
    {
        path: '/main-page',
        name: 'MainPage',
        component: MainPage,
        meta: { requiresAuth: true }
    },
    {
        path: '/task/:id',
        name: 'TaskDetails',
        component: TaskDetails,
        meta: { requiresAuth: true }
    },
    {
        path: '/profile',
        name: 'ProfilePage',
        component: ProfilePage,
        meta: { requiresAuth: true }
    },
    {
        path: '/profile/:ownerId',
        name: 'ProfileOwner',
        component: ProfilePage,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/create-startup',
        name: 'CreateStartup',
        component: CreateStartup,
        meta: { requiresAuth: true }
    },
    {
        path: '/edit-startup/:id',
        name: 'EditStartup',
        component: EditStartup,
        meta: { requiresAuth: true }
    },
    {
        path: '/create-task',
        name: 'CreateTask',
        component: CreateTask,
        meta: { requiresAuth: true }
    },
    {
        path: '/create-task/:id',
        name: 'CreateTaskWithId',
        component: CreateTaskPage, // Перевірте, чи це правильний компонент, бо ім'я змінної CreateTaskPage
        meta: { requiresAuth: true }
    },
    {
        path: '/edit-task/:id',
        name: 'EditTask',
        component: EditTask,
        meta: { requiresAuth: true }
    },
    {
        path: '/complete-task/:taskId',
        name: 'CompleteTask',
        component: CompleteTask,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/task-result/:taskId',
        name: 'TaskResult',
        component: TaskResult,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/chats',
        component: ChatsLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                component: ChatWindow
            },
            {
                path: ':id', // Шлях для конкретного чату
                name: 'ChatWithUser', // Додайте ім'я, якщо потрібно посилатися на нього
                component: ChatWindow,
                props: true
            }
        ]
    },
    { // <--- НОВИЙ МАРШРУТ ДОДАНО ТУТ
        path: '/about-us',
        name: 'AboutUs',
        component: AboutUs
    },
    {
        path: '/',
        redirect: '/login' // Зазвичай, '/' перенаправляє на головну сторінку після логіну, або на /login, якщо не авторизований
    },
    {
        path: '/:pathMatch(.*)*', // "Catch all" для неіснуючих шляхів
        name: 'NotFound',
        redirect: '/login' // Або на спеціальну сторінку 404
    }
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
});

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('jwtToken');
    // Якщо користувач авторизований і намагається перейти на /login або /register, перенаправити на /main-page
    if (token && (to.name === 'Login' || to.name === 'Register')) {
        next({ name: 'MainPage' });
    } else if (to.matched.some(record => record.meta.requiresAuth) && !token) {
        next('/login');
    } else {
        next();
    }
});

export default router;