; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd96879bc_net_staked_includes_slashed () Bool)
(declare-fun cd96879bc_stake_reverts () Bool)
(declare-fun cd96879bc_staking_limit_positive () Bool)
(declare-fun cd96879bc_validators_slashed_occurred () Bool)
(assert
 (= cd96879bc_net_staked_includes_slashed cd96879bc_net_staked_includes_slashed))
(assert
 (= cd96879bc_stake_reverts cd96879bc_stake_reverts))
(assert
 (= cd96879bc_staking_limit_positive cd96879bc_staking_limit_positive))
(assert
 (= cd96879bc_validators_slashed_occurred cd96879bc_validators_slashed_occurred))
(define-fun report_preconditions () Bool (and cd96879bc_validators_slashed_occurred cd96879bc_staking_limit_positive))
(define-fun report_safety () Bool cd96879bc_net_staked_includes_slashed)
(define-fun report_effects () Bool (and cd96879bc_staking_limit_positive
     (not cd96879bc_net_staked_includes_slashed)
     cd96879bc_stake_reverts
     cd96879bc_stake_reverts))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
