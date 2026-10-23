; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbc921c83_first_epoch_yield_destroyed () Bool)
(declare-fun cbc921c83_is_first_claim () Bool)
(declare-fun cbc921c83_is_new_passive_staker () Bool)
(declare-fun cbc921c83_raw_utilization_delta () Int)
(assert
 (= cbc921c83_first_epoch_yield_destroyed cbc921c83_first_epoch_yield_destroyed))
(assert
 (= cbc921c83_is_first_claim cbc921c83_is_first_claim))
(assert
 (= cbc921c83_is_new_passive_staker cbc921c83_is_new_passive_staker))
(assert
 (= cbc921c83_raw_utilization_delta cbc921c83_raw_utilization_delta))
(define-fun report_preconditions () Bool (and cbc921c83_is_new_passive_staker
     cbc921c83_is_first_claim
     (= 0 cbc921c83_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and cbc921c83_is_new_passive_staker
         cbc921c83_is_first_claim
         (= 0 cbc921c83_raw_utilization_delta))
    (not cbc921c83_first_epoch_yield_destroyed)))
(define-fun report_effects () Bool (and cbc921c83_is_new_passive_staker
     cbc921c83_is_first_claim
     (= 0 cbc921c83_raw_utilization_delta)
     (not (not cbc921c83_first_epoch_yield_destroyed))))
(assert report_preconditions)
(check-sat)
(get-model)
