<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/rooms')).items })
</script>
<template><div class="page"><h1>房间</h1>
<table><tr v-for="r in items" :key="r.id"><td>{{ r.name }}</td><td>{{ r.length }}×{{ r.width }}×{{ r.height }}</td>
<td><router-link :to="`/rooms/${r.id}`">详情</router-link></td></tr></table></div></template>
