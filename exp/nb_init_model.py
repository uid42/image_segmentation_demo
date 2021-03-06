
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/init_model.ipynb

#================================================
from fastai.callbacks.hooks import Hook,Hooks


#================================================
from torch import nn


#================================================
import torch


#================================================
from fastprogress.fastprogress import progress_bar


#================================================
import re


#================================================
def get_convs(model,return_names=False):
    ns = []
    ms = []
    for n,m in model.named_modules():
        if isinstance(m,(nn.Conv2d,nn.ConvTranspose2d)):
            ns += [n]
            ms += [m]

    if return_names: return ns,ms
    else: return ms


#================================================
def hook_mean_std(m, i, o):
    "Take the shape, mean and std of `o`."
    return m.kernel_size[0], o.shape[1:], o.mean().item(), o.std().item()


#================================================
# helper function
def show_layer_stats(model,x_batch):
    ns,ms = get_convs(model,return_names=True)
    with Hooks(ms,hook_mean_std) as hooks_hd:
        _ = model(x_batch)

    for n,s in zip(ns,hooks_hd.stored):
        print('{}:'.format(n))
        print(s)
        print('----------------')


#================================================
def hook_init(m,i,o):
    m.weight.data /= o.std()


#================================================
def runtime_init_linear(model, x_batch, hook_init=hook_init, module_names=[]):
    '''
    Idea come from LSUV (https://arxiv.org/pdf/1511.06422.pdf).
    Initialize linear layer(conv,fc) weights and bias at runtime using a hook function.
    这个过程是按照顺序逐层初始化：
    （1）跑一遍模型，初始化第一层，该层的输入是x_batch(它是规则的)，则初始化操作之后保证该层的输出也是规则的；
    （2）再跑一遍模型，这时第一层的输出（即第二层的输入）已经是规则的了，初始化第二层；
    （3）再跑一遍模型，这时第一、二层的输出已经是规则的了，初始化第三层；
    （4）以此类推。
    因此这个过程的运行时间会较长。
    -----------------------
    参数：
    -- model: the model will get initialized.
    -- x_batch: a batch of data to run the model, you shoud make sure that x_batch is normalized.
    -- init_hook_func: a hook function used to initialize each layer
    -----------------------
    返回值：
    -- the model whose weights and bias is initialized by this function.
    '''
    # set model.require_grad to False, otherwise you can not modify layer weights at runtime.
    model.requires_grad_(False)

    # get models to be initialized
    ms = []
    for n,m in model.named_children():
        if n in module_names:
            print('find '+n)
            ms += get_convs(m)


    # 粗初始化：bias->0；weights->N(0,1)
    for m in ms:
        if m.bias is not None:
            m.bias.zero_()
        m.weight.normal_(0,1)

    # 逐模块初始化
    pb_ms = progress_bar(ms)
    pb_ms.comment = 'runing init'
    for m in pb_ms:
        with Hook(m, hook_init):
            _ = model(x_batch)

    # set model.require_grad to True
    model.requires_grad_(True)

    return model
