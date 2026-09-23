<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const detail = ref(null)
const est = ref(null)
const load = async () => {
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  est.value = await postJSON('/api/estimate/precheck', { room_id: +route.params.id })
}
onMounted(load); watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="detail"><h1>{{ detail.room.name }}</h1>
<p>净面积 {{ est?.net_m2 }} m² · 需漆 <span class="hero-num">{{ est?.liters }} L</span></p>
<ul><li v-for="o in detail.openings" :key="o.id">{{ o.kind }} {{ o.w }}×{{ o.h }}</li></ul>
</div></template>
