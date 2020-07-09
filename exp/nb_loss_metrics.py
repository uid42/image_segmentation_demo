
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/loss_metrics.ipynb

#================================================
import torch


#================================================
from torch.nn import functional as F


#================================================
from torch import tensor


#================================================
from IPython.core import debugger as idb


#================================================
import numpy as np


#================================================
import math


#================================================
def dice_coef(input, target):
    smooth = 1.

    pred = input.sigmoid()
    target = target.float()

    return ((2. * (pred * target).sum() + smooth) / (pred.sum() + target.sum() +smooth))


#================================================
def dice_loss(input, target):
    return 1 - dice_coef(input, target)


#================================================
def weighted_bce(input, target, pos_weight=1):
    """
    pos_weight: positive weight relative to negative weight(which is 1)
    """
    mask = (target>0).float()
    weight = (mask*pos_weight + (1-mask))
    weight = weight/weight.sum()*mask.numel()
    return F.binary_cross_entropy_with_logits(input,target,weight=weight)


#================================================
def balance_bce(input, target, balance_ratio=1):
    """
    Auto adjust positive/negative ration as set by balance_ratio.
    """
    mask = (target>0).float()
    posN = mask.sum()
    negN = (1-mask).sum()
    pos_weight = balance_ratio*negN/posN

    return weighted_bce(input, target, pos_weight)


#================================================
def mask_iou(input, target):
    """
    iou for segmentation
    """
    pred_mask = input>0
    target_mask = target>0

    i = (pred_mask&target_mask).float().sum()
    u = (pred_mask|target_mask).float().sum()
    return i/u
