; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun operator_has_creator_allowance () Bool)
(declare-fun start_timestamp_not_future () Bool)
(declare-fun creator_predeposited_rewards_available () Bool)
(declare-fun campaign_creation_rejected () Bool)
(declare-fun funds_pulled_for_ended_campaign () Bool)
(assert
 (= operator_has_creator_allowance operator_has_creator_allowance))
(assert
 (= start_timestamp_not_future start_timestamp_not_future))
(assert
 (= creator_predeposited_rewards_available creator_predeposited_rewards_available))
(assert
 (= campaign_creation_rejected campaign_creation_rejected))
(assert
 (= funds_pulled_for_ended_campaign funds_pulled_for_ended_campaign))
(define-fun report_preconditions () Bool (and operator_has_creator_allowance
     start_timestamp_not_future
     creator_predeposited_rewards_available))
(define-fun report_safety () Bool (=> (and operator_has_creator_allowance
         start_timestamp_not_future
         creator_predeposited_rewards_available)
    (and campaign_creation_rejected (not funds_pulled_for_ended_campaign))))
(define-fun report_effects () Bool (and operator_has_creator_allowance
     start_timestamp_not_future
     creator_predeposited_rewards_available
     (not (and campaign_creation_rejected (not funds_pulled_for_ended_campaign)))))
