; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce7ee8e20_tx_executed_after_deadline () Bool)
(declare-fun ce7ee8e20_tx_pending_after_submission () Bool)
(assert
 (= ce7ee8e20_tx_executed_after_deadline ce7ee8e20_tx_executed_after_deadline))
(assert
 (= ce7ee8e20_tx_pending_after_submission ce7ee8e20_tx_pending_after_submission))
(define-fun report_preconditions () Bool ce7ee8e20_tx_pending_after_submission)
(define-fun report_safety () Bool (=> ce7ee8e20_tx_pending_after_submission
    (not ce7ee8e20_tx_executed_after_deadline)))
(define-fun report_effects () Bool (and ce7ee8e20_tx_pending_after_submission
     (not (not ce7ee8e20_tx_executed_after_deadline))))
