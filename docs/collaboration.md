# 协作规范

> 状态：生效 ｜ 负责人：A ｜ 日期：2026-11-06
> 适用：`SeatVerse` 仓库的全部成员与全部改动
> 说明：本文固定分支模型、提交信息与锁文件规则；与仓库现有 `master` 分支配套使用

---

## 1. 分支模型

### 1.1 长期分支

| 分支 | 用途 | 规则 |
|---|---|---|
| `master` | 可演示、可联调的主线 | **受保护**，禁止直接 push；只接受 Pull Request 合并 |
| `feat/<模块>-<简述>` | 新功能 | 从最新 `master` 切出，例：`feat/bookings-list` |
| `fix/<简述>` | 缺陷修复 | 从最新 `master` 切出，例：`fix/login-401-loop` |

### 1.2 命名规则

- 分支名一律小写，单词之间用连字符 `-`，不使用中文、空格、下划线。
- `feat/` 后的第一段写模块名，使用与目录或契约一致的英文单词：
  - `authentication`：登录、注册、登录态
  - `events`：活动列表、详情、主办方活动
  - `seatmap`：3D 选座与预约提交
  - `bookings`：我的预约与取消
  - `tickets`：电子票、二维码、核验
  - `infra`：工程配置、检查入口、部署
- 示例：
  - `feat/bookings-list`
  - `feat/tickets-qr`
  - `feat/events-search`
  - `fix/cancel-409-message`

### 1.3 生命周期

1. 开工前先同步 `master`：`git switch master && git pull`。
2. 从 `master` 切出功能或修复分支。
3. 开发完成后推送分支，向 `master` 发起 Pull Request。
4. PR 合并后删除远程分支；本地分支可保留，但不得继续在已合并分支上开发新功能。
5. 不在 `master` 上直接提交；紧急修复同样走 `fix/` 分支与 PR。

---

## 2. 提交信息

### 2.1 格式

```text
type(scope): 描述
```

- `type` 只能取以下六个值：
  - `feat`：新增功能
  - `fix`：修复缺陷
  - `docs`：文档
  - `chore`：工程配置、依赖、构建
  - `refactor`：不改变行为的重构
  - `test`：测试
- `scope` 写模块名，与分支命名中的模块一致；跨模块改动可写 `repo` 或 `docs`。
- 描述使用中文，简洁说明“做了什么”，不超过 50 字，句末不加句号。
- 一个提交只做一件事；不要把格式化、依赖升级和业务改动混在同一次提交。

### 2.2 示例

```text
feat(bookings): 增加我的预约列表与状态分组
fix(authentication): 登录失败时不再清除本地令牌
docs(contracts): 冻结预约取消与电子票样本
chore(infra): 修复前端 lint 依赖与检查命令
test(bookings): 补充重复取消的 409 用例
refactor(seatmap): 拆分座位状态与本地选中逻辑
```

### 2.3 禁止

- 禁止 `update`、`fix bug`、`修改`、`提交` 这类无信息量的提交信息。
- 禁止把多个不相关模块塞进同一个提交。
- 禁止在提交信息中写入令牌、密码、真实用户邮箱等敏感信息。

---

## 3. 锁文件规则

### 3.1 硬规则

**同一次 Pull Request 只允许修改一次锁文件；新增或升级依赖必须在 PR 说明中写明理由。**

锁文件指：

- `frontend/package-lock.json`
- `backend/uv.lock`

### 3.2 新增依赖的流程

1. 在 PR 说明中写清：新增哪个依赖、为什么必须新增、影响哪个模块。
2. 只在功能分支上执行一次安装命令：
   - 前端：`npm install`
   - 后端：`uv sync`
3. 同一次 PR 内不要反复 `npm install` / `uv sync` 制造多次锁文件变更。
4. 合并前确认锁文件只包含本次新增依赖及其传递依赖，不夹带无关升级。

### 3.3 冲突处理

锁文件冲突时**不要手工编辑**。由最后合并的人在最新 `master` 上重新生成后单独提交：

```bash
# 前端
cd frontend
git checkout --theirs package-lock.json
npm install
git add package-lock.json

# 后端
cd backend
git checkout --theirs uv.lock
uv sync
git add uv.lock
```

- 重新生成后必须再跑一次检查命令。
- 锁文件重生成单独成一个 `chore(infra): 重生成锁文件` 提交，不混入业务代码。

### 3.4 禁止

- 禁止手改 `package-lock.json` / `uv.lock` 的版本号或完整性字段。
- 禁止在业务 PR 中夹带无关依赖升级。
- 禁止删除锁文件后重新生成整份文件来“解决冲突”。

---

## 4. Pull Request 要求

### 4.1 发起前

- [ ] 分支基于最新 `master`
- [ ] 本地检查通过（`bash scripts/check.sh`；脚本未落地前按根 README「检查入口」执行等价命令）
- [ ] 提交信息符合第 2 节
- [ ] 未手改 `frontend/src/lib/components/ui/`
- [ ] 锁文件变更已在说明中标注理由

### 4.2 PR 说明必须包含

1. 变更目的与影响范围。
2. 关联任务或 Issue 编号（没有则写“无”）。
3. 自检结果：执行了哪些命令、结果如何。
4. 界面改动附截图或录屏；接口改动附请求与响应样例。
5. 锁文件若有变更，写明新增依赖与理由。

### 4.3 评审与合并

- `master` 至少要求“合并前必须有 Pull Request”，当前不强制要求 approval。
- 评审人优先看：契约是否一致、错误码是否正确、是否手改生成件、锁文件是否干净。
- 合并后删除功能分支；合并方式由仓库管理员统一，不在本文硬编码。

---

## 5. 分支保护配置（仓库管理员）

在 GitHub 仓库页面完成：

1. 进入 **Settings → Branches → Add branch protection rule**。
2. 目标分支填 `master`。
3. 勾选 **Require a pull request before merging**。
4. 当前没有 CI，暂不要求 approval 与 status checks。
5. 保存后确认 `master` 不能直接 push。

> 若后续接入 CI，再追加 “Require status checks to pass before merging”。

---

## 6. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-06 | 首版生效：分支模型、提交信息、锁文件规则与 PR 要求 | A |
