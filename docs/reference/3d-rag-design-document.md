> ## Borrowing Guide — read this first
>
> **Status:** External reference (recovered from gm-lite / NEW-GM / GM-SkillForge).
> Conceptual menu, **not an implementation blueprint**.
>
> Opportunity OS absorbs 3D-RAG at the *idea* level only. The kernel below is
> already largely realized by the `evidence` layer (SHA-256, `captured_time`,
> immutable writes) and the deterministic candidate state machine.
>
> **Borrow (light, resonates with evidence layer):**
> - `at_time` exact anchoring; **forbid drift values** (now / today / recent / latest)
> - Replayability: `query + at_time + commit_sha = deterministic result`
> - Tombstone + fail-closed: invalidate by appending a negation, never by deleting
> - Irreversible state transitions; append-only evolution log
>
> **Do NOT implement now (too heavy / gm-lite-specific):**
> - Layers 1/3/4: embeddings, vector cosine, HYDE, ALG3D weighted fusion
> - Layer 5: local 7B three-role workers (parser/planner/judge)
> - Layer 7: data flywheel (audit → experience → regression)
>
> The "semantic axis" (vector retrieval) is the one we lack — and don't need yet.
> Same anti-bloat rule as `CLAUDE.md` §2 and §3.6 applies here.



# 三维 RAG（3D RAG）完整设计文档

> 来源：D:\NEW-GM + D:\GM-SkillForge
> 设计时间：2025-10 ~ 2026-02
> 整理日期：2026-05-08
> 说明：从 new-gm 和 SkillForge 代码库中恢复的完整 RAG 设计

---

## 一、核心概念

三维 RAG 不是一个检索优化技巧，而是一套**带时间锚定、可重播、fail-closed 的知识治理架构**。

与普通 RAG 的区别：

| 维度 | 普通 RAG | 三维 RAG |
|------|---------|---------|
| 检索方式 | 纯语义相似度 | 时间轴 × 语义轴 × 证据质量，三轴交叉定位 |
| 时间处理 | 无 / 隐式 | at-time 精确锚定，禁止漂移值 |
| 结果可信度 | 相信 top-K | tombstone 强制拦截，已下架知识无法绕过 |
| 可重播性 | 无 | query + at_time + commit_sha = 确定性结果 |
| 失败策略 | 返回最佳猜测 | fail-closed，任何约束违反直接拒绝 |

---

## 二、七层架构

```
┌─────────────────────────────────────────┐
│  Layer 7: 数据飞轮                       │
│  审计 → 经验提取 → 版本化沉淀 → 回归评估   │
├─────────────────────────────────────────┤
│  Layer 6: 治理合约                       │
│  at-time 可重播 / tombstone / fail-closed│
├─────────────────────────────────────────┤
│  Layer 5: 意图与质量                     │
│  本地 7B：意图路由 + 质量评审              │
├─────────────────────────────────────────┤
│  Layer 4: 证据融合引擎                    │
│  ALG3D_V1：时间 + 空间 + 语义 + HYDE     │
├─────────────────────────────────────────┤
│  Layer 3: 检索服务                       │
│  metadata 过滤 → 语义余弦 → 证据评分      │
├─────────────────────────────────────────┤
│  Layer 2: 存储                          │
│  Vault SQLite：NOTES / SYSTEM / WORKFLOW │
├─────────────────────────────────────────┤
│  Layer 1: 嵌入                          │
│  双模式：模拟 hash / 生产 Ollama 7B       │
└─────────────────────────────────────────┘
```

---

## 三、交叉定位机制

### 3.1 三轴定义

| 轴 | 维度 | 说明 |
|---|------|------|
| X 轴 | Outer（证据层） | EvidencePackV1，只读，advisory_only=true |
| Y 轴 | Inner（决策层） | DecisionPackV1，系统内部决策 |
| Z 轴 | Evolution（演化层） | SedimentationPackV1，知识版本化沉淀 |

### 3.2 交叉定位流程

```
1. 查询锚定 at_time（时间轴）
   - 必须是精确 ISO-8601 时间戳
   - 禁止漂移值：latest, now, current, today, yesterday, tomorrow, recent, newest
   - 结合 repo_url + commit_sha 创建确定性快照

2. 语义嵌入检索（语义轴）
   - 查询向量与时间过滤后的语料库做余弦相似度
   - 支持 HYDE：先生成假设答案，再用假设答案检索

3. 交叉定位
   - 时间窗口（X轴）× 语义相关性（Y轴）= 具体证据点
   - Z轴验证：即使时间和语义都匹配，证据质量低（状态 rejected）也会被降级

4. Tombstone 强制拦截
   - tombstone=true 的知识无法绕过检索链
   - 即使语义完全匹配也拒绝返回

5. 可重播
   - 同 query + at_time + commit_sha = 相同结果
   - 每次查询返回 ReplayPointer（at_time, repo_url, commit_sha, run_id）
```

