; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cab569e87_bundler_compute_wasted () Bool)
(declare-fun cab569e87_bundler_simulation_reverts () Bool)
(declare-fun cab569e87_high_s_derivable () Bool)
(declare-fun cab569e87_high_s_signature_length_bytes () Int)
(declare-fun cab569e87_owner_signature_observed () Bool)
(declare-fun cab569e87_validate_userop_returns_failed () Bool)
(assert
 (= cab569e87_bundler_compute_wasted cab569e87_bundler_compute_wasted))
(assert
 (= cab569e87_bundler_simulation_reverts cab569e87_bundler_simulation_reverts))
(assert
 (= cab569e87_high_s_derivable cab569e87_high_s_derivable))
(assert
 (= cab569e87_high_s_signature_length_bytes cab569e87_high_s_signature_length_bytes))
(assert
 (= cab569e87_owner_signature_observed cab569e87_owner_signature_observed))
(assert
 (= cab569e87_validate_userop_returns_failed cab569e87_validate_userop_returns_failed))
(define-fun report_preconditions () Bool (and cab569e87_owner_signature_observed
     cab569e87_high_s_derivable
     (= 65 cab569e87_high_s_signature_length_bytes)))
(define-fun report_safety () Bool (=> (and cab569e87_owner_signature_observed
         cab569e87_high_s_derivable
         (= 65 cab569e87_high_s_signature_length_bytes))
    (and cab569e87_validate_userop_returns_failed
         (not cab569e87_bundler_simulation_reverts)
         (not cab569e87_bundler_compute_wasted))))
(define-fun report_effects () Bool (and cab569e87_owner_signature_observed
     cab569e87_high_s_derivable
     (= 65 cab569e87_high_s_signature_length_bytes)
     (not (and cab569e87_validate_userop_returns_failed
               (not cab569e87_bundler_simulation_reverts)
               (not cab569e87_bundler_compute_wasted)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
