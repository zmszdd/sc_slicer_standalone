; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca1c67d3e_epoch_emissions_stuck () Bool)
(declare-fun ca1c67d3e_notify_reward_called () Bool)
(declare-fun ca1c67d3e_time_passes_no_deposits () Bool)
(declare-fun ca1c67d3e_total_supply () Int)
(assert
 (= ca1c67d3e_epoch_emissions_stuck ca1c67d3e_epoch_emissions_stuck))
(assert
 (= ca1c67d3e_notify_reward_called ca1c67d3e_notify_reward_called))
(assert
 (= ca1c67d3e_time_passes_no_deposits ca1c67d3e_time_passes_no_deposits))
(assert
 (= ca1c67d3e_total_supply ca1c67d3e_total_supply))
(define-fun report_preconditions () Bool (and (= 0 ca1c67d3e_total_supply)
     ca1c67d3e_time_passes_no_deposits
     ca1c67d3e_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 ca1c67d3e_total_supply)
         ca1c67d3e_time_passes_no_deposits
         ca1c67d3e_notify_reward_called)
    (not ca1c67d3e_epoch_emissions_stuck)))
(define-fun report_effects () Bool (and (= 0 ca1c67d3e_total_supply)
     ca1c67d3e_time_passes_no_deposits
     ca1c67d3e_notify_reward_called
     (not (not ca1c67d3e_epoch_emissions_stuck))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
