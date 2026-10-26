; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c01a3caab_atoken_supply_zero () Bool)
(declare-fun c01a3caab_attacker_holds_remaining_supply () Bool)
(declare-fun c01a3caab_cap_bypass_path_reachable () Bool)
(declare-fun c01a3caab_redeems_full_both_supplies () Bool)
(declare-fun c01a3caab_remaining_lp_funds_trapped () Bool)
(declare-fun c01a3caab_ztoken_supply_zero () Bool)
(assert
 (= c01a3caab_atoken_supply_zero c01a3caab_atoken_supply_zero))
(assert
 (= c01a3caab_attacker_holds_remaining_supply c01a3caab_attacker_holds_remaining_supply))
(assert
 (= c01a3caab_cap_bypass_path_reachable c01a3caab_cap_bypass_path_reachable))
(assert
 (= c01a3caab_redeems_full_both_supplies c01a3caab_redeems_full_both_supplies))
(assert
 (= c01a3caab_remaining_lp_funds_trapped c01a3caab_remaining_lp_funds_trapped))
(assert
 (= c01a3caab_ztoken_supply_zero c01a3caab_ztoken_supply_zero))
(define-fun report_preconditions () Bool (and (or c01a3caab_atoken_supply_zero c01a3caab_ztoken_supply_zero)
     c01a3caab_attacker_holds_remaining_supply))
(define-fun report_safety () Bool (=> c01a3caab_cap_bypass_path_reachable c01a3caab_redeems_full_both_supplies))
(define-fun report_effects () Bool c01a3caab_remaining_lp_funds_trapped)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
