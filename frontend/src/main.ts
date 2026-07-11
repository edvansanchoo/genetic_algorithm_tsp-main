import { createApp } from "vue";
import App from "./App.vue";
import { useTheme } from "./composables/useTheme";
import "./styles/tokens.css";
import "./styles/theme.css";
import "./styles/layout.css";

useTheme().initTheme();

createApp(App).mount("#app");
