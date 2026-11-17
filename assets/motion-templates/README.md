# 可编辑 .motion 模板

`kinetic-tech-zh.motion` 是现有「酷炫科技风」公开包的原样副本，版本 `0.2.7-open-beta`，横屏 1920×1080、60fps。它是含制作入口、参数和素材的 ZIP 模板，不是剪辑软件安装包。

上传接口传送整份大文件失败，因此仓库以 `kinetic-tech-zh.motion.parts/` 保存 34 个连续分卷。下载或克隆整个仓库后，在仓库根目录运行：

```text
python scripts/restore_motion_template.py
```

脚本先校验各分卷和整包 SHA256，再生成本目录的 `kinetic-tech-zh.motion`。它不下载额外内容、不启动模板软件、不覆盖不同内容的已有文件。还原后应为 **17,596,250 字节**，SHA256 为 `472a95af35f8e0c09c0f7dc2ca0992b7c9a3405c5aa8063730c347fc4e015c21`。没有 Python 时可按文件名 001–034 的顺序二进制拼接；不要当文本合并。

[官方作品页](https://motiongit.com/adunext/385712) · [上游公开仓库](https://github.com/motiontemplates/385712)

代码和 grain 纹理按 MIT 再分发；字体保留 SIL OFL；品牌素材仅按随包声明原样随该模板分发，不能当作可任意挪用的品牌素材库。包内全部许可保持原样，外部副本见 [第三方声明](../../LICENSES/third-party-assets/kinetic-tech/THIRD-PARTY-NOTICES.md)。

本次检查通过 ZIP CRC、330 项文件指纹和 279 项素材指纹，未改变包内容；未运行模板或验证 Windows 渲染。它是历史公开版本，不代表当前在线版本。使用前解压阅读 `00-START-HERE.md`、`motion.json` 和 `CREATION.md`，按包内参数与环境要求执行。

另一个竖屏 alpha.5 包是带个人凭据与加密内容的授权封套，未收录，也未通过拆包绕过其分发限制。
