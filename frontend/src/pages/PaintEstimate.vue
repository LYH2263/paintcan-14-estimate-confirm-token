<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const room_id = ref(1)
const pre = ref(null)   // 预检回执
const confirmed = ref(null)
const error = ref('')
const busy = ref(false)

const precheck = async () => {
  busy.value = true; error.value = ''; confirmed.value = null
  try {
    pre.value = await postJSON('/api/estimate/precheck', { room_id: room_id.value })
  } catch (e) { pre.value = null; error.value = e.message }
  finally { busy.value = false }
}

const confirm = async () => {
  busy.value = true; error.value = ''
  try {
    confirmed.value = await postJSON('/api/estimate/confirm', { receipt: pre.value.receipt })
    pre.value = null
  } catch (e) {
    // 回执复用/过期/快照变化等：预检结果作废，需重新预检
    pre.value = null
    error.value = e.message
  } finally { busy.value = false }
}
</script>
<template><div class="page"><h1>估漆工作台</h1>
<label>房间ID <input v-model.number="room_id" :disabled="busy" /></label>
<button @click="precheck" :disabled="busy">预检</button>
<div v-if="pre" class="card">
  <p>预检结果：净 {{ pre.net_m2 }} m² · {{ pre.liters }} 升</p>
  <p class="hint">请确认结果；若房间长宽高或门窗有变动，确认将被拒绝。</p>
  <button @click="confirm" :disabled="busy">确认落库</button>
</div>
<p v-if="confirmed" class="ok">已落库 #{{ confirmed.run_id }}：净 {{ confirmed.net_m2 }} m² · {{ confirmed.liters }} 升</p>
<p v-if="error" class="err">{{ error }}</p></div></template>
