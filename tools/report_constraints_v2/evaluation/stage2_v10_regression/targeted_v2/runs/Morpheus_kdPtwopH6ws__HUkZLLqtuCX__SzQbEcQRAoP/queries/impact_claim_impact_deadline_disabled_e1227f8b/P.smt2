; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfd2f569a_caller_is_owner () Bool)
(declare-fun cfd2f569a_deadline_protection_disabled () Bool)
(declare-fun cfd2f569a_pending_tx_observable () Bool)
(assert
 (= cfd2f569a_caller_is_owner cfd2f569a_caller_is_owner))
(assert
 (= cfd2f569a_deadline_protection_disabled cfd2f569a_deadline_protection_disabled))
(assert
 (= cfd2f569a_pending_tx_observable cfd2f569a_pending_tx_observable))
(define-fun report_preconditions () Bool (and cfd2f569a_caller_is_owner cfd2f569a_pending_tx_observable))
(define-fun report_safety () Bool (=> (and cfd2f569a_caller_is_owner cfd2f569a_pending_tx_observable)
    (not cfd2f569a_deadline_protection_disabled)))
(define-fun report_effects () Bool (and cfd2f569a_caller_is_owner
     cfd2f569a_pending_tx_observable
     (not (not cfd2f569a_deadline_protection_disabled))))
(assert report_preconditions)
(check-sat)
(get-model)
