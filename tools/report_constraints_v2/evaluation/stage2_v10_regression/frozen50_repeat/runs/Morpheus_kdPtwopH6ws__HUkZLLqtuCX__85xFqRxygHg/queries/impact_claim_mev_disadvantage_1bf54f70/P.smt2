; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c985f2f69_executed_after_deadline () Bool)
(declare-fun c985f2f69_mev_disadvantage_occurs () Bool)
(declare-fun c985f2f69_tx_pending_beyond_deadline () Bool)
(assert
 (= c985f2f69_executed_after_deadline c985f2f69_executed_after_deadline))
(assert
 (= c985f2f69_mev_disadvantage_occurs c985f2f69_mev_disadvantage_occurs))
(assert
 (= c985f2f69_tx_pending_beyond_deadline c985f2f69_tx_pending_beyond_deadline))
(define-fun report_preconditions () Bool c985f2f69_tx_pending_beyond_deadline)
(define-fun report_safety () Bool (=> c985f2f69_tx_pending_beyond_deadline
    (and (not c985f2f69_executed_after_deadline)
         (not c985f2f69_mev_disadvantage_occurs))))
(define-fun report_effects () Bool (and c985f2f69_tx_pending_beyond_deadline
     (not (and (not c985f2f69_executed_after_deadline)
               (not c985f2f69_mev_disadvantage_occurs)))))
(assert report_preconditions)
(check-sat)
(get-model)
