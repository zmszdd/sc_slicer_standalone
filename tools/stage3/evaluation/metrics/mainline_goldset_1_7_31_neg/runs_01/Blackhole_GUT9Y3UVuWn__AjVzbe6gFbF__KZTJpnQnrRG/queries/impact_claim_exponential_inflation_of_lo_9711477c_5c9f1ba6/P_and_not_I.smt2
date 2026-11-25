; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c66c3db70_bonus_reapplied_during_split () Bool)
(declare-fun c66c3db70_locked_balance_inflated () Bool)
(declare-fun c66c3db70_original_lock_is_sm_nft () Bool)
(declare-fun c66c3db70_split_operation_occurs () Bool)
(assert
 (= c66c3db70_bonus_reapplied_during_split c66c3db70_bonus_reapplied_during_split))
(assert
 (= c66c3db70_locked_balance_inflated c66c3db70_locked_balance_inflated))
(assert
 (= c66c3db70_original_lock_is_sm_nft c66c3db70_original_lock_is_sm_nft))
(assert
 (= c66c3db70_split_operation_occurs c66c3db70_split_operation_occurs))
(define-fun report_preconditions () Bool c66c3db70_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> (and c66c3db70_original_lock_is_sm_nft c66c3db70_split_operation_occurs)
    (not c66c3db70_bonus_reapplied_during_split)))
(define-fun report_effects () Bool (and c66c3db70_original_lock_is_sm_nft
     c66c3db70_split_operation_occurs
     c66c3db70_bonus_reapplied_during_split
     c66c3db70_locked_balance_inflated))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
