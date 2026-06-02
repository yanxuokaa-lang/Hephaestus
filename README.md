<div align="center">

# 🔨 Hephaestus

**Simulation-first robotic-agent architecture for embodied manipulation**<br>
**面向具身操作的仿真优先机器人智能体架构**

<p>
  <a href="#english">English</a> |
  <a href="#中文">中文</a>
</p>

<p>
  <a href="docs/architecture.md">Architecture</a> ·
  <a href="docs/system-architecture.md">System Design</a> ·
  <a href="docs/phase1c-closure.md">Phase 1C Closure</a>
</p>

</div>

---

## English

### Overview

Hephaestus is a robotic-agent project that turns natural-language manipulation requests into
safe, structured, and inspectable robot behavior. This public repository is an open-core
showcase snapshot: it publishes the stable core source subset and public-facing architecture
story, while keeping private development process, planning records, and internal workflow state
out of the public tree.

### Architecture

![Overall Hephaestus architecture](docs/figures/overall-hephaestus-architecture.png)

The project is organized around four explicit owner layers:

- `task`: interprets the request and selects a bounded strategy
- `skill`: stores reusable manipulation policies
- `atom`: provides semantic action primitives such as `detect`, `approach`, `grasp`, and `move_to`
- `tool`: owns typed interfaces for robot control, perception, IK, safety checks, and simulation

The design keeps planning, execution, memory, and evolution boundaries explicit so the system
can improve over time without giving up runtime safety ownership.

### Highlights

#### Runtime memory sidecar

![Runtime memory sidecar](docs/figures/runtime-memory-sidecar.png)

Hephaestus treats memory as execution-backed evidence rather than free-form notes. Runtime traces
become structured records, then compact retrieval context for later planning, retry, and
diagnosis.

#### Autonomous strategy improvement

![Autonomous evolution loop](docs/figures/autonomous-evolution-loop.png)

The project is designed to improve strategy assets from evidence while keeping execution
authority inside runtime safety gates. Strategy can evolve; safety-critical execution boundaries
remain guarded.

### Public Snapshot Scope

| Module | Purpose | Public files |
| --- | --- | --- |
| `tool` | typed robot, perception, safety, simulation, and scene-truth interfaces | `hephaestus/tool/*` |
| `atom` | reusable semantic action primitives | `hephaestus/atom/*` |
| `skill` | stable public grasp/place policy surfaces | `hephaestus/skill/*` |
| `task` | task registry seams and proof-case contracts | `hephaestus/task/*` |
| `cli` | inspection commands for the public bundle | `hephaestus/cli/main.py` |

### Included

- stable core source files for `tool`, `atom`, `skill`, and `task`
- a lightweight CLI for inspecting the public bundle
- architecture documents and diagrams that explain how the published code fits into the full project

### Not Included

- internal working notes or private review records
- raw capture artifacts, recordings, or demo assets
- private runtime orchestration internals
- private memory stores and project-only knowledge bases

### Quick Start

#### Install

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

#### Inspect the public bundle

```bash
python -m hephaestus.cli.main list-core-files --json
python -m hephaestus.cli.main list-proof-cases --json
python -m hephaestus.cli.main show-scene-carrier tabletop_organization_v1 --json
python -m hephaestus.cli.main show-grasp-policy --json
```

#### Validate

```bash
git diff --check
python -m pytest -q
```

### Documentation

- [docs/architecture.md](docs/architecture.md): layer-by-layer owner map and public module boundaries
- [docs/system-architecture.md](docs/system-architecture.md): runtime flow, memory sidecar, and evolution loop
- [docs/phase1c-closure.md](docs/phase1c-closure.md): public closure note for this snapshot

---

## 中文

### 项目简介

Hephaestus 是一个面向机械臂操作的机器人智能体项目，目标是把自然语言操作请求转成
安全、结构化、可检查的机器人行为。这个公开仓库是 open-core 方式下的展示型快照：
它公开稳定核心源码子集和面向外部读者的架构说明，同时把私有开发过程、计划记录和
内部 workflow 状态留在私有仓。

### 系统架构

![Overall Hephaestus architecture](docs/figures/overall-hephaestus-architecture.png)

项目核心采用四层 owner 架构：

- `task`：理解任务并选择受约束的策略
- `skill`：保存可复用的操作策略
- `atom`：提供 `detect`、`approach`、`grasp`、`move_to` 等语义动作原子
- `tool`：拥有机器人控制、感知、IK、安全检查与仿真接口

这种设计把规划、执行、记忆和演化边界明确拆开，使系统可以持续改进，同时不放弃
运行时安全所有权。

### 核心亮点

#### 运行期记忆侧车

![Runtime memory sidecar](docs/figures/runtime-memory-sidecar.png)

Hephaestus 把记忆定义为执行证据，而不是自由笔记。运行轨迹会沉淀成结构化记录，
再压缩成后续规划、重试和诊断可检索的上下文。

#### 自主演化式策略改进

![Autonomous evolution loop](docs/figures/autonomous-evolution-loop.png)

项目被设计成可以依据证据改进策略资产，但执行权限始终留在运行时安全门控内。
策略可以进化，安全关键的执行边界不会被直接放开。

### 公开仓切片范围

| 模块 | 作用 | 公开文件 |
| --- | --- | --- |
| `tool` | 类型化机器人、感知、安全、仿真与场景真相接口 | `hephaestus/tool/*` |
| `atom` | 可复用语义动作原子 | `hephaestus/atom/*` |
| `skill` | 稳定公开的抓取/放置策略表面 | `hephaestus/skill/*` |
| `task` | 任务注册接缝和 proof-case 契约 | `hephaestus/task/*` |
| `cli` | 用于检查公开包内容的命令入口 | `hephaestus/cli/main.py` |

### 已公开内容

- `tool`、`atom`、`skill`、`task` 四层的稳定核心源码
- 用于检查公开包内容的轻量 CLI
- 用来解释公开代码如何放进完整项目中的架构文档与配图

### 当前不公开内容

- 内部工作笔记和私有审查记录
- 原始采集数据、录屏或演示素材
- 私有运行时编排细节
- 私有记忆存储与项目内部知识库

### 快速开始

#### 安装

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

#### 查看公开包内容

```bash
python -m hephaestus.cli.main list-core-files --json
python -m hephaestus.cli.main list-proof-cases --json
python -m hephaestus.cli.main show-scene-carrier tabletop_organization_v1 --json
python -m hephaestus.cli.main show-grasp-policy --json
```

#### 验证

```bash
git diff --check
python -m pytest -q
```

### 文档入口

- [docs/architecture.md](docs/architecture.md)：分层 owner 关系和公开模块边界
- [docs/system-architecture.md](docs/system-architecture.md)：运行流转、记忆侧车与演化闭环
- [docs/phase1c-closure.md](docs/phase1c-closure.md)：本次公开快照的阶段闭环说明
