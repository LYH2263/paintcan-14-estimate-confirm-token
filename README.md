# 16-paintcan（刷墙涂料）

Paintcan — 墙面积 − 门窗开洞；按涂布率与遍数换升数

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4500 |
| API | http://localhost:9500 |

## 主链

房间墙面减门窗 → 涂料升数 → 用量清单

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
