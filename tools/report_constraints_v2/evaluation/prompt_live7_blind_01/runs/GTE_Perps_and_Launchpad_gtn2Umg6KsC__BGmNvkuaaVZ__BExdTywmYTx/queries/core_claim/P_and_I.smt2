; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun user_sent_both_tokens () Bool)
(declare-fun swap_completed_with_one_token_unprocessed () Bool)
(assert
 (= user_sent_both_tokens user_sent_both_tokens))
(assert
 (= swap_completed_with_one_token_unprocessed swap_completed_with_one_token_unprocessed))
(define-fun report_preconditions () Bool user_sent_both_tokens)
(define-fun report_safety () Bool (=> user_sent_both_tokens (not swap_completed_with_one_token_unprocessed)))
(define-fun report_effects () Bool (and user_sent_both_tokens
     (not (not swap_completed_with_one_token_unprocessed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
