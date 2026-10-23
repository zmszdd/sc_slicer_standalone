; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c35ae278a_block_timestamp_at_creation () Int)
(declare-fun c35ae278a_campaign_duration () Int)
(declare-fun c35ae278a_full_fee_paid () Bool)
(declare-fun c35ae278a_start_timestamp () Int)
(assert
 (= c35ae278a_block_timestamp_at_creation c35ae278a_block_timestamp_at_creation))
(assert
 (= c35ae278a_campaign_duration c35ae278a_campaign_duration))
(assert
 (= c35ae278a_full_fee_paid c35ae278a_full_fee_paid))
(assert
 (= c35ae278a_start_timestamp c35ae278a_start_timestamp))
(define-fun report_preconditions () Bool (and (< c35ae278a_start_timestamp c35ae278a_block_timestamp_at_creation)
     (<= 3600 c35ae278a_campaign_duration)))
(define-fun report_safety () Bool (=> c35ae278a_full_fee_paid
    (=> c35ae278a_full_fee_paid
        (< c35ae278a_block_timestamp_at_creation c35ae278a_start_timestamp))))
(define-fun report_effects () Bool (and c35ae278a_full_fee_paid
     c35ae278a_full_fee_paid
     (not (< c35ae278a_block_timestamp_at_creation c35ae278a_start_timestamp))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
