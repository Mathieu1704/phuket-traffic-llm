# Version Summary

This file summarizes the main LLM experiment variants used in the Phuket project.

## Snapshot

| Version | Main idea | Numeric outcome | Explainability outcome | Status |
| --- | --- | --- | --- | --- |
| V4 | Base full-prompt fine-tuning | Best balanced forecast result | Moderate | Best overall baseline |
| V5 | Strong grounded re-training | Forecast degraded | Saved scores partially unreliable because of an old scoring bug | Diagnostic branch |
| V6 | Forecast-first dataset redesign | Forecast still worse than V4 | Best explainability control | Best explainability branch |
| V7 | V4 warm-start + light explain top-up | Forecast still worse than V4 | Strong but not as good as V6 | Hybrid attempt, not final |
| V8 | Scratch forecast-pure LoRA from base model | Better than V5/V6/V7, still worse than V4 | Counterfactual strong, grounding weak | Forecast-focused experiment |
| V9 | Scratch forecast-only branch with traffic-memory lags + JSON target | Second-best forecast result, best post-V4 | Strongest explainability proxy scores | Best overall compromise |
| V10 | V9 + YoY comparison + corridor ranking enrichment | Better val, worse test than V9 | Still strong, but weaker than V9 | Useful enrichment test, not final |

## V4 - `v4_full`

Purpose:
- establish the first strong fine-tuned Phuket baseline
- train on the original base dataset (`576` prompts total)

Key results:
- test forecast +1 `MAE=0.1200`, `RMSE=0.1703`, `MAPE=8.59%`
- Ablation `70%`
- Counterfactual `100%`
- Grounding `45%`

Pros:
- best overall forecast result among all fine-tuned variants
- beats `PERSIST_current_month`
- beats `TRAIN_corr_mean`
- stable enough to serve as the main balanced baseline

Cons:
- does not beat `TRAIN_same_corr_month`
- explainability control is only moderate
- model still leaks hidden variables under masking

Recommended interpretation:
- best overall / balanced model
- strongest candidate when prediction still matters materially

## V5 - `v5_grounded`

Purpose:
- inject much stronger grounded explain supervision
- reduce hallucinated weather / tourism / trend references

Key results:
- test forecast +1 `MAE=0.1610`, `RMSE=0.2150`, `MAPE=11.39%`
- saved explainability CSV showed `0% / 100% / 0%`

Pros:
- useful experiment diagnostically
- showed that stronger grounded supervision changes model behavior materially

Cons:
- forecast quality dropped sharply
- explainability CSV for this run was polluted by a historical substring-matching bug
- not reliable as a final model or as a clean explainability reference

Recommended interpretation:
- keep as a learning step, not as a final result to foreground

## V6 - `v6_forecast_first`

Purpose:
- restore forecast priority after V5
- keep explicit variable discipline through data design

Key results:
- test forecast +1 `MAE=0.1620`, `RMSE=0.2109`, `MAPE=11.22%`
- Ablation `100%`
- Counterfactual `100%`
- Grounding `90%`

Pros:
- best explainability / grounding control
- very clean ablation behavior
- very clean counterfactual behavior
- grounding failures are rare and concentrated

Cons:
- forecast still clearly worse than V4
- still loses to simple forecast baselines
- not the best choice if predictive usefulness is the primary criterion

Recommended interpretation:
- best explainability-controlled variant
- strong evidence that the model can be disciplined by visible-variable constraints

## V7 - `v7_hybrid_topup`

Purpose:
- start from V4
- add only a light explainability top-up
- try to recover the best of V4 and V6 in one model

Key results:
- test forecast +1 `MAE=0.1690`, `RMSE=0.2249`, `MAPE=10.91%`
- Ablation `100%`
- Counterfactual `100%`
- Grounding `75%`

Pros:
- much better explainability than V4
- preserves clean ablation behavior
- preserves clean counterfactual behavior
- no large weather / tourism leakage pattern in grounding

Cons:
- forecast did not recover to V4 level
- grounding got worse again vs V6
- still loses to simple forecast baselines
- hybrid objective did not produce a true best-of-both-worlds merge

Recommended interpretation:
- useful hybrid attempt
- not the final recommended model

## V8 - `v8_forecast_pure_scratch`

