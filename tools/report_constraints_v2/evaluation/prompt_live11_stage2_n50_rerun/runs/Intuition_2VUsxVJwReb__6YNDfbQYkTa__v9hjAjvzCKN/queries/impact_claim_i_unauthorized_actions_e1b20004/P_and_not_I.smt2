; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf739a358_has_valid_77byte_signed_op () Bool)
(declare-fun cf739a358_hash_excludes_signature () Bool)
(declare-fun cf739a358_suffix_encodes_window_metadata () Bool)
(declare-fun cf739a358_unauthorized_actions_occur () Bool)
(declare-fun cf739a358_window_covered_by_signature () Bool)
(assert
 (= cf739a358_has_valid_77byte_signed_op cf739a358_has_valid_77byte_signed_op))
(assert
 (= cf739a358_hash_excludes_signature cf739a358_hash_excludes_signature))
(assert
 (= cf739a358_suffix_encodes_window_metadata cf739a358_suffix_encodes_window_metadata))
(assert
 (= cf739a358_unauthorized_actions_occur cf739a358_unauthorized_actions_occur))
(assert
 (= cf739a358_window_covered_by_signature cf739a358_window_covered_by_signature))
(define-fun report_preconditions () Bool (and cf739a358_has_valid_77byte_signed_op
     cf739a358_suffix_encodes_window_metadata
     cf739a358_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and cf739a358_has_valid_77byte_signed_op
         cf739a358_suffix_encodes_window_metadata
         cf739a358_hash_excludes_signature)
    (and cf739a358_window_covered_by_signature
         (not cf739a358_unauthorized_actions_occur))))
(define-fun report_effects () Bool (and cf739a358_has_valid_77byte_signed_op
     cf739a358_suffix_encodes_window_metadata
     cf739a358_hash_excludes_signature
     (not (and cf739a358_window_covered_by_signature
               (not cf739a358_unauthorized_actions_occur)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