---

## 四、ALG3D_V1 融合策略

### 4.1 四个子分数

| 子分数 | 计算方式 | 说明 |
|--------|---------|------|
| time_score | 指数衰减 + 24h 近期增益 | 越新越好，但有衰减曲线 |
| space_score | Jaccard 相似度去重聚类 | 相似证据聚为一簇，选最佳代表 |
| semantic_score | 嵌入向量余弦相似度 | 语义相关性 |
| hyde_score | 假设答案与证据的词重叠度 | 先让模型生成假设答案，再用假设检索 |

### 4.2 融合公式

```python
total = time_score * time_weight \
      + space_score * cluster_weight \
      + semantic_score * 0.3 \
      + hyde_score * hyde_weight
```

### 4.3 时间带分类

| 时间带 | 定义 | 用途 |
|--------|------|------|
| FUTURE | HYDE 生成的假设证据 | 预测性检索 |
| PRESENT | 24 小时内的内容 | 最新知识优先 |
| PAST | 其他所有内容 | 历史知识 |

### 4.4 检索服务评分

单条结果的三步评分：

```python
final_score = semantic_score * 0.6    # 语义相似度
            + evidence_score * 0.3    # 证据质量
            + (0.1 if metadata_hit else 0)  # metadata 匹配
```

---

## 五、7B 三工种集成

| 工种 | Profile | 职责 |
|------|---------|------|
| 结构工头 | local_7b_parser | 意图路由：docs_query / system_analysis / flywheel_query / chat |
| 草稿规划师 | local_7b_planner | 步骤分解 + Inner 回答生成 |
| 值班法官 | local_7b_judge | 质量评审：PASS / FAIL，评估相关性、完整性、准确性、时效性 |

---

## 六、Z 轴状态机

知识的生命周期管理：

```
DRAFT → CANDIDATE → VERIFIED → ACTIVE → DEPRECATED → EXPIRED
                                              ↓
                                        INVALIDATED
                                              ↓
                                         REPLACED
```

| 状态 | 说明 |
|------|------|
| DRAFT | 草稿，不可检索 |
| CANDIDATE | 候选，待验证 |
| VERIFIED | 已验证，待激活 |
| ACTIVE | 活跃，可检索 |
| DEPRECATED | 已弃用，tombstone 生效 |
| EXPIRED | 自然过期 |
| INVALIDATED | 被判定无效 |
| REPLACED | 被新版本替换 |

**关键约束**：所有状态转换不可逆，evolution.json 只增不改。

---

## 七、Fail-Closed 规则

### 7.1 AtTimeReference 规则（FC-ATR）

| 规则 | 说明 |
|------|------|
| FC-ATR-1 | at_time 缺失 → REJECTED |
| FC-ATR-2 | at_time 不是 ISO-8601 → REJECTED |
| FC-ATR-3 | at_time 是漂移值（now/latest/current...）→ REJECTED |
| FC-ATR-4 | tombstone=true 但仍被检索到 → REJECTED |

### 7.2 ExperienceEntry 规则（FC-EXP）

| 规则 | 说明 |
|------|------|
| FC-EXP-1 | issue_key 缺失 → REJECTED |
| FC-EXP-2 | evidence_ref 缺失 → REJECTED |
| FC-EXP-3 | content_hash 不匹配 → REJECTED |

### 7.3 Evolution 规则（FC-EVO）

| 规则 | 说明 |
|------|------|
| FC-EVO-1 | evolution.json 不可覆写，只增不改 |
| FC-EVO-2 | 重复条目去重，不报错但跳过 |

### 7.4 闭环规则（FC-LOOP）

| 规则 | 说明 |
|------|------|
| FC-LOOP-1 | 无 permit 不可 publish |
| FC-LOOP-2 | n8n 不可持有治理逻辑 |
| FC-LOOP-3 | 确定性输入（repo_url + commit_sha + at_time）不可缺失 |

---

## 八、治理边界

| 类别 | 范围 |
|------|------|
| 内核（不可替换） | at-time 锚定、tombstone 强制、system-of-record、experience capture、permit |
| 可替换技能 | 提取、索引、检索算法 |
| 编排器 | 路由、重试 |
| 禁止操作 | n8n 持有治理逻辑、绕过 permit、绕过 tombstone、覆写 evolution.json |

