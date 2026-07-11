import { ref } from "vue";

export type Theme = "light" | "dark";

const theme = ref<Theme>("light");

function applyTheme(value: Theme) {
  theme.value = value;
  document.documentElement.dataset.theme = value === "dark" ? "dark" : "";
  localStorage.setItem("theme", value);
}

export function useTheme() {
  function initTheme() {
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored === "light" || stored === "dark") {
      applyTheme(stored);
      return;
    }
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark ? "dark" : "light");
  }

  function toggleTheme() {
    applyTheme(theme.value === "light" ? "dark" : "light");
  }

  return { theme, initTheme, toggleTheme };
}
