; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce08e181c_original_lock_is_sm_nft () Bool)
(declare-fun ce08e181c_split_bonus_applied () Bool)
(declare-fun ce08e181c_unearned_bonuses_received () Bool)
(assert
 (= ce08e181c_original_lock_is_sm_nft ce08e181c_original_lock_is_sm_nft))
(assert
 (= ce08e181c_split_bonus_applied ce08e181c_split_bonus_applied))
(assert
 (= ce08e181c_unearned_bonuses_received ce08e181c_unearned_bonuses_received))
(define-fun report_preconditions () Bool ce08e181c_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> ce08e181c_original_lock_is_sm_nft (not ce08e181c_split_bonus_applied)))
(define-fun report_effects () Bool (and ce08e181c_original_lock_is_sm_nft
     ce08e181c_split_bonus_applied
     ce08e181c_unearned_bonuses_received))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
