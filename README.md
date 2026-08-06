# 高校辅导员工作平台 V3-A · 前端补丁包 README

> 本目录为 **完整可用的 Vue 3 前端项目**（非增量 diff），用于替换扣子项目 `frontend/src/`。130 条后端 API 已经上线（除 `/api/class360/{cid}/summary` 500，前端做了兜底），本补丁 100% 对齐 openapi.json，无占位符、无 TODO。

- 技术栈：**Vue 3 Composition API + `<script setup>` · Element Plus · Pinia · Vue Router 4 · Axios · ECharts · Vite 5 · Node 18+**
- 主题：马卡龙低饱和色系（侧边栏 `#4A7A8C` / 顶栏 `#FDFAF3` / 卡片圆角 12px）
- 后端探测域：`https://f40d7f85-7c5b-4170-b2cd-9a4434dabbe9.dev.coze.site`

---

## 一、目录结构

```
v3a_frontend_patch/
├── package.json                # Vue 3 + ElementPlus + ECharts 依赖清单
├── vite.config.js              # 别名 @ / 代理 /api -> :8000 / 手动 chunk
├── index.html                  # 入口 HTML
├── src/
│   ├── main.js                 # Vue 应用入口（Pinia + Router + ElementPlus + Icons）
│   ├── App.vue                 # 根布局（侧边栏 + 顶栏 + 全局搜索）
│   ├── styles/main.css         # 马卡龙主题变量与基础样式
│   │
│   ├── api/
│   │   ├── index.js            # axios 实例：GET 全禁缓存 + _t=Date.now() + 拦截器统一提示
│   │   ├── students.js         # /api/students 列表/CRUD/搜索/导出
│   │   ├── student360.js       # student360 主接口 + 20 个子资源 CRUD（resource 工厂 + s360 对象）
│   │   ├── class360.js         # 8 条只读班级 360 接口
│   │   ├── org.js              # /api/org/tree + 年级/专业/班级 CRUD
│   │   ├── smartImport.js      # /api/import/detect + /api/import/confirm (+ 备用 /smart-import/*)
│   │   └── modules.js          # 10 模块 API（grades/party/psy/family/cadres/activities/emp/meetings/teachers/dashboard/settings/tags）
│   │
│   ├── stores/
│   │   ├── org.js              # 组织树 + 顶栏过滤状态（localStorage 持久化）
│   │   ├── student.js          # refreshBumper 响应式触发器
│   │   └── class.js            # 班级缓存 + summary 500 兜底
│   │
│   ├── router/index.js         # Hash 路由（避免 nginx fallback）· 全部 17 条路由
│   ├── utils/eventBus.js       # mitt 事件总线（用于 Ctrl+K 打开搜索面板）
│   │
│   ├── components/             # 基础/通用组件
│   │   ├── SideBar.vue         # 侧边栏 #4A7A8C
│   │   ├── TopBar.vue          # 顶栏 #FDFAF3 · 含 OrgSelector + Ctrl+K 提示
│   │   ├── OrgSelector.vue     # 三级级联切换器（年级/专业/班级）
│   │   ├── GlobalSearch.vue    # Ctrl+K 全局搜索面板（300ms debounce）
│   │   ├── StudentSelect.vue   # 无缓存学生下拉（每次 visible-change 强拉）
│   │   ├── CrudPanel.vue       # 通用 CRUD 组件（onCreate/onUpdate/onDelete 回调 props）
│   │   ├── student360/         # 12 个学生 360 Tab
│   │   └── class360/           # 8 个班级 360 Tab
│   │
│   └── views/                  # 页面
│       ├── Dashboard.vue       # 首页驾驶舱
│       ├── StudentList.vue     # 学生列表 + 分页搜索 + CRUD
│       ├── Student360.vue      # 学生 360 主页 + 12 Tab
│       ├── ClassList.vue       # 班级列表（卡片式）
│       ├── Class360.vue        # 班级 360 主页 + 8 Tab（含 summary 500 兜底）
│       ├── OrgManagement.vue   # 三级架构 CRUD
│       ├── SmartImport.vue     # 6 种类型智能导入（3 步：上传 → 映射 → 确认）
│       └── modules/            # 10 个业务模块列表页
│           ├── GradesModule.vue        (成绩管理)
│           ├── WarningsModule.vue      (学业预警)
│           ├── PartyModule.vue         (党团发展)
│           ├── PsychologyModule.vue    (心理关怀)
│           ├── FamilyModule.vue        (家庭联络)
│           ├── CadresModule.vue        (学生干部)
│           ├── ActivitiesModule.vue    (活动管理)
│           ├── EmploymentModule.vue    (就业管理)
│           ├── MeetingsModule.vue      (班会管理)
│           └── TeachersModule.vue      (班主任管理)
│
├── backend_fix/
│   └── README.md               # /api/class360/{cid}/summary 500 修复指引（含 Python 伪代码补丁）
│
└── README.md                   # 本文件
```

