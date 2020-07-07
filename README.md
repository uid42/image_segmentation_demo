# image_segmentation_demo

## 项目简述
使用CCF数据集，仅关心水体类别。

## 生成数据集

对生成数据集的要求：
1. 正方形图片
2. 可设置大小
3. 可设置总数
4. 可设置有/无目标的比例
5. 无需缩放
6. 图片和mask都保存为jpg格式（节省空间）
7. mask中背景像素值0，目标像素值255，方便人眼查看

路径结构：
- image_segmentation_demo/
    - data/
        - src/
            - image/
- label/
    - 生成的数据集的目录，以dataset_yyyymmdd为目录名，例如 dataset_20200707
