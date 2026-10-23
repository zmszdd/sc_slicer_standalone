; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c25467387_min_amount_ld () Int)
(declare-fun c25467387_shared_decimals () Int)
(declare-fun c25467387_slippage_exceeded_revert_occurred () Bool)
(declare-fun c25467387_transfer_amount_ld () Int)
(assert
 (= c25467387_min_amount_ld c25467387_min_amount_ld))
(assert
 (= c25467387_shared_decimals c25467387_shared_decimals))
(assert
 (= c25467387_slippage_exceeded_revert_occurred c25467387_slippage_exceeded_revert_occurred))
(assert
 (= c25467387_transfer_amount_ld c25467387_transfer_amount_ld))
(define-fun report_preconditions () Bool (and (= 6 c25467387_shared_decimals)
     (= c25467387_min_amount_ld c25467387_transfer_amount_ld)
     (distinct 0 (mod c25467387_transfer_amount_ld 1000000000000))))
(define-fun report_safety () Bool (=> (and (= c25467387_min_amount_ld c25467387_transfer_amount_ld)
         (distinct 0 (mod c25467387_transfer_amount_ld 1000000000000)))
    (not c25467387_slippage_exceeded_revert_occurred)))
(define-fun report_effects () Bool (and (= c25467387_min_amount_ld c25467387_transfer_amount_ld)
     (distinct 0 (mod c25467387_transfer_amount_ld 1000000000000))
     (not (not c25467387_slippage_exceeded_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
