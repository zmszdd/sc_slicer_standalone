; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfbfa56f6_instant_redemption_without_custodian_delay () Bool)
(declare-fun cfbfa56f6_rebalance_callable_by_anyone () Bool)
(declare-fun cfbfa56f6_user_redemption_pending () Bool)
(declare-fun cfbfa56f6_vault_excess_above_buffer () Bool)
(assert
 (= cfbfa56f6_instant_redemption_without_custodian_delay cfbfa56f6_instant_redemption_without_custodian_delay))
(assert
 (= cfbfa56f6_rebalance_callable_by_anyone cfbfa56f6_rebalance_callable_by_anyone))
(assert
 (= cfbfa56f6_user_redemption_pending cfbfa56f6_user_redemption_pending))
(assert
 (= cfbfa56f6_vault_excess_above_buffer cfbfa56f6_vault_excess_above_buffer))
(define-fun report_preconditions () Bool (and cfbfa56f6_rebalance_callable_by_anyone
     cfbfa56f6_user_redemption_pending
     cfbfa56f6_vault_excess_above_buffer))
(define-fun report_safety () Bool (=> (and cfbfa56f6_rebalance_callable_by_anyone
         cfbfa56f6_user_redemption_pending
         cfbfa56f6_vault_excess_above_buffer)
    cfbfa56f6_instant_redemption_without_custodian_delay))
(define-fun report_effects () Bool (and cfbfa56f6_rebalance_callable_by_anyone
     cfbfa56f6_user_redemption_pending
     cfbfa56f6_vault_excess_above_buffer
     (not cfbfa56f6_instant_redemption_without_custodian_delay)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
