; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c556b485a_batch_fund_movement_occurred () Bool)
(declare-fun c556b485a_caller_is_validator () Bool)
(declare-fun c556b485a_standard_flow_kyc_gated () Bool)
(declare-fun c556b485a_standard_transfer_pause_gated () Bool)
(declare-fun c556b485a_token_paused () Bool)
(declare-fun c556b485a_verified_holder_has_funds () Bool)
(assert
 (= c556b485a_batch_fund_movement_occurred c556b485a_batch_fund_movement_occurred))
(assert
 (= c556b485a_caller_is_validator c556b485a_caller_is_validator))
(assert
 (= c556b485a_standard_flow_kyc_gated c556b485a_standard_flow_kyc_gated))
(assert
 (= c556b485a_standard_transfer_pause_gated c556b485a_standard_transfer_pause_gated))
(assert
 (= c556b485a_token_paused c556b485a_token_paused))
(assert
 (= c556b485a_verified_holder_has_funds c556b485a_verified_holder_has_funds))
(define-fun report_preconditions () Bool (and c556b485a_caller_is_validator
     c556b485a_standard_flow_kyc_gated
     c556b485a_standard_transfer_pause_gated
     c556b485a_verified_holder_has_funds))
(define-fun report_safety () Bool (=> (and c556b485a_token_paused
         c556b485a_caller_is_validator
         c556b485a_verified_holder_has_funds)
    (not c556b485a_batch_fund_movement_occurred)))
(define-fun report_effects () Bool (and c556b485a_token_paused
     c556b485a_caller_is_validator
     c556b485a_verified_holder_has_funds
     (not (not c556b485a_batch_fund_movement_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
