; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd8a9bbff_secp256k1n_half () Int)
(declare-fun cd8a9bbff_signature_s () Int)
(declare-fun cd8a9bbff_try_recover_invalid_s () Bool)
(declare-fun cd8a9bbff_validate_user_op_reverted () Bool)
(assert
 (= cd8a9bbff_secp256k1n_half cd8a9bbff_secp256k1n_half))
(assert
 (= cd8a9bbff_signature_s cd8a9bbff_signature_s))
(assert
 (= cd8a9bbff_try_recover_invalid_s cd8a9bbff_try_recover_invalid_s))
(assert
 (= cd8a9bbff_validate_user_op_reverted cd8a9bbff_validate_user_op_reverted))
(define-fun report_preconditions () Bool (and (> cd8a9bbff_signature_s cd8a9bbff_secp256k1n_half)
     cd8a9bbff_try_recover_invalid_s))
(define-fun report_safety () Bool (=> (and (> cd8a9bbff_signature_s cd8a9bbff_secp256k1n_half)
         cd8a9bbff_try_recover_invalid_s)
    (not cd8a9bbff_validate_user_op_reverted)))
(define-fun report_effects () Bool (and (> cd8a9bbff_signature_s cd8a9bbff_secp256k1n_half)
     cd8a9bbff_try_recover_invalid_s
     (not (not cd8a9bbff_validate_user_op_reverted))))
