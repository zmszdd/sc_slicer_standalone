; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c9248d0_block_timestamp_at_creation () Int)
(declare-fun c9c9248d0_campaign_created_fully_elapsed () Bool)
(declare-fun c9c9248d0_campaign_end_timestamp () Int)
(declare-fun c9c9248d0_duration () Int)
(declare-fun c9c9248d0_full_fee_paid () Bool)
(declare-fun c9c9248d0_start_timestamp () Int)
(assert
 (= c9c9248d0_block_timestamp_at_creation c9c9248d0_block_timestamp_at_creation))
(assert
 (= c9c9248d0_campaign_created_fully_elapsed c9c9248d0_campaign_created_fully_elapsed))
(assert
 (= c9c9248d0_campaign_end_timestamp c9c9248d0_campaign_end_timestamp))
(assert
 (= c9c9248d0_duration c9c9248d0_duration))
(assert
 (= c9c9248d0_full_fee_paid c9c9248d0_full_fee_paid))
(assert
 (= c9c9248d0_start_timestamp c9c9248d0_start_timestamp))
(define-fun report_preconditions () Bool (and (< c9c9248d0_start_timestamp c9c9248d0_block_timestamp_at_creation)
     (<= 3600 c9c9248d0_duration)))
(define-fun report_safety () Bool (let ((a!1 (=> (and c9c9248d0_campaign_created_fully_elapsed
                    c9c9248d0_full_fee_paid)
               (=> (and (< c9c9248d0_start_timestamp
                           c9c9248d0_block_timestamp_at_creation)
                        (<= 3600 c9c9248d0_duration))
                   (< c9c9248d0_block_timestamp_at_creation
                      c9c9248d0_campaign_end_timestamp)))))
  (=> (= c9c9248d0_campaign_end_timestamp
         (+ c9c9248d0_start_timestamp c9c9248d0_duration))
      a!1)))
(define-fun report_effects () Bool (and (= c9c9248d0_campaign_end_timestamp
        (+ c9c9248d0_start_timestamp c9c9248d0_duration))
     c9c9248d0_campaign_created_fully_elapsed
     c9c9248d0_full_fee_paid
     (< c9c9248d0_start_timestamp c9c9248d0_block_timestamp_at_creation)
     (<= 3600 c9c9248d0_duration)
     (not (< c9c9248d0_block_timestamp_at_creation
             c9c9248d0_campaign_end_timestamp))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
