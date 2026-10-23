; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c47444df2_factory_rejection_threshold () Int)
(declare-fun c47444df2_fee_accepted_by_factory () Bool)
(declare-fun c47444df2_max_fee_cap () Int)
(declare-fun c47444df2_swap_fee_value () Int)
(assert
 (= c47444df2_factory_rejection_threshold c47444df2_factory_rejection_threshold))
(assert
 (= c47444df2_fee_accepted_by_factory c47444df2_fee_accepted_by_factory))
(assert
 (= c47444df2_max_fee_cap c47444df2_max_fee_cap))
(assert
 (= c47444df2_swap_fee_value c47444df2_swap_fee_value))
(define-fun report_preconditions () Bool (> c47444df2_swap_fee_value c47444df2_factory_rejection_threshold))
(define-fun report_safety () Bool (=> (> c47444df2_swap_fee_value c47444df2_factory_rejection_threshold)
    (=> (and (<= c47444df2_swap_fee_value c47444df2_max_fee_cap)
             (> c47444df2_swap_fee_value c47444df2_factory_rejection_threshold))
        c47444df2_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and (> c47444df2_swap_fee_value c47444df2_factory_rejection_threshold)
     (<= c47444df2_swap_fee_value c47444df2_max_fee_cap)
     (> c47444df2_swap_fee_value c47444df2_factory_rejection_threshold)
     (not c47444df2_fee_accepted_by_factory)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
