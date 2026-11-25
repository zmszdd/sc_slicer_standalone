; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccf545ac9_bob_pnl () Int)
(declare-fun ccf545ac9_bob_positive_pnl () Bool)
(declare-fun ccf545ac9_fee_bypass_occurs () Bool)
(declare-fun ccf545ac9_performance_fee_paid_on_exit () Bool)
(declare-fun ccf545ac9_protocol_harm_occurs () Bool)
(declare-fun ccf545ac9_shares_transferable () Bool)
(assert
 (= ccf545ac9_bob_pnl ccf545ac9_bob_pnl))
(assert
 (= ccf545ac9_bob_positive_pnl ccf545ac9_bob_positive_pnl))
(assert
 (= ccf545ac9_fee_bypass_occurs ccf545ac9_fee_bypass_occurs))
(assert
 (= ccf545ac9_performance_fee_paid_on_exit ccf545ac9_performance_fee_paid_on_exit))
(assert
 (= ccf545ac9_protocol_harm_occurs ccf545ac9_protocol_harm_occurs))
(assert
 (= ccf545ac9_shares_transferable ccf545ac9_shares_transferable))
(define-fun report_preconditions () Bool (and ccf545ac9_bob_positive_pnl ccf545ac9_shares_transferable))
(define-fun report_safety () Bool (=> (= ccf545ac9_bob_pnl (- 20 18))
    (=> ccf545ac9_bob_positive_pnl ccf545ac9_performance_fee_paid_on_exit)))
(define-fun report_effects () Bool (and (= ccf545ac9_bob_pnl (- 20 18))
     ccf545ac9_bob_positive_pnl
     (not ccf545ac9_performance_fee_paid_on_exit)
     ccf545ac9_fee_bypass_occurs
     ccf545ac9_protocol_harm_occurs))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
