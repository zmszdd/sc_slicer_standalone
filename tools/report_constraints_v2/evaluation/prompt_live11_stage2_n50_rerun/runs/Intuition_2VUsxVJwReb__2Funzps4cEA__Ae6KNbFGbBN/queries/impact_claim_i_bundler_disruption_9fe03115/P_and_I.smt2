; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6b7b7a7e_bundler_disruption_occurs () Bool)
(declare-fun c6b7b7a7e_high_s_signature_derivable () Bool)
(declare-fun c6b7b7a7e_high_s_triggers_invalid_s_branch () Bool)
(declare-fun c6b7b7a7e_valid_owner_signature_exists () Bool)
(declare-fun c6b7b7a7e_validation_returns_sig_validation_failed_without_rever () Bool)
(assert
 (= c6b7b7a7e_bundler_disruption_occurs c6b7b7a7e_bundler_disruption_occurs))
(assert
 (= c6b7b7a7e_high_s_signature_derivable c6b7b7a7e_high_s_signature_derivable))
(assert
 (= c6b7b7a7e_high_s_triggers_invalid_s_branch c6b7b7a7e_high_s_triggers_invalid_s_branch))
(assert
 (= c6b7b7a7e_valid_owner_signature_exists c6b7b7a7e_valid_owner_signature_exists))
(assert
 (= c6b7b7a7e_validation_returns_sig_validation_failed_without_rever c6b7b7a7e_validation_returns_sig_validation_failed_without_rever))
(define-fun report_preconditions () Bool (and c6b7b7a7e_valid_owner_signature_exists
     c6b7b7a7e_high_s_signature_derivable
     c6b7b7a7e_high_s_triggers_invalid_s_branch))
(define-fun report_safety () Bool (=> (and c6b7b7a7e_valid_owner_signature_exists
         c6b7b7a7e_high_s_signature_derivable
         c6b7b7a7e_high_s_triggers_invalid_s_branch)
    (and c6b7b7a7e_validation_returns_sig_validation_failed_without_rever
         (not c6b7b7a7e_bundler_disruption_occurs))))
(define-fun report_effects () Bool (and c6b7b7a7e_valid_owner_signature_exists
     c6b7b7a7e_high_s_signature_derivable
     c6b7b7a7e_high_s_triggers_invalid_s_branch
     (not (and c6b7b7a7e_validation_returns_sig_validation_failed_without_rever
               (not c6b7b7a7e_bundler_disruption_occurs)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