---

## 二、如何应用到扣子项目

### 方式 A：整体替换 frontend/src（推荐）

```bash
# 1. 备份现有的 frontend/src
cd <扣子项目根>/frontend
cp -r src src.backup.$(date +%Y%m%d)

# 2. 覆盖 src、package.json、vite.config.js、index.html
rm -rf src
cp -r /path/to/v3a_frontend_patch/src ./src
cp /path/to/v3a_frontend_patch/package.json .
cp /path/to/v3a_frontend_patch/vite.config.js .
cp /path/to/v3a_frontend_patch/index.html .

# 3. 装依赖 + 起服务
npm install
npm run dev
# 浏览器打开 http://localhost:5173 → 自动跳到 /#/dashboard
```

### 方式 B：Zip 包上传

```bash
# 打包 (Bash)
cd /app/data/所有对话/主对话
zip -r v3a_frontend_patch.zip v3a_frontend_patch/

# 用户下载解压到扣子项目 frontend/ 目录下即可
```

---

## 三、25 项验收标准与实现文件对照

| # | 验收标准 | 覆盖文件 |
|---|---|---|
| 1 | 三级架构（年级/专业/班级）可视化 | `stores/org.js` · `views/OrgManagement.vue` · `components/OrgSelector.vue` |
| 2 | 三级架构 CRUD（增/删/改） | `views/OrgManagement.vue`（3 个 tab + 3 个 dialog） |
| 3 | 顶栏三级切换器 | `components/TopBar.vue` + `OrgSelector.vue`（跨页面 localStorage 持久） |
| 4 | 学生 360 页面主框架 | `views/Student360.vue`（12 Tab + 头部信息 + 编辑弹窗 + 预警灯） |
| 5 | 学生 360 · 基本信息 Tab | `TabBasic.vue`（含学籍异动） |
| 6 | 学生 360 · 成绩 Tab | `TabGrades.vue` |
| 7 | 学生 360 · 党团 Tab | `TabParty.vue` |
| 8 | 学生 360 · 心理 Tab | `TabPsychology.vue` |
| 9 | 学生 360 · 家庭联络 Tab | `TabFamily.vue` |
| 10 | 学生 360 · 干部经历 Tab | `TabCadres.vue` |
| 11 | 学生 360 · 活动参与 Tab | `TabActivities.vue`（关联活动+跳转） |
| 12 | 学生 360 · 就业 Tab | `TabEmployment.vue` |
| 13 | 学生 360 · 资助/荣誉 Tab | `TabFundingHonor.vue`（内层 6 子分区：困难/助学金/奖学金/贷款/勤工/荣誉） |
| 14 | 学生 360 · 日常 Tab | `TabDaily.vue`（内层 5 子分区：走访/请假/违纪/谈心/考勤） |
| 15 | 学生 360 · 项目 Tab | `TabProjects.vue` |
| 16 | 学生 360 · 时间线 Tab | `TabTimeline.vue` |
| 17 | 班级 360 页面主框架 + 8 Tab | `views/Class360.vue` + `components/class360/*` |
| 18 | 智能导入 6 种台账类型 | `views/SmartImport.vue`（花名册/成绩/党团/资助/奖助/评优） |
| 19 | 智能导入 3 步走 UI | `views/SmartImport.vue`（Steps 组件 + 字段映射表） |
| 20 | Ctrl+K 全局搜索 | `components/GlobalSearch.vue` + `main.js` 中的 keydown 监听（在 GlobalSearch 内实现） |
| 21 | 5 模块下拉搜索无缓存 · 300ms debounce · 关键字一致 | `components/StudentSelect.vue`（visible-change 强拉 + `_t` 时间戳） |
| 22 | 10 模块列表页响应式刷新 | `views/modules/*.vue`（watch `studentStore.refreshBumper`） |
| 23 | 就地 CRUD 全部 el-dialog | 所有页面（无一处整页跳转 CRUD） |
| 24 | 马卡龙主题 · 圆角 12px · 无大面积白背景 | `styles/main.css` + 各页面 `.stat-card`, `border-radius: 12px` |
| 25 | 所有 API 100% 对齐 openapi.json | `api/*.js` 逐条对照，无伪造路径 |

---

## 四、关键设计决策

