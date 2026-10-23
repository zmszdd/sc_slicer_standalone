; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04e861e1_empty_period_elapsed () Int)
(declare-fun c04e861e1_full_epoch_unclaimable () Bool)
(declare-fun c04e861e1_notify_reward_called () Bool)
(declare-fun c04e861e1_reward_duration () Int)
(declare-fun c04e861e1_total_supply_before_empty () Int)
(assert
 (= c04e861e1_empty_period_elapsed c04e861e1_empty_period_elapsed))
(assert
 (= c04e861e1_full_epoch_unclaimable c04e861e1_full_epoch_unclaimable))
(assert
 (= c04e861e1_notify_reward_called c04e861e1_notify_reward_called))
(assert
 (= c04e861e1_reward_duration c04e861e1_reward_duration))
(assert
 (= c04e861e1_total_supply_before_empty c04e861e1_total_supply_before_empty))
(define-fun report_preconditions () Bool (and (= 0 c04e861e1_total_supply_before_empty)
     (>= c04e861e1_empty_period_elapsed c04e861e1_reward_duration)
     c04e861e1_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 c04e861e1_total_supply_before_empty)
         (>= c04e861e1_empty_period_elapsed c04e861e1_reward_duration)
         c04e861e1_notify_reward_called)
    (not c04e861e1_full_epoch_unclaimable)))
(define-fun report_effects () Bool (and (= 0 c04e861e1_total_supply_before_empty)
     (>= c04e861e1_empty_period_elapsed c04e861e1_reward_duration)
     c04e861e1_notify_reward_called
     (not (not c04e861e1_full_epoch_unclaimable))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
