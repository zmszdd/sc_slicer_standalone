; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun duration_is_multiple_of_epoch () Bool)
(declare-fun campaign_created () Bool)
(declare-fun epoch_duration_s () Int)
(declare-fun epoch_based_reward_calculation () Bool)
(declare-fun creator_controls_duration () Bool)
(assert
 (= duration_is_multiple_of_epoch duration_is_multiple_of_epoch))
(assert
 (= campaign_created campaign_created))
(assert
 (= epoch_duration_s epoch_duration_s))
(assert
 (= epoch_based_reward_calculation epoch_based_reward_calculation))
(assert
 (= creator_controls_duration creator_controls_duration))
(define-fun report_preconditions () Bool (and duration_is_multiple_of_epoch
     epoch_based_reward_calculation
     creator_controls_duration
     (= 3600 epoch_duration_s)))
(define-fun report_safety () Bool (=> campaign_created duration_is_multiple_of_epoch))
(define-fun report_effects () Bool (and campaign_created (not duration_is_multiple_of_epoch)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
