; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c57932ae6_eligible_rewards_final_epoch () Int)
(declare-fun c57932ae6_lock_end_le_epoch_end () Bool)
(declare-fun c57932ae6_lock_reaches_natural_expiry () Bool)
(declare-fun c57932ae6_pro_rata_share_final_epoch () Int)
(declare-fun c57932ae6_user_bonded_final_epoch () Bool)
(assert
 (= c57932ae6_eligible_rewards_final_epoch c57932ae6_eligible_rewards_final_epoch))
(assert
 (= c57932ae6_lock_end_le_epoch_end c57932ae6_lock_end_le_epoch_end))
(assert
 (= c57932ae6_lock_reaches_natural_expiry c57932ae6_lock_reaches_natural_expiry))
(assert
 (= c57932ae6_pro_rata_share_final_epoch c57932ae6_pro_rata_share_final_epoch))
(assert
 (= c57932ae6_user_bonded_final_epoch c57932ae6_user_bonded_final_epoch))
(define-fun report_preconditions () Bool (and c57932ae6_lock_reaches_natural_expiry
     c57932ae6_lock_end_le_epoch_end
     c57932ae6_user_bonded_final_epoch))
(define-fun report_safety () Bool (=> (and c57932ae6_lock_reaches_natural_expiry
         c57932ae6_lock_end_le_epoch_end
         c57932ae6_user_bonded_final_epoch)
    (= c57932ae6_eligible_rewards_final_epoch
       c57932ae6_pro_rata_share_final_epoch)))
(define-fun report_effects () Bool (and c57932ae6_lock_reaches_natural_expiry
     c57932ae6_lock_end_le_epoch_end
     c57932ae6_user_bonded_final_epoch
     (not (= c57932ae6_eligible_rewards_final_epoch
             c57932ae6_pro_rata_share_final_epoch))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
