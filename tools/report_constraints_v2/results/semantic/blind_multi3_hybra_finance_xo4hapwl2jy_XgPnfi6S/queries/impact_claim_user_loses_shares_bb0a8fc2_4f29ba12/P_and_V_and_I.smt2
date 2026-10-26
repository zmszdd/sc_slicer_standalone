; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cedd7c049_shares_burned () Bool)
(declare-fun cedd7c049_user_supply_share_pct () Int)
(declare-fun cedd7c049_user_venft_value_share_pct () Int)
(declare-fun cedd7c049_withdrawal_completed () Bool)
(assert
 (= cedd7c049_shares_burned cedd7c049_shares_burned))
(assert
 (= cedd7c049_user_supply_share_pct cedd7c049_user_supply_share_pct))
(assert
 (= cedd7c049_user_venft_value_share_pct cedd7c049_user_venft_value_share_pct))
(assert
 (= cedd7c049_withdrawal_completed cedd7c049_withdrawal_completed))
(define-fun report_preconditions () Bool (and (= 100 cedd7c049_user_supply_share_pct)
     (= 100 cedd7c049_user_venft_value_share_pct)))
(define-fun report_safety () Bool (=> cedd7c049_shares_burned cedd7c049_withdrawal_completed))
(define-fun report_effects () Bool (and cedd7c049_shares_burned
     (not cedd7c049_withdrawal_completed)
     cedd7c049_shares_burned))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
