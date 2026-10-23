; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdbfeec00_block_timestamp_at_creation () Int)
(declare-fun cdbfeec00_campaign_can_never_distribute_rewards () Bool)
(declare-fun cdbfeec00_campaign_duration () Int)
(declare-fun cdbfeec00_full_fees_paid () Bool)
(declare-fun cdbfeec00_start_timestamp () Int)
(assert
 (= cdbfeec00_block_timestamp_at_creation cdbfeec00_block_timestamp_at_creation))
(assert
 (= cdbfeec00_campaign_can_never_distribute_rewards cdbfeec00_campaign_can_never_distribute_rewards))
(assert
 (= cdbfeec00_campaign_duration cdbfeec00_campaign_duration))
(assert
 (= cdbfeec00_full_fees_paid cdbfeec00_full_fees_paid))
(assert
 (= cdbfeec00_start_timestamp cdbfeec00_start_timestamp))
(define-fun report_preconditions () Bool (and (<= 3600 cdbfeec00_campaign_duration)
     (< cdbfeec00_start_timestamp cdbfeec00_block_timestamp_at_creation)))
(define-fun report_safety () Bool (=> cdbfeec00_full_fees_paid
    (<= cdbfeec00_block_timestamp_at_creation cdbfeec00_start_timestamp)))
(define-fun report_effects () Bool (and cdbfeec00_full_fees_paid cdbfeec00_campaign_can_never_distribute_rewards))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
