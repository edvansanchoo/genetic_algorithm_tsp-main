<script setup lang="ts">
import UiButton from "./ui/UiButton.vue";

const emit = defineEmits<{
  shuffle: [];
  hospital: [];
  reset: [];
}>();
</script>

<template>
  <section>
    <h3 class="section-title">Ações rápidas</h3>
    <div class="action-stack">
      <UiButton icon="dice" @click="emit('shuffle')">Sortear posições</UiButton>
      <UiButton icon="hospital" @click="emit('hospital')">Cenário hospitalar</UiButton>
      <UiButton variant="danger" icon="reset" @click="emit('reset')">Resetar cenário</UiButton>
    </div>
  </section>
</template>
