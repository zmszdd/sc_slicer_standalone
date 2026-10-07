; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_is_anyone () Bool)
(declare-fun reward_tokens_held () Int)
(declare-fun reward_token_is_pool_token () Bool)
(declare-fun reward_tokens_sent_to_bribe () Int)
(assert
 (= caller_is_anyone caller_is_anyone))
(assert
 (= reward_tokens_held reward_tokens_held))
(assert
 (= reward_token_is_pool_token reward_token_is_pool_token))
(assert
 (= reward_tokens_sent_to_bribe reward_tokens_sent_to_bribe))
(define-fun report_preconditions () Bool (and caller_is_anyone (< 0 reward_tokens_held) reward_token_is_pool_token))
(define-fun report_safety () Bool (=> (and caller_is_anyone (< 0 reward_tokens_held) reward_token_is_pool_token)
    (= 0 reward_tokens_sent_to_bribe)))
(define-fun report_effects () Bool (and caller_is_anyone
     (< 0 reward_tokens_held)
     reward_token_is_pool_token
     (not (= 0 reward_tokens_sent_to_bribe))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
