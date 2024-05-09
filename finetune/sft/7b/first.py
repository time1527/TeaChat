# Copyright (c) OpenMMLab. All rights reserved.
import torch
from datasets import load_dataset
from mmengine.dataset import DefaultSampler
from mmengine.hooks import (CheckpointHook, DistSamplerSeedHook, IterTimerHook,
                            LoggerHook, ParamSchedulerHook)
from mmengine.optim import AmpOptimWrapper, CosineAnnealingLR, LinearLR
from peft import LoraConfig
from torch.optim import AdamW
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig)

from xtuner.dataset import process_hf_dataset
from xtuner.dataset.collate_fns import default_collate_fn
# modified:
from xtuner.dataset.map_fns import openai_map_fn, template_map_fn_factory
from xtuner.engine.hooks import (DatasetInfoHook, EvaluateChatHook,
                                 VarlenAttnArgsToMessageHubHook)
from xtuner.engine.runner import TrainLoop
from xtuner.model import SupervisedFinetune
from xtuner.parallel.sequence import SequenceParallelSampler
from xtuner.utils import PROMPT_TEMPLATE, SYSTEM_TEMPLATE

#######################################################################
#                          PART 1  Settings                           #
#######################################################################
# Model
# modified: model path
pretrained_model_name_or_path = '/root/model/internlm2-math-7b'
use_varlen_attn = False

# Data
# modified: data path
alpaca_en_path = '/root/dataset/2024-04-18-15:57:59_wanjuan_openai.json'
prompt_template = PROMPT_TEMPLATE.internlm2_chat
max_length = 2048
pack_to_max_length = True

# parallel
sequence_parallel_size = 1

# Scheduler & Optimizer
batch_size = 1  # per_device
accumulative_counts = 16
accumulative_counts *= sequence_parallel_size
dataloader_num_workers = 0
max_epochs = 3
optim_type = AdamW
lr = 2e-4
betas = (0.9, 0.999)
weight_decay = 0
max_norm = 1  # grad clip
warmup_ratio = 0.03

# Save
save_steps = 500
save_total_limit = 2  # Maximum checkpoints to keep (-1 means unlimited)

# Evaluate the generation performance during the training
evaluation_freq = 500
SYSTEM = SYSTEM_TEMPLATE.alpaca
# modified:
question1 = "（1）已知$m\in \mathbf{R}$，若$z=\left(m+\text{i}\right)\left(-2+\text{mi}\right)$为实数，求$m$的值．\n \
（2）已知复数$\text{z}$满足$z+\left| \overline{z}\right| =8+4\text{i}$，若复数$z$是实系数一元二次方程$x^{2}+bx+c=0$的一个根，求$b+c$的值．"

question2 = "果蝇是遗传学研究的良好材料，在遗传规律的发现过程中发挥了重要作用。摩尔根用一只白眼雄果蝇与一只红眼雌果蝇交配，所得F1全为红眼，F1雌雄交配所得F2中只有雄果蝇中出现了白眼。下列分析正确的是（       ）\n \
A．F1雄果蝇产生的精子中均不含X染色体\n \
B．果蝇作为遗传学材料的优点有易饲养、繁殖快等\n \
C．F2中出现白眼果蝇的原因是发生了基因的自由组合\n \
D．果蝇白眼的遗传和性别相关联，F2中红眼∶白眼=2∶1"

question3 = "阅读材料，完成下列要求。\n \
材料一   清初，黄河下游堤防失修，决口频繁。康熙年间，河道总督靳辅“遍历河干，广咨博询，求贤才之硕画，访谙练之老成”。他主张从全局出发，将黄河、淮河、运河三者进行综合治理，并指出：“用水刷沙，虽为治河不易之策，然河身淤土有新旧之不同……五年以前之久淤……冲刷甚难，故必须设法疏浚也。”主要措施是坚筑堤防、蓄清刷浑、河运分离。由于治河经费紧缺，靳辅预支数个省份康熙二十年正税的十分之一、并允诺“以淮扬水涸之后溜出田地的屯田收入及商船货物缴纳的商税补还”。经治理，黄河安澜十余年，之后又连年决溢。——摘编自王育民《中国历史地理概论》等\n \
材料二   清末民初以来，原有黄河治理体系逐渐解体，黄河水患频发。1913年，濮阳双合岭决口，当时北京政府着力进攻南方革命力量，无暇顾及，导致灾情不断扩大，拖延两年才完全堵复。1921年，《大公报》报道：“黄河上下游近来迭次决口，被水区域益形扩大，加以款项支绌，河工经费不能尽力筹拔，因之河防设施多有未周。”1933年，黄河水利委员会委员长李仪祉提出了黄河治本思想，强调黄河治理要上中下游并重，防洪与航运、水电、灌溉兼顾，还认识到黄土高原水土保持在黄河治理中的重要性，从根本上改变了传统的治河策略。但由于主管机关职权不定，治理工作难以有效推进。——摘编自苏全有等《民国时期黄河治理成效不佳的历史反思》\n \
材料三   新中国成立后，毛泽东多次考察黄河并提出“要把黄河的事情办好”。1999年，江泽民强调黄河治理开发应将经济效益、社会效益和生态效益相统一、实现经济建设与人口、资源、环境协调发展。2019年，习近平将“黄河流域生态保护和高质量发展”提升为国家战略，标志着黄河流域的治理开发步入新征途。 ——摘编自邓生菊等《新中国成立以来黄河流域治理开发及其经验启示》\n \
(1)根据材料一并结合所学知识，概括清代靳辅治理黄河的特点并予以评价。 (2)根据材料二并结合所学知识，简析民国时期黄河治理成效不佳的原因。 (3)根据上述材料并结合所学知识，谈谈你从黄河治理中得到的启示。"
evaluation_inputs = [question1,question2,question3]

