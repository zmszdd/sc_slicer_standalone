; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c31058b8d_early_buyers_earning_amm_fees_indefinitely () Bool)
(declare-fun c31058b8d_rewards_stopped_after_graduation () Bool)
(declare-fun c31058b8d_token_graduated_to_amm () Bool)
(declare-fun c31058b8d_unlocked_after_graduation () Bool)
(declare-fun c31058b8d_unlocked_bonding_phase () Bool)
(assert
 (= c31058b8d_early_buyers_earning_amm_fees_indefinitely c31058b8d_early_buyers_earning_amm_fees_indefinitely))
(assert
 (= c31058b8d_rewards_stopped_after_graduation c31058b8d_rewards_stopped_after_graduation))
(assert
 (= c31058b8d_token_graduated_to_amm c31058b8d_token_graduated_to_amm))
(assert
 (= c31058b8d_unlocked_after_graduation c31058b8d_unlocked_after_graduation))
(assert
 (= c31058b8d_unlocked_bonding_phase c31058b8d_unlocked_bonding_phase))
(define-fun report_preconditions () Bool (and (not c31058b8d_unlocked_bonding_phase)
     c31058b8d_token_graduated_to_amm
     c31058b8d_unlocked_after_graduation))
(define-fun report_safety () Bool (=> c31058b8d_token_graduated_to_amm c31058b8d_rewards_stopped_after_graduation))
(define-fun report_effects () Bool (and c31058b8d_token_graduated_to_amm
     c31058b8d_early_buyers_earning_amm_fees_indefinitely
     (not c31058b8d_rewards_stopped_after_graduation)
     c31058b8d_token_graduated_to_amm
     c31058b8d_early_buyers_earning_amm_fees_indefinitely))
