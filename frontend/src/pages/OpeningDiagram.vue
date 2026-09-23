<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const detail = ref(null)
onMounted(async () => { detail.value = await getJSON('/api/rooms/2') })
</script>
<template><div class="page"><h1>洞口示意（种子房间）</h1>
<ul v-if="detail"><li v-for="o in detail.openings" :key="o.id">{{ o.kind }} 扣除 {{ (o.w*o.h).toFixed(2) }} m²</li></ul>
</div></template>
