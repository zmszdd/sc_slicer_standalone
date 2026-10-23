; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c4c70ea5e_actual_pair_address () ReportAddress)
(declare-fun c4c70ea5e_end_rewards_completed () Bool)
(declare-fun c4c70ea5e_predicted_pair_address () ReportAddress)
(declare-fun c4c70ea5e_total_fee_share_zero () Bool)
(assert
 (= c4c70ea5e_actual_pair_address c4c70ea5e_actual_pair_address))
(assert
 (= c4c70ea5e_end_rewards_completed c4c70ea5e_end_rewards_completed))
(assert
 (= c4c70ea5e_predicted_pair_address c4c70ea5e_predicted_pair_address))
(assert
 (= c4c70ea5e_total_fee_share_zero c4c70ea5e_total_fee_share_zero))
(define-fun report_preconditions () Bool c4c70ea5e_total_fee_share_zero)
(define-fun report_safety () Bool (=> c4c70ea5e_total_fee_share_zero
    (and (= c4c70ea5e_predicted_pair_address c4c70ea5e_actual_pair_address)
         c4c70ea5e_end_rewards_completed)))
(define-fun report_effects () Bool (and c4c70ea5e_total_fee_share_zero
     (not (and (= c4c70ea5e_predicted_pair_address
                  c4c70ea5e_actual_pair_address)
               c4c70ea5e_end_rewards_completed))))
