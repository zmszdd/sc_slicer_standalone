; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6c79fe35_locked_balance_inflated_beyond_deposit () Bool)
(declare-fun c6c79fe35_original_lock_is_sm_nft () Bool)
(declare-fun c6c79fe35_split_bonus_applied () Bool)
(assert
 (= c6c79fe35_locked_balance_inflated_beyond_deposit c6c79fe35_locked_balance_inflated_beyond_deposit))
(assert
 (= c6c79fe35_original_lock_is_sm_nft c6c79fe35_original_lock_is_sm_nft))
(assert
 (= c6c79fe35_split_bonus_applied c6c79fe35_split_bonus_applied))
(define-fun report_preconditions () Bool c6c79fe35_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> c6c79fe35_original_lock_is_sm_nft (not c6c79fe35_split_bonus_applied)))
(define-fun report_effects () Bool (and c6c79fe35_original_lock_is_sm_nft
     c6c79fe35_split_bonus_applied
     c6c79fe35_locked_balance_inflated_beyond_deposit))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
