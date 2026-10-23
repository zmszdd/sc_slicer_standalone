; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc77661c6_bundler_simulation_fails () Bool)
(declare-fun cc77661c6_high_s_counterpart_derived () Bool)
(declare-fun cc77661c6_high_s_invalid_signature_s () Bool)
(declare-fun cc77661c6_signature_validation_returns_failed () Bool)
(declare-fun cc77661c6_valid_owner_sig_observed () Bool)
(assert
 (= cc77661c6_bundler_simulation_fails cc77661c6_bundler_simulation_fails))
(assert
 (= cc77661c6_high_s_counterpart_derived cc77661c6_high_s_counterpart_derived))
(assert
 (= cc77661c6_high_s_invalid_signature_s cc77661c6_high_s_invalid_signature_s))
(assert
 (= cc77661c6_signature_validation_returns_failed cc77661c6_signature_validation_returns_failed))
(assert
 (= cc77661c6_valid_owner_sig_observed cc77661c6_valid_owner_sig_observed))
(define-fun report_preconditions () Bool (and cc77661c6_valid_owner_sig_observed
     cc77661c6_high_s_counterpart_derived
     cc77661c6_high_s_invalid_signature_s))
(define-fun report_safety () Bool (=> (and cc77661c6_valid_owner_sig_observed
         cc77661c6_high_s_counterpart_derived
         cc77661c6_high_s_invalid_signature_s)
    (and cc77661c6_signature_validation_returns_failed
         (not cc77661c6_bundler_simulation_fails))))
(define-fun report_effects () Bool (and cc77661c6_valid_owner_sig_observed
     cc77661c6_high_s_counterpart_derived
     cc77661c6_high_s_invalid_signature_s
     (not (and cc77661c6_signature_validation_returns_failed
               (not cc77661c6_bundler_simulation_fails)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
