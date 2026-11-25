; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c50f17af0_original_lock_is_sm_nft () Bool)
(declare-fun c50f17af0_split_bonus_applied () Bool)
(declare-fun c50f17af0_unearned_bonus_tokens_farmed () Bool)
(assert
 (= c50f17af0_original_lock_is_sm_nft c50f17af0_original_lock_is_sm_nft))
(assert
 (= c50f17af0_split_bonus_applied c50f17af0_split_bonus_applied))
(assert
 (= c50f17af0_unearned_bonus_tokens_farmed c50f17af0_unearned_bonus_tokens_farmed))
(define-fun report_preconditions () Bool c50f17af0_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> c50f17af0_original_lock_is_sm_nft (not c50f17af0_split_bonus_applied)))
(define-fun report_effects () Bool (and c50f17af0_original_lock_is_sm_nft
     c50f17af0_split_bonus_applied
     c50f17af0_unearned_bonus_tokens_farmed))
(assert report_preconditions)
(check-sat)
(get-model)
