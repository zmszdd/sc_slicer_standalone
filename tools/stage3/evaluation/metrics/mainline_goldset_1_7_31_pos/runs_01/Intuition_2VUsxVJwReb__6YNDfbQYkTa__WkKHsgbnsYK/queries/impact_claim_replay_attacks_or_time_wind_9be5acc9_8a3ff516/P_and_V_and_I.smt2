; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c29f0f361_caller_is_malicious_bundler () Bool)
(declare-fun c29f0f361_replay_or_time_window_bypass_occurs () Bool)
(declare-fun c29f0f361_signature_length_bytes () Int)
(declare-fun c29f0f361_timestamps_bound_to_signature () Bool)
(declare-fun c29f0f361_timestamps_controllable_without_invalidating_sig () Bool)
(declare-fun c29f0f361_trailing_poison_bytes_count () Int)
(assert
 (= c29f0f361_caller_is_malicious_bundler c29f0f361_caller_is_malicious_bundler))
(assert
 (= c29f0f361_replay_or_time_window_bypass_occurs c29f0f361_replay_or_time_window_bypass_occurs))
(assert
 (= c29f0f361_signature_length_bytes c29f0f361_signature_length_bytes))
(assert
 (= c29f0f361_timestamps_bound_to_signature c29f0f361_timestamps_bound_to_signature))
(assert
 (= c29f0f361_timestamps_controllable_without_invalidating_sig c29f0f361_timestamps_controllable_without_invalidating_sig))
(assert
 (= c29f0f361_trailing_poison_bytes_count c29f0f361_trailing_poison_bytes_count))
(define-fun report_preconditions () Bool (and (= 77 c29f0f361_signature_length_bytes)
     (<= 20 c29f0f361_trailing_poison_bytes_count)
     c29f0f361_caller_is_malicious_bundler
     c29f0f361_timestamps_controllable_without_invalidating_sig))
(define-fun report_safety () Bool (= c29f0f361_timestamps_controllable_without_invalidating_sig
   c29f0f361_timestamps_bound_to_signature))
(define-fun report_effects () Bool (and c29f0f361_timestamps_controllable_without_invalidating_sig
     (not (= c29f0f361_timestamps_controllable_without_invalidating_sig
             c29f0f361_timestamps_bound_to_signature))
     c29f0f361_replay_or_time_window_bypass_occurs
     c29f0f361_timestamps_controllable_without_invalidating_sig))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
