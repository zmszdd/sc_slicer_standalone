; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c60639406_block_timestamp_before_creation () Int)
(declare-fun c60639406_campaign_duration () Int)
(declare-fun c60639406_campaign_fully_elapsed_at_creation () Bool)
(declare-fun c60639406_full_fees_paid_for_campaign () Bool)
(declare-fun c60639406_start_timestamp () Int)
(declare-fun c60639406_start_timestamp_supplied () Bool)
(assert
 (= c60639406_block_timestamp_before_creation c60639406_block_timestamp_before_creation))
(assert
 (= c60639406_campaign_duration c60639406_campaign_duration))
(assert
 (= c60639406_campaign_fully_elapsed_at_creation c60639406_campaign_fully_elapsed_at_creation))
(assert
 (= c60639406_full_fees_paid_for_campaign c60639406_full_fees_paid_for_campaign))
(assert
 (= c60639406_start_timestamp c60639406_start_timestamp))
(assert
 (= c60639406_start_timestamp_supplied c60639406_start_timestamp_supplied))
(define-fun report_preconditions () Bool (and c60639406_start_timestamp_supplied
     (< c60639406_start_timestamp c60639406_block_timestamp_before_creation)
     (<= 3600 c60639406_campaign_duration)))
(define-fun report_safety () Bool (=> (and c60639406_campaign_fully_elapsed_at_creation
         c60639406_full_fees_paid_for_campaign)
    (=> (and c60639406_start_timestamp_supplied
             (<= 3600 c60639406_campaign_duration))
        (< c60639406_block_timestamp_before_creation c60639406_start_timestamp))))
(define-fun report_effects () Bool (and c60639406_campaign_fully_elapsed_at_creation
     c60639406_full_fees_paid_for_campaign
     c60639406_start_timestamp_supplied
     (<= 3600 c60639406_campaign_duration)
     (not (< c60639406_block_timestamp_before_creation
             c60639406_start_timestamp))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
