; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0e196f0a_actual_token_holdings () Int)
(declare-fun c0e196f0a_fot_token_is_whitelisted () Bool)
(declare-fun c0e196f0a_late_withdrawer_loss_occurs () Bool)
(declare-fun c0e196f0a_recorded_creator_balance_total () Int)
(declare-fun c0e196f0a_transfer_amount_received () Int)
(declare-fun c0e196f0a_transfer_amount_requested () Int)
(assert
 (= c0e196f0a_actual_token_holdings c0e196f0a_actual_token_holdings))
(assert
 (= c0e196f0a_fot_token_is_whitelisted c0e196f0a_fot_token_is_whitelisted))
(assert
 (= c0e196f0a_late_withdrawer_loss_occurs c0e196f0a_late_withdrawer_loss_occurs))
(assert
 (= c0e196f0a_recorded_creator_balance_total c0e196f0a_recorded_creator_balance_total))
(assert
 (= c0e196f0a_transfer_amount_received c0e196f0a_transfer_amount_received))
(assert
 (= c0e196f0a_transfer_amount_requested c0e196f0a_transfer_amount_requested))
(define-fun report_preconditions () Bool (and c0e196f0a_fot_token_is_whitelisted
     (< c0e196f0a_transfer_amount_received c0e196f0a_transfer_amount_requested)))
(define-fun report_safety () Bool (=> c0e196f0a_fot_token_is_whitelisted
    (<= c0e196f0a_recorded_creator_balance_total
        c0e196f0a_actual_token_holdings)))
(define-fun report_effects () Bool (and c0e196f0a_fot_token_is_whitelisted
     (not (<= c0e196f0a_recorded_creator_balance_total
              c0e196f0a_actual_token_holdings))
     c0e196f0a_late_withdrawer_loss_occurs))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
