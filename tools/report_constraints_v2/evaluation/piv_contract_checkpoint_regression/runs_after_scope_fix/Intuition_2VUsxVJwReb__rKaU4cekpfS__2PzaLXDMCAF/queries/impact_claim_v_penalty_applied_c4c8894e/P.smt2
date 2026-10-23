; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c86e06db3_exemption_ratio () Int)
(declare-fun c86e06db3_first_claim_attempted () Bool)
(declare-fun c86e06db3_new_user_stakes_trust () Bool)
(declare-fun c86e06db3_no_multivault_interaction () Bool)
(declare-fun c86e06db3_raw_utilization_delta_first_epoch () Int)
(declare-fun c86e06db3_returned_utilization_ratio () Int)
(assert
 (= c86e06db3_exemption_ratio c86e06db3_exemption_ratio))
(assert
 (= c86e06db3_first_claim_attempted c86e06db3_first_claim_attempted))
(assert
 (= c86e06db3_new_user_stakes_trust c86e06db3_new_user_stakes_trust))
(assert
 (= c86e06db3_no_multivault_interaction c86e06db3_no_multivault_interaction))
(assert
 (= c86e06db3_raw_utilization_delta_first_epoch c86e06db3_raw_utilization_delta_first_epoch))
(assert
 (= c86e06db3_returned_utilization_ratio c86e06db3_returned_utilization_ratio))
(define-fun report_preconditions () Bool (and c86e06db3_new_user_stakes_trust
     c86e06db3_no_multivault_interaction
     c86e06db3_first_claim_attempted
     (= 0 c86e06db3_raw_utilization_delta_first_epoch)))
(define-fun report_safety () Bool (=> (and c86e06db3_new_user_stakes_trust
         c86e06db3_no_multivault_interaction
         c86e06db3_first_claim_attempted
         (= 0 c86e06db3_raw_utilization_delta_first_epoch))
    (= c86e06db3_returned_utilization_ratio c86e06db3_exemption_ratio)))
(define-fun report_effects () Bool (and c86e06db3_new_user_stakes_trust
     c86e06db3_no_multivault_interaction
     c86e06db3_first_claim_attempted
     (= 0 c86e06db3_raw_utilization_delta_first_epoch)
     (not (= c86e06db3_returned_utilization_ratio c86e06db3_exemption_ratio))))
(assert report_preconditions)
(check-sat)
(get-model)