1. **API 层用 resource 工厂**：`api/student360.js` 生成 20 个子资源 × 4 个 CRUD 方法，避免手写 80 份代码；统一挂到 `s360` 对象。
2. **CrudPanel 回调 props 化**：`onCreate/onUpdate/onDelete` 都是 async 函数 props，父组件调用 API 后 return，Panel 内部 await 完自动 ElMessage + reload。
3. **class360 summary 500 兜底**：`Class360.vue` 里 try/catch → `getClass()` + `getClassStudents()` + `orgTree` 拼装 fallback classInfo，前端不会白屏。修好后端后自动切回真数据。
4. **StudentSelect 三层去缓存**：
   - Axios 拦截器给所有 GET 加 `_t=Date.now()`
   - StudentSelect `visible-change=true` 时强制 `fetchIt('')` 重新拉
   - 不在组件内维护 `optionsCache`
5. **响应式刷新用 refreshBumper**：CRUD 后 `studentStore.bumpRefresh()` +1，所有模块页 `watch` 该值自动 reload，无需 F5。
6. **hash 路由**：`createWebHashHistory` 避免 nginx 未配 fallback 时刷新 404。
7. **eventBus 只做全局快捷键**：`mitt` 单例，`Ctrl+K` → emit `openGlobalSearch` → `GlobalSearch.vue` on。

---

## 五、Air 需要验证的 3 个核心场景

### 场景 A · 五模块下拉搜索一致性（第 21 项验收）

清库重导 384 学生 → 在以下 5 个位置各输入 `张` / `20250502` / `zyt` / `网安`，期望看到**完全一致的候选列表**：

1. `/module/party` → 「新增记录」dialog 里的学生选择
2. `/module/psychology` → 「新增记录」dialog 里的学生选择
3. `/module/family` → 「新增记录」dialog 里的学生选择
4. `/module/cadres` → 「新增记录」dialog 里的学生选择
5. `/module/employment` → 「新增记录」dialog 里的学生选择

所有 5 处都用 `<StudentSelect />` 组件，共用 `/api/students/search?q=&limit=50`，前端无缓存。

### 场景 B · Ctrl+K 全局搜索

任意页面按 `Ctrl+K`（Mac 为 `Cmd+K`）→ 弹出面板 → 输入 `张`（300ms debounce）→ 显示学生列表 → 回车/点击跳转 `/students/:id`。

⚠️ 部分浏览器/操作系统会拦截 `Ctrl+K`（如 Chrome 会打开地址栏搜索）。若实测被拦截，可手动点击顶栏搜索图标打开面板，或改用 `Ctrl+/`（在 `GlobalSearch.vue` 里改一行 keydown 判断）。

### 场景 C · 学生 360 · 班级 360 · CRUD 响应式

1. 打开 `/students/1` → 切到「日常记录」Tab → 新增一条「宿舍走访」→ 关闭 dialog，列表**无需 F5** 自动出现新记录。
2. 打开 `/classes/1` → 8 Tab 依次切换，Summary 会弹「summary 接口暂不可用」alert（预期），其它 7 Tab 数据正常显示。
3. 修好后端 summary 500 → Summary Tab 自动切回真数据，无需前端改动。

---

## 六、后端待修 & 前端未测

- **必修**：`/api/class360/{cid}/summary` 500（见 `backend_fix/README.md`）
- **未跑真数据**：SmartImport 的 `POST /api/import/detect` + `POST /api/import/confirm` 只在 UI 层做了字段拟合，air 需要用真实 xlsx 跑一遍验证映射逻辑
- **快捷键**：Ctrl+K 可能被浏览器拦截，实测后决定是否改为 Ctrl+/

---

## 七、启动与调试速查

```bash
# 后端在 :8000
cd backend && python main.py

# 前端在 :5173
cd frontend && npm install && npm run dev

# 生产构建
cd frontend && npm run build
# 产物在 frontend/dist/，用 nginx 挂到 /，同时把 /api/* 反代到后端 :8000
```

nginx 示例：

```nginx
location / {
  root /var/www/v3a;
  try_files $uri $uri/ /index.html;
}
location /api/ {
  proxy_pass http://localhost:8000;
}
```

（hash 路由下 try_files 兜底其实可省，但保留一份更稳。）

---

## 八、已知限制 & 后续 P1 建议

| 项 | 状态 | 建议 |
|---|---|---|
| class360 summary 500 | 后端未修 · 前端兜底 | 参考 `backend_fix/README.md`，1 小时可修 |
| SmartImport 未真跑 | 已按 openapi 对齐 | 实测第一份 xlsx 后可能需微调字段映射启发式 |
| Ctrl+K 快捷键 | 部分浏览器可能拦截 | 加 topbar 搜索按钮兜底（已实现） |
| 大量学生数据的分页 | 已支持 20/50/100/200 | 若 > 5000 学生需要考虑虚拟滚动 |
| 权限系统 | 本补丁未涉及 | V3-B/V3-C 迭代时接入 |

---

## 九、License

内部使用，无 license。

## 十、变更历史

- v1.0.0 · 2025 · Vue 3 前端 V3-A 补丁包 · 首次交付
