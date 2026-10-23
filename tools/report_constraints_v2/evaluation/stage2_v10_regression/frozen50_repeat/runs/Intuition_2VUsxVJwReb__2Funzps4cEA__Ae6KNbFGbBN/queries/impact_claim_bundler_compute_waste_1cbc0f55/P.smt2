; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc77661c6_bundler_simulation_reverts () Bool)
(declare-fun cc77661c6_high_s_derivable () Bool)
(declare-fun cc77661c6_high_s_signature_length () Int)
(declare-fun cc77661c6_owner_signature_observable () Bool)
(declare-fun cc77661c6_returns_sig_validation_failed () Bool)
(declare-fun cc77661c6_signature_mismatch () Bool)
(assert
 (= cc77661c6_bundler_simulation_reverts cc77661c6_bundler_simulation_reverts))
(assert
 (= cc77661c6_high_s_derivable cc77661c6_high_s_derivable))
(assert
 (= cc77661c6_high_s_signature_length cc77661c6_high_s_signature_length))
(assert
 (= cc77661c6_owner_signature_observable cc77661c6_owner_signature_observable))
(assert
 (= cc77661c6_returns_sig_validation_failed cc77661c6_returns_sig_validation_failed))
(assert
 (= cc77661c6_signature_mismatch cc77661c6_signature_mismatch))
(define-fun report_preconditions () Bool (and cc77661c6_owner_signature_observable
     cc77661c6_high_s_derivable
     (= 65 cc77661c6_high_s_signature_length)))
(define-fun report_safety () Bool (=> (and cc77661c6_owner_signature_observable
         cc77661c6_high_s_derivable
         (= 65 cc77661c6_high_s_signature_length)
         cc77661c6_signature_mismatch)
    (and cc77661c6_returns_sig_validation_failed
         (not cc77661c6_bundler_simulation_reverts))))
(define-fun report_effects () Bool (and cc77661c6_owner_signature_observable
     cc77661c6_high_s_derivable
     (= 65 cc77661c6_high_s_signature_length)
     cc77661c6_signature_mismatch
     (not (and cc77661c6_returns_sig_validation_failed
               (not cc77661c6_bundler_simulation_reverts)))))
(assert report_preconditions)
(check-sat)
(get-model)
