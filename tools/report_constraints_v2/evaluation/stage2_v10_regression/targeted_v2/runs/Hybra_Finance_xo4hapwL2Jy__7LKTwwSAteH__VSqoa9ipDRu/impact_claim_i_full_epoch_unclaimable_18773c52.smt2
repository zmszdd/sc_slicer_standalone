; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cabf0c33b_empty_period_elapsed () Bool)
(declare-fun cabf0c33b_full_epoch_unclaimable () Bool)
(declare-fun cabf0c33b_notify_reward_called () Bool)
(declare-fun cabf0c33b_total_supply () Int)
(assert
 (= cabf0c33b_empty_period_elapsed cabf0c33b_empty_period_elapsed))
(assert
 (= cabf0c33b_full_epoch_unclaimable cabf0c33b_full_epoch_unclaimable))
(assert
 (= cabf0c33b_notify_reward_called cabf0c33b_notify_reward_called))
(assert
 (= cabf0c33b_total_supply cabf0c33b_total_supply))
(define-fun report_preconditions () Bool (and (= 0 cabf0c33b_total_supply)
     cabf0c33b_empty_period_elapsed
     cabf0c33b_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 cabf0c33b_total_supply)
         cabf0c33b_empty_period_elapsed
         cabf0c33b_notify_reward_called)
    (not cabf0c33b_full_epoch_unclaimable)))
(define-fun report_effects () Bool (and (= 0 cabf0c33b_total_supply)
     cabf0c33b_empty_period_elapsed
     cabf0c33b_notify_reward_called
     (not (not cabf0c33b_full_epoch_unclaimable))))
