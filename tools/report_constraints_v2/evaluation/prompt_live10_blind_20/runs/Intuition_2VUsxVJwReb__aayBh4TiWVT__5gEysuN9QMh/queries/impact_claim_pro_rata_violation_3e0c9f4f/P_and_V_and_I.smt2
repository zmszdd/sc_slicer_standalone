; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c87df72cf_lock_end_le_epoch_end () Bool)
(declare-fun c87df72cf_lock_reaches_natural_expiry () Bool)
(declare-fun c87df72cf_pro_rata_share () Int)
(declare-fun c87df72cf_user_bonded_in_final_epoch () Bool)
(declare-fun c87df72cf_user_received_rewards () Int)
(assert
 (= c87df72cf_lock_end_le_epoch_end c87df72cf_lock_end_le_epoch_end))
(assert
 (= c87df72cf_lock_reaches_natural_expiry c87df72cf_lock_reaches_natural_expiry))
(assert
 (= c87df72cf_pro_rata_share c87df72cf_pro_rata_share))
(assert
 (= c87df72cf_user_bonded_in_final_epoch c87df72cf_user_bonded_in_final_epoch))
(assert
 (= c87df72cf_user_received_rewards c87df72cf_user_received_rewards))
(define-fun report_preconditions () Bool (and c87df72cf_lock_reaches_natural_expiry
     c87df72cf_lock_end_le_epoch_end
     c87df72cf_user_bonded_in_final_epoch))
(define-fun report_safety () Bool (=> (and c87df72cf_lock_reaches_natural_expiry
         c87df72cf_lock_end_le_epoch_end
         c87df72cf_user_bonded_in_final_epoch)
    (>= c87df72cf_user_received_rewards c87df72cf_pro_rata_share)))
(define-fun report_effects () Bool (and c87df72cf_lock_reaches_natural_expiry
     c87df72cf_lock_end_le_epoch_end
     c87df72cf_user_bonded_in_final_epoch
     (not (>= c87df72cf_user_received_rewards c87df72cf_pro_rata_share))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
