<template>
  <div id="app">
    <router-view />
  </div>

</template>

<script>
import {defineComponent} from "vue";
import MainPage from "@/views/MainPage.vue";

export default defineComponent({
  components: {MainPage}
})
</script>

<style>
/* Загальні стилі для усього додатку */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}



#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  min-height: 100vh;  /* Мінімальна висота 100% від екрану */
  display: flex;
  flex-direction: column;
}


#nav a {
  font-weight: bold;
  color: #2c3e50;
}

#nav a.router-link-exact-active {
  color: #42b983;
}


</style>
