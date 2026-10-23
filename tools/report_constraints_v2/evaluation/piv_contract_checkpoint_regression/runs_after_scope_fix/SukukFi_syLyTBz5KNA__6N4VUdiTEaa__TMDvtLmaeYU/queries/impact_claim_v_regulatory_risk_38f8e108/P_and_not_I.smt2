; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb5a83a3a_caller_has_validator_role () Bool)
(declare-fun cb5a83a3a_destination_is_kyc_verified () Bool)
(declare-fun cb5a83a3a_kyc_guarantee_reliable () Bool)
(declare-fun cb5a83a3a_source_is_kyc_verified () Bool)
(assert
 (= cb5a83a3a_caller_has_validator_role cb5a83a3a_caller_has_validator_role))
(assert
 (= cb5a83a3a_destination_is_kyc_verified cb5a83a3a_destination_is_kyc_verified))
(assert
 (= cb5a83a3a_kyc_guarantee_reliable cb5a83a3a_kyc_guarantee_reliable))
(assert
 (= cb5a83a3a_source_is_kyc_verified cb5a83a3a_source_is_kyc_verified))
(define-fun report_preconditions () Bool (and cb5a83a3a_caller_has_validator_role
     cb5a83a3a_source_is_kyc_verified
     (not cb5a83a3a_destination_is_kyc_verified)))
(define-fun report_safety () Bool (=> (and cb5a83a3a_caller_has_validator_role
         cb5a83a3a_source_is_kyc_verified
         (not cb5a83a3a_destination_is_kyc_verified))
    cb5a83a3a_kyc_guarantee_reliable))
(define-fun report_effects () Bool (and cb5a83a3a_caller_has_validator_role
     cb5a83a3a_source_is_kyc_verified
     (not cb5a83a3a_destination_is_kyc_verified)
     (not cb5a83a3a_kyc_guarantee_reliable)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
