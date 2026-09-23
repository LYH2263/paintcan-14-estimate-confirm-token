<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const d = ref(null)
onMounted(async () => { d.value = await getJSON('/api/dashboard') })
</script>
<template><div class="page"><h1>户型涂量</h1><p v-if="d">房间 {{ d.room_count }} · 对照 {{ d.clean }}/{{ d.dirty }}</p></div></template>
