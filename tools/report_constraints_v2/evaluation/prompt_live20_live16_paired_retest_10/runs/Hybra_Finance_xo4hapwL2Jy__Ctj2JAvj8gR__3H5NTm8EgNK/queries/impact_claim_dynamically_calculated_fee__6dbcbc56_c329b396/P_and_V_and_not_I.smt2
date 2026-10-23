; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cce12701c_dynamic_fee () Int)
(declare-fun cce12701c_fee_accepted () Bool)
(declare-fun cce12701c_fee_rejected () Bool)
(declare-fun cce12701c_max_fee_cap () Int)
(assert
 (= cce12701c_dynamic_fee cce12701c_dynamic_fee))
(assert
 (= cce12701c_fee_accepted cce12701c_fee_accepted))
(assert
 (= cce12701c_fee_rejected cce12701c_fee_rejected))
(assert
 (= cce12701c_max_fee_cap cce12701c_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 cce12701c_max_fee_cap))
(define-fun report_safety () Bool (=> (<= cce12701c_dynamic_fee cce12701c_max_fee_cap) cce12701c_fee_accepted))
(define-fun report_effects () Bool (and cce12701c_fee_rejected (< 10 cce12701c_dynamic_fee)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
