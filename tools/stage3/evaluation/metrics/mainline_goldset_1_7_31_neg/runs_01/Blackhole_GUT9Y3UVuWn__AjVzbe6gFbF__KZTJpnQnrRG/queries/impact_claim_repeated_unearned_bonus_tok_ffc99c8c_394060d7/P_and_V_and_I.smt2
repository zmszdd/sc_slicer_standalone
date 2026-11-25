; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfc0bedf2_additional_bonus_tokens_received () Bool)
(declare-fun cfc0bedf2_original_lock_is_sm_nft () Bool)
(declare-fun cfc0bedf2_split_applies_sm_nft_bonus () Bool)
(assert
 (= cfc0bedf2_additional_bonus_tokens_received cfc0bedf2_additional_bonus_tokens_received))
(assert
 (= cfc0bedf2_original_lock_is_sm_nft cfc0bedf2_original_lock_is_sm_nft))
(assert
 (= cfc0bedf2_split_applies_sm_nft_bonus cfc0bedf2_split_applies_sm_nft_bonus))
(define-fun report_preconditions () Bool cfc0bedf2_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> cfc0bedf2_original_lock_is_sm_nft
    (not cfc0bedf2_split_applies_sm_nft_bonus)))
(define-fun report_effects () Bool (and cfc0bedf2_original_lock_is_sm_nft
     cfc0bedf2_split_applies_sm_nft_bonus
     cfc0bedf2_additional_bonus_tokens_received
     cfc0bedf2_additional_bonus_tokens_received))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
