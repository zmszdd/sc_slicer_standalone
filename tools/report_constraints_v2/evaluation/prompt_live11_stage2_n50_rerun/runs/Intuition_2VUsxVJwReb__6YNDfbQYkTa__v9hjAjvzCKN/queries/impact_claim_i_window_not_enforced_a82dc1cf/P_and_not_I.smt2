; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9b182c01_has_valid_signed_op () Bool)
(declare-fun c9b182c01_hash_excludes_signature () Bool)
(declare-fun c9b182c01_signer_window_enforced () Bool)
(declare-fun c9b182c01_suffix_encodes_window () Bool)
(declare-fun c9b182c01_window_authenticated () Bool)
(assert
 (= c9b182c01_has_valid_signed_op c9b182c01_has_valid_signed_op))
(assert
 (= c9b182c01_hash_excludes_signature c9b182c01_hash_excludes_signature))
(assert
 (= c9b182c01_signer_window_enforced c9b182c01_signer_window_enforced))
(assert
 (= c9b182c01_suffix_encodes_window c9b182c01_suffix_encodes_window))
(assert
 (= c9b182c01_window_authenticated c9b182c01_window_authenticated))
(define-fun report_preconditions () Bool (and c9b182c01_has_valid_signed_op
     c9b182c01_suffix_encodes_window
     c9b182c01_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and c9b182c01_has_valid_signed_op
         c9b182c01_suffix_encodes_window
         c9b182c01_hash_excludes_signature)
    (and c9b182c01_window_authenticated c9b182c01_signer_window_enforced)))
(define-fun report_effects () Bool (and c9b182c01_has_valid_signed_op
     c9b182c01_suffix_encodes_window
     c9b182c01_hash_excludes_signature
     (not (and c9b182c01_window_authenticated c9b182c01_signer_window_enforced))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
