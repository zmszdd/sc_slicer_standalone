; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun signature_uses_77_byte_format () Bool)
(declare-fun validity_outside_digest () Bool)
(declare-fun recovery_over_userophash_only () Bool)
(declare-fun attacker_rewrites_suffix () Bool)
(declare-fun signature_accepted_with_rewritten_window () Bool)
(assert
 (= signature_uses_77_byte_format signature_uses_77_byte_format))
(assert
 (= validity_outside_digest validity_outside_digest))
(assert
 (= recovery_over_userophash_only recovery_over_userophash_only))
(assert
 (= attacker_rewrites_suffix attacker_rewrites_suffix))
(assert
 (= signature_accepted_with_rewritten_window signature_accepted_with_rewritten_window))
(define-fun report_preconditions () Bool (and signature_uses_77_byte_format
     validity_outside_digest
     recovery_over_userophash_only
     attacker_rewrites_suffix))
(define-fun report_safety () Bool (=> (and signature_uses_77_byte_format
         validity_outside_digest
         recovery_over_userophash_only
         attacker_rewrites_suffix)
    (not signature_accepted_with_rewritten_window)))
(define-fun report_effects () Bool (and signature_uses_77_byte_format
     validity_outside_digest
     recovery_over_userophash_only
     attacker_rewrites_suffix
     (not (not signature_accepted_with_rewritten_window))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
