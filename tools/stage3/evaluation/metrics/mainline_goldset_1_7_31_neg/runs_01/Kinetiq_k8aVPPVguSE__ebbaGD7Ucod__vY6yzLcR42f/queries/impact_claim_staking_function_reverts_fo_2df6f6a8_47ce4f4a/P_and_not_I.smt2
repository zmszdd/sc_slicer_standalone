; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced7c8b11_net_staked_includes_slashed () Bool)
(declare-fun ced7c8b11_stake_reverts_for_valid_amount () Bool)
(declare-fun ced7c8b11_staking_limit_positive () Bool)
(declare-fun ced7c8b11_validators_slashed_occurred () Bool)
(assert
 (= ced7c8b11_net_staked_includes_slashed ced7c8b11_net_staked_includes_slashed))
(assert
 (= ced7c8b11_stake_reverts_for_valid_amount ced7c8b11_stake_reverts_for_valid_amount))
(assert
 (= ced7c8b11_staking_limit_positive ced7c8b11_staking_limit_positive))
(assert
 (= ced7c8b11_validators_slashed_occurred ced7c8b11_validators_slashed_occurred))
(define-fun report_preconditions () Bool (and ced7c8b11_validators_slashed_occurred ced7c8b11_staking_limit_positive))
(define-fun report_safety () Bool ced7c8b11_net_staked_includes_slashed)
(define-fun report_effects () Bool (and ced7c8b11_staking_limit_positive
     (not ced7c8b11_net_staked_includes_slashed)
     ced7c8b11_stake_reverts_for_valid_amount))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
