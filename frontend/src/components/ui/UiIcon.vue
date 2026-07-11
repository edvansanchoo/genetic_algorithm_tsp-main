<script setup lang="ts">
withDefaults(
  defineProps<{
    name: string;
    size?: number;
  }>(),
  { size: 20 },
);

const icons: Record<string, string> = {
  ambulance:
    "M3 12h2l1.5-4.5h11L19 12h2v6h-2v-2H5v2H3v-6zm4 4a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm10 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 10h8l-1-3H9l-1 3z",
  pause: "M6 5h4v14H6V5zm8 0h4v14h-4V5z",
  play: "M8 5v14l11-7L8 5z",
  dice: "M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2zm2 4h2v2H7V7zm8 0h2v2h-2V7zM7 15h2v2H7v-2zm8 0h2v2h-2v-2z",
  hospital:
    "M12 3l8 4v10H4V7l8-4zm0 3.5L6 9.5V17h12V9.5L12 6.5zM11 10h2v3h3v2h-3v3h-2v-3H8v-2h3v-3z",
  reset:
    "M12 4V1L8 5l4 4V6a6 6 0 016 6 6 6 0 01-6 6 6 6 0 01-5.65-4H4.35A8 8 0 1012 4z",
  fullscreen:
    "M3 3h6v2H5v4H3V3zm12 0h6v6h-2V5h-4V3zM3 15h2v4h4v2H3v-6zm16 0v6h-6v-2h4v-4h2z",
  "zoom-in": "M11 5a6 6 0 104.24 10.24l3.53 3.53 1.41-1.41-3.53-3.53A6 6 0 0011 5zm0 2a4 4 0 110 8 4 4 0 010-8zm-1 3h2v2h-2v-2z",
  "zoom-out":
    "M11 5a6 6 0 104.24 10.24l3.53 3.53 1.41-1.41-3.53-3.53A6 6 0 0011 5zm-2 6h4v2H9v-2z",
  sun: "M12 7a5 5 0 100 10 5 5 0 000-10zm0-5v2m0 16v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M2 12h2m16 0h2M4.22 19.78l1.42-1.42M19.78 19.78l-1.42-1.42",
  moon: "M21 14.5A8.5 8.5 0 1110.5 3a7 7 0 0010.5 11.5z",
  truck: "M3 6h11v9H3V6zm11 2h3l2 3v4h-5V8zM6 17a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm9 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z",
  box: "M3 7l9-4 9 4-9 4-9-4zm0 2.5l9 4 9-4V17l-9 4-9-4V9.5z",
  pin: "M12 2a5 5 0 00-5 5c0 3.75 5 11 5 11s5-7.25 5-11a5 5 0 00-5-5zm0 6.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3z",
  block:
    "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
};
</script>

<template>
  <svg
    class="ui-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
  >
    <path :d="icons[name] ?? icons.block" />
  </svg>
</template>

<style scoped>
.ui-icon {
  flex-shrink: 0;
  display: block;
}
</style>
