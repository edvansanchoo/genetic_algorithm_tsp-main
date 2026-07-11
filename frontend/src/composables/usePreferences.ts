import { ref, watch } from "vue";

const showRunnerUp = ref(localStorage.getItem("pref.show_runner_up") !== "false");
const showTransit = ref(localStorage.getItem("pref.show_transit") !== "false");

watch(showRunnerUp, (value) => {
  localStorage.setItem("pref.show_runner_up", String(value));
});

watch(showTransit, (value) => {
  localStorage.setItem("pref.show_transit", String(value));
});

export function usePreferences() {
  return { showRunnerUp, showTransit };
}
