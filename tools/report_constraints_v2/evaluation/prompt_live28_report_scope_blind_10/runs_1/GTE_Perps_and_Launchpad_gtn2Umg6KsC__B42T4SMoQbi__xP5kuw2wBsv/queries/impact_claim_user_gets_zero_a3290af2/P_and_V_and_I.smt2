; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c56e7a029_pending_quote_rewards_before () Int)
(declare-fun c56e7a029_total_shares_before () Int)
(declare-fun c56e7a029_user_rewards_received_after () Int)
(declare-fun c56e7a029_user_shares_before () Int)
(declare-fun c56e7a029_zero_rewards () Int)
(assert
 (= c56e7a029_pending_quote_rewards_before c56e7a029_pending_quote_rewards_before))
(assert
 (= c56e7a029_total_shares_before c56e7a029_total_shares_before))
(assert
 (= c56e7a029_user_rewards_received_after c56e7a029_user_rewards_received_after))
(assert
 (= c56e7a029_user_shares_before c56e7a029_user_shares_before))
(assert
 (= c56e7a029_zero_rewards c56e7a029_zero_rewards))
(define-fun report_preconditions () Bool (and (= c56e7a029_user_shares_before c56e7a029_total_shares_before)
     (< 0 c56e7a029_pending_quote_rewards_before)))
(define-fun report_safety () Bool (=> (= c56e7a029_user_rewards_received_after c56e7a029_zero_rewards)
    (=> (and (= c56e7a029_user_shares_before c56e7a029_total_shares_before)
             (< 0 c56e7a029_pending_quote_rewards_before))
        (> c56e7a029_user_rewards_received_after c56e7a029_zero_rewards))))
(define-fun report_effects () Bool (and (= c56e7a029_user_rewards_received_after c56e7a029_zero_rewards)
     (= c56e7a029_user_shares_before c56e7a029_total_shares_before)
     (< 0 c56e7a029_pending_quote_rewards_before)
     (not (> c56e7a029_user_rewards_received_after c56e7a029_zero_rewards))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
