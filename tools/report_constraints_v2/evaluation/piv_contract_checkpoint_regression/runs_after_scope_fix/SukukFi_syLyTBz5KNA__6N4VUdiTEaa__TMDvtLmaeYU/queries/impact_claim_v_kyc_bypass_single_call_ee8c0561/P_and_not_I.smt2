; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5338751c_caller_has_validator_role () Bool)
(declare-fun c5338751c_destination_is_kyc_verified () Bool)
(declare-fun c5338751c_funds_moved_to_non_kyc_destination () Bool)
(declare-fun c5338751c_source_is_kyc_verified () Bool)
(assert
 (= c5338751c_caller_has_validator_role c5338751c_caller_has_validator_role))
(assert
 (= c5338751c_destination_is_kyc_verified c5338751c_destination_is_kyc_verified))
(assert
 (= c5338751c_funds_moved_to_non_kyc_destination c5338751c_funds_moved_to_non_kyc_destination))
(assert
 (= c5338751c_source_is_kyc_verified c5338751c_source_is_kyc_verified))
(define-fun report_preconditions () Bool (and c5338751c_caller_has_validator_role
     c5338751c_source_is_kyc_verified
     (not c5338751c_destination_is_kyc_verified)))
(define-fun report_safety () Bool (=> (and c5338751c_caller_has_validator_role
         c5338751c_source_is_kyc_verified
         (not c5338751c_destination_is_kyc_verified))
    (not c5338751c_funds_moved_to_non_kyc_destination)))
(define-fun report_effects () Bool (and c5338751c_caller_has_validator_role
     c5338751c_source_is_kyc_verified
     (not c5338751c_destination_is_kyc_verified)
     (not (not c5338751c_funds_moved_to_non_kyc_destination))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