Purpose:
- restart from the base model instead of inheriting V4
- focus the train split almost entirely on `forecast` plus a small `nowcast` anchor
- force shorter, more target-first forecast outputs

Key results:
- val forecast +1 `MAE=0.1108`, `RMSE=0.1526`, `MAPE=8.26%`
- test forecast +1 `MAE=0.1605`, `RMSE=0.2159`, `MAPE=11.61%`
- Ablation `100%`
- Counterfactual `100%`
- Grounding `50%`

Pros:
- best validation MAE among all fine-tuned variants
- slightly better test MAE than V5 / V6 / V7
- much more diverse forecast outputs than earlier branches
- clean evidence that warm-start inheritance was not necessary

Cons:
- still clearly worse than V4 on test
- still loses to `PERSIST_current_month`
- still loses to `TRAIN_corr_mean`
- still loses badly to `TRAIN_same_corr_month`
- grounded explanation quality degrades again

Recommended interpretation:
- useful forecast-focused experiment
- not strong enough to replace V4
- useful evidence that forecast improvement may require changes upstream of notebook 04 / 06 as well

## V9 - `v9_forecast_traffic_memory_scratch`

Purpose:
- rework the pipeline after a full `01 -> 06` review
- add traffic-memory lag features upstream in notebook 03
- redesign forecast prompts around current traffic shape + short traffic memory
- train forecast-only with a canonical JSON target

Key results:
- val forecast +1 `MAE=0.1175`, `RMSE=0.1455`, `MAPE=8.69%`
- test forecast +1 `MAE=0.1305`, `RMSE=0.1850`, `MAPE=9.39%`
- Ablation `100%`
- Counterfactual `100%`
- Grounding `95%`

Pros:
- best post-V4 forecast result
- clearly better than V5 / V6 / V7 / V8 on test
- beats `PERSIST_current_month`
- comes very close to `TRAIN_corr_mean`
- best grounding score of all LLM branches
- strongest overall compromise between forecast usefulness and disciplined behavior
- forecast outputs are more diverse than earlier branches

Cons:
- still does not beat V4 on pure forecast
- still does not beat `TRAIN_same_corr_month`
- still narrowly loses to `TRAIN_corr_mean`
- forecast text sometimes repeats the JSON object or appends extra prose
- Airport Road and Bypass Road remain difficult

Recommended interpretation:
- strongest single-model LLM branch overall
- best choice when one version must balance forecast quality and explainability discipline
- not the absolute best pure numeric forecast branch, because V4 is still slightly better there

## V10 - `v10_enriched_yoy_corridors`

Purpose:
- keep the V9 forecast-only scratch branch intact
- enrich prompts with year-over-year comparison
- add inter-corridor ranking for the current month
- test whether richer structured context improves forecast behavior

Key results:
- val forecast +1 `MAE=0.1079`, `RMSE=0.1604`, `MAPE=8.28%`
- test forecast +1 `MAE=0.1460`, `RMSE=0.1966`, `MAPE=10.64%`
- Ablation `100%`
- Counterfactual `95%`
- Grounding `90%`

Pros:
- best validation MAE of all branches except V8-like territory, and better than V9 on val
- still better on test than V5 / V6 / V7 / V8
- keeps strong grounding / ablation behavior
- useful evidence about prompt-complexity limits

Cons:
- clearly worse than V9 on test
- no longer beats `PERSIST_current_month`
- worse than `TRAIN_corr_mean`
- prediction diversity collapses again
- forecast outputs become noisier and more repetitive again
- extra context did not help the hardest corridors

Recommended interpretation:
- useful prompt-enrichment experiment
- not a new best model
- good evidence that more context is not automatically better for this task
- confirms that V9 was closer to the right prompt complexity level

## Final recommendation

If one model must be chosen as the **main single-model reference**:
- choose **V9** as the best overall compromise

If the project needs the **best pure forecast LLM**:
- choose **V4**

If the project needs a clear historical explainability milestone:
- keep **V6** as the earlier explainability-first reference, while noting that V9 later surpassed it on the proxy explainability scores

If discussing the iterative path honestly:
- present **V7** as the failed hybrid recovery attempt
- present **V8** as the useful forecast-only scratch experiment
- present **V9** as the first branch where upstream traffic-memory changes materially improved both forecast and grounding behavior
- present **V10** as the useful warning that extra comparative context (YoY + corridor ranking) can improve validation while still hurting test generalization
