; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbeff369a_bonus_reapplied_during_split () Bool)
(declare-fun cbeff369a_original_lock_is_sm_nft () Bool)
(declare-fun cbeff369a_unearned_bonus_tokens_farmed () Bool)
(assert
 (= cbeff369a_bonus_reapplied_during_split cbeff369a_bonus_reapplied_during_split))
(assert
 (= cbeff369a_original_lock_is_sm_nft cbeff369a_original_lock_is_sm_nft))
(assert
 (= cbeff369a_unearned_bonus_tokens_farmed cbeff369a_unearned_bonus_tokens_farmed))
(define-fun report_preconditions () Bool cbeff369a_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> cbeff369a_original_lock_is_sm_nft
    (not cbeff369a_bonus_reapplied_during_split)))
(define-fun report_effects () Bool (and cbeff369a_original_lock_is_sm_nft
     cbeff369a_bonus_reapplied_during_split
     cbeff369a_unearned_bonus_tokens_farmed))
(assert report_preconditions)
(check-sat)
(get-model)
