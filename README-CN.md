<div align="center">
<p align="center">
  <img src="examples/e1res.gif" height="110" alt="claudecy idle" />
  <img src="examples/e2res.gif" height="110" alt="claudecy running" />
  <img src="examples/e3res.gif" height="110" alt="claudecy success" />
  <img src="examples/e4res.gif" height="110" alt="claudecy talking" />
  <img src="examples/e7res.gif" height="110" alt="howl success" />
  <img src="examples/e6res.gif" height="110" alt="howl running" />
</p>  

# 2dimg2motion.skill

<p align="center">
  <a href="README.md"><strong>English</strong></a>
  &nbsp;·&nbsp;
  <strong>简体中文</strong>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-green)](https://agentskills.io)
[![Multi-Runtime](https://img.shields.io/badge/Runtime-ClaudeCode%20·%20Codex-blueviolet)]()

<br>

<p align="center">
2dimg2motion.skill -- 不是“让图片动起来”的滤镜，而是一套可运行的游戏动画帧生成框架
</p>
<br>
<p align="center">
基于整角色关键姿势重绘、身份锁定、肢体拓扑约束的 spritesheet 交付流程，<br>
它把每一次“这个角色应该怎么动”的直觉，拆成可执行、可校验、可复用的动画生成管线。<br>
输入一张 2D 角色、怪物、武器或道具图，<br>
输出一组风格一致、透明背景、可直接导入游戏引擎的动作序列帧。
</p>


![head](examples/github-header-1.png)

</div>

---



## 这是什么

`2dimg2motion.skill` 是一个面向 Codex / Claude Code / Agent Skills 的 2D 游戏动画生成 skill。它接收一张静态角色、怪物、载具、武器或道具图，生成一组风格一致、透明背景、可打包成 spritesheet 的动作序列帧。

它不是“单图动效滤镜”。滤镜通常只是平移、旋转、缩放、扭曲局部图层；这个 skill 的核心是 **whole-character key-pose redraw**：先锁定角色身份，再让模型重绘完整关键姿势，最后生成补间帧，并用本地脚本做透明化、统一画布、打包和验证。

## 为什么需要它

AI 很容易画出“像同一个系列”的角色，却不容易稳定画出“同一个角色的连续动作”。游戏动画还会额外要求：

- 每一帧都要是透明 RGBA PNG；
- 角色比例、脚底基线和画布尺寸要稳定；
- 武器、手臂、角、尾巴、翅膀不能换边或丢失；
- 关键帧和补间帧要能连成可读动作；
- 最终结果要能被 Godot、Unity、Cocos 或自研 2D 引擎直接消费。

这个仓库把这些经验沉淀成一套可执行流程：分析基准图、建立身份锁、设计动作节拍、生成共享关键姿势表、生成补间帧、去背景、归一化、打包、校验和目检。

## 快速开始

### 1. 安装 skill

把仓库放进你的 Agent Skills 目录即可。推荐保持整个仓库结构不变，因为主 skill、子 skill、脚本、参考文件和知识库会互相引用。

Codex 示例：

```powershell
git clone https://github.com/WU-HAOTIAN34/2dimg2motion.git $env:USERPROFILE\.codex\skills\2dimg2motion
```

Claude Code 示例：

```bash
git clone https://github.com/WU-HAOTIAN34/2dimg2motion.git ~/.claude/skills/2dimg2motion
```

本地开发时也可以直接在当前仓库运行。确认依赖：

```powershell
python -m pip install pillow
```

### 2. 使用主 skill 生成动画

在 Codex 或 Claude Code 中给出一张基准图和动作描述：

```text
/2dimg2motion 使用 sample/s3.png 生成挥动手臂的攻击动画
```

或者：

```text
用这张角色图生成 walk 动作。
/2dimg2motion 用 sample/s7.png 生成挥剑劈砍动作。
/2dimg2motion 用 sample/s1.png 做一个重砸地面的攻击动画。
```

主 skill 会按完整流程执行：分析基准图、建立身份锁、设计 02/05/08/11 关键姿势、生成补间帧、去背景、归一化、打包 spritesheet，并输出 `preview.gif` 和 `manifest.json`。

### 3. 使用标准化子 skill

如果输入图太大、贴边、白底明显，或缺少攻击/行走所需的透明边距，先调用标准化子 skill：

```text
/img2mo-std s7
/img2mo-std sample\s7.png
```

它会解析图片路径，并调用脚本生成标准化基准图：

```powershell
python scripts\standardize_baseline.py sample\s7.png
```

常用参数：

```powershell
python scripts\standardize_baseline.py sample\s7.png --check-only
python scripts\standardize_baseline.py sample\s7.png --subject-max 360 --margin-ratio 0.75
python scripts\standardize_baseline.py sample\s7.png --output sample\s7-standard.png
```

默认输出：

```text
sample\<input-stem>-standard.png
```

标准化后的图片应作为后续动画生成的 `00` 和 `13` 基准帧。

### 4. 使用学习子 skill

如果你有参考视频、已有输出、失败案例、GIF、spritesheet、Spine 资源或动作帧文件夹，可以让 skill 从中沉淀项目经验：

```text
/img2mo-learn output\s3-arm-swing-attack
/img2mo-learn motion\some-reference-folder
/img2mo-learn sample\attack-reference.mp4
```

学习结果会写入：

```text
img2mo-knowledge/
|-- index.md
|-- learnings.jsonl
|-- action-patterns.md
|-- style-patterns.md
|-- prompt-patterns.md
`-- failures.md
```

后续生成动画时，主 skill 会优先读取这些项目级经验，用来改进动作节拍、提示词、画布边距和失败检查。

### 5. 直接使用脚本

脚本只负责非创作后处理和验证，不负责“画动作”。

标准化基准图：

```powershell
python scripts\standardize_baseline.py sample\s7.png
```

把透明 fullframe 序列转成白底 GIF 预览：

```powershell
python scripts\fullframes_to_gif.py output\s3-arm-swing-attack\fullframe --output output\s3-arm-swing-attack\preview.gif --duration-ms 75
```

验证 14 帧交付结构：

```powershell
python scripts\validate_14frame_pattern.py --baseline sample\s3-standard.png --keyframes-dir output\s3-arm-swing-attack\keyframe --fullframes-dir output\s3-arm-swing-attack\fullframe --preview output\s3-arm-swing-attack\preview.gif --prefix s3-arm-swing-attack
```

通过时输出：

```text
OK
```

## 效果展示

<table>
  <tr>
    <th align="center"><p align="center">浪人-劈砍</p></th>
    <th align="center"><p align="center">魔像-砸击</p></th>
    <th align="center"><p align="center">怪兽-抓挠</p></th>
    <th align="center"><p align="center">巨人-挥剑</p></th>
    <th align="center"><p align="center">工人-行走</p></th>
    <th align="center"><p align="center">甲虫-爬行</p></th>
  </tr>
  <tr>
    <td align="center"><img src="examples/s1.png" width="110" alt="浪人输入图"></td>
    <td align="center"><img src="examples/s2.png" width="110" alt="魔像输入图"></td>
    <td align="center"><img src="examples/s3.png" width="110" alt="怪兽输入图"></td>
    <td align="center"><img src="examples/s5.png" width="110" alt="巨人输入图"></td>
    <td align="center"><img src="examples/s6.png" width="110" alt="工人输入图"></td>
    <td align="center"><img src="examples/s4.png" width="110" alt="甲虫输入图"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s1-spritesheet .png" width="1200" alt="浪人劈砍 14 帧精灵表"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s2-spritesheet.png" width="1200" alt="魔像砸击 14 帧精灵表"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s3-spritesheet.png" width="1200" alt="怪兽抓挠 14 帧精灵表"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s5-spritesheet.png" width="1200" alt="巨人挥剑 14 帧精灵表"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s6-spritesheet.png" width="1200" alt="工人行走 14 帧精灵表"></td>
  </tr>
  <tr>
    <td colspan="6"><img src="examples/s4-spritesheet.png" width="1200" alt="甲虫爬行 14 帧精灵表"></td>
  </tr>
</table>

## 输入与输出

输入通常是一张静态 PNG：

```text
sample/s3.png
```

你描述想要的动作：

```text
使用 sample/s3.png 生成挥动手臂的攻击动画
```

输出是一套标准交付物：

```text
output/<action-id>/
|-- keyframe-prompts.md   # 02/05/08/11 四个关键帧的提示词和身份锁
|-- keyframe/             # 4 个关键帧，固定索引 02、05、08、11
|-- fullframe/            # 14 个透明 RGBA 序列帧，固定索引 00-13
|-- spritesheet.png       # 横向打包的精灵表
|-- contact-sheet.png     # 目检用接触表
|-- preview.gif           # 白底 14 帧播放预览
`-- manifest.json         # 画布、帧序、拓扑锁、关键帧索引和处理记录
```

其中 `fullframe/*.png` 是真正应该导入引擎的透明帧；`preview.gif` 只是给人看的播放预览。

## 核心机制

### 1. 身份锁

在生成前先记录角色不可变特征：脸、眼睛、轮廓、比例、配色、描边、服装、武器、角、尾巴、翅膀、爪子、标记和其他附件。后续所有提示词都继承这份身份锁。

### 2. 拓扑锁

对攻击、挥手、挥剑、尾扫等动作，skill 会用屏幕空间记录主动肢体和锚定肢体，例如：

```text
activeLimb: screen-right arm
anchorLimb: screen-left arm
```

这样可以减少“右手突然变左手”“武器换手”“尾巴根部消失”这类动画失败。

### 3. 14 帧结构

默认动作使用固定锚点：

```text
00 -> 02 -> 05 -> 08 -> 11 -> 13
```

其中 `00` 和 `13` 是基准图，`02/05/08/11` 是模型生成的四个关键姿势，其他帧是参考相邻锚点生成的补间。这个结构让短动作足够紧凑，也方便验证。

### 4. 整角色重绘

关键帧和补间帧必须由图像模型生成完整角色姿势。脚本只能做非创作后处理：标准化基准图、拆格、去色键、统一画布、生成 GIF、打包 spritesheet 和运行验证。

### 5. 可验证交付

仓库提供校验脚本，检查帧数、命名、RGBA、画布尺寸、透明角、00/13 是否一致、关键帧是否和 fullframe 对应帧像素一致，以及 GIF 是否为 14 帧白底预览。

## 支持的动作类型

| 动作 | 常用节拍 |
|---|---|
| idle / 待机 | settle -> rise -> settle |
| walk / move | contact -> down -> passing -> up -> opposite contact |
| attack / 攻击 | guard -> anticipation -> acceleration -> contact -> follow-through -> recovery |
| block / 格挡 | raise guard -> hold -> return |
| hit / suffer | impact -> recoil -> squash/stretch -> recovery |
| death / 死亡 | imbalance -> fall -> impact -> rest |
| born / spawn | small/curled shape -> unfold -> full identity |
| skill / cast | anticipation -> charge -> peak cast -> recovery |

## 工作流程

1. **标准化基准图**：必要时把输入图裁切、缩放并放到带透明边距的画布中，避免动作出界。
2. **分析角色**：记录主体结构、颜色、风格、面部、肢体、武器、附件和不确定区域。
3. **建立锁定规则**：写入身份锁、拓扑锁、武器/道具归属和画布约束。
4. **设计关键姿势**：为 `02/05/08/11` 设计动作节拍。
5. **生成关键姿势表**：一次性生成四个关键姿势，减少独立生成带来的身份漂移。
6. **生成补间帧**：按 `1/2/2/2/1` 的插入计划生成 8 个补间。
7. **后处理**：去除 chroma-key 背景，统一画布、比例、中心和脚底基线。
8. **打包交付**：输出 fullframe、keyframe、spritesheet、contact-sheet、preview.gif 和 manifest。
9. **验证与目检**：跑结构校验，同时检查 contact sheet 和 GIF 是否有换手、裁切、青边、比例跳变或动作不可读。

## 仓库结构

```text
.
|-- SKILL.md                  # 主 skill 说明和完整生成规约
|-- references/               # 关键姿势重绘、动作提示词模式等参考
|-- skills/img2mo-std/        # 基准图标准化子 skill
|-- scripts/
|   |-- standardize_baseline.py
|   |-- fullframes_to_gif.py
|   `-- validate_14frame_pattern.py
|-- sample/                   # 输入示例图
|-- examples/                 # README 展示素材
|-- motion/                   # 本地动作参考库
`-- img2mo-knowledge/         # 项目级经验沉淀
```

## 设计原则

- **整角色生成优先**：不要用脚本旋转局部肢体伪造关键姿势。
- **一次生成共享关键姿势**：不要把 02/05/08/11 分成四次独立生成。
- **00/13 保持基准图一致**：循环动作的首尾必须是同一个基准帧。
- **一个批次一个比例策略**：避免逐帧 auto-fit 造成 scale popping。
- **视觉检查不能省**：验证脚本只能发现结构问题，发现不了所有动画失败。
- **最终目录保持干净**：只保留交付文件，失败草稿和模型源图不放进最终输出目录。

## 依赖

- Python 3.x
- [Pillow](https://python-pillow.org/)
- Codex / Claude Code / Agent Skills 风格的运行环境
- 可用的图像生成能力，用于关键姿势和补间帧生成

## 许可

MIT © 2026 Haotian Wu

---

## 使用案例

<div >
  <table>
    <tr>
      <td align="center">
        <a href="#小程序://搬家塔防/bQrrvXJtLMv04Bh">
          <img src="examples/logo.png" width="120" height="120" alt="搬家塔防大作战"><br>
          <strong>搬家塔防大作战</strong>
        </a>
        <br>
        <span>微信小游戏 · 塔防策略</span>
        <br>
        <img src="https://img.shields.io/badge/微信小游戏-已上线-07C160" alt="WeChat">
      </td>
    </tr>
  </table>
</div>

