# voxel-model（svox）

石炉气质的 **独立道具 / 食物** 体素批处理管线 MVP（第一刀）。

- 范围：道具 / 物品 / 植物等独立模型（`carrot` / `crate` / `stew` / `basket`），**不做建筑**
- 颜色：跟主题资产 / Job 参数走（胡萝卜＝橘＋草绿），不是全局暖土黄强制色板
- 导出：`.vox`（必出）＋ `.qb` ＋ `.glb`
- 形态：Python CLI（`python -m svox` / `svox`）

> **GitHub 仓库**：https://github.com/BreezedropSleezes/VoxelModelAgent

## 安装

```bash
cd voxel-model
python3 -m pip install -e .
# 或不用安装，直接：
PYTHONPATH=src python3 -m svox --help
```

依赖：Python ≥ 3.11、`numpy`、`PyYAML`。

## 一条命令跑 example

```bash
# 胡萝卜 → out/carrot-demo.vox（非空）等
PYTHONPATH=src python3 -m svox run \
  --manifest manifests/examples/carrot.yaml \
  --out out/carrot

# 木箱
PYTHONPATH=src python3 -m svox run -m manifests/examples/crate.yaml -o out/crate

# 或 CLI 参数（无 manifest）
PYTHONPATH=src python3 -m svox run --theme carrot --seed 42 --formats vox,qb,glb --out out/cli-carrot
```

安装 editable 后也可用：

```bash
svox run -m manifests/examples/carrot.yaml -o out/carrot
```

成功时 stdout 会打印 `filled=…` 与各产物路径；`out/<id>.vox` 应用 MagicaVoxel 可打开。

## 主题

| theme | 说明 |
|-------|------|
| `carrot` | 锥形根＋绿叶（食物向优先） |
| `crate` | 板条箱＋铁箍 |
| `stew` | 炖锅占位（色板参考 food 气质统计） |
| `basket` | 浆果篮占位 |

`svox themes` 可列出。建筑类 theme（`house` / `cottage` / …）在 normalize 阶段直接拒绝。

## 与参考样例对照（不在仓库内）

验收用石炉风格 food `.qb` 仅存在于 **Agent Store**，**禁止**提交进公开/私有 Git 仓：

- 路径：`/cursor/stores/self/media/refs/food/*.qb`
- 清单：`/cursor/stores/self/docs/food-ref-samples.md`
- 本仓只保留 **统计摘要**：[`docs/food-ref-stats.md`](docs/food-ref-stats.md)

对照方式：用本 CLI 生成 `stew` / `basket` 等，与参考样例并排看尺度（多约 10³）与色数气质；不要把官方二进制拷进本树。

## 流水线模块

```
normalize → generate → stylize → export → validate
```

| 模块 | MVP 状态 |
|------|----------|
| Job Spec / YAML manifest | ✅ |
| 程序化 `carrot`/`crate`/`stew`/`basket` | ✅ |
| 主题色量化 + 去孤点 | ✅ |
| `.vox` / `.qb` / `.glb` | ✅ |
| 参考图 → 像图路径（P1/P2） | ❌ 未实现（骨架可后接） |
| Web3D 预览站 | ❌ 空壳目录 `web-preview/` |
| 批跑 manifest 列表 | ❌ 目前一次一个 job |

## 方案文档

产品/技术计划见 Project store：`docs/stonehearth-voxel-pipeline.md`（不随本快照强制复制）。
