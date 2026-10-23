; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdc4805a4_fast_redeem_assets () Int)
(declare-fun cdc4805a4_fast_redeem_min_amount_ld () Int)
(declare-fun cdc4805a4_local_decimals () Int)
(declare-fun cdc4805a4_shared_decimals () Int)
(declare-fun cdc4805a4_slippage_exceeded_revert_occurred () Bool)
(declare-fun cdc4805a4_unstake_assets () Int)
(declare-fun cdc4805a4_unstake_min_amount_ld () Int)
(assert
 (= cdc4805a4_fast_redeem_assets cdc4805a4_fast_redeem_assets))
(assert
 (= cdc4805a4_fast_redeem_min_amount_ld cdc4805a4_fast_redeem_min_amount_ld))
(assert
 (= cdc4805a4_local_decimals cdc4805a4_local_decimals))
(assert
 (= cdc4805a4_shared_decimals cdc4805a4_shared_decimals))
(assert
 (= cdc4805a4_slippage_exceeded_revert_occurred cdc4805a4_slippage_exceeded_revert_occurred))
(assert
 (= cdc4805a4_unstake_assets cdc4805a4_unstake_assets))
(assert
 (= cdc4805a4_unstake_min_amount_ld cdc4805a4_unstake_min_amount_ld))
(define-fun report_preconditions () Bool (and (= 6 cdc4805a4_shared_decimals)
     (= cdc4805a4_fast_redeem_min_amount_ld cdc4805a4_fast_redeem_assets)
     (= cdc4805a4_unstake_min_amount_ld cdc4805a4_unstake_assets)))
(define-fun report_safety () Bool (=> (and (= 6 cdc4805a4_shared_decimals)
         (= 18 cdc4805a4_local_decimals)
         (= cdc4805a4_fast_redeem_min_amount_ld cdc4805a4_fast_redeem_assets)
         (= cdc4805a4_unstake_min_amount_ld cdc4805a4_unstake_assets))
    (not cdc4805a4_slippage_exceeded_revert_occurred)))
(define-fun report_effects () Bool (and (= 6 cdc4805a4_shared_decimals)
     (= 18 cdc4805a4_local_decimals)
     (= cdc4805a4_fast_redeem_min_amount_ld cdc4805a4_fast_redeem_assets)
     (= cdc4805a4_unstake_min_amount_ld cdc4805a4_unstake_assets)
     (not (not cdc4805a4_slippage_exceeded_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