#######################################################################
#                      PART 2  Model & Tokenizer                      #
#######################################################################
tokenizer = dict(
    type=AutoTokenizer.from_pretrained,
    pretrained_model_name_or_path=pretrained_model_name_or_path,
    trust_remote_code=True,
    padding_side='right')

model = dict(
    type=SupervisedFinetune,
    use_varlen_attn=use_varlen_attn,
    llm=dict(
        type=AutoModelForCausalLM.from_pretrained,
        pretrained_model_name_or_path=pretrained_model_name_or_path,
        trust_remote_code=True,
        torch_dtype=torch.float16,
        quantization_config=dict(
            type=BitsAndBytesConfig,
            load_in_4bit=True,
            load_in_8bit=False,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type='nf4')),
    lora=dict(
        type=LoraConfig,
        r=64,
        lora_alpha=16,
        lora_dropout=0.1,
        bias='none',
        task_type='CAUSAL_LM'))

#######################################################################
#                      PART 3  Dataset & Dataloader                   #
#######################################################################
alpaca_en = dict(
    type=process_hf_dataset,
    # modified:
    dataset=dict(type=load_dataset, path='json', data_files=dict(train=alpaca_en_path)),
    tokenizer=tokenizer,
    max_length=max_length,
    # modified:
    dataset_map_fn=openai_map_fn,
    template_map_fn=dict(
        type=template_map_fn_factory, template=prompt_template),
    remove_unused_columns=True,
    shuffle_before_pack=True,
    pack_to_max_length=pack_to_max_length,
    use_varlen_attn=use_varlen_attn)

sampler = SequenceParallelSampler \
    if sequence_parallel_size > 1 else DefaultSampler
train_dataloader = dict(
    batch_size=batch_size,
    num_workers=dataloader_num_workers,
    dataset=alpaca_en,
    sampler=dict(type=sampler, shuffle=True),
    collate_fn=dict(type=default_collate_fn, use_varlen_attn=use_varlen_attn))

#######################################################################
#                    PART 4  Scheduler & Optimizer                    #
#######################################################################
# optimizer
optim_wrapper = dict(
    type=AmpOptimWrapper,
    optimizer=dict(
        type=optim_type, lr=lr, betas=betas, weight_decay=weight_decay),
    clip_grad=dict(max_norm=max_norm, error_if_nonfinite=False),
    accumulative_counts=accumulative_counts,
    loss_scale='dynamic',
    dtype='float16')

# learning policy
# More information: https://github.com/open-mmlab/mmengine/blob/main/docs/en/tutorials/param_scheduler.md  # noqa: E501
param_scheduler = [
    dict(
        type=LinearLR,
        start_factor=1e-5,
        by_epoch=True,
        begin=0,
        end=warmup_ratio * max_epochs,
        convert_to_iter_based=True),
    dict(
        type=CosineAnnealingLR,
        eta_min=0.0,
        by_epoch=True,
        begin=warmup_ratio * max_epochs,
        end=max_epochs,
        convert_to_iter_based=True)
]

# train, val, test setting
train_cfg = dict(type=TrainLoop, max_epochs=max_epochs)

#######################################################################
#                           PART 5  Runtime                           #
#######################################################################
# Log the dialogue periodically during the training process, optional
custom_hooks = [
    dict(type=DatasetInfoHook, tokenizer=tokenizer),
    dict(
        type=EvaluateChatHook,
        tokenizer=tokenizer,
        every_n_iters=evaluation_freq,
        evaluation_inputs=evaluation_inputs,
        system=SYSTEM,
        prompt_template=prompt_template)
]

if use_varlen_attn:
    custom_hooks += [dict(type=VarlenAttnArgsToMessageHubHook)]

# configure default hooks
default_hooks = dict(
    # record the time of every iteration.
    timer=dict(type=IterTimerHook),
    # print log every 10 iterations.
    logger=dict(type=LoggerHook, log_metric_by_epoch=False, interval=10),
    # enable the parameter scheduler.
    param_scheduler=dict(type=ParamSchedulerHook),
    # save checkpoint per `save_steps`.
    checkpoint=dict(
        type=CheckpointHook,
        by_epoch=False,
        interval=save_steps,
        max_keep_ckpts=save_total_limit),
    # set sampler seed in distributed evrionment.
    sampler_seed=dict(type=DistSamplerSeedHook),
)

# configure environment
env_cfg = dict(
    # whether to enable cudnn benchmark
    cudnn_benchmark=False,
    # set multi process parameters
    mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0),
    # set distributed parameters
    dist_cfg=dict(backend='nccl'),
)

# set visualizer
visualizer = None

# set log level
log_level = 'INFO'

# load from which checkpoint
load_from = None

# whether to resume training from the loaded checkpoint
resume = False

# Defaults to use random seed and disable `deterministic`
randomness = dict(seed=None, deterministic=False)

# set log processor
log_processor = dict(by_epoch=False)
