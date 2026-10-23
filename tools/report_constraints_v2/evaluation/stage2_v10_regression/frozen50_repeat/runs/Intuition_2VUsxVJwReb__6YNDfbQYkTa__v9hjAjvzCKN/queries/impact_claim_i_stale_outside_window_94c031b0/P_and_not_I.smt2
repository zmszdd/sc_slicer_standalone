; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf4dfa789_executed_outside_approved_window () Bool)
(declare-fun cf4dfa789_has_valid_signed_op () Bool)
(declare-fun cf4dfa789_hash_excludes_signature () Bool)
(declare-fun cf4dfa789_signature_length_bytes () Int)
(declare-fun cf4dfa789_time_window_suffix_bytes () Int)
(assert
 (= cf4dfa789_executed_outside_approved_window cf4dfa789_executed_outside_approved_window))
(assert
 (= cf4dfa789_has_valid_signed_op cf4dfa789_has_valid_signed_op))
(assert
 (= cf4dfa789_hash_excludes_signature cf4dfa789_hash_excludes_signature))
(assert
 (= cf4dfa789_signature_length_bytes cf4dfa789_signature_length_bytes))
(assert
 (= cf4dfa789_time_window_suffix_bytes cf4dfa789_time_window_suffix_bytes))
(define-fun report_preconditions () Bool (and cf4dfa789_has_valid_signed_op
     (= 77 cf4dfa789_signature_length_bytes)
     (= 12 cf4dfa789_time_window_suffix_bytes)
     cf4dfa789_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and cf4dfa789_has_valid_signed_op
         (= 77 cf4dfa789_signature_length_bytes)
         (= 12 cf4dfa789_time_window_suffix_bytes)
         cf4dfa789_hash_excludes_signature)
    (not cf4dfa789_executed_outside_approved_window)))
(define-fun report_effects () Bool (and cf4dfa789_has_valid_signed_op
     (= 77 cf4dfa789_signature_length_bytes)
     (= 12 cf4dfa789_time_window_suffix_bytes)
     cf4dfa789_hash_excludes_signature
     (not (not cf4dfa789_executed_outside_approved_window))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
