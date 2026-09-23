<template>
  <div class="blueprint">
    <header>
      <span>Paintcan 涂量估算</span>
      <nav>
        <router-link to="/">平面图</router-link>
        <router-link to="/rooms">房间</router-link>
        <router-link to="/estimate">估漆</router-link>
        <router-link to="/coverage">遮盖力</router-link>
        <router-link to="/diagram">洞口</router-link>
        <router-link to="/history">记录</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
    </header>
    <router-view />
  </div>
</template>
