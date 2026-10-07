; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_is_authorized () Bool)
(declare-fun rebalance_callable_by_anyone () Bool)
(declare-fun excess_liquidity_present () Bool)
(declare-fun target_buffer_configured () Bool)
(declare-fun fast_redemption_disabled () Bool)
(assert
 (= caller_is_authorized caller_is_authorized))
(assert
 (= rebalance_callable_by_anyone rebalance_callable_by_anyone))
(assert
 (= excess_liquidity_present excess_liquidity_present))
(assert
 (= target_buffer_configured target_buffer_configured))
(assert
 (= fast_redemption_disabled fast_redemption_disabled))
(define-fun report_preconditions () Bool (and rebalance_callable_by_anyone
     excess_liquidity_present
     target_buffer_configured))
(define-fun report_safety () Bool (=> (and rebalance_callable_by_anyone
         excess_liquidity_present
         target_buffer_configured)
    (or caller_is_authorized (not fast_redemption_disabled))))
(define-fun report_effects () Bool (and rebalance_callable_by_anyone
     excess_liquidity_present
     target_buffer_configured
     (not (or caller_is_authorized (not fast_redemption_disabled)))))
