; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cae632da9_batch_settlement_authorized () Bool)
(declare-fun cae632da9_funds_moved_to_non_kyc () Bool)
(declare-fun cae632da9_recipient_is_kyc_verified () Bool)
(declare-fun cae632da9_source_funds_kyc_verified () Bool)
(declare-fun cae632da9_standard_flow_kyc_gated () Bool)
(assert
 (= cae632da9_batch_settlement_authorized cae632da9_batch_settlement_authorized))
(assert
 (= cae632da9_funds_moved_to_non_kyc cae632da9_funds_moved_to_non_kyc))
(assert
 (= cae632da9_recipient_is_kyc_verified cae632da9_recipient_is_kyc_verified))
(assert
 (= cae632da9_source_funds_kyc_verified cae632da9_source_funds_kyc_verified))
(assert
 (= cae632da9_standard_flow_kyc_gated cae632da9_standard_flow_kyc_gated))
(define-fun report_preconditions () Bool (and cae632da9_batch_settlement_authorized
     cae632da9_standard_flow_kyc_gated
     cae632da9_source_funds_kyc_verified))
(define-fun report_safety () Bool (=> (and cae632da9_batch_settlement_authorized
         cae632da9_source_funds_kyc_verified)
    (or cae632da9_recipient_is_kyc_verified
        (not cae632da9_funds_moved_to_non_kyc))))
(define-fun report_effects () Bool (and cae632da9_batch_settlement_authorized
     cae632da9_source_funds_kyc_verified
     (not (or cae632da9_recipient_is_kyc_verified
              (not cae632da9_funds_moved_to_non_kyc)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
