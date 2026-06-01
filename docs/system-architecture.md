# System Architecture / 系统架构总览

This page explains how the published public core fits into the larger Hephaestus system. The
repository itself is intentionally narrow, but the architecture is broader: it combines
task-level reasoning, strategy assets, semantic action primitives, robot/perception tools,
runtime memory, and evidence-driven strategy improvement.

本页解释的是：已经公开的核心源码，如何放进更完整的 Hephaestus 系统里理解。公开仓库本身是有意收窄的，但整体架构更宽，它同时包含任务级推理、策略资产、语义动作原子、机器人/感知工具、运行期记忆，以及基于证据的策略改进闭环。

## End-to-end architecture / 端到端总览

![Overall Hephaestus architecture](figures/overall-hephaestus-architecture.png)

The overall design starts with a user request and flows downward through explicit ownership
layers:

1. the `task` layer interprets the request and chooses a bounded strategy
2. the `skill` layer provides reusable policy assets
3. the `atom` layer expands strategies into semantic action primitives
4. the `tool` layer binds those actions to robot, perception, IK, safety, and simulation

整体设计从用户请求出发，沿着明确的 owner 层级向下流动：

1. `task` 层理解任务并选择受约束的策略
2. `skill` 层提供可复用的策略资产
3. `atom` 层把策略展开成语义动作原子
4. `tool` 层把这些动作绑定到机器人、感知、IK、安全和仿真接口

The critical architectural choice is that execution authority stays in the runtime safety loop.
Hephaestus is designed so planning can become smarter over time without collapsing the boundary
between "deciding what to try" and "being allowed to execute it on a robot or simulator."

这个系统最关键的架构选择是：执行权限始终留在运行时安全闭环里。Hephaestus 的目标是让规划越来越聪明，但不能把“决定尝试什么”和“是否允许真正执行”这两件事混为一体。

## Runtime-owned execution loop / 运行时拥有执行权的闭环

The architecture image above includes the execution loop on the right-hand side. That loop is
what prevents the system from becoming an unsafe direct-control stack:

- tool name and payload are validated before execution
- safety checks run before commands are allowed through
- execution produces structured results rather than ad hoc side effects
- success is evaluated explicitly
- retries and strategy updates are bounded rather than unconstrained

上面的架构图右侧就是执行闭环，这也是系统不会退化成“不安全直接控制栈”的关键：

- 执行前会先校验 tool 名称和 payload
- 命令真正通过前要做安全检查
- 执行结果是结构化返回，而不是随意副作用
- 成功与否会被显式评估
- 重试与策略更新都是有边界的，而不是无限放开

This matters because a robotic-agent architecture needs more than planning quality. It also needs
repeatability, diagnostics, and a clear authority boundary when a plan meets the physical world.

这很重要，因为机器人智能体架构不只需要“会规划”，还必须在计划接触物理世界时，保留可复现、可诊断、可追责的权限边界。

## Runtime memory sidecar / 运行期记忆侧车

![Runtime memory sidecar](figures/runtime-memory-sidecar.png)

Hephaestus separates runtime memory from project documentation. Runtime memory is built from
execution evidence:

- episode traces capture what actually happened
- structured records distill stable facts from those traces
- query pages compress those facts into retrieval context for later planning and diagnosis

Hephaestus 把运行期记忆和项目文档严格分开。运行期记忆来自执行证据：

- episode trace 记录真实发生了什么
- structured record 从 trace 中抽取稳定事实
- query page 再把这些事实压缩成后续规划和诊断可检索的上下文

That design keeps memory useful for robotic decision-making instead of turning it into an
unverifiable chat summary store. The public repo does not publish private memory contents, but it
does expose the architectural contract that memory should be evidence-backed, structured, and
queryable.

这种设计让记忆真正服务于机器人决策，而不是退化成无法验证的聊天摘要仓库。公开仓库不会发布私有记忆内容，但会公开这个架构契约：记忆必须是有证据支撑、结构化且可检索的。

## Autonomous evolution loop / 自主演化闭环

![Autonomous evolution loop](figures/autonomous-evolution-loop.png)

Hephaestus is built to improve strategy assets from evidence. The important point is how that
improvement happens:

- task execution generates success and failure evidence
- runtime evaluation decides whether a run succeeded
- failures can trigger diagnosis and bounded strategy-update proposals
- proposed updates pass through validation before becoming reusable assets

Hephaestus 被设计成可以基于证据改进策略资产，但关键在于“如何改进”：

- 任务执行会产生成败证据
- 运行时评估器判断这次执行是否成功
- 失败可以触发诊断和受约束的策略更新提案
- 提案必须先通过验证，才能成为新的可复用资产

This is why the project uses a layered design instead of direct executor mutation. Strategy can
evolve. Safety-critical execution boundaries remain guarded.

这也是为什么项目坚持分层设计，而不是直接修改执行器。策略可以演化，但安全关键的执行边界必须继续被保护。

## What the public repository exposes directly / 公开仓库直接暴露什么

The public repository keeps the stable, inspectable core visible:

- `task` contracts and proof cases
- `skill` policy surfaces
- `atom` semantic primitives
- `tool` capability interfaces
- CLI commands for bundle inspection

公开仓库保留了稳定、可检查的核心部分：

- `task` 层契约和 proof case
- `skill` 层策略表面
- `atom` 层语义动作原子
- `tool` 层能力接口
- 用于检查公开包内容的 CLI 命令

Those pieces are enough for an outside reader to understand what the system is trying to build
and where the real module boundaries are, without exporting private runtime internals, traces, or
working-process artifacts.

这些内容已经足够让外部读者理解：系统在试图构建什么、真实模块边界在哪里，同时又不会把私有运行时细节、轨迹数据或工作过程产物直接暴露出来。

## Public inspection commands / 公开检查命令

- `list-core-files`
- `list-proof-cases`
- `show-scene-carrier`
- `show-grasp-policy`
