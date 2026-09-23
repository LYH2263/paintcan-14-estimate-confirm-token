<script setup>
import { computed, ref } from 'vue'
import { postJSON } from '../api'

const room_id = ref(1)
const pre = ref(null)        // 预检回执
const busy = ref(false)
const confirmed = ref(null)  // 确认成功的落库结果
const error = ref('')

const token = computed(() => pre.value?.receipt_token ?? '')

async function precheck() {
  busy.value = true; error.value = ''; confirmed.value = null; pre.value = null
  try {
    pre.value = await postJSON('/api/estimate/precheck', { room_id: room_id.value })
  } catch (e) { error.value = msg(e) }
  finally { busy.value = false }
}

async function confirm() {
  if (!token.value) return
  busy.value = true; error.value = ''
  const t = token.value
  try {
    confirmed.value = await postJSON('/api/estimate/confirm', { receipt_token: t })
    pre.value = null  // 一次性回执，确认成功即作废旧态
  } catch (e) {
    // 复用/过期/快照变更均被后端拒绝：回执已不可用，必须重新预检
    pre.value = null
    error.value = msg(e)
  } finally { busy.value = false }
}

function msg(e) {
  try {
    const d = JSON.parse(e.message).detail
    return typeof d === 'string' ? d : (d?.detail ?? e.message)
  } catch { return e.message }
}
</script>

<template>
  <div class="page">
    <h1>估漆工作台</h1>
    <label>房间ID <input v-model.number="room_id" :disabled="busy" /></label>
    <button @click="precheck" :disabled="busy || !!pre">1. 预检</button>

    <div v-if="pre" class="receipt">
      <p>预检结果：净 {{ pre.net_m2 }} m² · {{ pre.liters }} 升</p>
      <p class="hint">回执 {{ pre.expires_at }} 前有效，仅限使用一次。</p>
      <button @click="confirm" :disabled="busy">2. 确认落库</button>
    </div>

    <p v-if="confirmed" class="ok">
      已落库 #{{ confirmed.run_id }}：净 {{ confirmed.net_m2 }} m² · {{ confirmed.liters }} 升 ·
      <router-link to="/history">查看历史新行</router-link>
    </p>
    <p v-if="error" class="error">操作被拒绝：{{ error }}（请重新预检）</p>
  </div>
</template>
