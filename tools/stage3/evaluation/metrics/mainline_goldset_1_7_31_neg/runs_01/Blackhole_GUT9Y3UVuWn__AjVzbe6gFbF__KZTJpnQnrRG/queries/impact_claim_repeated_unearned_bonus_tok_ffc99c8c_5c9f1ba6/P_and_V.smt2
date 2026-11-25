; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce6241cb3_additional_bonus_tokens_received () Bool)
(declare-fun ce6241cb3_bonus_applied_during_split () Bool)
(declare-fun ce6241cb3_original_lock_is_sm_nft () Bool)
(assert
 (= ce6241cb3_additional_bonus_tokens_received ce6241cb3_additional_bonus_tokens_received))
(assert
 (= ce6241cb3_bonus_applied_during_split ce6241cb3_bonus_applied_during_split))
(assert
 (= ce6241cb3_original_lock_is_sm_nft ce6241cb3_original_lock_is_sm_nft))
(define-fun report_preconditions () Bool ce6241cb3_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> ce6241cb3_original_lock_is_sm_nft
    (not ce6241cb3_bonus_applied_during_split)))
(define-fun report_effects () Bool (and ce6241cb3_original_lock_is_sm_nft
     ce6241cb3_bonus_applied_during_split
     ce6241cb3_additional_bonus_tokens_received
     ce6241cb3_additional_bonus_tokens_received))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
