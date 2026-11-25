; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c09121ff9_original_lock_is_sm_nft_flag () Bool)
(declare-fun c09121ff9_resulting_nft_has_inflated_balances () Bool)
(declare-fun c09121ff9_split_applies_bonus () Bool)
(assert
 (= c09121ff9_original_lock_is_sm_nft_flag c09121ff9_original_lock_is_sm_nft_flag))
(assert
 (= c09121ff9_resulting_nft_has_inflated_balances c09121ff9_resulting_nft_has_inflated_balances))
(assert
 (= c09121ff9_split_applies_bonus c09121ff9_split_applies_bonus))
(define-fun report_preconditions () Bool c09121ff9_original_lock_is_sm_nft_flag)
(define-fun report_safety () Bool (=> c09121ff9_original_lock_is_sm_nft_flag (not c09121ff9_split_applies_bonus)))
(define-fun report_effects () Bool (and c09121ff9_original_lock_is_sm_nft_flag
     c09121ff9_split_applies_bonus
     c09121ff9_resulting_nft_has_inflated_balances))
(assert report_preconditions)
(check-sat)
(get-model)
