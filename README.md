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
        -
生成的数据集的目录，以dataset_yyyymmdd为目录名，例如dataset_20200707
            - image/
- label/

## 模型
使用UNet结构，以ResNet为Encoder，有以下两种变化：

1. **resnet_unet_vanilla**：
原始的UNet结构，以ResNet为Encoder

2. **resnet unet, all resnetish**：
在resnet_unet_vanilla的基础上做了修改：在侧向连接和上采用路径上广泛采用了残差连接

此外，Encoder可以选择
resnet18,
resnet34, resnet50 等不同复杂度的模型。


## 损失函数
- dice_loss
- balance_bce:
可以设置正/负比例，函数内会自动计算权重，将正/负比例调节到你设置的值。
- combo_loss：dice_loss+balance_bce

##
Metrics
定义了 iou 作为 metric

## 训练
可以从几个方面做不同的组合尝试：
1. 模型结构：
    - allres
    -
vanila
2. 模型复杂度：
    - res18
    - res34
3. 损失函数：
    - dice_loss
    -
balance_bce
    - combo_loss
4. balance_ratio：
    - 0.1
    - 1
    - 10
5.
dataset 的大小
    - 200
    - 2000
5. 不同的augmentation
