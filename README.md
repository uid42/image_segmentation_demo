# image_segmentation_demo

## 项目简述
使用CCF数据集，仅关心水体类别。

## 生成数据集

对生成数据集的要求：
1.
正方形图片
2. 可设置大小
3. 可设置总数
4. 可设置有/无目标的比例
5. 无需缩放
6. 可设置图片和mask的保存格式（jpg或png）
7.
mask中背景像素值0，目标像素值255，方便人眼查看

路径结构：
- image_segmentation_demo/
    - data/
- src/
            - image/
- label/
    - 生成的数据集的目录，以dataset_yyyymmdd为目录名，例如
dataset_20200707

## 模型
使用UNet结构，以ResNet为Encoder，有以下两种变化：

1.
**resnet_unet_vanilla**：
原始的UNet结构，以ResNet为Encoder

2. **resnet unet, all
resnetish**：
在resnet_unet_vanilla的基础上做了修改：在侧向连接和上采用路径上广泛采用了残差连接

此外，Encoder可以选择
resnet18, resnet34, resnet50 等不同复杂度的模型。


## 损失函数
定义了两种损失函数：soft_dice 和
balance_bce，可以对二者的效果做对比。
balance_bce，是对bce做了自动权重，不论正/负像素的比例如何，通过自动权重，把二者对总损失的贡献比例调节到一个固定值。

## Metrics
定义了 iou 作为 metric
