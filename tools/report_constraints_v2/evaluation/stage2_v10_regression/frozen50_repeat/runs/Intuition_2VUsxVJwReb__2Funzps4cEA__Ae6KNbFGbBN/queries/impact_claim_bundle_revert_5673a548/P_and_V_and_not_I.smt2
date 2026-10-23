; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c82964ada_bundle_tx_failed () Bool)
(declare-fun c82964ada_high_s_derivable () Bool)
(declare-fun c82964ada_owner_sig_observable () Bool)
(declare-fun c82964ada_returns_sig_validation_failed () Bool)
(declare-fun c82964ada_sig_length_bytes () Int)
(declare-fun c82964ada_signature_mismatch () Bool)
(declare-fun c82964ada_validate_userop_reverted () Bool)
(assert
 (= c82964ada_bundle_tx_failed c82964ada_bundle_tx_failed))
(assert
 (= c82964ada_high_s_derivable c82964ada_high_s_derivable))
(assert
 (= c82964ada_owner_sig_observable c82964ada_owner_sig_observable))
(assert
 (= c82964ada_returns_sig_validation_failed c82964ada_returns_sig_validation_failed))
(assert
 (= c82964ada_sig_length_bytes c82964ada_sig_length_bytes))
(assert
 (= c82964ada_signature_mismatch c82964ada_signature_mismatch))
(assert
 (= c82964ada_validate_userop_reverted c82964ada_validate_userop_reverted))
(define-fun report_preconditions () Bool (and c82964ada_owner_sig_observable
     c82964ada_high_s_derivable
     (= 65 c82964ada_sig_length_bytes)))
(define-fun report_safety () Bool (=> (and c82964ada_signature_mismatch
         c82964ada_owner_sig_observable
         c82964ada_high_s_derivable
         (= 65 c82964ada_sig_length_bytes))
    (and c82964ada_returns_sig_validation_failed
         (not c82964ada_validate_userop_reverted)
         (not c82964ada_bundle_tx_failed))))
(define-fun report_effects () Bool (and c82964ada_signature_mismatch
     c82964ada_owner_sig_observable
     c82964ada_high_s_derivable
     (= 65 c82964ada_sig_length_bytes)
     (not (and c82964ada_returns_sig_validation_failed
               (not c82964ada_validate_userop_reverted)
               (not c82964ada_bundle_tx_failed)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