---

## 九、API 端点

### RAG 端点（7 个）

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | /rag/index | 索引 Vault 条目 |
| POST | /rag/search | 通用搜索 |
| POST | /rag/search/docs | 文档搜索 |
| POST | /rag/search/system | 系统分析搜索 |
| POST | /rag/search/flywheel | 数据飞轮搜索 |
| POST | /rag/search/unified | 统一搜索 |
| POST | /rag/search/with-quality | 带质量评审的搜索 |
| POST | /rag/evidence/fusion | 证据融合 |

所有响应标记 `advisory_only=true`，只读不执行。

### Inner 端点（4 个）

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | /inner/ask | 系统状态问答 |
| GET | /inner/status | 系统状态 |
| GET | /inner/events/summary | 事件摘要 |
| GET | /inner/health/check | 健康检查 |

---

## 十、关键技术文件索引

### NEW-GM

| 文件 | 用途 |
|------|------|
| src/rag/evidence_fusion.py (762 行) | 证据融合引擎，ALG3D_V1 策略 |
| src/services/rag/rag_service.py (266 行) | 3D RAG v0.1 SSOT 服务 |
| src/services/vector_embedding.py (205 行) | 向量嵌入服务，双模式 |
| src/services/query/query_intent_parser.py | 查询意图解析，本地 7B |
| src/services/rag/quality_evaluator.py | RAG 质量评估，本地 7B |
| src/services/inner/inner_assistant.py | 内部助手 |
| src/api/routes/rag.py | RAG API 端点 |
| src/api/routes/inner.py | Inner API 端点 |

### SkillForge

| 文件 | 用途 |
|------|------|
| skillforge-spec-pack/skillforge/src/contracts/rag_3d.yaml (328 行) | 3D RAG 治理合约 |
| skillforge/src/adapters/rag_adapter.py (334 行) | RAG 适配器接口 |
| skillforge/src/adapters/external_skill_rag_adapter.py | 外部技能 RAG 适配器 |

### 设计文档

| 文件 | 内容 |
|------|------|
| docs/2026-02-17/三维RAG与数据飞轮约束_v1.md | 约束文档 |
| docs/architecture/waves/WAVE12_OPERATIONAL_3D_RAG_V1.md | WAVE12 波次设计 |
| docs/2026-01-23/三维RAG的集成应用/ | 综合集成完成报告 |
| archives/deprecated/genesismind_new-20251123/docs/project_plan/2025-10-08_rag_double_helix_plan.md | 最早的 RAG 计划 |

---

## 十一、与 GM-Lite 的关系

三维 RAG 和 GM-Lite 不是同一个层面的东西，但共享同一个设计哲学：

| 设计哲学 | 三维 RAG | GM-Lite |
|---------|---------|---------|
| Fail-closed | AT_TIME_FORBIDDEN_VALUES 拒绝漂移 | EXCLUDED_PACKET_TYPES 拒绝误 claim |
| 时间维度 | at-time 锚定 + tombstone | staleness guard (096) + loop guard (092) |
| 可审计性 | ReplayPointer 可重播 | triad 三份报告可追溯 |
| 不可逆约束 | evolution.json 只增不改 | 协议对象 append-only |
| 治理边界 | 内核不可替换 | 架构 gate + CLAUDE.md 约束 |

**三维 RAG 解决的是"agent 怎么获取正确知识"，GM-Lite 解决的是"agent 之间怎么协作才不会出事"。两者互补，不冲突。**

---

## 十二、当前状态

| 项目 | 状态 |
|------|------|
| 核心概念 | ✅ 完整定义 |
| 治理合约 | ✅ rag_3d.yaml 328 行 |
| 证据融合引擎 | ✅ evidence_fusion.py 762 行，ALG3D_V1 策略 |
| 检索服务 | ✅ rag_service.py 266 行 |
| 向量嵌入 | ✅ 双模式实现 |
| 7B 三工种 | ✅ 集成完成 |
| API 端点 | ✅ 16 个端点 |
| at-time 可重播 | ⚠️ 概念完整，工程闭环未验证 |
| tombstone 强制 | ⚠️ 规则定义，自动化执行未完成 |
| 数据飞轮闭环 | ⚠️ 流程设计完成，自动化未完成 |

> 结论：概念和代码都已实现，但工程级闭环验证（at-time 重播、tombstone 拦截、experience capture 自动化）尚未完成。
