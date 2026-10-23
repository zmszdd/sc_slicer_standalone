; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c55bd32c2_recover_error_invalid_s () Bool)
(declare-fun c55bd32c2_secp256k1n_half () Int)
(declare-fun c55bd32c2_signature_s () Int)
(declare-fun c55bd32c2_user_op_processed () Bool)
(declare-fun c55bd32c2_validate_signature_reverted () Bool)
(assert
 (= c55bd32c2_recover_error_invalid_s c55bd32c2_recover_error_invalid_s))
(assert
 (= c55bd32c2_secp256k1n_half c55bd32c2_secp256k1n_half))
(assert
 (= c55bd32c2_signature_s c55bd32c2_signature_s))
(assert
 (= c55bd32c2_user_op_processed c55bd32c2_user_op_processed))
(assert
 (= c55bd32c2_validate_signature_reverted c55bd32c2_validate_signature_reverted))
(define-fun report_preconditions () Bool (and (> c55bd32c2_signature_s c55bd32c2_secp256k1n_half)
     c55bd32c2_recover_error_invalid_s))
(define-fun report_safety () Bool (=> (and (> c55bd32c2_signature_s c55bd32c2_secp256k1n_half)
         c55bd32c2_recover_error_invalid_s)
    (and (not c55bd32c2_validate_signature_reverted)
         c55bd32c2_user_op_processed)))
(define-fun report_effects () Bool (and (> c55bd32c2_signature_s c55bd32c2_secp256k1n_half)
     c55bd32c2_recover_error_invalid_s
     (not (and (not c55bd32c2_validate_signature_reverted)
               c55bd32c2_user_op_processed))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
