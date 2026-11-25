; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfc216fb6_actual_received_amount () Int)
(declare-fun cfc216fb6_credited_balance () Int)
(declare-fun cfc216fb6_fot_token_whitelisted_flag () Bool)
(declare-fun cfc216fb6_late_withdrawer_loss_severity () Int)
(declare-fun cfc216fb6_transfer_received_amount () Int)
(declare-fun cfc216fb6_transfer_requested_amount () Int)
(assert
 (= cfc216fb6_actual_received_amount cfc216fb6_actual_received_amount))
(assert
 (= cfc216fb6_credited_balance cfc216fb6_credited_balance))
(assert
 (= cfc216fb6_fot_token_whitelisted_flag cfc216fb6_fot_token_whitelisted_flag))
(assert
 (= cfc216fb6_late_withdrawer_loss_severity cfc216fb6_late_withdrawer_loss_severity))
(assert
 (= cfc216fb6_transfer_received_amount cfc216fb6_transfer_received_amount))
(assert
 (= cfc216fb6_transfer_requested_amount cfc216fb6_transfer_requested_amount))
(define-fun report_preconditions () Bool (and cfc216fb6_fot_token_whitelisted_flag
     (< cfc216fb6_transfer_received_amount cfc216fb6_transfer_requested_amount)))
(define-fun report_safety () Bool (=> cfc216fb6_fot_token_whitelisted_flag
    (= cfc216fb6_credited_balance cfc216fb6_actual_received_amount)))
(define-fun report_effects () Bool (and cfc216fb6_fot_token_whitelisted_flag
     (not (= cfc216fb6_credited_balance cfc216fb6_actual_received_amount))
     (< 0 cfc216fb6_late_withdrawer_loss_severity)))
