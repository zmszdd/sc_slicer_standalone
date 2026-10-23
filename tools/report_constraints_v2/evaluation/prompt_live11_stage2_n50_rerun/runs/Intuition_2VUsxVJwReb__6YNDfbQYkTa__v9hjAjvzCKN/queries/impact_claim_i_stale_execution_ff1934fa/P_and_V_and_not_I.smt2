; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc67038ce_executed_outside_window () Bool)
(declare-fun cc67038ce_has_valid_signed_op () Bool)
(declare-fun cc67038ce_hash_excludes_signature () Bool)
(declare-fun cc67038ce_suffix_encodes_window () Bool)
(assert
 (= cc67038ce_executed_outside_window cc67038ce_executed_outside_window))
(assert
 (= cc67038ce_has_valid_signed_op cc67038ce_has_valid_signed_op))
(assert
 (= cc67038ce_hash_excludes_signature cc67038ce_hash_excludes_signature))
(assert
 (= cc67038ce_suffix_encodes_window cc67038ce_suffix_encodes_window))
(define-fun report_preconditions () Bool (and cc67038ce_has_valid_signed_op
     cc67038ce_suffix_encodes_window
     cc67038ce_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and cc67038ce_has_valid_signed_op
         cc67038ce_suffix_encodes_window
         cc67038ce_hash_excludes_signature)
    (not cc67038ce_executed_outside_window)))
(define-fun report_effects () Bool (and cc67038ce_has_valid_signed_op
     cc67038ce_suffix_encodes_window
     cc67038ce_hash_excludes_signature
     (not (not cc67038ce_executed_outside_window))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
