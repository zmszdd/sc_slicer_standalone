; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8902783b_caller_is_malicious_bundler () Bool)
(declare-fun c8902783b_signature_length_bytes () Int)
(declare-fun c8902783b_timestamps_bound_to_signature () Bool)
(declare-fun c8902783b_timestamps_controllable_without_invalidating_signature () Bool)
(declare-fun c8902783b_trailing_poison_bytes_present () Bool)
(declare-fun c8902783b_valid_until_is_uint48_max () Bool)
(assert
 (= c8902783b_caller_is_malicious_bundler c8902783b_caller_is_malicious_bundler))
(assert
 (= c8902783b_signature_length_bytes c8902783b_signature_length_bytes))
(assert
 (= c8902783b_timestamps_bound_to_signature c8902783b_timestamps_bound_to_signature))
(assert
 (= c8902783b_timestamps_controllable_without_invalidating_signature c8902783b_timestamps_controllable_without_invalidating_signature))
(assert
 (= c8902783b_trailing_poison_bytes_present c8902783b_trailing_poison_bytes_present))
(assert
 (= c8902783b_valid_until_is_uint48_max c8902783b_valid_until_is_uint48_max))
(define-fun report_preconditions () Bool (and (= 77 c8902783b_signature_length_bytes)
     c8902783b_trailing_poison_bytes_present
     c8902783b_caller_is_malicious_bundler))
(define-fun report_safety () Bool (=> c8902783b_trailing_poison_bytes_present
    (= c8902783b_timestamps_controllable_without_invalidating_signature
       c8902783b_timestamps_bound_to_signature)))
(define-fun report_effects () Bool (and c8902783b_trailing_poison_bytes_present
     (not (= c8902783b_timestamps_controllable_without_invalidating_signature
             c8902783b_timestamps_bound_to_signature))
     c8902783b_valid_until_is_uint48_max))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
