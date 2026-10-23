; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caff8a7d2_high_s_derivable () Bool)
(declare-fun caff8a7d2_high_s_triggers_invalid_s () Bool)
(declare-fun caff8a7d2_owner_signature_valid () Bool)
(declare-fun caff8a7d2_validation_reverts () Bool)
(declare-fun caff8a7d2_wallet_serviced () Bool)
(assert
 (= caff8a7d2_high_s_derivable caff8a7d2_high_s_derivable))
(assert
 (= caff8a7d2_high_s_triggers_invalid_s caff8a7d2_high_s_triggers_invalid_s))
(assert
 (= caff8a7d2_owner_signature_valid caff8a7d2_owner_signature_valid))
(assert
 (= caff8a7d2_validation_reverts caff8a7d2_validation_reverts))
(assert
 (= caff8a7d2_wallet_serviced caff8a7d2_wallet_serviced))
(define-fun report_preconditions () Bool (and caff8a7d2_owner_signature_valid
     caff8a7d2_high_s_derivable
     caff8a7d2_high_s_triggers_invalid_s))
(define-fun report_safety () Bool (=> (and caff8a7d2_owner_signature_valid
         caff8a7d2_high_s_derivable
         caff8a7d2_high_s_triggers_invalid_s)
    (and (not caff8a7d2_validation_reverts) caff8a7d2_wallet_serviced)))
(define-fun report_effects () Bool (and caff8a7d2_owner_signature_valid
     caff8a7d2_high_s_derivable
     caff8a7d2_high_s_triggers_invalid_s
     (not (and (not caff8a7d2_validation_reverts) caff8a7d2_wallet_serviced))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
