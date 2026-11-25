; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3204888d_first_deposit_shares () Int)
(declare-fun c3204888d_first_deposit_wei () Int)
(declare-fun c3204888d_integrator_preview_panic_revert () Bool)
(declare-fun c3204888d_offset18 () Int)
(declare-fun c3204888d_preview_withdraw_completes () Bool)
(declare-fun c3204888d_preview_withdraw_valid_input () Bool)
(declare-fun c3204888d_slope18 () Int)
(assert
 (= c3204888d_first_deposit_shares c3204888d_first_deposit_shares))
(assert
 (= c3204888d_first_deposit_wei c3204888d_first_deposit_wei))
(assert
 (= c3204888d_integrator_preview_panic_revert c3204888d_integrator_preview_panic_revert))
(assert
 (= c3204888d_offset18 c3204888d_offset18))
(assert
 (= c3204888d_preview_withdraw_completes c3204888d_preview_withdraw_completes))
(assert
 (= c3204888d_preview_withdraw_valid_input c3204888d_preview_withdraw_valid_input))
(assert
 (= c3204888d_slope18 c3204888d_slope18))
(define-fun report_preconditions () Bool (and (= 0 c3204888d_offset18)
     (= 2000000000000000000 c3204888d_slope18)
     (= 2 c3204888d_first_deposit_wei)
     (= 1414213562 c3204888d_first_deposit_shares)
     c3204888d_preview_withdraw_valid_input))
(define-fun report_safety () Bool c3204888d_preview_withdraw_completes)
(define-fun report_effects () Bool (and c3204888d_preview_withdraw_valid_input
     (not c3204888d_preview_withdraw_completes)
     c3204888d_integrator_preview_panic_revert))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
