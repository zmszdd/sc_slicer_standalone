; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3231d938_batch_moves_funds () Bool)
(declare-fun c3231d938_caller_is_validator () Bool)
(declare-fun c3231d938_funds_reach_non_kyc_destination () Bool)
(declare-fun c3231d938_holder_is_kyc_verified () Bool)
(declare-fun c3231d938_recipient_is_kyc_verified () Bool)
(assert
 (= c3231d938_batch_moves_funds c3231d938_batch_moves_funds))
(assert
 (= c3231d938_caller_is_validator c3231d938_caller_is_validator))
(assert
 (= c3231d938_funds_reach_non_kyc_destination c3231d938_funds_reach_non_kyc_destination))
(assert
 (= c3231d938_holder_is_kyc_verified c3231d938_holder_is_kyc_verified))
(assert
 (= c3231d938_recipient_is_kyc_verified c3231d938_recipient_is_kyc_verified))
(define-fun report_preconditions () Bool (and c3231d938_caller_is_validator
     c3231d938_recipient_is_kyc_verified
     c3231d938_holder_is_kyc_verified))
(define-fun report_safety () Bool (=> (and c3231d938_caller_is_validator
         c3231d938_batch_moves_funds
         c3231d938_holder_is_kyc_verified)
    (or c3231d938_recipient_is_kyc_verified
        (not c3231d938_funds_reach_non_kyc_destination))))
(define-fun report_effects () Bool (and c3231d938_caller_is_validator
     c3231d938_batch_moves_funds
     c3231d938_holder_is_kyc_verified
     (not (or c3231d938_recipient_is_kyc_verified
              (not c3231d938_funds_reach_non_kyc_destination)))))
(assert report_preconditions)
(check-sat)
(get-model)
