; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c713b1bfa_executed_later_by_mev () Bool)
(declare-fun c713b1bfa_tx_pending_not_mined () Bool)
(assert
 (= c713b1bfa_executed_later_by_mev c713b1bfa_executed_later_by_mev))
(assert
 (= c713b1bfa_tx_pending_not_mined c713b1bfa_tx_pending_not_mined))
(define-fun report_preconditions () Bool c713b1bfa_tx_pending_not_mined)
(define-fun report_safety () Bool (=> c713b1bfa_tx_pending_not_mined (not c713b1bfa_executed_later_by_mev)))
(define-fun report_effects () Bool (and c713b1bfa_tx_pending_not_mined (not (not c713b1bfa_executed_later_by_mev))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
