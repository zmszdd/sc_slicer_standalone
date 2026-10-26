; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce8e42095_user_supply_share_pct () Int)
(declare-fun ce8e42095_user_venft_value_share_pct () Int)
(declare-fun ce8e42095_withdraw_reverted_zw () Bool)
(assert
 (= ce8e42095_user_supply_share_pct ce8e42095_user_supply_share_pct))
(assert
 (= ce8e42095_user_venft_value_share_pct ce8e42095_user_venft_value_share_pct))
(assert
 (= ce8e42095_withdraw_reverted_zw ce8e42095_withdraw_reverted_zw))
(define-fun report_preconditions () Bool (and (= 100 ce8e42095_user_supply_share_pct)
     (= 100 ce8e42095_user_venft_value_share_pct)))
(define-fun report_safety () Bool (=> (and (= 100 ce8e42095_user_supply_share_pct)
         (= 100 ce8e42095_user_venft_value_share_pct))
    (not ce8e42095_withdraw_reverted_zw)))
(define-fun report_effects () Bool ce8e42095_withdraw_reverted_zw)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
