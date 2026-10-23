; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7dc043ff_block_timestamp_at_creation () Int)
(declare-fun c7dc043ff_campaign_duration () Int)
(declare-fun c7dc043ff_full_fees_paid_for_nondistributing_campaign () Bool)
(declare-fun c7dc043ff_start_timestamp () Int)
(assert
 (= c7dc043ff_block_timestamp_at_creation c7dc043ff_block_timestamp_at_creation))
(assert
 (= c7dc043ff_campaign_duration c7dc043ff_campaign_duration))
(assert
 (= c7dc043ff_full_fees_paid_for_nondistributing_campaign c7dc043ff_full_fees_paid_for_nondistributing_campaign))
(assert
 (= c7dc043ff_start_timestamp c7dc043ff_start_timestamp))
(define-fun report_preconditions () Bool (and (<= 3600 c7dc043ff_campaign_duration)
     (< c7dc043ff_start_timestamp c7dc043ff_block_timestamp_at_creation)))
(define-fun report_safety () Bool (=> (< c7dc043ff_start_timestamp c7dc043ff_block_timestamp_at_creation)
    (< c7dc043ff_block_timestamp_at_creation c7dc043ff_start_timestamp)))
(define-fun report_effects () Bool c7dc043ff_full_fees_paid_for_nondistributing_campaign)
(assert report_preconditions)
(check-sat)
(get-model)
