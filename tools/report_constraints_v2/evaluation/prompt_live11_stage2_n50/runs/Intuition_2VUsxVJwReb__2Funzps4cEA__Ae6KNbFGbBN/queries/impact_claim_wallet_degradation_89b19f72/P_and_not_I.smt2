; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6a6d355e_high_s_counterpart_derived () Bool)
(declare-fun c6a6d355e_high_s_invalid_signature_s () Bool)
(declare-fun c6a6d355e_sig_validation_returns_failed_no_revert () Bool)
(declare-fun c6a6d355e_valid_owner_sig_observed () Bool)
(declare-fun c6a6d355e_wallet_serviced_by_bundlers () Bool)
(assert
 (= c6a6d355e_high_s_counterpart_derived c6a6d355e_high_s_counterpart_derived))
(assert
 (= c6a6d355e_high_s_invalid_signature_s c6a6d355e_high_s_invalid_signature_s))
(assert
 (= c6a6d355e_sig_validation_returns_failed_no_revert c6a6d355e_sig_validation_returns_failed_no_revert))
(assert
 (= c6a6d355e_valid_owner_sig_observed c6a6d355e_valid_owner_sig_observed))
(assert
 (= c6a6d355e_wallet_serviced_by_bundlers c6a6d355e_wallet_serviced_by_bundlers))
(define-fun report_preconditions () Bool (and c6a6d355e_valid_owner_sig_observed
     c6a6d355e_high_s_counterpart_derived
     c6a6d355e_high_s_invalid_signature_s))
(define-fun report_safety () Bool (=> (and c6a6d355e_valid_owner_sig_observed
         c6a6d355e_high_s_counterpart_derived
         c6a6d355e_high_s_invalid_signature_s)
    (and c6a6d355e_sig_validation_returns_failed_no_revert
         c6a6d355e_wallet_serviced_by_bundlers)))
(define-fun report_effects () Bool (and c6a6d355e_valid_owner_sig_observed
     c6a6d355e_high_s_counterpart_derived
     c6a6d355e_high_s_invalid_signature_s
     (not (and c6a6d355e_sig_validation_returns_failed_no_revert
               c6a6d355e_wallet_serviced_by_bundlers))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
