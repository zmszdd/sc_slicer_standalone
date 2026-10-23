; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10ebfe47_fast_redeem_min_amount_ld () Int)
(declare-fun c10ebfe47_local_decimals () Int)
(declare-fun c10ebfe47_redeem_amount () Int)
(declare-fun c10ebfe47_redeem_amount_has_dust () Bool)
(declare-fun c10ebfe47_redeem_unstake_succeeds () Bool)
(declare-fun c10ebfe47_shared_decimals () Int)
(declare-fun c10ebfe47_unstake_min_amount_ld () Int)
(assert
 (= c10ebfe47_fast_redeem_min_amount_ld c10ebfe47_fast_redeem_min_amount_ld))
(assert
 (= c10ebfe47_local_decimals c10ebfe47_local_decimals))
(assert
 (= c10ebfe47_redeem_amount c10ebfe47_redeem_amount))
(assert
 (= c10ebfe47_redeem_amount_has_dust c10ebfe47_redeem_amount_has_dust))
(assert
 (= c10ebfe47_redeem_unstake_succeeds c10ebfe47_redeem_unstake_succeeds))
(assert
 (= c10ebfe47_shared_decimals c10ebfe47_shared_decimals))
(assert
 (= c10ebfe47_unstake_min_amount_ld c10ebfe47_unstake_min_amount_ld))
(define-fun report_preconditions () Bool (and (> c10ebfe47_local_decimals c10ebfe47_shared_decimals)
     (= c10ebfe47_fast_redeem_min_amount_ld c10ebfe47_redeem_amount)
     (= c10ebfe47_unstake_min_amount_ld c10ebfe47_redeem_amount)
     c10ebfe47_redeem_amount_has_dust))
(define-fun report_safety () Bool (=> (and (= c10ebfe47_fast_redeem_min_amount_ld c10ebfe47_redeem_amount)
         (= c10ebfe47_unstake_min_amount_ld c10ebfe47_redeem_amount)
         c10ebfe47_redeem_amount_has_dust)
    c10ebfe47_redeem_unstake_succeeds))
(define-fun report_effects () Bool (and (= c10ebfe47_fast_redeem_min_amount_ld c10ebfe47_redeem_amount)
     (= c10ebfe47_unstake_min_amount_ld c10ebfe47_redeem_amount)
     c10ebfe47_redeem_amount_has_dust
     (not c10ebfe47_redeem_unstake_succeeds)))
