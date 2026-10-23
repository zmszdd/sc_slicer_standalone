; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc4fcd4e0_admin_can_flip_emergency () Bool)
(declare-fun cc4fcd4e0_emergency_flag_active () Bool)
(declare-fun cc4fcd4e0_nft_inaccessible_during_emergency () Bool)
(declare-fun cc4fcd4e0_nft_recovered () Bool)
(declare-fun cc4fcd4e0_staker_has_staked_nft () Bool)
(assert
 (= cc4fcd4e0_admin_can_flip_emergency cc4fcd4e0_admin_can_flip_emergency))
(assert
 (= cc4fcd4e0_emergency_flag_active cc4fcd4e0_emergency_flag_active))
(assert
 (= cc4fcd4e0_nft_inaccessible_during_emergency cc4fcd4e0_nft_inaccessible_during_emergency))
(assert
 (= cc4fcd4e0_nft_recovered cc4fcd4e0_nft_recovered))
(assert
 (= cc4fcd4e0_staker_has_staked_nft cc4fcd4e0_staker_has_staked_nft))
(define-fun report_preconditions () Bool (and cc4fcd4e0_staker_has_staked_nft
     cc4fcd4e0_emergency_flag_active
     cc4fcd4e0_admin_can_flip_emergency))
(define-fun report_safety () Bool (=> cc4fcd4e0_nft_inaccessible_during_emergency
    (=> (and cc4fcd4e0_staker_has_staked_nft cc4fcd4e0_emergency_flag_active)
        cc4fcd4e0_nft_recovered)))
(define-fun report_effects () Bool (and cc4fcd4e0_nft_inaccessible_during_emergency
     cc4fcd4e0_staker_has_staked_nft
     cc4fcd4e0_emergency_flag_active
     (not cc4fcd4e0_nft_recovered)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
