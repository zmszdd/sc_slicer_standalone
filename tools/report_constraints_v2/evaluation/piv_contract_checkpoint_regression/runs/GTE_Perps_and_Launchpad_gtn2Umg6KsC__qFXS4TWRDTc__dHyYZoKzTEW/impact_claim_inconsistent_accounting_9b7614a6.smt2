; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7c027d93_fake_token_approved () Bool)
(declare-fun c7c027d93_pending_quote_user_view () Int)
(declare-fun c7c027d93_pending_rewards_fake_token_key () Int)
(declare-fun c7c027d93_pending_rewards_real_quote_key () Int)
(declare-fun c7c027d93_pool_total_shares () Int)
(assert
 (= c7c027d93_fake_token_approved c7c027d93_fake_token_approved))
(assert
 (= c7c027d93_pending_quote_user_view c7c027d93_pending_quote_user_view))
(assert
 (= c7c027d93_pending_rewards_fake_token_key c7c027d93_pending_rewards_fake_token_key))
(assert
 (= c7c027d93_pending_rewards_real_quote_key c7c027d93_pending_rewards_real_quote_key))
(assert
 (= c7c027d93_pool_total_shares c7c027d93_pool_total_shares))
(define-fun report_preconditions () Bool (and (< 0 c7c027d93_pool_total_shares) c7c027d93_fake_token_approved))
(define-fun report_safety () Bool (=> (and (< 0 c7c027d93_pool_total_shares) c7c027d93_fake_token_approved)
    (and (= c7c027d93_pending_quote_user_view
            c7c027d93_pending_rewards_real_quote_key)
         (= 0 c7c027d93_pending_rewards_fake_token_key))))
(define-fun report_effects () Bool (and (< 0 c7c027d93_pool_total_shares)
     c7c027d93_fake_token_approved
     (not (and (= c7c027d93_pending_quote_user_view
                  c7c027d93_pending_rewards_real_quote_key)
               (= 0 c7c027d93_pending_rewards_fake_token_key)))))
