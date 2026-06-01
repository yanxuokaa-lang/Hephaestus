# 🔨 Hephaestus

**Simulation-first robotic-agent architecture for embodied manipulation**<br>
**面向具身操作的仿真优先机器人智能体架构**

> Inspired by the craftsman god, Hephaestus is built to give robot arms safe, reusable, and evolvable manipulation intelligence.<br>
> 受工匠之神的意象启发，Hephaestus 希望为机械臂构建安全、可复用、可进化的操作智能。

<div align="center">
  <p>
    <a href="docs/architecture.md">Architecture</a> ·
    <a href="docs/system-architecture.md">System Design</a> ·
    <a href="docs/phase1c-closure.md">Public Closure Note</a>
  </p>
</div>

---

## 🎯 Project Goal / 项目目标

Hephaestus aims to turn natural-language manipulation requests into safe, structured, and
inspectable robot behavior. The public repository exists to make the core architecture legible:
what the project is building, how the modules are separated, and why planning, execution,
memory, and improvement are kept behind explicit boundaries.

Hephaestus 的目标，是把自然语言操作请求转成安全、结构化、可检查的机器人行为。这个公开仓库的作用，不是暴露全部私有运行时细节，而是把核心架构讲清楚：项目在做什么、模块怎么拆、以及为什么规划、执行、记忆和演化要被明确分层。

- 🧠 Task-level reasoning with bounded execution authority.<br>
  在任务层做高层推理，但执行权限始终受边界约束。
- 🏭 Simulation-first verification for embodied manipulation.<br>
  先在仿真里验证，再把具身能力逐步落稳。
- 🧩 Reusable strategy assets instead of one-off scripts.<br>
  用可复用策略资产，而不是一次性脚本。
- 🔒 Safety-gated runtime execution and evidence-backed iteration.<br>
  通过运行时安全门控和执行证据驱动后续迭代。

## 🏗️ System Architecture / 系统架构

### Overall Architecture / 总体架构图

![Overall Hephaestus architecture](docs/figures/overall-hephaestus-architecture.png)

The image above shows the broader system context. This public repository exposes the stable,
inspectable core inside that picture rather than every private runtime service.

上图展示的是更完整的系统上下文。公开仓库发布的是其中稳定、可检查的核心部分，而不是所有私有运行时服务。

### Four-layer core / 四层核心

- 🧭 `task`: interprets the request and selects a bounded strategy.<br>
  `task`：理解任务并选择受约束的策略。
- 🧠 `skill`: stores reusable manipulation policies.<br>
  `skill`：保存可复用的操作策略。
- ⚙️ `atom`: provides semantic action primitives such as `detect`, `approach`, `grasp`, and `move_to`.<br>
  `atom`：提供 `detect`、`approach`、`grasp`、`move_to` 等语义动作原子。
- 🔌 `tool`: owns typed interfaces for robot control, perception, IK, safety checks, and simulation.<br>
  `tool`：拥有机器人控制、感知、IK、安全检查与仿真接口。

### Runtime memory sidecar / 运行期记忆侧车

![Runtime memory sidecar](docs/figures/runtime-memory-sidecar.png)

Hephaestus treats memory as execution-backed evidence rather than free-form notes. Runtime traces
become structured records, then compact retrieval context for later planning, retry, and
diagnosis.

Hephaestus 把记忆定义为执行证据，而不是自由笔记。运行轨迹会沉淀成结构化记录，再压缩成后续规划、重试和诊断可检索的上下文。

### Autonomous strategy improvement / 自主演化式策略改进

![Autonomous evolution loop](docs/figures/autonomous-evolution-loop.png)

The project is designed to improve strategy assets from evidence while keeping execution
authority inside runtime safety gates. Strategy can evolve; safety-critical execution boundaries
remain guarded.

项目被设计成可以依据证据改进策略资产，但执行权限始终留在运行时安全门控内。策略可以进化，安全关键的执行边界不会被直接放开。

## 📦 Public Snapshot / 公开仓库切片

| Module | Purpose | Public files |
| --- | --- | --- |
| `tool` | typed robot, perception, safety, simulation, and scene-truth interfaces | `hephaestus/tool/*` |
| `atom` | reusable semantic action primitives | `hephaestus/atom/*` |
| `skill` | stable public grasp/place policy surfaces | `hephaestus/skill/*` |
| `task` | task registry seams and proof-case contracts | `hephaestus/task/*` |
| `cli` | inspection commands for the public bundle | `hephaestus/cli/main.py` |

### Included / 已公开内容

- 📄 Stable core source files for `tool`, `atom`, `skill`, and `task`.<br>
  `tool`、`atom`、`skill`、`task` 四层的稳定核心源码。
- 🧪 A lightweight CLI for inspecting the public bundle.<br>
  用于检查公开包内容的轻量 CLI。
- 🗺️ Architecture docs and diagrams that explain how the published code fits into the full project.<br>
  用来解释公开代码如何放进完整项目中的架构文档与配图。

### Not included / 当前不公开内容

- 🔐 Internal working notes or private review records.<br>
  内部工作笔记和私有审查记录。
- 🎬 Raw capture artifacts, recordings, or demo assets.<br>
  原始采集数据、录屏或演示素材。
- 🧱 Private runtime orchestration internals.<br>
  私有运行时编排细节。
- 🗄️ Private memory stores and project-only knowledge bases.<br>
  私有记忆存储与项目内部知识库。

## 🚀 Quick Start / 快速开始

### Install / 安装

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

### Inspect the public bundle / 查看公开包内容

```bash
python -m hephaestus.cli.main list-core-files --json
python -m hephaestus.cli.main list-proof-cases --json
python -m hephaestus.cli.main show-scene-carrier tabletop_organization_v1 --json
python -m hephaestus.cli.main show-grasp-policy --json
```

### Validate / 验证

```bash
git diff --check
python -m pytest -q
```

## 📚 Docs / 文档入口

- [docs/architecture.md](docs/architecture.md): layer-by-layer owner map and public module boundaries<br>
  [docs/architecture.md](docs/architecture.md)：分层 owner 关系和公开模块边界
- [docs/system-architecture.md](docs/system-architecture.md): runtime flow, memory sidecar, and evolution loop<br>
  [docs/system-architecture.md](docs/system-architecture.md)：运行流转、记忆侧车与演化闭环
- [docs/phase1c-closure.md](docs/phase1c-closure.md): the public closure note for this snapshot<br>
  [docs/phase1c-closure.md](docs/phase1c-closure.md)：本次公开快照的阶段闭环说明
