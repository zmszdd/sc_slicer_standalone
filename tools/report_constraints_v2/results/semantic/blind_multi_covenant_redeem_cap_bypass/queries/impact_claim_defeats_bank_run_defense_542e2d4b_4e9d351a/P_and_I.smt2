; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c672c05d6_attacker_holds_entire_remaining_supply () Bool)
(declare-fun c672c05d6_bank_run_defense_defeated () Bool)
(declare-fun c672c05d6_one_synth_supply_is_zero () Bool)
(declare-fun c672c05d6_redeem_cap_enforced_on_swap () Bool)
(declare-fun c672c05d6_swap_synth_to_base_executed () Bool)
(assert
 (= c672c05d6_attacker_holds_entire_remaining_supply c672c05d6_attacker_holds_entire_remaining_supply))
(assert
 (= c672c05d6_bank_run_defense_defeated c672c05d6_bank_run_defense_defeated))
(assert
 (= c672c05d6_one_synth_supply_is_zero c672c05d6_one_synth_supply_is_zero))
(assert
 (= c672c05d6_redeem_cap_enforced_on_swap c672c05d6_redeem_cap_enforced_on_swap))
(assert
 (= c672c05d6_swap_synth_to_base_executed c672c05d6_swap_synth_to_base_executed))
(define-fun report_preconditions () Bool (and c672c05d6_one_synth_supply_is_zero
     c672c05d6_attacker_holds_entire_remaining_supply))
(define-fun report_safety () Bool (=> c672c05d6_swap_synth_to_base_executed c672c05d6_redeem_cap_enforced_on_swap))
(define-fun report_effects () Bool c672c05d6_bank_run_defense_defeated)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
