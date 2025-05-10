import { createRouter, createWebHistory } from 'vue-router';

import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import MainPage from '../views/MainPage.vue';
import TaskDetails from '../views/TaskDetails.vue';
import ProfilePage from '../views/ProfilePage.vue';
import TaskResult from '../views/TaskResult.vue';

import ChatsLayout from '../views/ChatsLayout.vue';
import ChatWindow from '../views/ChatWindow.vue';

// Динамічні імпорти
const CreateStartup = () => import('@/views/CreateStartup.vue');
const EditStartup = () => import('@/views/EditStartup.vue');
const CreateTask = () => import('@/views/CreateTask.vue');
const CreateTaskPage = () => import('@/views/CreateTask.vue');
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
        component: CreateTaskPage,
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
                path: ':id',
                component: ChatWindow,
                props: true
            }
        ]
    },
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/login'
    }
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
});

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('jwtToken');
    if (to.matched.some(record => record.meta.requiresAuth) && !token) {
        next('/login');
    } else {
        next();
    }
});

export default router;
