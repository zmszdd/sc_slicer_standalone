; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c86a0ec03_deadline_check_enforced () Bool)
(declare-fun c86a0ec03_tx_may_be_delayed () Bool)
(assert
 (= c86a0ec03_deadline_check_enforced c86a0ec03_deadline_check_enforced))
(assert
 (= c86a0ec03_tx_may_be_delayed c86a0ec03_tx_may_be_delayed))
(define-fun report_preconditions () Bool c86a0ec03_tx_may_be_delayed)
(define-fun report_safety () Bool (=> c86a0ec03_tx_may_be_delayed c86a0ec03_deadline_check_enforced))
(define-fun report_effects () Bool (and c86a0ec03_tx_may_be_delayed (not c86a0ec03_deadline_check_enforced)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
