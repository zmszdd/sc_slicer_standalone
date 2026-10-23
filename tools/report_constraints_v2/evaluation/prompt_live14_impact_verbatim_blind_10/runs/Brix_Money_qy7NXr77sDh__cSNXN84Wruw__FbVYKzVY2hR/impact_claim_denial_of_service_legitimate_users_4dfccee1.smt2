; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5c45b87f_rebalance_callable_by_anyone () Bool)
(declare-fun c5c45b87f_redemption_completes () Bool)
(declare-fun c5c45b87f_redemption_denied () Bool)
(declare-fun c5c45b87f_user_redemption_pending () Bool)
(declare-fun c5c45b87f_vault_excess_above_buffer () Bool)
(assert
 (= c5c45b87f_rebalance_callable_by_anyone c5c45b87f_rebalance_callable_by_anyone))
(assert
 (= c5c45b87f_redemption_completes c5c45b87f_redemption_completes))
(assert
 (= c5c45b87f_redemption_denied c5c45b87f_redemption_denied))
(assert
 (= c5c45b87f_user_redemption_pending c5c45b87f_user_redemption_pending))
(assert
 (= c5c45b87f_vault_excess_above_buffer c5c45b87f_vault_excess_above_buffer))
(define-fun report_preconditions () Bool (and c5c45b87f_rebalance_callable_by_anyone
     c5c45b87f_user_redemption_pending
     c5c45b87f_vault_excess_above_buffer))
(define-fun report_safety () Bool (=> (and c5c45b87f_rebalance_callable_by_anyone
         c5c45b87f_user_redemption_pending
         c5c45b87f_vault_excess_above_buffer)
    (and c5c45b87f_redemption_completes (not c5c45b87f_redemption_denied))))
(define-fun report_effects () Bool (and c5c45b87f_rebalance_callable_by_anyone
     c5c45b87f_user_redemption_pending
     c5c45b87f_vault_excess_above_buffer
     (not (and c5c45b87f_redemption_completes (not c5c45b87f_redemption_denied)))))
