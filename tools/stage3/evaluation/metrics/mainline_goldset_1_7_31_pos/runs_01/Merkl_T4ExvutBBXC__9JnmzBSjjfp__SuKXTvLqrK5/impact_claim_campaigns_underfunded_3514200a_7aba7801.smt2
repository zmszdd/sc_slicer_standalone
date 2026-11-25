; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cde6e236d_actually_received_amount () Int)
(declare-fun cde6e236d_campaign_underfunded () Bool)
(declare-fun cde6e236d_credited_amount () Int)
(declare-fun cde6e236d_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun cde6e236d_transfer_received_amount () Int)
(declare-fun cde6e236d_transfer_requested_amount () Int)
(assert
 (= cde6e236d_actually_received_amount cde6e236d_actually_received_amount))
(assert
 (= cde6e236d_campaign_underfunded cde6e236d_campaign_underfunded))
(assert
 (= cde6e236d_credited_amount cde6e236d_credited_amount))
(assert
 (= cde6e236d_fot_token_is_whitelisted_reward_token cde6e236d_fot_token_is_whitelisted_reward_token))
(assert
 (= cde6e236d_transfer_received_amount cde6e236d_transfer_received_amount))
(assert
 (= cde6e236d_transfer_requested_amount cde6e236d_transfer_requested_amount))
(define-fun report_preconditions () Bool (and cde6e236d_fot_token_is_whitelisted_reward_token
     (< cde6e236d_transfer_received_amount cde6e236d_transfer_requested_amount)))
(define-fun report_safety () Bool (=> cde6e236d_fot_token_is_whitelisted_reward_token
    (= cde6e236d_credited_amount cde6e236d_actually_received_amount)))
(define-fun report_effects () Bool (and cde6e236d_fot_token_is_whitelisted_reward_token
     (not (= cde6e236d_credited_amount cde6e236d_actually_received_amount))
     cde6e236d_campaign_underfunded))
