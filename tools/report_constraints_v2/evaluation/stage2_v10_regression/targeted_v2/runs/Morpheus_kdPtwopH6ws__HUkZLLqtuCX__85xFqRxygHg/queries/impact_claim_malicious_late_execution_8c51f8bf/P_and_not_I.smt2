; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf224ec4_late_execution_occurred () Bool)
(declare-fun cbf224ec4_tx_pending_insufficient_gas () Bool)
(assert
 (= cbf224ec4_late_execution_occurred cbf224ec4_late_execution_occurred))
(assert
 (= cbf224ec4_tx_pending_insufficient_gas cbf224ec4_tx_pending_insufficient_gas))
(define-fun report_preconditions () Bool cbf224ec4_tx_pending_insufficient_gas)
(define-fun report_safety () Bool (=> cbf224ec4_tx_pending_insufficient_gas
    (not cbf224ec4_late_execution_occurred)))
(define-fun report_effects () Bool (and cbf224ec4_tx_pending_insufficient_gas
     (not (not cbf224ec4_late_execution_occurred))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
