; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff5f70f4_block_timestamp_before_creation () Int)
(declare-fun cff5f70f4_campaign_can_distribute_rewards () Bool)
(declare-fun cff5f70f4_campaign_duration () Int)
(declare-fun cff5f70f4_full_fees_paid () Bool)
(declare-fun cff5f70f4_start_timestamp () Int)
(declare-fun cff5f70f4_start_timestamp_param_supplied_flag () Bool)
(assert
 (= cff5f70f4_block_timestamp_before_creation cff5f70f4_block_timestamp_before_creation))
(assert
 (= cff5f70f4_campaign_can_distribute_rewards cff5f70f4_campaign_can_distribute_rewards))
(assert
 (= cff5f70f4_campaign_duration cff5f70f4_campaign_duration))
(assert
 (= cff5f70f4_full_fees_paid cff5f70f4_full_fees_paid))
(assert
 (= cff5f70f4_start_timestamp cff5f70f4_start_timestamp))
(assert
 (= cff5f70f4_start_timestamp_param_supplied_flag cff5f70f4_start_timestamp_param_supplied_flag))
(define-fun report_preconditions () Bool (and cff5f70f4_start_timestamp_param_supplied_flag
     (< cff5f70f4_start_timestamp cff5f70f4_block_timestamp_before_creation)
     (<= 3600 cff5f70f4_campaign_duration)))
(define-fun report_safety () Bool (=> (and cff5f70f4_full_fees_paid
         (not cff5f70f4_campaign_can_distribute_rewards))
    (=> cff5f70f4_start_timestamp_param_supplied_flag
        (<= cff5f70f4_block_timestamp_before_creation cff5f70f4_start_timestamp))))
(define-fun report_effects () Bool (and cff5f70f4_full_fees_paid
     (not cff5f70f4_campaign_can_distribute_rewards)
     cff5f70f4_start_timestamp_param_supplied_flag
     (not (<= cff5f70f4_block_timestamp_before_creation
              cff5f70f4_start_timestamp))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
