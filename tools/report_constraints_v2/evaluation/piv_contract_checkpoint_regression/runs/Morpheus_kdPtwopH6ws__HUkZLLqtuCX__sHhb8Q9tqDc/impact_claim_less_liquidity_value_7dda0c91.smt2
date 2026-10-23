; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd1b2535a_attacker_monitors_mempool () Bool)
(declare-fun cd1b2535a_deadline_is_block_timestamp () Bool)
(declare-fun cd1b2535a_liquidity_addition_pending () Bool)
(declare-fun cd1b2535a_liquidity_value_received_matches_assets_provided () Bool)
(declare-fun cd1b2535a_rate_manipulable_by_surrounding_price_changes () Bool)
(assert
 (= cd1b2535a_attacker_monitors_mempool cd1b2535a_attacker_monitors_mempool))
(assert
 (= cd1b2535a_deadline_is_block_timestamp cd1b2535a_deadline_is_block_timestamp))
(assert
 (= cd1b2535a_liquidity_addition_pending cd1b2535a_liquidity_addition_pending))
(assert
 (= cd1b2535a_liquidity_value_received_matches_assets_provided cd1b2535a_liquidity_value_received_matches_assets_provided))
(assert
 (= cd1b2535a_rate_manipulable_by_surrounding_price_changes cd1b2535a_rate_manipulable_by_surrounding_price_changes))
(define-fun report_preconditions () Bool (and cd1b2535a_attacker_monitors_mempool
     cd1b2535a_liquidity_addition_pending
     cd1b2535a_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> (and cd1b2535a_attacker_monitors_mempool
         cd1b2535a_liquidity_addition_pending
         cd1b2535a_deadline_is_block_timestamp)
    (and (not cd1b2535a_rate_manipulable_by_surrounding_price_changes)
         cd1b2535a_liquidity_value_received_matches_assets_provided)))
(define-fun report_effects () Bool (and cd1b2535a_attacker_monitors_mempool
     cd1b2535a_liquidity_addition_pending
     cd1b2535a_deadline_is_block_timestamp
     (not (and (not cd1b2535a_rate_manipulable_by_surrounding_price_changes)
               cd1b2535a_liquidity_value_received_matches_assets_provided))))
