; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c71825bf8_atoken_total_supply () Int)
(declare-fun c71825bf8_attacker_other_synth_balance () Int)
(declare-fun c71825bf8_cap_bypass_path_reachable () Bool)
(declare-fun c71825bf8_collateral_drained_single_block () Bool)
(declare-fun c71825bf8_other_synth_total_supply () Int)
(declare-fun c71825bf8_redeems_full_supply_of_both () Bool)
(declare-fun c71825bf8_ztoken_total_supply () Int)
(assert
 (= c71825bf8_atoken_total_supply c71825bf8_atoken_total_supply))
(assert
 (= c71825bf8_attacker_other_synth_balance c71825bf8_attacker_other_synth_balance))
(assert
 (= c71825bf8_cap_bypass_path_reachable c71825bf8_cap_bypass_path_reachable))
(assert
 (= c71825bf8_collateral_drained_single_block c71825bf8_collateral_drained_single_block))
(assert
 (= c71825bf8_other_synth_total_supply c71825bf8_other_synth_total_supply))
(assert
 (= c71825bf8_redeems_full_supply_of_both c71825bf8_redeems_full_supply_of_both))
(assert
 (= c71825bf8_ztoken_total_supply c71825bf8_ztoken_total_supply))
(define-fun report_preconditions () Bool (and (or (= 0 c71825bf8_atoken_total_supply)
         (= 0 c71825bf8_ztoken_total_supply))
     (= c71825bf8_attacker_other_synth_balance
        c71825bf8_other_synth_total_supply)))
(define-fun report_safety () Bool (=> c71825bf8_cap_bypass_path_reachable c71825bf8_redeems_full_supply_of_both))
(define-fun report_effects () Bool (and c71825bf8_collateral_drained_single_block
     c71825bf8_collateral_drained_single_block))
