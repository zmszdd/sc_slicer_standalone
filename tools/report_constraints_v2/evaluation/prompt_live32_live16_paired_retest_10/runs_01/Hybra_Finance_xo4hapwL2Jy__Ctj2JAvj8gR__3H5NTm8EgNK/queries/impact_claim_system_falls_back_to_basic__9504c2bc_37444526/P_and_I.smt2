; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca6ca06ba_fallback_fee_applied () Int)
(declare-fun ca6ca06ba_fallback_used_basic_tick_spacing () Bool)
(declare-fun ca6ca06ba_max_fee_cap () Int)
(assert
 (= ca6ca06ba_fallback_fee_applied ca6ca06ba_fallback_fee_applied))
(assert
 (= ca6ca06ba_fallback_used_basic_tick_spacing ca6ca06ba_fallback_used_basic_tick_spacing))
(assert
 (= ca6ca06ba_max_fee_cap ca6ca06ba_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 ca6ca06ba_max_fee_cap))
(define-fun report_safety () Bool (=> ca6ca06ba_fallback_used_basic_tick_spacing
    (=> ca6ca06ba_fallback_used_basic_tick_spacing
        (= 100000 ca6ca06ba_fallback_fee_applied))))
(define-fun report_effects () Bool (and ca6ca06ba_fallback_used_basic_tick_spacing
     ca6ca06ba_fallback_used_basic_tick_spacing
     (not (= 100000 ca6ca06ba_fallback_fee_applied))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
