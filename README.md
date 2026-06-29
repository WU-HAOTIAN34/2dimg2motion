<div align="center">

# 2dimg2motion.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-green)](https://agentskills.io)
[![Multi-Runtime](https://img.shields.io/badge/Runtime-ClaudeCode%20·%20Codex-blueviolet)]()

<br>

**2dimg2motion.skill：将一张静态 2D 角色、怪物、载具、武器或道具图片，通过 AI 图像生成转换为风格一致、透明背景、可用于游戏的动画序列帧。**

</div>

---

## 示例

<table>
  <tr>
    <th>示例</th>
    <th>基准图</th>
    <th>动画预览</th>
  </tr>
  <tr>
    <td>双拳重砸</td>
    <td><img src="examples/s1.png" width="160" alt="岩石魔像输入图"></td>
    <td><img src="examples/s1res.gif" width="240" alt="重砸地面动画预览"></td>
  </tr>
  <tr>
    <td colspan="3"><img src="examples/s1res.png" width="1200" alt="重砸地面 14 帧精灵表"></td>
  </tr>
  <tr>
    <td>甲壳生物行走</td>
    <td><img src="examples/s2.png" width="160" alt="甲壳生物输入图"></td>
    <td><img src="examples/s2res.gif" width="240" alt="甲壳生物行走动画预览"></td>
  </tr>
  <tr>
    <td colspan="3"><img src="examples/s2res.png" width="1200" alt="甲壳生物行走 14 帧精灵表"></td>
  </tr>
</table>

## 这是什么

这是一个 **AI 驱动的 2D 游戏动画帧生成管线**。输入一张角色设定图，输出一套风格一致、透明背景、可直接用于游戏引擎的动画序列帧。

它不是“给单图加动效”的补间工具，而是一套完整的**整角色关键姿势重绘流程**：先锁定角色身份特征，再生成共享关键姿势，最后以原图和关键姿势表为参考生成补间帧，尽量保持透视、遮挡、挤压拉伸与整体轮廓的连续性。

## 适合谁用

| 角色 | 场景 |
|---|---|
| **独立游戏开发者** | 没有专属像素画师或动画师时，快速产出可用动作帧用于原型或正式素材。 |
| **原型阶段团队** | 在美术资源到位前，用 AI 生成的序列帧验证玩法、节奏和手感。 |
| **AI 辅助美术管线探索者** | 研究如何将 AI 图像生成纳入游戏美术生产流程。 |

如果已有成熟美术团队且对风格一致性要求极高，这个工具更适合作为**快速预演或占位素材**，而不是直接替代最终手绘交付。

## 产出内容

一次完整的动画生成会产出以下文件：

```text
output/
|-- keyframe/            # 4 个关键帧，固定索引 02/05/08/11
|-- fullframe/           # 14 个透明 RGBA 序列帧，固定索引 00-13
|-- spritesheet.png      # 精灵表，打包所有帧，适配 2D 引擎
|-- contact-sheet.png    # 接触表，用于检查身份漂移和动作连续性
|-- preview.gif          # 14 帧播放预览，固定纯白 #FFFFFF 背景
`-- manifest.json        # 元数据清单，记录画布、帧顺序、基线和拓扑锁
```

每一帧都应满足：**RGBA 透明背景、统一画布尺寸、稳定脚底基线、连续命名**。产物可直接导入 Godot 的 `AnimatedSprite2D` 或 Unity 的 `Sprite Animation` 使用。

## 核心思路

先建立身份锁（identity lock），批准共享关键姿势表，再以原始图和关键姿势表为参考生成所有补间帧。**不要独立生成每一帧**，否则很容易出现身份漂移、比例跳变和动作不连续。

## 支持的动作类型

| 动作 | 节拍 |
|---|---|
| 待机 | 下沉 -> 抬起 -> 下沉 |
| 行走 | 触地 -> 下沉 -> 迈步/通过 -> 上升 -> 对侧触地 |
| 攻击 | 防御 -> 预备 -> 加速 -> 命中 -> 命中保持 -> 恢复 |
| 受击 | 命中 -> 后仰 -> 恢复 |
| 死亡 | 失衡 -> 倒塌 -> 冲击 -> 静止 |

## 工作流程

1. **身份锁**：从原图记录不可变特征，包括脸、表情、比例、配色、轮廓、服装、武器、标记和肢体拓扑。
2. **动作节拍设计**：选择动作类型，拆解关键姿势，固定 14 帧中的关键帧索引。
3. **关键姿势表**：在一张等分网格中重绘完整角色，得到 02/05/08/11 四个关键帧。
4. **补间帧生成**：以原图和关键姿势表为双重参考，按 `00 -> 02 -> 05 -> 08 -> 11 -> 13` 顺序生成补间。
5. **去背景与归一化**：移除色键背景，统一缩放、居中和脚底基线。
6. **漂移修正**：检查相邻帧的身份、轮廓、比例、肢体连接和动作轨迹。
7. **验证交付**：运行验证脚本，并检查接触表和播放预览。

## 使用方式

这是一个 Codex/Claude Code 风格的自定义技能。使用时提供一张基准角色图片，并描述需要的动作类型即可。

示例：

```text
用这张魔像图做一个重砸地面攻击动画。
用 sample/s1.png 生成 walk 动作。
```

## 验证

```bash
python scripts/validate_14frame_pattern.py --baseline source.png --keyframes-dir output/keyframe --fullframes-dir output/fullframe --preview output/preview.gif --prefix hero-attack
```

验证内容包括：14 帧连续命名、RGBA 模式、统一画布、透明四角、首尾基准帧一致、关键帧与完整帧像素一致，以及 GIF 使用纯白背景。

## 依赖

- Python 3.x + [Pillow](https://python-pillow.org/)
- OpenAI 图像生成接口，通过 `agents/openai.yaml` 配置

## 许可

MIT © 2026 Haotian Wu
