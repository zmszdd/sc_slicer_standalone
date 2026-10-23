; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cab2f0215_empty_period_elapsed () Bool)
(declare-fun cab2f0215_full_epoch_stuck () Bool)
(declare-fun cab2f0215_notify_reward_called () Bool)
(declare-fun cab2f0215_total_supply_zero () Bool)
(assert
 (= cab2f0215_empty_period_elapsed cab2f0215_empty_period_elapsed))
(assert
 (= cab2f0215_full_epoch_stuck cab2f0215_full_epoch_stuck))
(assert
 (= cab2f0215_notify_reward_called cab2f0215_notify_reward_called))
(assert
 (= cab2f0215_total_supply_zero cab2f0215_total_supply_zero))
(define-fun report_preconditions () Bool (and cab2f0215_total_supply_zero
     cab2f0215_empty_period_elapsed
     cab2f0215_notify_reward_called))
(define-fun report_safety () Bool (=> (and cab2f0215_total_supply_zero
         cab2f0215_empty_period_elapsed
         cab2f0215_notify_reward_called)
    (not cab2f0215_full_epoch_stuck)))
(define-fun report_effects () Bool (and cab2f0215_total_supply_zero
     cab2f0215_empty_period_elapsed
     cab2f0215_notify_reward_called
     (not (not cab2f0215_full_epoch_stuck))))
(assert report_preconditions)
(check-sat)
(get-model)
