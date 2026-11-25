; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c57877476_actual_hype_below_staking_limit () Bool)
(declare-fun c57877476_limit_metric_consistent_with_exchange_ratio () Bool)
(declare-fun c57877476_metrics_discrepancy_observed () Bool)
(declare-fun c57877476_slashed_funds_present () Bool)
(assert
 (= c57877476_actual_hype_below_staking_limit c57877476_actual_hype_below_staking_limit))
(assert
 (= c57877476_limit_metric_consistent_with_exchange_ratio c57877476_limit_metric_consistent_with_exchange_ratio))
(assert
 (= c57877476_metrics_discrepancy_observed c57877476_metrics_discrepancy_observed))
(assert
 (= c57877476_slashed_funds_present c57877476_slashed_funds_present))
(define-fun report_preconditions () Bool (and c57877476_slashed_funds_present c57877476_actual_hype_below_staking_limit))
(define-fun report_safety () Bool (=> c57877476_slashed_funds_present
    (= c57877476_limit_metric_consistent_with_exchange_ratio
       c57877476_metrics_discrepancy_observed)))
(define-fun report_effects () Bool (and c57877476_slashed_funds_present
     (not (= c57877476_limit_metric_consistent_with_exchange_ratio
             c57877476_metrics_discrepancy_observed))
     c57877476_metrics_discrepancy_observed
     c57877476_metrics_discrepancy_observed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
