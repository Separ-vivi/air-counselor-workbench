<template>
  <div class="app-layout">
    <SideBar />
    <div class="app-main">
      <TopBar />
      <div class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    <GlobalSearch />
  </div>
</template>

<script setup>
import SideBar from '@/components/SideBar.vue'
import TopBar from '@/components/TopBar.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import { onMounted } from 'vue'
import { useOrgStore } from '@/stores/org.js'

const orgStore = useOrgStore()

onMounted(async () => {
  // 应用启动时预加载一次组织树
  try { await orgStore.loadTree(true) } catch (e) { /* 已在拦截器 message */ }
})
</script>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity .15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
