# backend_fix · `/api/class360/{cid}/summary` HTTP 500 修复指引

> 说明：V3-A 地基批的 130 条接口中，已确认这一条**唯一**返回 500。前端已做兜底（用 org 树 + `/students` + `/api/class360/{cid}/students` 组装 fallback 数据），但仍强烈建议尽快修好后端，让 summary tab 显示真实统计。

---

## 1. 现象

```bash
curl -s https://f40d7f85-7c5b-4170-b2cd-9a4434dabbe9.dev.coze.site/api/class360/1/summary
# HTTP/1.1 500 Internal Server Error
# {"detail":"Internal Server Error"}
```

同域名下其它 7 个 class360 只读接口（students、activities、daily、funding、grades、party、psychology）均正常。

## 2. 已交叉验证的事实

| 接口 | 状态 | 举例 |
|---|---|---|
| `/api/class360/1/students` | ✅ 32 条 | 学生对象数组 |
| `/api/class360/1/grades` | ✅ 空数组 | 因当前库无 grade_records |
| `/api/class360/1/party` | ✅ 32 条 | 各阶段发展记录 |
| `/api/class360/1/summary` | ❌ 500 | 全库任意 cid 都 500 |

⇒ 排除 "cid=1 数据脏" 假设，问题是 handler 本身的**代码 bug**，与数据规模无关。

## 3. 根因猜测（按优先级）

**猜测 A · 空聚合导致 `None` 参与算术**（可能性 60%）
`summary` 的 handler 里典型写法：

```python
total = sum(r.score for r in grade_rows)  # grade_rows == [] 时 total = 0，OK
avg = total / len(grade_rows)             # ← 除零：ZeroDivisionError
```

- 当前库还没有 `grade_records`，因此 `grade_rows == []` → `len() == 0` → 除零。
- 或者：`avg = sum(...) / count`，`count` 是另一次 SQL 查出的 `None`。

**猜测 B · JOIN 后 `NoneType` 属性访问**（可能性 25%）
比如：

```python
teacher_name = clazz.teacher.name  # teacher 关系为空
```

**猜测 C · 字段名对不上**（可能性 15%）
schema/model 层字段名和 handler 里预期不一致（如 `class_name` vs `name`）。

## 4. 定位步骤（Air 侧只需 5 分钟）

```bash
# 1. 打开后端服务日志（tail -f 或 pm2 logs / journalctl）
# 2. 触发一次请求
curl -s /api/class360/1/summary
# 3. 看栈顶两行错误定位到具体 handler 与行号
```

如果 handler 使用了 SQLAlchemy，追踪对象名类似 `def get_class_summary(cid: int)` 或路由绑定 `@router.get("/class360/{cid}/summary")`。

## 5. 建议补丁（Python 伪代码）

```python
# app/api/class360.py  或  app/routers/class360.py
from sqlalchemy import func

@router.get("/class360/{cid}/summary")
def get_class_summary(cid: int, db: Session = Depends(get_db)):
    clazz = db.query(Class).filter(Class.id == cid).first()
    if not clazz:
        raise HTTPException(404, "班级不存在")

    students = db.query(Student).filter(Student.class_id == cid).all()
    student_ids = [s.id for s in students]
    student_count = len(students)

    # ---- 全部聚合都用 None-safe 写法 ----
    grade_avg = None
    fail_count = 0
    if student_ids:
        rows = (db.query(GradeRecord)
                  .filter(GradeRecord.student_id.in_(student_ids))
                  .all())
        scores = [r.score for r in rows if r.score is not None]
        if scores:
            grade_avg = round(sum(scores) / len(scores), 2)
        fail_count = sum(1 for s in scores if s < 60)

    party_count = 0
    if student_ids:
        party_count = (db.query(func.count(PartyProgress.id))
                         .filter(PartyProgress.student_id.in_(student_ids),
                                 PartyProgress.stage.in_(['预备党员', '正式党员']))
                         .scalar()) or 0

    # 兜底：所有可能为 None 的字段全部用 or ''、or 0
    return {
        "class_id":         cid,
        "class_name":       clazz.class_name or '',
        "class_teacher":    clazz.class_teacher or '',
        "monitor":          clazz.monitor or '',
        "league_secretary": clazz.league_secretary or '',
        "student_count":    student_count,
        "male_count":       sum(1 for s in students if s.gender == '男'),
        "female_count":     sum(1 for s in students if s.gender == '女'),
        "party_count":      party_count,
        "grade_avg":        grade_avg,          # None 时前端显示 "-"
        "fail_count":       fail_count,
        "hardship_count":   0,                  # 建议同样加聚合但保底为 0
        "warning_count":    0
    }
```

> 关键改动：**任何 `sum()/count/avg` 前都先判断集合非空，且给字符串字段 `or ''`、数值字段 `or 0`。**

## 6. 验证脚本

修完后先本地 curl 一遍：

```bash
curl -s http://localhost:8000/api/class360/1/summary | jq .
curl -s http://localhost:8000/api/class360/2/summary | jq .
curl -s http://localhost:8000/api/class360/999/summary   # 期望 404
```

前端可无缝识别修复：`views/Class360.vue` 在 `getClassSummary()` 成功时会自动切回真实数据，不再走 fallback 分支。

## 7. 前端兜底的容忍时间

前端已在 `ClassSummary.vue` 显示 `el-alert` 提示"summary 接口暂不可用，以下数据由学生名册反推"。修好之后**无需修改前端**，只要接口返回 200 且包含 `student_count / class_name` 字段即自动恢复。
