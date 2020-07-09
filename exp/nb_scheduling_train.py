
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/scheduling_train.ipynb

#================================================
from fastai.basic_train import LearnerCallback


#================================================
from fastai.callbacks.general_sched import *
from fastai.callback import *


#================================================
from fastai.core import *


#================================================
from IPython.core import debugger as idb


#================================================
class CustomEpochLength(Callback):
    def __init__(self, epoch_len=1e99):
        '''
        在fastai定义的训练过程中，只有在一个epoch结束后才会进行一次valid loss和metrics计算。
        在数据集很大，batch size很小时，一个epoch包含的iteration数非常多，就会导致非常多的iteration后才会进行一次valid loss和metrics
        计算。这会是个问题，因为你往往根据valid loss或metrics来做一些决定，例如early stop，如果valid loss和metrics更新周期太长，可能
        会使你错过最好的时机。
        本callback使你能指定一个epoch包含更少的iteration.
        注意：如果你指定一个epoch包含更多的iteration，则实际上本callback是不起作用的。
        注意：如果你使用该callback，你要确定你的dataloader的sample方式是随机的，否则可能会导致每个epoch都只看到固定的一部分训练
        数据，而另一部分训练数据永远不会参与训练。
        ------------------------------------------------------
        参数：
        -- epoch_len：指定一个epoch包含多少个iteration，默认为一个非常大的数（1e99），这保证如果你使用了该callback但没有指定epoch_len，
        那么实际上该callback是不起作用的.
        '''
        self.epoch_len=epoch_len
        print('ALLERT: You are using CumtomEpochLength, please make sure that your training dataloader is using random sampler, or this may cause problem.')

    def on_batch_end(self, num_batch, **kwargs):
        if (num_batch+1)%self.epoch_len: return
        return {'stop_epoch': True}



#================================================
class MultiAnneal_Scheduler(LearnerCallback):
    def __init__(self,
                 learn,
                 base_lr_sched,
                 monitor='valid',
                 worseN_thres=3,
                 annealRate=5,
                 duration_thres=5,
                 annealIte=100,
                 phaseMaxN=3,
                 finetune_stop=0):
        '''
        将训练过程分为多个constant lr训练阶段，当一个训练阶段到达平台期后，以线性下降的方式将lr衰减一定倍率，然后进入
        下一个constant lr训练阶段，如此重复，直至最后一个训练到达平台期后结束训练。其中第一个训练阶段的lr由base_lr_sched决定。
        参数：
            -- learn：Learner对象
            -- base_lr_sched：一个对learn的lr做scheduling的对象，它应该是constant lr的方式。本类就是通过自适应地修改它来修改对learn的lr的scheduling方式。
            -- monitor：根据哪个损失值来判定是否达到平台期，字符串，可选'valid'或'train_smooth'。不论你选各个变量，监测周期都是一个epoch.
            -- worseN_thres：当有warseN_thres个epoch都没有出现更好的loss时，认为达到了平台
            -- annealRate：loss到达平台后，将当前使用的lr衰减至1/annealRate
            -- duration_thres：一个constant lr训练阶段至少持续duration_thres个epoch
            -- annealIte：lr衰减至lr/annealRate经历的iteration数
            -- phaseMaxN：至多phaseMaxN个训练阶段
            -- finetune_stop：一个整数，在某个train phase刚开始，其lr稳定后，决定是否结束微调，变为全模型学习。若为0，则不起作用，即整个训练
            过程维持开始的微调策略；若大于phaseMaxN，也不会起作用。
        '''
        super().__init__(learn)
        self.scheduler = base_lr_sched
        self.monitor = monitor
        self.worseN_thres = worseN_thres
        self.annealRate = annealRate
        self.duration_thres = duration_thres
        self.annealIte = annealIte
        self.phaseMaxN = phaseMaxN
        self.finetune_stop = finetune_stop


        self.best_loss = None
        self.worseN = 0
        self.phaseDuration = 0
        self.phaseN = 0
        self.expectConstantLr = False


    def _get_monitoring_loss(self,**kwargs):
        if self.monitor=='valid': loss = kwargs['last_metrics'][0]
        if self.monitor=='train_smooth': loss = kwargs['smooth_loss']
        return loss


    def _finetune_stop(self,iteration,**kwargs):
        if self.finetune_stop==self.phaseN:
            if isinstance(self.scheduler.start,Iterable) and len(self.scheduler.start)>1:
                self.scheduler.start[0] = self.scheduler.start[1]
                self.scheduler.end[0] = self.scheduler.end[1]
                print(f'at iteration {iteration}, stop finetune and begin to train entire model.')


    def on_epoch_end(self, epoch, num_batch, **kwargs):
        # 更新当前phase持续周期
        self.phaseDuration += 1

        loss = self._get_monitoring_loss(**kwargs)

        # 首次epoch
        if self.best_loss is None:
            self.best_loss = loss
            return

        # 更新best_loss, self.warseN
        if loss<self.best_loss:
            self.best_loss = loss
            self.worseN = 0
        else:
            self.worseN += 1

        # 若达到phase结束条件
        if self.phaseDuration>=self.duration_thres and self.worseN>=self.worseN_thres:
            # 复位 phaseDuration
            self.phaseDuration = 0
            # 更新 phaseN
            self.phaseN += 1

            # 设置lr的线性下降阶段
            self.scheduler.start = self.scheduler.start
            self.scheduler.end = self.scheduler.start / self.annealRate
            self.scheduler.func = annealing_linear

            self.scheduler.n_iter = self.annealIte
            self.scheduler.n = 0

            print(f'on end of epoch#{epoch}: start annealing from {self.scheduler.start} to {self.scheduler.end}')

            # 如果不是最后一个phase
            if self.phaseN<self.phaseMaxN:
                # 使end稍降，n_iter稍增，防止下降结束后结束训练
                self.scheduler.end -= (self.scheduler.start - self.scheduler.end)/self.annealIte
                self.scheduler.n_iter += 1
                # 设置 self.expectConstantLr=True，使下降阶段临结束时换为恒lr训练
                self.expectConstantLr = True
            # 如果是最后一个phase，则等待下降结束后自动结束训练，无需额外处理

    def on_batch_end(self, **kwargs):
        # 如果正在等待下降阶段结束后开始恒lr训练，并且下降阶段已经到了马上结束的时候
        if self.expectConstantLr and self.scheduler.n==(self.scheduler.n_iter-1):
            self.expectConstantLr = False
            self.scheduler.start = self.scheduler.start / self.annealRate
            self.scheduler.end = self.scheduler.start
            self.scheduler.func = annealing_no

            self.scheduler.n_iter = 1e99 # 将 n_iter 设置为一个非常大的数，防止该phase自动结束
            self.scheduler.n = 0

            self._finetune_stop(**kwargs)


