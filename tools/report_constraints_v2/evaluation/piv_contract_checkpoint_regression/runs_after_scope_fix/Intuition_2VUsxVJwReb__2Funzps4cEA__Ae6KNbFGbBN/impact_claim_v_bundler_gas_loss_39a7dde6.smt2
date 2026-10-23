; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cde9f07ad_bundler_gas_loss_occurred () Bool)
(declare-fun cde9f07ad_high_s_signature_derived () Bool)
(declare-fun cde9f07ad_high_s_signature_length_bytes () Int)
(declare-fun cde9f07ad_owner_signature_observed () Bool)
(declare-fun cde9f07ad_validate_userop_returns_sig_validation_failed () Bool)
(declare-fun cde9f07ad_validate_userop_reverts () Bool)
(assert
 (= cde9f07ad_bundler_gas_loss_occurred cde9f07ad_bundler_gas_loss_occurred))
(assert
 (= cde9f07ad_high_s_signature_derived cde9f07ad_high_s_signature_derived))
(assert
 (= cde9f07ad_high_s_signature_length_bytes cde9f07ad_high_s_signature_length_bytes))
(assert
 (= cde9f07ad_owner_signature_observed cde9f07ad_owner_signature_observed))
(assert
 (= cde9f07ad_validate_userop_returns_sig_validation_failed cde9f07ad_validate_userop_returns_sig_validation_failed))
(assert
 (= cde9f07ad_validate_userop_reverts cde9f07ad_validate_userop_reverts))
(define-fun report_preconditions () Bool (and cde9f07ad_owner_signature_observed
     cde9f07ad_high_s_signature_derived
     (= 65 cde9f07ad_high_s_signature_length_bytes)))
(define-fun report_safety () Bool (=> (and cde9f07ad_owner_signature_observed
         cde9f07ad_high_s_signature_derived
         (= 65 cde9f07ad_high_s_signature_length_bytes))
    (and cde9f07ad_validate_userop_returns_sig_validation_failed
         (not cde9f07ad_validate_userop_reverts)
         (not cde9f07ad_bundler_gas_loss_occurred))))
(define-fun report_effects () Bool (and cde9f07ad_owner_signature_observed
     cde9f07ad_high_s_signature_derived
     (= 65 cde9f07ad_high_s_signature_length_bytes)
     (not (and cde9f07ad_validate_userop_returns_sig_validation_failed
               (not cde9f07ad_validate_userop_reverts)
               (not cde9f07ad_bundler_gas_loss_occurred)))))
