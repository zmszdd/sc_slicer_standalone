; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04e861e1_empty_period_elapsed () Bool)
(declare-fun c04e861e1_full_epoch_emissions_unclaimable () Bool)
(declare-fun c04e861e1_notify_reward_called_during_empty () Bool)
(declare-fun c04e861e1_total_supply_before_empty () Int)
(assert
 (= c04e861e1_empty_period_elapsed c04e861e1_empty_period_elapsed))
(assert
 (= c04e861e1_full_epoch_emissions_unclaimable c04e861e1_full_epoch_emissions_unclaimable))
(assert
 (= c04e861e1_notify_reward_called_during_empty c04e861e1_notify_reward_called_during_empty))
(assert
 (= c04e861e1_total_supply_before_empty c04e861e1_total_supply_before_empty))
(define-fun report_preconditions () Bool (and (= 0 c04e861e1_total_supply_before_empty)
     c04e861e1_empty_period_elapsed
     c04e861e1_notify_reward_called_during_empty))
(define-fun report_safety () Bool (=> (and (= 0 c04e861e1_total_supply_before_empty)
         c04e861e1_empty_period_elapsed
         c04e861e1_notify_reward_called_during_empty)
    (not c04e861e1_full_epoch_emissions_unclaimable)))
(define-fun report_effects () Bool (and (= 0 c04e861e1_total_supply_before_empty)
     c04e861e1_empty_period_elapsed
     c04e861e1_notify_reward_called_during_empty
     (not (not c04e861e1_full_epoch_emissions_unclaimable))))
