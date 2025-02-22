from filter import filter_wanjuan,filter_firefly,filter_cot

DATASET_FUNC_MAP = {
    "wanjuan":filter_wanjuan,
    "firefly-train-1.1M":filter_firefly,
    "Alpaca-CoT":filter_cot
}