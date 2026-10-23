; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c556b485a_balance_movement_occurred () Bool)
(declare-fun c556b485a_caller_is_validator () Bool)
(declare-fun c556b485a_destination_is_kyc_verified () Bool)
(declare-fun c556b485a_source_is_kyc_verified () Bool)
(declare-fun c556b485a_token_paused () Bool)
(assert
 (= c556b485a_balance_movement_occurred c556b485a_balance_movement_occurred))
(assert
 (= c556b485a_caller_is_validator c556b485a_caller_is_validator))
(assert
 (= c556b485a_destination_is_kyc_verified c556b485a_destination_is_kyc_verified))
(assert
 (= c556b485a_source_is_kyc_verified c556b485a_source_is_kyc_verified))
(assert
 (= c556b485a_token_paused c556b485a_token_paused))
(define-fun report_preconditions () Bool (and c556b485a_caller_is_validator
     c556b485a_source_is_kyc_verified
     (not c556b485a_destination_is_kyc_verified)))
(define-fun report_safety () Bool (=> (and c556b485a_token_paused c556b485a_caller_is_validator)
    (not c556b485a_balance_movement_occurred)))
(define-fun report_effects () Bool (and c556b485a_token_paused
     c556b485a_caller_is_validator
     (not (not c556b485a_balance_movement_occurred))))
