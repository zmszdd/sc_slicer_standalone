; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2eb34dfa_atoken_total_supply () Int)
(declare-fun c2eb34dfa_attacker_other_synth_balance () Int)
(declare-fun c2eb34dfa_collateral_drained_large_single_block () Bool)
(declare-fun c2eb34dfa_other_synth_total_supply () Int)
(declare-fun c2eb34dfa_swap_subject_to_redeem_cap () Bool)
(declare-fun c2eb34dfa_ztoken_total_supply () Int)
(assert
 (= c2eb34dfa_atoken_total_supply c2eb34dfa_atoken_total_supply))
(assert
 (= c2eb34dfa_attacker_other_synth_balance c2eb34dfa_attacker_other_synth_balance))
(assert
 (= c2eb34dfa_collateral_drained_large_single_block c2eb34dfa_collateral_drained_large_single_block))
(assert
 (= c2eb34dfa_other_synth_total_supply c2eb34dfa_other_synth_total_supply))
(assert
 (= c2eb34dfa_swap_subject_to_redeem_cap c2eb34dfa_swap_subject_to_redeem_cap))
(assert
 (= c2eb34dfa_ztoken_total_supply c2eb34dfa_ztoken_total_supply))
(define-fun report_preconditions () Bool (and (or (= 0 c2eb34dfa_atoken_total_supply)
         (= 0 c2eb34dfa_ztoken_total_supply))
     (= c2eb34dfa_attacker_other_synth_balance
        c2eb34dfa_other_synth_total_supply)))
(define-fun report_safety () Bool (=> c2eb34dfa_swap_subject_to_redeem_cap c2eb34dfa_swap_subject_to_redeem_cap))
(define-fun report_effects () Bool (and c2eb34dfa_collateral_drained_large_single_block
     c2eb34dfa_collateral_drained_large_single_block))
(assert report_preconditions)
(check-sat)
(get-model)
