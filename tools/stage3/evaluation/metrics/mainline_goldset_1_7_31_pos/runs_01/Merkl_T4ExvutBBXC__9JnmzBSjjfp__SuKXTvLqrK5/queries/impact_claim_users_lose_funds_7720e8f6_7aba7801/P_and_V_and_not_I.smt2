; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cde6035a6_actual_received_amount () Int)
(declare-fun cde6035a6_credited_balance_amount () Int)
(declare-fun cde6035a6_fot_token_is_whitelisted () Bool)
(declare-fun cde6035a6_transfer_received_amount () Int)
(declare-fun cde6035a6_transfer_requested_amount () Int)
(declare-fun cde6035a6_users_lose_funds_observed () Bool)
(assert
 (= cde6035a6_actual_received_amount cde6035a6_actual_received_amount))
(assert
 (= cde6035a6_credited_balance_amount cde6035a6_credited_balance_amount))
(assert
 (= cde6035a6_fot_token_is_whitelisted cde6035a6_fot_token_is_whitelisted))
(assert
 (= cde6035a6_transfer_received_amount cde6035a6_transfer_received_amount))
(assert
 (= cde6035a6_transfer_requested_amount cde6035a6_transfer_requested_amount))
(assert
 (= cde6035a6_users_lose_funds_observed cde6035a6_users_lose_funds_observed))
(define-fun report_preconditions () Bool (and cde6035a6_fot_token_is_whitelisted
     (< cde6035a6_transfer_received_amount cde6035a6_transfer_requested_amount)))
(define-fun report_safety () Bool (=> cde6035a6_fot_token_is_whitelisted
    (= cde6035a6_credited_balance_amount cde6035a6_actual_received_amount)))
(define-fun report_effects () Bool (and cde6035a6_fot_token_is_whitelisted
     (not (= cde6035a6_credited_balance_amount cde6035a6_actual_received_amount))
     cde6035a6_users_lose_funds_observed))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
