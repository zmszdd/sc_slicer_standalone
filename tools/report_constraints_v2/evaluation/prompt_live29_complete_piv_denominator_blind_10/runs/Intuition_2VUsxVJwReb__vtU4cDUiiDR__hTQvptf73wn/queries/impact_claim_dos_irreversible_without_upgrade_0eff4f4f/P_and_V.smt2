; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccce5719a_deposit_via_preview_mint () Bool)
(declare-fun ccce5719a_invariant_drift_after_deposit () Bool)
(declare-fun ccce5719a_preview_withdraw_panics () Bool)
(assert
 (= ccce5719a_deposit_via_preview_mint ccce5719a_deposit_via_preview_mint))
(assert
 (= ccce5719a_invariant_drift_after_deposit ccce5719a_invariant_drift_after_deposit))
(assert
 (= ccce5719a_preview_withdraw_panics ccce5719a_preview_withdraw_panics))
(define-fun report_preconditions () Bool ccce5719a_deposit_via_preview_mint)
(define-fun report_safety () Bool (=> ccce5719a_invariant_drift_after_deposit
    (=> (and ccce5719a_deposit_via_preview_mint
             ccce5719a_invariant_drift_after_deposit)
        (not ccce5719a_preview_withdraw_panics))))
(define-fun report_effects () Bool (and ccce5719a_invariant_drift_after_deposit
     ccce5719a_deposit_via_preview_mint
     ccce5719a_invariant_drift_after_deposit
     (not (not ccce5719a_preview_withdraw_panics))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
