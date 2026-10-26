; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c30de9ba2_atoken_supply_zero () Bool)
(declare-fun c30de9ba2_attacker_holds_entire_other_supply () Bool)
(declare-fun c30de9ba2_remaining_lp_funds_trapped () Bool)
(declare-fun c30de9ba2_swap_synth_to_base_subject_to_redeem_cap () Bool)
(declare-fun c30de9ba2_ztoken_supply_zero () Bool)
(assert
 (= c30de9ba2_atoken_supply_zero c30de9ba2_atoken_supply_zero))
(assert
 (= c30de9ba2_attacker_holds_entire_other_supply c30de9ba2_attacker_holds_entire_other_supply))
(assert
 (= c30de9ba2_remaining_lp_funds_trapped c30de9ba2_remaining_lp_funds_trapped))
(assert
 (= c30de9ba2_swap_synth_to_base_subject_to_redeem_cap c30de9ba2_swap_synth_to_base_subject_to_redeem_cap))
(assert
 (= c30de9ba2_ztoken_supply_zero c30de9ba2_ztoken_supply_zero))
(define-fun report_preconditions () Bool (and (or c30de9ba2_atoken_supply_zero c30de9ba2_ztoken_supply_zero)
     c30de9ba2_attacker_holds_entire_other_supply))
(define-fun report_safety () Bool (=> c30de9ba2_swap_synth_to_base_subject_to_redeem_cap
    c30de9ba2_swap_synth_to_base_subject_to_redeem_cap))
(define-fun report_effects () Bool c30de9ba2_remaining_lp_funds_trapped)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