#================================================
def fit_with_warmup_multiAnnealPlat(learn,
                                    epoch_len:int=10,
                                    num_epoch:int=100,

                                    lr_start:float=3e-4,
                                    lr_constant:float=3e-3,
                                    warmup_iter:int=10,

                                    monitor:str='valid',
                                    worseN_thres:int=3,
                                    annealRate:float=5,
                                    duration_thres:int=5,
                                    annealIte:int=200,
                                    phaseMaxN:int=3,
                                    finetune_stop=0,
                                    callbacks=None)->None:
    '''
    训练开始时先warmup，然后以constant lr训练，valid loss到达平台后衰减lr继续constant lr训练，
    如此直到设置的epoch上限，或者constant lr训练阶段数达到上限，结束训练。
    参数：
    -- learn：Learner对象
    -- epoch_len：设置一个epoch包含的iteration数，（见CustomEpochLength的定义）。
    -- num_epochs：训练epoch数上限

    -- lr_start：warmup起始lr
    -- lr_constant：warmup结束lr，也是phase0的constant lr
    -- warmup_iter：warmup持续iteration数

    -- worseN_thres：当有warseN_thres个epoch都没有出现更好的valid loss时，认为达到了平台
    -- annealRate：valid loss到达平台后，将当前使用的lr衰减至1/annealRate
    -- duration_thres：一个constant lr训练阶段至少持续duration_thres个epoch
    -- annealIte：lr衰减至lr/annealRate经历的iteration数
    -- phaseMaxN：至多phaseMaxN个训练阶段
    -- finetune_stop：一个整数，在某个train phase刚开始，其lr稳定后，决定是否结束微调，变为全模型学习。若为0，则不起作用，即整个训练
    过程维持开始的微调策略；若大于phaseMaxN，也不会起作用。
    '''
    # 先建一个基础scheduler
    phase0 = TrainingPhase(warmup_iter).schedule_hp('lr',(lr_start,lr_constant),annealing_cos) # warmup
    phase1 = TrainingPhase(len(learn.data.train_dl)*num_epoch-warmup_iter).schedule_hp('lr',lr_constant,annealing_no) # constant lr
    base_sched = GeneralScheduler(learn, [phase0, phase1])


    # 提取base_sched的constant lr部分，传入MultiAnneal_Scheduler，供其自适应调整
    lr_sched = phase1.scheds['lr']
    autoPhases = MultiAnneal_Scheduler(learn=learn,
                                       base_lr_sched=lr_sched,
                                       monitor=monitor,
                                       worseN_thres=worseN_thres,
                                       annealRate=annealRate,
                                       duration_thres=duration_thres,
                                       annealIte=annealIte,
                                       phaseMaxN=phaseMaxN,
                                       finetune_stop=finetune_stop)

    # 加入fit函数的callbacks中
    callbacks = listify(callbacks)
    callbacks.append(base_sched)
    callbacks.append(autoPhases)

    # 设置一个epoch包含的iteration数
    set_epochLen = CustomEpochLength(epoch_len=epoch_len)
    callbacks.append(set_epochLen)

    learn.fit(num_epoch, callbacks=callbacks)
