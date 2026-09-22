; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun maturity_time () Int)
(declare-fun block_timestamp () Int)
(declare-fun maturity_check_present () Bool)
(declare-fun never_initialized () Bool)
(declare-fun deposit_capable () Bool)
(declare-fun withdraw_completed () Bool)
(assert
 (= maturity_time maturity_time))
(assert
 (= block_timestamp block_timestamp))
(assert
 (= maturity_check_present maturity_check_present))
(assert
 (= never_initialized never_initialized))
(assert
 (= deposit_capable deposit_capable))
(assert
 (= withdraw_completed withdraw_completed))
(define-fun report_preconditions () Bool (and maturity_check_present
     never_initialized
     (= 0 maturity_time)
     (< 0 block_timestamp)
     deposit_capable))
(define-fun report_safety () Bool (=> withdraw_completed (< 0 maturity_time)))
(define-fun report_effects () Bool (and withdraw_completed (not (< 0 maturity_time))))
(assert report_preconditions)
(check-sat)
(get-model)
