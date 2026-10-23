; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1bcaa211_fees_paid_without_completion () Bool)
(declare-fun c1bcaa211_min_amount_ld_fast_redeem () Int)
(declare-fun c1bcaa211_min_amount_ld_unstake () Int)
(declare-fun c1bcaa211_redeem_amount () Int)
(declare-fun c1bcaa211_shared_decimals () Int)
(assert
 (= c1bcaa211_fees_paid_without_completion c1bcaa211_fees_paid_without_completion))
(assert
 (= c1bcaa211_min_amount_ld_fast_redeem c1bcaa211_min_amount_ld_fast_redeem))
(assert
 (= c1bcaa211_min_amount_ld_unstake c1bcaa211_min_amount_ld_unstake))
(assert
 (= c1bcaa211_redeem_amount c1bcaa211_redeem_amount))
(assert
 (= c1bcaa211_shared_decimals c1bcaa211_shared_decimals))
(define-fun report_preconditions () Bool (and (= 6 c1bcaa211_shared_decimals)
     (= c1bcaa211_min_amount_ld_fast_redeem c1bcaa211_redeem_amount)
     (= c1bcaa211_min_amount_ld_unstake c1bcaa211_redeem_amount)
     (distinct 0 (mod c1bcaa211_redeem_amount 1000000000000))))
(define-fun report_safety () Bool (=> (and (= c1bcaa211_min_amount_ld_fast_redeem c1bcaa211_redeem_amount)
         (= c1bcaa211_min_amount_ld_unstake c1bcaa211_redeem_amount)
         (distinct 0 (mod c1bcaa211_redeem_amount 1000000000000)))
    (not c1bcaa211_fees_paid_without_completion)))
(define-fun report_effects () Bool (and (= c1bcaa211_min_amount_ld_fast_redeem c1bcaa211_redeem_amount)
     (= c1bcaa211_min_amount_ld_unstake c1bcaa211_redeem_amount)
     (distinct 0 (mod c1bcaa211_redeem_amount 1000000000000))
     (not (not c1bcaa211_fees_paid_without_completion))))
(assert report_preconditions)
(check-sat)
(get-model)
