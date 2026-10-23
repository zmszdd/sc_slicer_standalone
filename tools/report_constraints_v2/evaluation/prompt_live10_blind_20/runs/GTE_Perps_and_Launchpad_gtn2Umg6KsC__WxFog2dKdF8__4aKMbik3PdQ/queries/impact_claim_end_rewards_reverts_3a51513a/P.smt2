; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c103a8f5a_actual_pair_address () ReportAddress)
(declare-fun c103a8f5a_end_rewards_completed () Bool)
(declare-fun c103a8f5a_predicted_pair_address () ReportAddress)
(declare-fun c103a8f5a_total_fee_share () Int)
(assert
 (= c103a8f5a_actual_pair_address c103a8f5a_actual_pair_address))
(assert
 (= c103a8f5a_end_rewards_completed c103a8f5a_end_rewards_completed))
(assert
 (= c103a8f5a_predicted_pair_address c103a8f5a_predicted_pair_address))
(assert
 (= c103a8f5a_total_fee_share c103a8f5a_total_fee_share))
(define-fun report_preconditions () Bool (= 0 c103a8f5a_total_fee_share))
(define-fun report_safety () Bool (=> (and (= 0 c103a8f5a_total_fee_share)
         (= c103a8f5a_predicted_pair_address c103a8f5a_actual_pair_address))
    c103a8f5a_end_rewards_completed))
(define-fun report_effects () Bool (and (= 0 c103a8f5a_total_fee_share)
     (= c103a8f5a_predicted_pair_address c103a8f5a_actual_pair_address)
     (not c103a8f5a_end_rewards_completed)))
(assert report_preconditions)
(check-sat)
(get-model)
