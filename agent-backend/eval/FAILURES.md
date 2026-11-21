# Evaluation Failures & Root Causes

- **seed_01 (baseline)**: utterance=`Find me an espresso machine under two hundred dollars` -> pick=`Garvee Compact 20 Bar Espresso Machine Stainless Steel, Steam Milk Frother, Removable Tank for Cappuccino/Latte,(Silver)` (price_minor=15099, budget_max_minor=20000, score=0.2274, budget_ok=True)
- **seed_02 (baseline)**: utterance=`Find me the Monday Cartoons Digital Sticker under one dollar` -> pick=`Digital Sticker` (price_minor=50, budget_max_minor=100, score=0.2732, budget_ok=True)
- **seed_03 (system)**: utterance=`Show me a Monday Cartoons hat under fifty dollars` -> pick=`Monday Cartoons Hat` (price_minor=3800, budget_max_minor=5000, score=0.5334, budget_ok=True)
- **seed_03 (baseline)**: utterance=`Show me a Monday Cartoons hat under fifty dollars` -> pick=`"Balance" Photo Print` (price_minor=900, budget_max_minor=5000, score=0.3699, budget_ok=True)
