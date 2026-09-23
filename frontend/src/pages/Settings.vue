<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const s = ref({})
onMounted(async () => { s.value = await getJSON('/api/settings') })
</script>
<template><div class="page"><pre>{{ s }}</pre></div></template>
