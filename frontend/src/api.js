async function parseResponse(r) {
  if (r.ok) return r.json()
  let message = `请求失败 (${r.status})`
  try {
    const d = JSON.parse(await r.text())
    if (typeof d.detail === 'string') message = d.detail
    else if (d.detail && d.detail.message) message = d.detail.message
  } catch { /* 非 JSON 错误体，保留默认文案 */ }
  throw new Error(message)
}
export async function getJSON(path) {
  return parseResponse(await fetch(path))
}
export async function postJSON(path, body) {
  return parseResponse(await fetch(path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }))
}
