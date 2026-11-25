; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c68927efb_bonus_reapplied_during_split () Bool)
(declare-fun c68927efb_original_lock_is_sm_nft () Bool)
(declare-fun c68927efb_resulting_nft_has_inflated_balances () Bool)
(declare-fun c68927efb_split_operation_occurs () Bool)
(assert
 (= c68927efb_bonus_reapplied_during_split c68927efb_bonus_reapplied_during_split))
(assert
 (= c68927efb_original_lock_is_sm_nft c68927efb_original_lock_is_sm_nft))
(assert
 (= c68927efb_resulting_nft_has_inflated_balances c68927efb_resulting_nft_has_inflated_balances))
(assert
 (= c68927efb_split_operation_occurs c68927efb_split_operation_occurs))
(define-fun report_preconditions () Bool c68927efb_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> (and c68927efb_original_lock_is_sm_nft c68927efb_split_operation_occurs)
    (not c68927efb_bonus_reapplied_during_split)))
(define-fun report_effects () Bool (and c68927efb_original_lock_is_sm_nft
     c68927efb_split_operation_occurs
     c68927efb_bonus_reapplied_during_split
     c68927efb_resulting_nft_has_inflated_balances))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
