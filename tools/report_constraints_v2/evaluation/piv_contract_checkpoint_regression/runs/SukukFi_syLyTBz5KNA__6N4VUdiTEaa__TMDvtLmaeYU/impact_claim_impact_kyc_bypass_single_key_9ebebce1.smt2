; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5175c722_batch_moved_funds_to_unverified () Bool)
(declare-fun c5175c722_caller_is_validator () Bool)
(declare-fun c5175c722_destination_kyc_verified () Bool)
(declare-fun c5175c722_source_kyc_verified () Bool)
(declare-fun c5175c722_standard_paths_kyc_gated () Bool)
(assert
 (= c5175c722_batch_moved_funds_to_unverified c5175c722_batch_moved_funds_to_unverified))
(assert
 (= c5175c722_caller_is_validator c5175c722_caller_is_validator))
(assert
 (= c5175c722_destination_kyc_verified c5175c722_destination_kyc_verified))
(assert
 (= c5175c722_source_kyc_verified c5175c722_source_kyc_verified))
(assert
 (= c5175c722_standard_paths_kyc_gated c5175c722_standard_paths_kyc_gated))
(define-fun report_preconditions () Bool (and c5175c722_caller_is_validator
     c5175c722_standard_paths_kyc_gated
     c5175c722_source_kyc_verified
     (not c5175c722_destination_kyc_verified)))
(define-fun report_safety () Bool (=> (and c5175c722_caller_is_validator
         c5175c722_source_kyc_verified
         (not c5175c722_destination_kyc_verified))
    (not c5175c722_batch_moved_funds_to_unverified)))
(define-fun report_effects () Bool (and c5175c722_caller_is_validator
     c5175c722_source_kyc_verified
     (not c5175c722_destination_kyc_verified)
     (not (not c5175c722_batch_moved_funds_to_unverified))))
