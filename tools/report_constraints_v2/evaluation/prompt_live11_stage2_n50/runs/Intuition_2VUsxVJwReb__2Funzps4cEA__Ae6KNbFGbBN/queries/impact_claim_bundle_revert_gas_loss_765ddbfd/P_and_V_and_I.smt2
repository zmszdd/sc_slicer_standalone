; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cecbe830a_bundle_revert_occurred () Bool)
(declare-fun cecbe830a_high_s_counterpart_derived () Bool)
(declare-fun cecbe830a_try_recover_invalid_signature_s () Bool)
(declare-fun cecbe830a_valid_owner_sig_observed () Bool)
(assert
 (= cecbe830a_bundle_revert_occurred cecbe830a_bundle_revert_occurred))
(assert
 (= cecbe830a_high_s_counterpart_derived cecbe830a_high_s_counterpart_derived))
(assert
 (= cecbe830a_try_recover_invalid_signature_s cecbe830a_try_recover_invalid_signature_s))
(assert
 (= cecbe830a_valid_owner_sig_observed cecbe830a_valid_owner_sig_observed))
(define-fun report_preconditions () Bool (and cecbe830a_valid_owner_sig_observed
     cecbe830a_high_s_counterpart_derived
     cecbe830a_try_recover_invalid_signature_s))
(define-fun report_safety () Bool (=> (and cecbe830a_valid_owner_sig_observed
         cecbe830a_high_s_counterpart_derived
         cecbe830a_try_recover_invalid_signature_s)
    (not cecbe830a_bundle_revert_occurred)))
(define-fun report_effects () Bool (and cecbe830a_valid_owner_sig_observed
     cecbe830a_high_s_counterpart_derived
     cecbe830a_try_recover_invalid_signature_s
     (not (not cecbe830a_bundle_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
