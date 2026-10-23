; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff5f70f4_block_timestamp () Int)
(declare-fun cff5f70f4_campaign_can_distribute () Bool)
(declare-fun cff5f70f4_campaign_duration () Int)
(declare-fun cff5f70f4_full_fees_paid () Bool)
(declare-fun cff5f70f4_start_timestamp () Int)
(assert
 (= cff5f70f4_block_timestamp cff5f70f4_block_timestamp))
(assert
 (= cff5f70f4_campaign_can_distribute cff5f70f4_campaign_can_distribute))
(assert
 (= cff5f70f4_campaign_duration cff5f70f4_campaign_duration))
(assert
 (= cff5f70f4_full_fees_paid cff5f70f4_full_fees_paid))
(assert
 (= cff5f70f4_start_timestamp cff5f70f4_start_timestamp))
(define-fun report_preconditions () Bool (and (<= 0 cff5f70f4_start_timestamp)
     (< cff5f70f4_start_timestamp cff5f70f4_block_timestamp)
     (<= 3600 cff5f70f4_campaign_duration)))
(define-fun report_safety () Bool (=> (and cff5f70f4_full_fees_paid (not cff5f70f4_campaign_can_distribute))
    (=> (< cff5f70f4_start_timestamp cff5f70f4_block_timestamp)
        (>= cff5f70f4_start_timestamp cff5f70f4_block_timestamp))))
(define-fun report_effects () Bool (and cff5f70f4_full_fees_paid
     (not cff5f70f4_campaign_can_distribute)
     (< cff5f70f4_start_timestamp cff5f70f4_block_timestamp)
     (not (>= cff5f70f4_start_timestamp cff5f70f4_block_timestamp))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
