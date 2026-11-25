; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7cddc8d0_bonus_reapplied_during_split () Bool)
(declare-fun c7cddc8d0_original_lock_is_sm_nft () Bool)
(declare-fun c7cddc8d0_unearned_bonuses_received () Bool)
(assert
 (= c7cddc8d0_bonus_reapplied_during_split c7cddc8d0_bonus_reapplied_during_split))
(assert
 (= c7cddc8d0_original_lock_is_sm_nft c7cddc8d0_original_lock_is_sm_nft))
(assert
 (= c7cddc8d0_unearned_bonuses_received c7cddc8d0_unearned_bonuses_received))
(define-fun report_preconditions () Bool c7cddc8d0_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> c7cddc8d0_original_lock_is_sm_nft
    (not c7cddc8d0_bonus_reapplied_during_split)))
(define-fun report_effects () Bool (and c7cddc8d0_original_lock_is_sm_nft
     c7cddc8d0_bonus_reapplied_during_split
     c7cddc8d0_unearned_bonuses_received))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
