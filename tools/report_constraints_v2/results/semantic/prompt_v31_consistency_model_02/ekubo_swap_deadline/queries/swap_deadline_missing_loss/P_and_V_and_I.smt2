; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun swap_has_deadline () Bool)
(declare-fun can_remain_pending () Bool)
(declare-fun block_timestamp () Int)
(declare-fun deadline () Int)
(declare-fun swap_executed () Bool)
(declare-fun user_loss () Bool)
(assert
 (= swap_has_deadline swap_has_deadline))
(assert
 (= can_remain_pending can_remain_pending))
(assert
 (= block_timestamp block_timestamp))
(assert
 (= deadline deadline))
(assert
 (= swap_executed swap_executed))
(assert
 (= user_loss user_loss))
(define-fun report_preconditions () Bool (and (= swap_has_deadline false) can_remain_pending))
(define-fun report_safety () Bool (=> (> block_timestamp deadline) (not swap_executed)))
(define-fun report_effects () Bool user_loss)
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
