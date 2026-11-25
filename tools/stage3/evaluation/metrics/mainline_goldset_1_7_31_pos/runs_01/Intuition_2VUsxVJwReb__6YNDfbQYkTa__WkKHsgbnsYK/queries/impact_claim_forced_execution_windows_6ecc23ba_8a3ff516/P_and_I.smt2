; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb3386e42_caller_is_malicious_bundler () Bool)
(declare-fun cb3386e42_forced_execution_window_observed () Bool)
(declare-fun cb3386e42_returned_valid_until () Int)
(declare-fun cb3386e42_signature_length_bytes () Int)
(declare-fun cb3386e42_signed_valid_until () Int)
(declare-fun cb3386e42_trailing_poison_bytes_present () Bool)
(assert
 (= cb3386e42_caller_is_malicious_bundler cb3386e42_caller_is_malicious_bundler))
(assert
 (= cb3386e42_forced_execution_window_observed cb3386e42_forced_execution_window_observed))
(assert
 (= cb3386e42_returned_valid_until cb3386e42_returned_valid_until))
(assert
 (= cb3386e42_signature_length_bytes cb3386e42_signature_length_bytes))
(assert
 (= cb3386e42_signed_valid_until cb3386e42_signed_valid_until))
(assert
 (= cb3386e42_trailing_poison_bytes_present cb3386e42_trailing_poison_bytes_present))
(define-fun report_preconditions () Bool (and (= 77 cb3386e42_signature_length_bytes)
     cb3386e42_trailing_poison_bytes_present
     cb3386e42_caller_is_malicious_bundler))
(define-fun report_safety () Bool (=> cb3386e42_trailing_poison_bytes_present
    (= cb3386e42_returned_valid_until cb3386e42_signed_valid_until)))
(define-fun report_effects () Bool (and cb3386e42_trailing_poison_bytes_present
     (not (= cb3386e42_returned_valid_until cb3386e42_signed_valid_until))
     cb3386e42_forced_execution_window_observed))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
