; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca83a51cd_caller_is_malicious_bundler () Bool)
(declare-fun ca83a51cd_signature_length_bytes () Int)
(declare-fun ca83a51cd_timestamps_bound_to_signature () Bool)
(declare-fun ca83a51cd_timestamps_controllable_without_invalidating_sig () Bool)
(declare-fun ca83a51cd_trailing_poison_bytes_present () Bool)
(assert
 (= ca83a51cd_caller_is_malicious_bundler ca83a51cd_caller_is_malicious_bundler))
(assert
 (= ca83a51cd_signature_length_bytes ca83a51cd_signature_length_bytes))
(assert
 (= ca83a51cd_timestamps_bound_to_signature ca83a51cd_timestamps_bound_to_signature))
(assert
 (= ca83a51cd_timestamps_controllable_without_invalidating_sig ca83a51cd_timestamps_controllable_without_invalidating_sig))
(assert
 (= ca83a51cd_trailing_poison_bytes_present ca83a51cd_trailing_poison_bytes_present))
(define-fun report_preconditions () Bool (and (= 77 ca83a51cd_signature_length_bytes)
     ca83a51cd_trailing_poison_bytes_present
     ca83a51cd_caller_is_malicious_bundler))
(define-fun report_safety () Bool (=> ca83a51cd_trailing_poison_bytes_present
    (= ca83a51cd_timestamps_controllable_without_invalidating_sig
       ca83a51cd_timestamps_bound_to_signature)))
(define-fun report_effects () Bool (and ca83a51cd_trailing_poison_bytes_present
     (not (= ca83a51cd_timestamps_controllable_without_invalidating_sig
             ca83a51cd_timestamps_bound_to_signature))
     ca83a51cd_timestamps_controllable_without_invalidating_sig
     ca83a51cd_timestamps_controllable_without_invalidating_sig))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
