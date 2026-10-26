# 第三方与资产声明

模型、材质、骨骼、动画、程序造型脚本及虚拟场景是本机项目的自有内容，采用MIT。规范GLB没有图像纹理或外部URI；8份原生Blender文件无链接库或外部图像。几何/动画在此次归档未重新生成。

Web/Godot/构建工具有各自的许可，根MIT不覆盖它们。锁定包的声明与LICENSE/NOTICE副本保留于[依赖登记](licenses/dependency-index.json)和`licenses/npm/`。React、React Three Fiber、Drei、Three.js等按其原声明使用；Godot、Blender、Node和外部MCP程序需另行安装，没有把软件安装目录打包上传。

部分npm包未随包提供独立许可文件，登记中保留该锁定版本的SPDX声明；能从官方上游补到的许可另存于`licenses/upstream/`，并注明其来自当前上游，不冒充锁定版本原文件。stats-gl 2.4.2声明MIT，但随包及当前上游均未找到独立LICENSE文件，记录此缺口；本项目没有主动使用它的监测组件。

Vite产物还可能包含Three.js附带的Draco/Basis通用解码器，即使当前规范GLB没有压缩/纹理也会输出相关文件。保留Google Draco与BinomialLLC Basis Universal的Apache2.0许可及官方来源：[Draco](https://github.com/google/draco)、[Basis Universal](https://github.com/BinomialLLC/basis_universal)。对应文本见`licenses/bundled/`；上游原NOTICE/版权声明按随包文件保留。

原Web中的远程city HDRI环境预设已移除，公开预览只用现有程序灯光，不再请求或重新分发那张外部图。原有渲染/转台视频由项目程序场景生成，PNG仅清理机器文件路径元数据，IDAT像素压缩流不变。
