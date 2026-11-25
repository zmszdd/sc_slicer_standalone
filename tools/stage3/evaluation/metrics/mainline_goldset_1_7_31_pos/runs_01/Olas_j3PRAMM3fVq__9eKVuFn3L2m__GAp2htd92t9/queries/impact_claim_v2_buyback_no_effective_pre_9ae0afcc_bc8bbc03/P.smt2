; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb23fe71a_buyback_callable_by_anyone_occurrence () Bool)
(declare-fun cb23fe71a_effective_pre_swap_price_validation_absent () Bool)
(declare-fun cb23fe71a_manipulated_spot_price_present () Bool)
(declare-fun cb23fe71a_manipulated_spot_price_rejected_before_swap () Bool)
(assert
 (= cb23fe71a_buyback_callable_by_anyone_occurrence cb23fe71a_buyback_callable_by_anyone_occurrence))
(assert
 (= cb23fe71a_effective_pre_swap_price_validation_absent cb23fe71a_effective_pre_swap_price_validation_absent))
(assert
 (= cb23fe71a_manipulated_spot_price_present cb23fe71a_manipulated_spot_price_present))
(assert
 (= cb23fe71a_manipulated_spot_price_rejected_before_swap cb23fe71a_manipulated_spot_price_rejected_before_swap))
(define-fun report_preconditions () Bool (and cb23fe71a_buyback_callable_by_anyone_occurrence
     cb23fe71a_manipulated_spot_price_present))
(define-fun report_safety () Bool cb23fe71a_manipulated_spot_price_rejected_before_swap)
(define-fun report_effects () Bool (and cb23fe71a_manipulated_spot_price_present
     (not cb23fe71a_manipulated_spot_price_rejected_before_swap)
     cb23fe71a_effective_pre_swap_price_validation_absent))
(assert report_preconditions)
(check-sat)
(get-model)
