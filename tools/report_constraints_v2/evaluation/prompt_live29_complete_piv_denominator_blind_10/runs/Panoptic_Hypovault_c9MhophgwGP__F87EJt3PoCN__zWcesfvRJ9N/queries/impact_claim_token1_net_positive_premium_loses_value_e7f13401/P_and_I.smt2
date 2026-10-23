; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c76980cf1_nav_reflects_correct_premium () Bool)
(declare-fun c76980cf1_token1_long_premium_usdc () Int)
(declare-fun c76980cf1_token1_nav_loses_value () Bool)
(declare-fun c76980cf1_token1_net_premium_positive () Bool)
(declare-fun c76980cf1_token1_short_premium_usdc () Int)
(assert
 (= c76980cf1_nav_reflects_correct_premium c76980cf1_nav_reflects_correct_premium))
(assert
 (= c76980cf1_token1_long_premium_usdc c76980cf1_token1_long_premium_usdc))
(assert
 (= c76980cf1_token1_nav_loses_value c76980cf1_token1_nav_loses_value))
(assert
 (= c76980cf1_token1_net_premium_positive c76980cf1_token1_net_premium_positive))
(assert
 (= c76980cf1_token1_short_premium_usdc c76980cf1_token1_short_premium_usdc))
(define-fun report_preconditions () Bool (and (> c76980cf1_token1_short_premium_usdc c76980cf1_token1_long_premium_usdc)
     c76980cf1_token1_net_premium_positive))
(define-fun report_safety () Bool (=> c76980cf1_token1_nav_loses_value
    (=> c76980cf1_token1_net_premium_positive
        c76980cf1_nav_reflects_correct_premium)))
(define-fun report_effects () Bool (and c76980cf1_token1_nav_loses_value
     c76980cf1_token1_net_premium_positive
     (not c76980cf1_nav_reflects_correct_premium)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
