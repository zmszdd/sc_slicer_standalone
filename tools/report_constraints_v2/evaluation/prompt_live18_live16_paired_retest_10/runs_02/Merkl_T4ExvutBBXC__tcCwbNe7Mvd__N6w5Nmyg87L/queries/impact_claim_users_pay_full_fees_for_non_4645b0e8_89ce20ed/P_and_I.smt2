; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c9248d0_block_timestamp_at_creation () Int)
(declare-fun c9c9248d0_campaign_created_fully_elapsed () Bool)
(declare-fun c9c9248d0_campaign_end_timestamp () Int)
(declare-fun c9c9248d0_duration_seconds () Int)
(declare-fun c9c9248d0_full_fee_charged () Bool)
(declare-fun c9c9248d0_start_timestamp () Int)
(assert
 (= c9c9248d0_block_timestamp_at_creation c9c9248d0_block_timestamp_at_creation))
(assert
 (= c9c9248d0_campaign_created_fully_elapsed c9c9248d0_campaign_created_fully_elapsed))
(assert
 (= c9c9248d0_campaign_end_timestamp c9c9248d0_campaign_end_timestamp))
(assert
 (= c9c9248d0_duration_seconds c9c9248d0_duration_seconds))
(assert
 (= c9c9248d0_full_fee_charged c9c9248d0_full_fee_charged))
(assert
 (= c9c9248d0_start_timestamp c9c9248d0_start_timestamp))
(define-fun report_preconditions () Bool (and (< c9c9248d0_start_timestamp c9c9248d0_block_timestamp_at_creation)
     (<= 3600 c9c9248d0_duration_seconds)))
(define-fun report_safety () Bool (let ((a!1 (=> (and c9c9248d0_campaign_created_fully_elapsed
                    c9c9248d0_full_fee_charged)
               (=> (and (< c9c9248d0_start_timestamp
                           c9c9248d0_block_timestamp_at_creation)
                        (<= 3600 c9c9248d0_duration_seconds))
                   (< c9c9248d0_block_timestamp_at_creation
                      c9c9248d0_campaign_end_timestamp)))))
  (=> (= c9c9248d0_campaign_end_timestamp
         (+ c9c9248d0_start_timestamp c9c9248d0_duration_seconds))
      a!1)))
(define-fun report_effects () Bool (and (= c9c9248d0_campaign_end_timestamp
        (+ c9c9248d0_start_timestamp c9c9248d0_duration_seconds))
     c9c9248d0_campaign_created_fully_elapsed
     c9c9248d0_full_fee_charged
     (< c9c9248d0_start_timestamp c9c9248d0_block_timestamp_at_creation)
     (<= 3600 c9c9248d0_duration_seconds)
     (not (< c9c9248d0_block_timestamp_at_creation
             c9c9248d0_campaign_end_timestamp))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
