import { createApp } from 'vue'
import './style.css'
import './styles/global.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)  
app.use(ElementPlus)
app.use(router)        
app.mount('#app')           