# LTCN LOGO CHANGER

![Version](https://img.shields.io/badge/version-v0.8.0-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.10.2%2B-41BDF5)
![License](https://img.shields.io/badge/license-MIT-green)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/ltcn_logo_changer/brand/dark_logo.png">
  <img alt="LTCN LOGO CHANGER" src="custom_components/ltcn_logo_changer/brand/logo.png" width="420">
</picture>

LTCN LOGO CHANGER 是一个 Home Assistant 自定义集成，让普通用户通过图形界面修改 Home Assistant 的品牌名称和图标。用户只需填写名称并上传一张常见格式的图片，集成会自动完成校验、转换、缩放和多尺寸图标生成。

项目完全本地运行，不上传图片到外部服务，不替换 Home Assistant 核心文件。采用 MIT 许可证，可免费用于个人项目和商业项目。

## 功能

- 在 Home Assistant 原生配置界面填写品牌名称、上传图标。
- 修改网页标题、左侧导航栏标题、浏览器图标、Apple 网页图标及 Web App manifest 名称和图标。
- 支持 PNG、JPG/JPEG、WebP 和 ICO，单个文件最大 5 MB。
- 自动纠正照片 EXIF 方向并移除原始图片元数据。
- 长方形图片保持比例、居中补边，不拉伸、不裁掉 Logo。
- 自动生成 16/32/48/64 像素的 `favicon.ico`，以及 180、192、512 像素 PNG。
- 网页图标保留透明背景；Apple Touch 图标自动补白色背景。
- 自动生成新的资源版本地址，减少手机 App 和浏览器读取旧缓存的问题。
- 支持简体中文和英文界面。
- 可随时修改品牌，也可恢复 Home Assistant 默认品牌。
- 可识别并安全隔离经过验证的旧版 Favicon changer，避免两个集成同时修改前端。

## 安装

### 通过 HACS

1. 在 HACS 中打开“集成”。
2. 右上角菜单选择“自定义存储库”。
3. 添加：`https://github.com/laitecn-tech/ltcn-logo-changer`
4. 类别选择“集成”，下载 **LTCN LOGO CHANGER**。
5. 重启 Home Assistant。

### 手动安装

1. 下载本仓库。
2. 将 `custom_components/ltcn_logo_changer` 完整复制到 Home Assistant 的 `config/custom_components/`。
3. 确认最终路径为 `config/custom_components/ltcn_logo_changer/manifest.json`。
4. 重启 Home Assistant。

## 使用

1. 打开“设置 → 设备与服务 → 添加集成”。
2. 搜索 **LTCN LOGO CHANGER**。
3. 填写品牌名称并上传一张图标。
4. 保存后重启 Home Assistant。
5. 完全退出并重新打开手机 App，或刷新浏览器页面。

后续可在该集成的“配置”中修改名称或图标。不上传新图片时会保留原图。选择“恢复 Home Assistant 默认品牌”后，同样需要重启才能生效。

## 图片处理与隐私

- 建议使用 512 × 512 或更大的正方形图片，但不要求用户提前转换。
- 每边允许 16–8192 像素，总像素不得超过 1600 万。
- 动画、损坏图片、SVG、HTML、过大文件和异常尺寸会被拒绝。
- 上传文件仅在 Home Assistant 本机处理。
- 原始文件名、EXIF 信息和原始照片不会发布到网页目录。
- 重新编码后的资源存放于 `config/www/ltcn_logo_changer/<内容版本>/`。
- 只有全部图标生成成功后才保存新配置；失败时保留原配置和原图。

## 稳定性设计

- 使用 Home Assistant 提供的前端扩展、manifest 和静态资源接口。
- 不修改 Home Assistant 核心文件、页面模板或登录页。
- 不替换 Lit 管理的 DOM，也不删除侧边栏渲染节点。
- 侧边栏标题功能不可用时会跳过该项，保留正常导航。
- 配置修改不会热替换当前页面，重启后统一应用，降低前端状态冲突。
- Home Assistant 安全模式会自动排除该自定义集成。

## Favicon changer 迁移

集成可以识别已验证的旧 `custom_components.favicon` 实现，恢复它已经应用的已知修改，并在当前 Home Assistant 进程中阻止旧钩子再次接管品牌。

此过程不会删除旧集成配置、文件或图标。遇到未知版本、异常钩子或其他组件已经修改模板时，LTCN LOGO CHANGER 会停止接管并显示冲突提示，避免覆盖来源不明的代码。

完成迁移后，建议删除旧 Favicon changer。若旧集成仍处于启用状态，将来删除 LTCN LOGO CHANGER 并重启 Home Assistant 后，旧品牌修改可能重新生效。

## 支持范围与限制

支持：

- Home Assistant 主界面网页标题。
- 左侧导航栏品牌标题。
- 浏览器 favicon。
- Apple Touch 图标。
- Web App manifest 名称和图标。

当前不支持：

- 独立 `/auth/authorize` 登录页。
- Home Assistant 启动画面。
- iOS、Android 系统桌面上的原生 Companion App 图标。
- 无需重启的品牌热更新。

本项目已针对 Home Assistant 2026.10.2 的配置流、文件上传和前端接口进行验证。Home Assistant 后续版本如果调整内部前端接口，侧边栏标题功能可能需要适配。

## 卸载

1. 在“设置 → 设备与服务”中删除 LTCN LOGO CHANGER。
2. 重启 Home Assistant，使前端恢复默认品牌。
3. 如不再需要，可删除 `config/custom_components/ltcn_logo_changer`。
4. 可选：删除 `config/www/ltcn_logo_changer` 中已经生成的图标。

删除生成图标前请确认集成已经停用并完成重启。

## 参与开发

欢迎提交 Issue 和 Pull Request。报告问题时请提供：

- Home Assistant 版本。
- LTCN LOGO CHANGER 版本。
- 浏览器或 Companion App 平台。
- 可复现步骤和相关日志。

请勿在 Issue 中提交访问令牌、公网地址、家庭位置、用户上传的私人图片或其他敏感信息。

## 开源许可

本项目使用 [MIT License](LICENSE)。在保留许可证和版权声明的前提下，允许免费使用、复制、修改、分发、再许可和商业使用。

第三方字体和品牌资源的许可说明保存在 `custom_components/ltcn_logo_changer/brand/` 目录中。

---

LTCN莱特智能 HAIOTS 平台  
基于Home Assistant开源系统底座的商业物联网解决方案平台  
让HA从极客专属，变成可复制、可交付，可管理的商业物联网系统  
欢迎做客 https://laitecn.taobao.com
