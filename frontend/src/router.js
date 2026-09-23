import { createRouter, createWebHistory } from 'vue-router'
import PlanOverview from './pages/PlanOverview.vue'
import RoomList from './pages/RoomList.vue'
import RoomDetail from './pages/RoomDetail.vue'
import PaintEstimate from './pages/PaintEstimate.vue'
import CoverageRules from './pages/CoverageRules.vue'
import OpeningDiagram from './pages/OpeningDiagram.vue'
import BatchHistory from './pages/BatchHistory.vue'
import Settings from './pages/Settings.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: PlanOverview },
    { path: '/rooms', component: RoomList },
    { path: '/rooms/:id', component: RoomDetail },
    { path: '/estimate', component: PaintEstimate },
    { path: '/coverage', component: CoverageRules },
    { path: '/diagram', component: OpeningDiagram },
    { path: '/history', component: BatchHistory },
    { path: '/settings', component: Settings },
  ],
})
